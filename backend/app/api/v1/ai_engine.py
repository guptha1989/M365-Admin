"""
AI Engine API Router — LLM Key Vault & Recommendation Viewer

BOUNDARY:
  This router handles TWO distinct concerns:
  1. LLM Key Vault   → Store/retrieve encrypted API keys for recommendation generation
  2. Recommendation Viewer → Expose the AI-generated recommendation feed (read-only)

  Workflow EXECUTION (approve/reject/remediate) is handled exclusively by
  action_engine.py (Python → Microsoft Graph REST API). This router does NOT
  execute any Graph API calls or trigger workflows directly.

  Role Summary:
    ┌─ /keys    ──→ AES-256 LLM key vault (Python: SQLAlchemy + Fernet)
    ├─ /recommendations ──→ Read DB-backed AI recommendation feed
    └─ /execute-recommendation ──→ Delegates to action_engine (Python only)
"""
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.security import get_current_user, require_roles
from app.core.database import get_db
from app.core.vault import encrypt_key, decrypt_key
from app.db.models import AIKeyConfig, AutomationPolicy, AIRecommendation, APIIntegrationConfig

router = APIRouter()


class KeyConfigRequest(BaseModel):
    provider: str  # openai, anthropic, local, gemini, azure_openai
    api_key: str
    endpoint_url: Optional[str] = None
    model_name: Optional[str] = "gpt-4o"


class PolicyRuleRequest(BaseModel):
    policy_name: str
    category: str
    trigger_condition: str  # e.g. "If Intune device flags CVE-2026-X"
    action_command: str     # e.g. "initiate_conditional_access_block"
    execution_mode: str     # MANUAL, SEMI_AUTOMATED, AUTONOMOUS


# ── LLM KEY VAULT ─────────────────────────────────────────────────────────────

@router.post("/keys", summary="Store LLM API Keys in AES-256 Vault (for Recommendation Generation)")
def store_llm_key(
    req: KeyConfigRequest,
    db: Session = Depends(get_db),
    user: dict = Depends(require_roles(["GlobalAdmin"]))
):
    """
    Encrypts and stores LLM API keys in SQL Express database (AES-256 Fernet Vault).

    These keys are used EXCLUSIVELY by ai_orchestrator._generate_llm_narrative()
    to generate recommendation description text. They are NOT used for data
    pulling or workflow execution — those are Python-only.
    """
    encrypted = encrypt_key(req.api_key)
    provider_name = req.provider.lower()
    config = db.query(AIKeyConfig).filter(AIKeyConfig.provider == provider_name).first()
    if not config:
        config = AIKeyConfig(
            provider=provider_name,
            encrypted_key=encrypted,
            endpoint_url=req.endpoint_url,
            model_name=req.model_name,
            is_active=True
        )
        db.add(config)
    else:
        config.encrypted_key = encrypted
        config.endpoint_url = req.endpoint_url
        config.model_name = req.model_name
        config.is_active = True

    # Sync with APIIntegrationConfig (unified provider registry)
    integration = db.query(APIIntegrationConfig).filter(
        APIIntegrationConfig.api_category == "LLM",
        APIIntegrationConfig.provider_name == provider_name
    ).first()
    if integration:
        integration.encrypted_key = encrypted
        integration.model_name = req.model_name
        integration.endpoint_url = req.endpoint_url
        integration.is_active = True
    else:
        db.add(APIIntegrationConfig(
            api_category="LLM",
            provider_name=provider_name,
            encrypted_key=encrypted,
            model_name=req.model_name or "gpt-4o",
            endpoint_url=req.endpoint_url,
            priority=1,
            is_active=True
        ))

    db.commit()
    return {
        "status": "Stored in AES-256 Vault",
        "provider": req.provider,
        "encrypted": True,
        "purpose": "Recommendation narrative generation only — not used for data pulling or workflows"
    }


@router.get("/keys", summary="List Active LLM Providers (Recommendation Generation Only)")
def list_llm_keys(
    db: Session = Depends(get_db),
    user: dict = Depends(require_roles(["GlobalAdmin"]))
):
    """List active LLM providers stored in the vault (masked keys)."""
    configs = db.query(AIKeyConfig).all()
    return [
        {
            "provider": c.provider,
            "endpoint_url": c.endpoint_url,
            "model_name": c.model_name,
            "is_active": c.is_active,
            "has_key": bool(c.encrypted_key),
            "purpose": "LLM recommendation narrative generation only"
        }
        for c in configs
    ]


# ── POLICY TRIGGER MANAGEMENT (Python) ────────────────────────────────────────

@router.post("/policy", summary="Define If/Then Trigger Policy (Python Governance Rule)")
def create_policy_trigger(
    req: PolicyRuleRequest,
    db: Session = Depends(get_db),
    user: dict = Depends(require_roles(["GlobalAdmin"]))
):
    """
    Define If/Then trigger policies for automated governance.
    These policies are evaluated by action_engine.py (Python) — not by the LLM.
    """
    policy = AutomationPolicy(
        policy_name=req.policy_name,
        category=req.category,
        phase_level=req.execution_mode,
        description=f"TRIGGER: {req.trigger_condition} => ACTION: {req.action_command}",
        is_enabled=True
    )
    db.add(policy)
    db.commit()
    return {
        "status": "Policy Created",
        "policy_id": policy.id,
        "execution_mode": req.execution_mode,
        "execution_layer": "Python:ActionEngine → MicrosoftGraphRESTAPI"
    }


# ── RECOMMENDATION VIEWER (Read-only — LLM-generated text + Python-determined facts) ──

@router.get("/recommendations", summary="AI Recommendation Dashboard (DB-backed)")
def get_ai_recommendations(
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """
    Returns the DB-backed AI recommendation feed.

    Recommendations are generated by ai_orchestrator.generate_recommendations():
    - Facts determined by Python (Microsoft Graph API data)
    - Narrative text written by LLM (or built-in rule engine if no LLM key)
    - Workflow execution handled by action_engine (Python only)
    """
    recs = db.query(AIRecommendation).all()
    return [
        {
            "id": r.id,
            "title": r.title,
            "category": r.category,
            "recommendation_type": r.recommendation_type,
            "benefit_category": r.benefit_category,
            "description": r.description,
            "security_benefit": r.security_benefit,
            "impact_level": r.impact_level,
            "potential_savings_usd": r.potential_savings_usd,
            "target_object": r.target_object,
            "status": r.status,
            "is_resolved": r.is_resolved,
            "action_type": r.action_type,
            "executed_by": r.executed_by,
            "executed_at": r.executed_at.isoformat() if r.executed_at else None
        }
        for r in recs
    ]


# ── RECOMMENDATION EXECUTION (Delegates to Python Action Engine) ───────────────

@router.post(
    "/execute-recommendation/{recommendation_id}",
    summary="Execute Approved Recommendation via Python (Microsoft Graph REST API)"
)
def execute_recommendation(
    recommendation_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(require_roles(["GlobalAdmin"]))
):
    """
    Executes an approved AI recommendation action.

    EXECUTION LAYER: Python only (action_engine → api_execution_service → Microsoft Graph REST API).
    The LLM is NOT involved in execution — it only generated the recommendation text.
    """
    from app.services.action_engine import action_engine
    user_upn = user.get("preferred_username", "admin@contoso.com")

    result = action_engine.approve_action(db, recommendation_id, user_upn=user_upn)
    result["execution_layer"] = "Python:ActionEngine → MicrosoftGraphRESTAPI"
    result["llm_involvement"] = "None — LLM was used only for recommendation text generation"
    return result
