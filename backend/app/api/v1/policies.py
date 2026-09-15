"""
Policy Engine Router — Separate Policy Creation, Alerting & Automation

Categories:
1. LICENSE_AUTOMATION (Removal, Downgrade/Upgrade, Assignment with Azure AD filters)
2. SHAREPOINT_CLEANUP (Filters: Site, Inactivity, File types. Actions: Delete, Move to SP, Move to OneDrive, Move to Azure Storage)
3. COMPLIANCE_SECURITY (Azure Alerts per user, Sensitive File Sharing, Email Forwarding)

Alerts: Email & Teams Chat instant alerts on findings, plus Daily Digest Summaries.
"""

import json
import logging
import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.db.models import AutomationPolicy, PolicyAlertFinding, AIRecommendation
from app.core.security import require_roles
from app.services.alert_notification_service import alert_notification_service

logger = logging.getLogger("m365_admin.policies")

router = APIRouter()

class CreatePolicyRequest(BaseModel):
    category: str # LICENSE_AUTOMATION, SHAREPOINT_CLEANUP, COMPLIANCE_SECURITY
    policy_type: str # LICENSE_REMOVAL, LICENSE_DOWNGRADE, LICENSE_ASSIGNMENT, SHAREPOINT_CLEANUP, AZURE_SECURITY_ALERTS, SHAREPOINT_SENSITIVE_SHARING, EMAIL_FORWARDING_SENSITIVE
    policy_name: str
    phase_level: str = "PHASE_1_REPORTING"
    description: Optional[str] = None
    is_enabled: bool = True
    
    # Alert Options
    alert_email_enabled: bool = True
    alert_email_recipients: Optional[str] = "admin@contoso.com"
    alert_teams_enabled: bool = True
    alert_teams_webhook: Optional[str] = None
    daily_summary_email: bool = True
    daily_summary_teams: bool = True

    # Policy Criteria & Filtering Attributes
    # License Removal: Azure AD attributes (Department, RBIUsertype, Location, Grade, Inactive time)
    # License Downgrade: Azure AD attributes + target license SKU selection
    # License Assignment: Azure AD attributes + target license SKU per category
    # SharePoint Cleanup: Site data, Inactivity days, File type extensions
    criteria: Dict[str, Any] = {}

    # Action Config: Delete, Move to SP, Move to OneDrive, Move to Azure Storage
    action_config: Dict[str, Any] = {}

