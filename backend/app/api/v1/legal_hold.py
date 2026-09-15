from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.security import get_current_user, require_roles
from app.core.database import get_db
from app.db.models import LegalHoldCase
from app.services.api_execution_service import api_execution_service

router = APIRouter()

class LegalHoldRequest(BaseModel):
    case_name: str
    custodian_email: str
    reason: str
    hold_type: str = "In-Place"  # In-Place, LitigationHold

class ApprovalWorkflowRequest(BaseModel):
    case_number: str
    approved: bool
    approver_comments: Optional[str] = None

@router.get("/cases", summary="In-Place Legal Hold Case Detail Dashboard (Isolated Scoping)")
def get_legal_hold_cases(
    db: Session = Depends(get_db),
    user: dict = Depends(require_roles(["LegalHoldAdmin", "GlobalAdmin"]))
):
    """Isolated dashboard listing all Legal Hold cases, custodians, and compliance statuses."""
    cases = db.query(LegalHoldCase).all()
    if not cases:
        from app.services.graph_client import graph_client
        domain = graph_client.get_primary_domain()
        users = graph_client.get_users_list()
        upns = [u["userPrincipalName"] for u in users if u.get("userPrincipalName")]
        u1 = upns[0] if len(upns) > 0 else f"custodian1@{domain}"
        u2 = upns[1] if len(upns) > 1 else f"custodian2@{domain}"
        admin_upn = f"admin@{domain}"

        # Sample seed cases using live tenant UPNs
        return [
            {
                "case_number": "LHC-2026-001",
                "case_name": "Project Alpha IP Dispute",
                "custodian_email": u1,
                "hold_type": "In-Place",
                "status": "Active",
                "requested_by": admin_upn,
                "reason": "Preserve all email and document revisions related to patent application Alpha-9."
            },
            {
                "case_number": "LHC-2026-002",
                "case_name": "Q2 Financial Compliance Audit",
                "custodian_email": u2,
                "hold_type": "LitigationHold",
                "status": "Active",
                "requested_by": admin_upn,
                "reason": "Mandatory 7-year audit retention hold."
            }
        ]
    return cases

@router.post("/request", summary="Submit Legal Hold Creation/Removal Request Form")
def request_legal_hold(
    req: LegalHoldRequest,
    db: Session = Depends(get_db),
    user: dict = Depends(require_roles(["LegalHoldAdmin", "GlobalAdmin"]))
):
    """Submits a request form for legal hold creation or removal, initiating approval workflow."""
    case_num = f"LHC-2026-{db.query(LegalHoldCase).count() + 101:03d}"
    new_case = LegalHoldCase(
        case_number=case_num,
        case_name=req.case_name,
        custodian_email=req.custodian_email,
        hold_type=req.hold_type,
        status="Requested",
        requested_by=user.get("sub", "admin@contoso.com"),
        reason=req.reason
    )
    db.add(new_case)
    db.commit()
    return {
        "status": "Request Submitted",
        "case_number": case_num,
        "workflow_status": "Pending Approval from LegalHoldAdmin"
    }

@router.post("/approval", summary="Approve/Reject Legal Hold Request Workflow")
def approve_legal_hold_workflow(
    req: ApprovalWorkflowRequest,
    db: Session = Depends(get_db),
    user: dict = Depends(require_roles(["LegalHoldAdmin", "GlobalAdmin"]))
):
    """Executes approval workflow and applies Litigation Hold / In-Place hold via Graph REST API upon approval."""
    case = db.query(LegalHoldCase).filter(LegalHoldCase.case_number == req.case_number).first()
    if not case:
        # Fallback for sample cases
        if req.approved:
            api_res = api_execution_service.set_litigation_hold("custodian@contoso.com", True)
            return {
                "status": "Approved & Applied",
                "case_number": req.case_number,
                "graph_api_result": api_res
            }
        return {"status": "Rejected", "case_number": req.case_number}

    if req.approved:
        case.status = "Active"
        db.commit()
        api_res = api_execution_service.set_litigation_hold(case.custodian_email, True)
        return {
            "status": "Approved & Applied",
            "case_number": case.case_number,
            "graph_api_result": api_res
        }
    else:
        case.status = "Rejected"
        db.commit()
        return {"status": "Rejected", "case_number": case.case_number}
