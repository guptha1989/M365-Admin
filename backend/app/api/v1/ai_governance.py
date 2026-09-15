from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from app.core.database import get_db
from app.core.security import get_current_user, encrypt_api_key, decrypt_api_key
from app.db.models import AIKeyConfig, AIRecommendation, AutomationPolicy, APIIntegrationConfig
from app.db.schemas import (
    AIKeySaveSchema,
    AIRecommendationSchema,
    ExportRequestSchema,
    AutomationPolicySchema,
    AutomationPolicyCreateSchema
)
from app.services.ai_orchestrator import ai_orchestrator
from app.services.export_service import export_service

router = APIRouter()

@router.get("/recommendations", response_model=List[AIRecommendationSchema], summary="Fetch Centralized AI Recommendation Feed")
def get_ai_recommendations(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Retrieve AI recommendations generated across license optimization, security, and storage."""
    recs = db.query(AIRecommendation).all()
    if not recs:
        ai_orchestrator.generate_recommendations(db)
        recs = db.query(AIRecommendation).all()
    return recs

@router.post("/recommendations/refresh", summary="Trigger On-Demand AI Recommendation Refresh")
def refresh_ai_recommendations(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Re-analyze M365 environment and update AI recommendation insights."""
    results = ai_orchestrator.generate_recommendations(db)
    return {"status": "SUCCESS", "recommendations_generated": len(results)}

@router.post("/config/keys", summary="Save External LLM API Keys (Encrypted)")
def save_llm_api_key(
    payload: AIKeySaveSchema,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Secure configuration page for entering API keys (OpenAI, Anthropic, local models).
    Keys are encrypted before storing in SQL Express database.
    """
    enc_key = encrypt_api_key(payload.api_key)
    provider = payload.provider.lower()
    existing = db.query(AIKeyConfig).filter(AIKeyConfig.provider == provider).first()
    if existing:
        existing.encrypted_key = enc_key
        existing.model_name = payload.model_name
        existing.endpoint_url = payload.endpoint_url
        existing.is_active = True
    else:
        new_config = AIKeyConfig(
            provider=provider,
            encrypted_key=enc_key,
            model_name=payload.model_name,
            endpoint_url=payload.endpoint_url,
            is_active=True
        )
        db.add(new_config)

    # Sync to APIIntegrationConfig
    integration = db.query(APIIntegrationConfig).filter(
        APIIntegrationConfig.api_category == "LLM",
        APIIntegrationConfig.provider_name == provider
    ).first()
    if integration:
        integration.encrypted_key = enc_key
        integration.model_name = payload.model_name
        integration.endpoint_url = payload.endpoint_url
        integration.is_active = True
    else:
        db.add(APIIntegrationConfig(
            api_category="LLM",
            provider_name=provider,
            encrypted_key=enc_key,
            model_name=payload.model_name or "gpt-4o",
            endpoint_url=payload.endpoint_url,
            priority=1,
            is_active=True
        ))

    db.commit()

    return {"status": "SUCCESS", "provider": payload.provider, "message": f"Encrypted API key saved for {payload.provider}."}

@router.get("/config/keys", summary="List Configured LLM Providers")
def list_llm_providers(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List configured LLM providers (masking sensitive key data)."""
    configs = db.query(AIKeyConfig).all()
    return [
        {
            "provider": c.provider,
            "model_name": c.model_name,
            "is_active": c.is_active,
            "has_key": bool(c.encrypted_key),
            "endpoint_url": c.endpoint_url
        }
        for c in configs
    ]

@router.post("/recommendations/{recommendation_id}/approve", summary="Phase 2 Action Approval")
def approve_recommendation_action(
    recommendation_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Approve execution of a recommended remediation action (Phase 2 Semi-Automated Mode)."""
    from app.services.action_engine import action_engine
    user_upn = current_user.get("preferred_username", "admin@contoso.com")
    result = action_engine.approve_action(db, recommendation_id, user_upn=user_upn)
    return result

@router.post("/recommendations/{recommendation_id}/reject", summary="Phase 2 Action Rejection")
def reject_recommendation_action(
    recommendation_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Dismiss or reject a recommended remediation action."""
    from app.services.action_engine import action_engine
    user_upn = current_user.get("preferred_username", "admin@contoso.com")
    result = action_engine.reject_action(db, recommendation_id, user_upn=user_upn)
    return result

@router.get("/policies", response_model=List[AutomationPolicySchema], summary="List Tenant Policy Rules & Conditions")
def list_automation_policies(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List configured tenant policies for all dashboards and reports."""
    policies = db.query(AutomationPolicy).all()
    
    # Comprehensive default policies covering every dashboard & report module
    default_defs = [
        {"category": "mailbox", "name": "Mailbox Quota & Litigation Hold Policy", "mode": "PHASE_2_SEMI_AUTOMATED", "enabled": True, "desc": "Enforce 45GB storage alert threshold and auto litigation hold for VIP accounts.", "criteria": '{"storage_limit_gb": 45, "auto_litigation_hold_vip": true, "archive_stale_days": 180}'},
        {"category": "exchange_rules", "name": "External Auto-Forwarding Exfiltration Prevention", "mode": "PHASE_3_FULLY_AUTOMATED", "enabled": True, "desc": "Purge unauthorized inbox rules forwarding emails to external domains.", "criteria": '{"block_external_forwarding": true, "notify_sec_ops": true}'},
        {"category": "failed_updates", "name": "Workstation Update Compliance & Defender Isolation", "mode": "PHASE_2_SEMI_AUTOMATED", "enabled": True, "desc": "Flag devices failing updates over 3 consecutive attempts for Defender isolation.", "criteria": '{"max_failed_attempts": 3, "auto_isolate_vulnerable": true}'},
        {"category": "inactive_users", "name": "Inactive Account License Reclaim Policy", "mode": "PHASE_3_FULLY_AUTOMATED", "enabled": True, "desc": "Reclaim licenses for users inactive > 60 days and downgrade to F3/unlicensed.", "criteria": '{"inactive_days_threshold": 60, "action": "downgrade_f3", "grace_period_days": 7}'},
        {"category": "licenses", "name": "License Consumption & Over-provisioning Warning", "mode": "PHASE_1_REPORTING", "enabled": True, "desc": "Alert admin when unassigned SKU count exceeds warning limits.", "criteria": '{"warning_unused_seats": 5, "utilization_target_pct": 95}'},
        {"category": "risky_users", "name": "Azure AD High-Risk User Remediation", "mode": "PHASE_3_FULLY_AUTOMATED", "enabled": True, "desc": "Trigger Conditional Access block for users flagged with HIGH risk severity.", "criteria": '{"risk_level_trigger": "HIGH", "require_mfa_reset": true}'},
        {"category": "mailflow", "name": "Mailflow Outbound Exfiltration & Surge Anomaly", "mode": "PHASE_2_SEMI_AUTOMATED", "enabled": True, "desc": "Detect sudden spikes in outbound email volume (>2000 msgs/hr).", "criteria": '{"hourly_limit_sent": 2000, "outbound_size_limit_mb": 50}'},
        {"category": "connectors", "name": "Exchange Outbound Connector TLS Enforcement", "mode": "PHASE_1_REPORTING", "enabled": True, "desc": "Enforce mandatory TLS 1.3 encryption on hybrid & outbound email connectors.", "criteria": '{"require_tls": true, "idle_expiration_days": 30}'},
        {"category": "legal_hold", "name": "Executive & Compliance Retention Hold Policy", "mode": "PHASE_3_FULLY_AUTOMATED", "enabled": True, "desc": "Apply 7-year immutable audit retention policy on executive/legal mailboxes.", "criteria": '{"retention_years": 7, "immutable_hold": true}'},
        {"category": "auditing", "name": "SOC 2 Audit Trail & Unauthorized Admin Alert", "mode": "PHASE_2_SEMI_AUTOMATED", "enabled": True, "desc": "Flag multiple failed admin authentication attempts and critical RBAC changes.", "criteria": '{"failed_login_threshold": 5, "alert_on_global_admin_change": true}'},
        {"category": "outages", "name": "M365 Service Degradation SLA Alert Policy", "mode": "PHASE_1_REPORTING", "enabled": True, "desc": "Broadcast instant notifications to Teams admin channel during active outages.", "criteria": '{"notify_teams_on_incident": true, "severity_level": "HIGH"}'},
        {"category": "sharepoint", "name": "SharePoint External Sharing & DLP Expiration Policy", "mode": "PHASE_3_FULLY_AUTOMATED", "enabled": True, "desc": "Enforce 30-day expiration on external anonymous sharing links.", "criteria": '{"anonymous_link_days": 30, "archive_stale_storage_gb": 500}'},
        {"category": "ai_governance", "name": "AI Autonomous Governance & Failover Policy", "mode": "PHASE_2_SEMI_AUTOMATED", "enabled": True, "desc": "Configure AI recommendation execution mode and multi-LLM failover behavior.", "criteria": '{"auto_failover_enabled": true, "primary_provider": "openai"}'}
    ]

    if not policies or len(policies) < len(default_defs):
        existing_cats = {p.category for p in policies}
        new_objs = []
        for d in default_defs:
            if d["category"] not in existing_cats:
                new_objs.append(AutomationPolicy(
                    category=d["category"],
                    policy_name=d["name"],
                    phase_level=d["mode"],
                    is_enabled=d["enabled"],
                    description=d["desc"],
                    criteria_json=d["criteria"]
                ))
        if new_objs:
            db.add_all(new_objs)
            db.commit()
            policies = db.query(AutomationPolicy).all()

    return policies

@router.post("/policies", response_model=AutomationPolicySchema, summary="Create/Update Automation Policy")
def save_automation_policy(
    payload: AutomationPolicyCreateSchema,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Configure or update Phase 3 automated governance policies."""
    existing = db.query(AutomationPolicy).filter(AutomationPolicy.category == payload.category).first()
    if existing:
        existing.policy_name = payload.policy_name
        existing.phase_level = payload.phase_level
        existing.is_enabled = payload.is_enabled
        existing.description = payload.description
        if payload.criteria_json is not None:
            existing.criteria_json = payload.criteria_json
        db.commit()
        db.refresh(existing)
        return existing
    else:
        new_pol = AutomationPolicy(
            category=payload.category,
            policy_name=payload.policy_name,
            phase_level=payload.phase_level,
            is_enabled=payload.is_enabled,
            description=payload.description,
            criteria_json=payload.criteria_json
        )
        db.add(new_pol)
        db.commit()
        db.refresh(new_pol)
        return new_pol

@router.post("/export", summary="Export Dedicated Data Report (15, 30, or 365 Days)")
def export_report_data(
    payload: ExportRequestSchema,
    current_user: dict = Depends(get_current_user)
):
    """
    Dedicated API route allowing users to download or export reporting data strictly filtered to 15 days, 30 days, or 1 year.
    """
    export_result = export_service.generate_export_payload(
        module_name=payload.module,
        days=payload.days,
        format_type=payload.format
    )

    return Response(
        content=export_result["content"],
        media_type=export_result["media_type"],
        headers={"Content-Disposition": f"attachment; filename={export_result['filename']}"}
    )