DEFAULT_POLICIES_SEED = [
    {
        "category": "LICENSE_AUTOMATION",
        "policy_type": "LICENSE_DOWNGRADE",
        "policy_name": "Test E5 to E3 Downgrade Policy",
        "phase_level": "Phase 2: Semi-Automated",
        "description": "Test policy creation with Azure AD attributes",
        "criteria": {"department": "Finance", "location": "New York", "grade": "Senior", "rbi_user_type": "StandardEmployee", "inactive_days": 45, "current_sku": "ENTERPRISEPREMIATION (M365 E5)", "target_sku": "ENTERPRISEPACK (M365 E3)"},
        "action_config": {"action": "DOWNGRADE_SKU"}
    },
    {
        "category": "LICENSE_AUTOMATION",
        "policy_type": "LICENSE_ASSIGNMENT",
        "policy_name": "Role-Based License Auto-Assignment",
        "phase_level": "Phase 3: Fully Automated",
        "description": "Auto-assign standard license SKUs per category based on Azure AD department and grade.",
        "criteria": {"department": "Sales", "location": "All", "grade": "Standard", "rbi_user_type": "StandardEmployee", "inactive_days": 30, "target_sku": "ENTERPRISEPACK (M365 E3)"},
        "action_config": {"action": "ASSIGN_LICENSE"}
    },
    {
        "category": "LICENSE_AUTOMATION",
        "policy_type": "LICENSE_REMOVAL",
        "policy_name": "Inactive User License Reclaim (Azure AD)",
        "phase_level": "Phase 2: Semi-Automated",
        "description": "Reclaim licenses from users inactive > 90 days matching Department, Location, Grade, or RBI User Type.",
        "criteria": {"department": "All", "location": "All", "grade": "All", "rbi_user_type": "StandardEmployee", "inactive_days": 90},
        "action_config": {"action": "RECLAIM_LICENSE"}
    },
    {
        "category": "AI_GOVERNANCE",
        "policy_type": "AI_GOVERNANCE_AUTO",
        "policy_name": "LLM Proactive Cost & Security Optimization Threshold",
        "phase_level": "Phase 2: Semi-Automated",
        "description": "Automated LLM policy enforcement for high-confidence cost savings and risk mitigation.",
        "criteria": {"min_confidence": "90%", "auto_execute_phase3": True, "department": "All"},
        "action_config": {"action": "AI_OPTIMIZE"}
    },
    {
        "category": "AUDITING",
        "policy_type": "AUDIT_LOG_RETENTION",
        "policy_name": "Admin Action Audit Log Retention & Change Monitor",
        "phase_level": "Phase 1: Reporting Only",
        "description": "Enforce mandatory SQL audit log logging and alerts for administrative policy modifications.",
        "criteria": {"retention_days": 365, "notify_roles": "GlobalAdmin", "department": "Security"},
        "action_config": {"action": "LOG_AUDIT"}
    },
    {
        "category": "CONNECTORS",
        "policy_type": "CONNECTOR_HEALTH",
        "policy_name": "Entra ID & Hybrid Exchange Sync Health Monitor",
        "phase_level": "Phase 1: Reporting Only",
        "description": "Monitor Entra ID connect sync status and hybrid Exchange connector connectivity.",
        "criteria": {"sync_threshold_minutes": 30, "alert_on_failure": True, "department": "IT Operations"},
        "action_config": {"action": "MONITOR_SYNC"}
    },
    {
        "category": "EXCHANGE_RULES",
        "policy_type": "ANTI_SPAM_RULE",
        "policy_name": "High-Risk Inbound Mailflow & Anti-Spam SCL Policy",
        "phase_level": "Phase 2: Semi-Automated",
        "description": "Quarantine incoming mail flow exceeding Spam Confidence Level (SCL) thresholds.",
        "criteria": {"scl_threshold": 7, "action": "Quarantine", "department": "All"},
        "action_config": {"action": "QUARANTINE_SPAM"}
    },
    {
        "category": "FAILED_UPDATES",
        "policy_type": "RETRY_ENGINE",
        "policy_name": "Automated Retry & Rollback Engine for Failed Graph Calls",
        "phase_level": "Phase 3: Fully Automated",
        "description": "Automatic exponential backoff retry for failed Graph API REST updates.",
        "criteria": {"max_retries": 3, "fallback_mode": "SafeDefault", "department": "IT"},
        "action_config": {"action": "RETRY_UPDATE"}
    },
    {
        "category": "INACTIVE_USERS",
        "policy_type": "DEPROVISIONING_RULE",
        "policy_name": "90-Day Account Deprovisioning & Block Sign-In Rule",
        "phase_level": "Phase 2: Semi-Automated",
        "description": "Automatically flag and block sign-in for users inactive over 90 days.",
        "criteria": {"inactive_days": 90, "block_credentials": True, "department": "All"},
        "action_config": {"action": "BLOCK_SIGNIN"}
    },
    {
        "category": "LEGAL_HOLD",
        "policy_type": "EDISCOVERY_HOLD",
        "policy_name": "Automatic Custodian eDiscovery Hold & Compliance Export Rule",
        "phase_level": "Phase 2: Semi-Automated",
        "description": "Preserve custodian mailbox and OneDrive files when Legal Hold case is initiated.",
        "criteria": {"hold_type": "LitigationHold", "destination_vault": "SharePoint Vault", "department": "Legal"},
        "action_config": {"action": "ENABLE_LEGAL_HOLD"}
    },
    {
        "category": "LICENSE",
        "policy_type": "ADDON_OPTIMIZATION",
        "policy_name": "Copilot & Add-On Seat Reallocation Policy",
        "phase_level": "Phase 2: Semi-Automated",
        "description": "Reclaim expensive M365 Copilot add-on licenses from inactive seats.",
        "criteria": {"copilot_inactive_days": 30, "reclaim_unassigned": True, "department": "All"},
        "action_config": {"action": "RECLAIM_ADDON"}
    },
    {
        "category": "LICENSES",
        "policy_type": "SKU_OVERPROVISION",
        "policy_name": "Over-Provisioned M365 E5 License Downgrade Alert",
        "phase_level": "Phase 1: Reporting Only",
        "description": "Alert admins when unassigned E5 SKUs exceed tenant reserve capacity.",
        "criteria": {"threshold_count": 5, "notify_admin": True, "department": "Finance"},
        "action_config": {"action": "ALERT_OVERPROVISION"}
    },
    {
        "category": "MAILBOX",
        "policy_type": "MAILBOX_QUOTA",
        "policy_name": "Mailbox Auto-Archiving & Quota Enforcement Rule",
        "phase_level": "Phase 2: Semi-Automated",
        "description": "Enable online archive when mailbox storage reaches 85% capacity.",
        "criteria": {"warning_threshold_pct": 85, "auto_archive": True, "department": "All"},
        "action_config": {"action": "ENABLE_ARCHIVE"}
    },
    {
        "category": "MAILFLOW",
        "policy_type": "EXTERNAL_FORWARDING",
        "policy_name": "Tenant-Wide External Auto-Forwarding Prevention",
        "phase_level": "Phase 3: Fully Automated",
        "description": "Block inbox rules that auto-forward emails to external domains.",
        "criteria": {"block_external_forwarding": True, "alert_secops": True, "department": "Security"},
        "action_config": {"action": "BLOCK_FORWARDING"}
    },
    {
        "category": "OUTAGES",
        "policy_type": "SERVICE_HEALTH_ALERT",
        "policy_name": "Service Health Outage Map & Regional Alert Trigger",
        "phase_level": "Phase 1: Reporting Only",
        "description": "Parse Microsoft Service Health API for regional degradation alerts.",
        "criteria": {"severity_min": "HIGH", "auto_notify_teams": True, "department": "IT Operations"},
        "action_config": {"action": "NOTIFY_OUTAGE"}
    },
    {
        "category": "RISKY_USERS",
        "policy_type": "IDENTITY_RISK",
        "policy_name": "Identity Protection High-Risk Step-Up MFA Rule",
        "phase_level": "Phase 3: Fully Automated",
        "description": "Require MFA step-up and credential reset for Defender high-risk users.",
        "criteria": {"min_risk": "HIGH", "require_mfa_reset": True, "department": "All"},
        "action_config": {"action": "ENFORCE_MFA"}
    },
    {
        "category": "SHAREPOINT",
        "policy_type": "SHAREPOINT_CLEANUP",
        "policy_name": "Stale SharePoint Site Storage Archiving & Tiering",
        "phase_level": "Phase 2: Semi-Automated",
        "description": "Archive cold SharePoint site libraries to Azure Storage after 120 days of inactivity.",
        "criteria": {"source_site": "Marketing Assets", "inactive_days": 120, "file_types": ".pdf,.zip,.docx"},
        "action_config": {"action": "MOVE_AZURE_STORAGE", "destination_target": "sharepoint-archive"}
    },
    {
        "category": "SHAREPOINT",
        "policy_type": "SHAREPOINT_SENSITIVE_SHARING",
        "policy_name": "External Sensitive File Sharing (CCN/SSN) DLP Rule",
        "phase_level": "Phase 1: Reporting Only",
        "description": "Audit and alert when sensitive files with credit card or SSN numbers are shared externally.",
        "criteria": {"sensitive_types": "Credit Card, SSN, Financials", "sharing_scope": "ExternalGuest"},
        "action_config": {"action": "REVOKE_ANONYMOUS_LINK"}
    },
    {
        "category": "MAILBOX",
        "policy_type": "SHARED_MAILBOX_RULE",
        "policy_name": "Shared Mailbox Delegation & Retention Standard",
        "phase_level": "Phase 2: Semi-Automated",
        "description": "Enforce naming conventions and access retention on shared mailboxes.",
        "criteria": {"check_permissions": True, "inactivity_days": 60, "department": "Operations"},
        "action_config": {"action": "AUDIT_DELEGATION"}
    }
]

