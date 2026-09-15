from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.security import get_current_user, require_roles
from app.core.database import get_db
from app.db.models import LegalHoldCase

router = APIRouter()

# In-memory / persistent assignment store for requests
ASSIGNMENT_STORE = {}
CUSTOM_REQUESTS = []

class RequestAssignModel(BaseModel):
    request_id: str
    assignee: str
    notes: Optional[str] = None

class RequestStatusUpdateModel(BaseModel):
    request_id: str
    status: str
    comments: Optional[str] = None

class CreateCustomRequestModel(BaseModel):
    title: str
    request_type: str
    category: Optional[str] = "GOVERNANCE"
    priority: Optional[str] = "MEDIUM"
    details: Optional[str] = None
    assignee: Optional[str] = "unassigned@contoso.com"

@router.post("/create-custom", summary="Create Separate Request for Recommendation or Task")
def create_custom_request(
    req: CreateCustomRequestModel,
    user: dict = Depends(require_roles(["GlobalAdmin", "LegalHoldAdmin", "SecurityAdmin"]))
):
    """Creates a dedicated request ticket for a specific recommendation or administrative task."""
    import datetime
    req_id = f"REQ-REC-{len(CUSTOM_REQUESTS) + 501:03d}"
    
    new_req = {
        "request_id": req_id,
        "title": req.title,
        "source": "📝 Recommendation / Admin Request",
        "category": req.category or "GOVERNANCE",
        "request_type": req.request_type,
        "impact": "Action Required",
        "assignee": req.assignee or "admin@contoso.com",
        "status": "Pending Approval",
        "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "priority": req.priority or "MEDIUM",
        "details": req.details or ""
    }
    CUSTOM_REQUESTS.append(new_req)
    ASSIGNMENT_STORE[req_id] = {
        "assignee": new_req["assignee"],
        "status": new_req["status"]
    }
    
    return {
        "status": "Success",
        "message": f"Request '{req_id}' created successfully for '{req.title}'.",
        "request": new_req
    }

@router.get("/all", summary="Centralized Requests Feed (AI Recommendations & Legal Hold Requests)")
def get_all_requests(
    db: Session = Depends(get_db),
    user: dict = Depends(require_roles(["GlobalAdmin", "LegalHoldAdmin", "SecurityAdmin"]))
):
    """Centralized location aggregating automatically created AI recommendation requests, custom recommendation requests, and manual legal hold requests."""
    from app.services.ai_orchestrator import ai_orchestrator
    
    requests_list = []

    # 1. Custom Recommendation Requests
    for creq in CUSTOM_REQUESTS:
        req_id = creq["request_id"]
        assigned_to = ASSIGNMENT_STORE.get(req_id, {}).get("assignee", creq["assignee"])
        req_status = ASSIGNMENT_STORE.get(req_id, {}).get("status", creq["status"])
        
        item = dict(creq)
        item["assignee"] = assigned_to
        item["status"] = req_status
        requests_list.append(item)

    # 2. Fetch AI recommendations (each becomes a separate auto-created request)
    try:
        ai_recs = ai_orchestrator.generate_recommendations(db)
    except Exception as e:
        from app.db.models import AIRecommendation
        ai_recs_db = db.query(AIRecommendation).all()
        ai_recs = [{"id": r.id, "title": r.title, "description": r.description, "category": r.category, "potential_savings_usd": r.potential_savings_usd} for r in ai_recs_db]

    # Map AI recommendations as auto-created requests
    for rec in ai_recs:
        req_id = f"REQ-AI-{rec.get('id', '101')}"
        assigned_to = ASSIGNMENT_STORE.get(req_id, {}).get("assignee", "ai_governance@contoso.com")
        req_status = ASSIGNMENT_STORE.get(req_id, {}).get("status", "Auto-Created (Pending Approval)")
        
        requests_list.append({
            "request_id": req_id,
            "title": rec.get("title", "AI Governance Recommendation"),
            "source": "🤖 AI Auto-Generated",
            "category": rec.get("category", "COST_SAVING"),
            "request_type": "AI Recommendation",
            "impact": f"+${rec.get('potential_savings_usd', 0)}/yr savings" if rec.get('potential_savings_usd') else "Security Hardening",
            "assignee": assigned_to,
            "status": req_status,
            "created_at": "2026-09-15 08:00:00",
            "priority": "HIGH" if rec.get("category") == "SECURITY" else "MEDIUM",
            "details": rec.get("description", "")
        })

    # 3. Fetch Legal Hold cases & requests from DB
    lh_cases = db.query(LegalHoldCase).order_by(LegalHoldCase.created_at.desc()).all()
    for case in lh_cases:
        req_id = f"REQ-LH-{case.case_number}"
        assigned_to = ASSIGNMENT_STORE.get(req_id, {}).get("assignee", case.requested_by or "legal_compliance@contoso.com")
        req_status = ASSIGNMENT_STORE.get(req_id, {}).get("status", case.status)

        requests_list.append({
            "request_id": req_id,
            "title": f"Legal Hold: {case.case_name}",
            "source": "📝 Manual Legal Hold Request",
            "category": "COMPLIANCE",
            "request_type": "Legal Hold " + case.hold_type,
            "impact": f"Custodians: {case.custodian_email or 'All Case Users'}",
            "assignee": assigned_to,
            "status": req_status,
            "created_at": case.created_at.strftime("%Y-%m-%d %H:%M:%S") if case.created_at else "2026-09-15 09:00:00",
            "priority": "CRITICAL" if "Active" in case.status else "NORMAL",
            "details": f"Reason: {case.reason or ''} | Keywords: {case.keywords or 'N/A'}"
        })

    return requests_list

@router.post("/assign", summary="Assign or Re-assign Request to Administrator")
def assign_request(
    req: RequestAssignModel,
    user: dict = Depends(require_roles(["GlobalAdmin", "LegalHoldAdmin", "SecurityAdmin"]))
):
    """Assigns or re-assigns a request ticket to an administrator or team member."""
    if req.request_id not in ASSIGNMENT_STORE:
        ASSIGNMENT_STORE[req.request_id] = {}
    
    ASSIGNMENT_STORE[req.request_id]["assignee"] = req.assignee
    if req.notes:
        ASSIGNMENT_STORE[req.request_id]["notes"] = req.notes

    return {
        "status": "Success",
        "message": f"Request '{req.request_id}' successfully assigned to '{req.assignee}'.",
        "request_id": req.request_id,
        "assignee": req.assignee
    }

@router.post("/update-status", summary="Update Request Status (Approve/Reject/In Progress/Closed)")
def update_request_status(
    req: RequestStatusUpdateModel,
    db: Session = Depends(get_db),
    user: dict = Depends(require_roles(["GlobalAdmin", "LegalHoldAdmin", "SecurityAdmin"]))
):
    """Updates status for a request ticket."""
    if req.request_id not in ASSIGNMENT_STORE:
        ASSIGNMENT_STORE[req.request_id] = {}
    
    ASSIGNMENT_STORE[req.request_id]["status"] = req.status
    if req.comments:
        ASSIGNMENT_STORE[req.request_id]["comments"] = req.comments

    # If it's a Legal Hold request, update DB status
    if req.request_id.startswith("REQ-LH-"):
        case_num = req.request_id.replace("REQ-LH-", "")
        case = db.query(LegalHoldCase).filter(LegalHoldCase.case_number == case_num).first()
        if case:
            case.status = req.status
            db.commit()

    return {
        "status": "Success",
        "message": f"Request '{req.request_id}' status updated to '{req.status}'.",
        "request_id": req.request_id,
        "new_status": req.status
    }