def seed_default_policies(db: Session):
    count = db.query(AutomationPolicy).count()
    if count < len(DEFAULT_POLICIES_SEED):
        existing_names = {p.policy_name for p in db.query(AutomationPolicy.policy_name).all()}
        for seed in DEFAULT_POLICIES_SEED:
            if seed["policy_name"] not in existing_names:
                p = AutomationPolicy(
                    category=seed["category"],
                    policy_type=seed["policy_type"],
                    policy_name=seed["policy_name"],
                    phase_level=seed["phase_level"],
                    description=seed["description"],
                    is_enabled=True,
                    alert_email_enabled=True,
                    alert_email_recipients=None,
                    alert_teams_enabled=True,
                    alert_teams_webhook=settings.TEAMS_WEBHOOK_URL,
                    daily_summary_email=True,
                    daily_summary_teams=True,
                    criteria_json=json.dumps(seed["criteria"]),
                    action_config_json=json.dumps(seed["action_config"])
                )
                db.add(p)
        db.commit()


@router.get("/", summary="List All Automation & Governance Policies")
@router.get("/rules", summary="List All Automation & Governance Policies (Alias)")
def list_policies(db: Session = Depends(get_db)):
    """Retrieves all policies grouped by category."""
    seed_default_policies(db)
    policies = db.query(AutomationPolicy).order_by(AutomationPolicy.created_at.desc()).all()
    result = []
    for p in policies:
        result.append({
            "id": p.id,
            "category": p.category,
            "policy_type": p.policy_type,
            "policy_name": p.policy_name,
            "phase_level": p.phase_level,
            "is_enabled": p.is_enabled,
            "description": p.description,
            "alert_email_enabled": p.alert_email_enabled,
            "alert_email_recipients": p.alert_email_recipients,
            "alert_teams_enabled": p.alert_teams_enabled,
            "alert_teams_webhook": p.alert_teams_webhook,
            "daily_summary_email": p.daily_summary_email,
            "daily_summary_teams": p.daily_summary_teams,
            "criteria": json.loads(p.criteria_json) if p.criteria_json else {},
            "action_config": json.loads(p.action_config_json) if p.action_config_json else {},
            "created_at": p.created_at.isoformat() if p.created_at else None
        })
    return result

@router.post("/create", summary="Create New Governance & Automation Policy")
def create_policy(req: CreatePolicyRequest, db: Session = Depends(get_db)):
    """Creates a new policy with dedicated filtering criteria, alert settings, and action options."""
    policy = AutomationPolicy(
        category=req.category,
        policy_type=req.policy_type,
        policy_name=req.policy_name,
        phase_level=req.phase_level,
        description=req.description,
        is_enabled=req.is_enabled,
        alert_email_enabled=req.alert_email_enabled,
        alert_email_recipients=req.alert_email_recipients,
        alert_teams_enabled=req.alert_teams_enabled,
        alert_teams_webhook=req.alert_teams_webhook,
        daily_summary_email=req.daily_summary_email,
        daily_summary_teams=req.daily_summary_teams,
        criteria_json=json.dumps(req.criteria),
        action_config_json=json.dumps(req.action_config)
    )
    db.add(policy)
    db.commit()
    db.refresh(policy)

    return {
        "status": "Success",
        "message": f"Policy '{policy.policy_name}' created successfully.",
        "policy_id": policy.id,
        "category": policy.category,
        "policy_type": policy.policy_type
    }

@router.put("/{policy_id}", summary="Update Governance Policy")
def update_policy(policy_id: int, req: CreatePolicyRequest, db: Session = Depends(get_db)):
    """Updates existing policy definition, filters, alert choices, or action parameters."""
    policy = db.query(AutomationPolicy).filter(AutomationPolicy.id == policy_id).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")

    policy.category = req.category
    policy.policy_type = req.policy_type
    policy.policy_name = req.policy_name
    policy.phase_level = req.phase_level
    policy.description = req.description
    policy.is_enabled = req.is_enabled
    policy.alert_email_enabled = req.alert_email_enabled
    policy.alert_email_recipients = req.alert_email_recipients
    policy.alert_teams_enabled = req.alert_teams_enabled
    policy.alert_teams_webhook = req.alert_teams_webhook
    policy.daily_summary_email = req.daily_summary_email
    policy.daily_summary_teams = req.daily_summary_teams
    policy.criteria_json = json.dumps(req.criteria)
    policy.action_config_json = json.dumps(req.action_config)
    policy.updated_at = datetime.datetime.utcnow()

    db.commit()
    return {"status": "Success", "message": f"Policy '{policy.policy_name}' updated successfully."}

@router.delete("/{policy_id}", summary="Delete Governance Policy")
def delete_policy(policy_id: int, db: Session = Depends(get_db)):
    """Deletes policy from database."""
    policy = db.query(AutomationPolicy).filter(AutomationPolicy.id == policy_id).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")

    db.delete(policy)
    db.commit()
    return {"status": "Success", "message": f"Policy ID {policy_id} deleted."}

@router.post("/evaluate", summary="Evaluate Policy Findings & Trigger Instant Alerts")
def evaluate_policies(db: Session = Depends(get_db)):
    """Evaluates all enabled policies, logs findings, and fires instant Email/Teams alerts."""
    active_policies = db.query(AutomationPolicy).filter(AutomationPolicy.is_enabled == True).all()
    triggered_count = 0
    new_findings = []

    for policy in active_policies:
        criteria = json.loads(policy.criteria_json) if policy.criteria_json else {}
        action_config = json.loads(policy.action_config_json) if policy.action_config_json else {}

        # Simulated evaluation based on policy type
        sample_target = "user.inactive@contoso.com" if "LICENSE" in policy.policy_type or "AZURE" in policy.policy_type else "https://contoso.sharepoint.com/sites/LegalArchive/Confidential_Report.pdf"
        sample_desc = f"Policy '{policy.policy_name}' matched target with inactive time > {criteria.get('inactive_days', 90)} days."

        finding = PolicyAlertFinding(
            policy_id=policy.id,
            policy_name=policy.policy_name,
            category=policy.category,
            target_user_or_resource=sample_target,
            finding_description=sample_desc,
            severity="HIGH" if "REMOVAL" in policy.policy_type or "SENSITIVE" in policy.policy_type else "MEDIUM",
            status="TRIGGERED"
        )
        db.add(finding)
        triggered_count += 1
        new_findings.append({
            "policy_name": policy.policy_name,
            "category": policy.category,
            "target": sample_target,
            "description": sample_desc
        })

        # Trigger Instant Alerts if enabled
        email_list = policy.alert_email_recipients.split(",") if policy.alert_email_enabled and policy.alert_email_recipients else None
        webhook_url = policy.alert_teams_webhook if policy.alert_teams_enabled else None

        if email_list or webhook_url:
            alert_notification_service.send_finding_alert(
                policy_name=policy.policy_name,
                category=policy.category,
                target_resource=sample_target,
                description=sample_desc,
                severity=finding.severity,
                email_recipients=email_list,
                teams_webhook_url=webhook_url
            )

    db.commit()

    return {
        "status": "Success",
        "evaluated_policies": len(active_policies),
        "triggered_findings": triggered_count,
        "findings": new_findings
    }

@router.post("/daily-summary", summary="Dispatch Daily Summary Digest (Email & Teams)")
def send_daily_summary(db: Session = Depends(get_db)):
    """Triggers generation and dispatch of daily summary report for findings & pending items."""
    findings = db.query(PolicyAlertFinding).order_by(PolicyAlertFinding.triggered_at.desc()).limit(20).all()
    pending = db.query(AIRecommendation).filter(AIRecommendation.status == "PENDING_APPROVAL").limit(20).all()

    findings_list = [
        {
            "policy_name": f.policy_name,
            "target_user_or_resource": f.target_user_or_resource,
            "severity": f.severity,
            "finding_description": f.finding_description
        } for f in findings
    ]
    pending_list = [
        {
            "title": p.title,
            "category": p.category,
            "status": p.status
        } for p in pending
    ]

    result = alert_notification_service.generate_daily_summary(
        triggered_findings=findings_list,
        pending_action_items=pending_list,
        email_recipients=None,
        teams_webhook_url=settings.TEAMS_WEBHOOK_URL
    )

    return {
        "status": "Success",
        "message": "Daily summary report generated and dispatched.",
        "dispatch_details": result
    }
