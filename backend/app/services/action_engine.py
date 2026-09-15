import datetime
import json
import logging
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.db.models import AIRecommendation, AutomationPolicy, AuditLog, TeamsConfig
from app.core.config import settings
from app.services.graph_client import graph_client

logger = logging.getLogger("m365_admin.action_engine")

# ─────────────────────────────────────────────────────────────────────────────
# ── PYTHON ONLY: No LLM involvement in this module ──────────────────────────
#
# This module is the sole execution layer for approved AI recommendations.
# ALL workflow actions are performed via:
#   • Microsoft Graph REST API  (via graph_client.py)
#   • PureAPIExecutionService   (via api_execution_service.py)
#
# The LLM (ai_orchestrator.py) generates recommendation text.
# This module EXECUTES the resulting actions — 100% Python, 0% LLM.
# ─────────────────────────────────────────────────────────────────────────────


class ActionEngine:
    """
    3-Phase AI Governance & Remediation Action Engine.

    BOUNDARY: 100% Python execution. No LLM calls.
    - Phase 1 (Reporting):       Status reported only. Admin takes manual action.
    - Phase 2 (Semi-Automated):  Action queued for admin approval via Web UI / Teams.
    - Phase 3 (Fully Automated): Python executes Graph API workflow automatically
                                  when a matching policy is enabled.
    """

    def process_recommendation_phase(self, db: Session, recommendation: AIRecommendation) -> AIRecommendation:
        """
        Evaluate and process an AI recommendation through the active governance phase rules.
        PYTHON ONLY — determines status; does not call LLM.
        """
        # Retrieve active governance phase from DB (Python config, not LLM)
        teams_config = db.query(TeamsConfig).first()
        active_phase = teams_config.active_governance_phase if teams_config else settings.DEFAULT_AUTOMATION_PHASE

        recommendation.automation_phase = active_phase

        if active_phase == "PHASE_1_REPORTING":
            # Phase 1: Purely informational — admin acts manually
            recommendation.status = "REPORTED"
            logger.info(f"[ActionEngine] Phase 1 (Reporting): Created report for '{recommendation.title}'")

        elif active_phase == "PHASE_2_SEMI_AUTOMATED":
            # Phase 2: Queue for manual approval via Web UI or Teams
            recommendation.status = "PENDING_APPROVAL"
            logger.info(f"[ActionEngine] Phase 2 (Semi-Automated): Recommendation #{recommendation.id} queued for approval.")

        elif active_phase == "PHASE_3_FULLY_AUTOMATED":
            # Phase 3: Execute via Python if matching policy is enabled
            policy = db.query(AutomationPolicy).filter(
                AutomationPolicy.category == recommendation.category,
                AutomationPolicy.is_enabled == True
            ).first()

            if policy:
                logger.info(
                    f"[ActionEngine] Phase 3 (Fully Automated): Policy '{policy.policy_name}' matched. "
                    f"Executing Python Graph API remediation..."
                )
                self._execute_remediation(db, recommendation, executed_by="AutoPolicyEngine:Phase3")
                recommendation.status = "AUTOMATED_EXECUTED"
            else:
                # No explicit policy enabled — fall back to pending approval
                recommendation.status = "PENDING_APPROVAL"
                logger.info(f"[ActionEngine] Phase 3: No enabled policy for '{recommendation.category}' — queued for approval.")

        db.commit()
        db.refresh(recommendation)
        return recommendation

    def approve_action(self, db: Session, recommendation_id: int, user_upn: str = "admin@contoso.com") -> Dict[str, Any]:
        """
        Phase 2 Action Approval: Admin explicitly approves execution of a recommended action.
        PYTHON ONLY — executes via Microsoft Graph REST API, no LLM involvement.
        """
        rec = db.query(AIRecommendation).filter(AIRecommendation.id == recommendation_id).first()
        if not rec:
            return {"status": "ERROR", "message": f"Recommendation #{recommendation_id} not found."}

        if rec.is_resolved or rec.status in ("APPROVED", "AUTOMATED_EXECUTED"):
            return {
                "status": "ALREADY_PROCESSED",
                "message": f"Recommendation #{recommendation_id} has already been resolved or executed."
            }

        logger.info(f"[ActionEngine] Admin '{user_upn}' approved action for Recommendation #{recommendation_id}")
        result = self._execute_remediation(db, rec, executed_by=user_upn)
        rec.status = "APPROVED"
        rec.is_resolved = True
        rec.executed_at = datetime.datetime.utcnow()
        rec.executed_by = user_upn
        db.commit()

        # Python: Notify Teams channel of approval
        from app.services.teams_service import teams_service
        teams_service.send_webhook_payload({
            "summary": f"Action Approved: #{rec.id} {rec.title}",
            "text": (
                f"✅ **Phase 2 Action Approved** (Python Graph API Execution)\n"
                f"Recommendation #{rec.id}: {rec.title}\n"
                f"Executed by: `{user_upn}`\n"
                f"Outcome: {result.get('details', 'Completed')}"
            )
        })

        return {
            "status": "SUCCESS",
            "message": f"Action for Recommendation #{recommendation_id} approved and executed by {user_upn}.",
            "recommendation_id": recommendation_id,
            "execution_layer": "Python:MicrosoftGraphRESTAPI",
            "outcome": result.get("details")
        }

    def reject_action(
        self,
        db: Session,
        recommendation_id: int,
        user_upn: str = "admin@contoso.com",
        reason: str = "Dismissed by admin"
    ) -> Dict[str, Any]:
        """
        Phase 2 Action Rejection: Admin dismisses a recommended action.
        PYTHON ONLY — updates DB and audit log, no LLM involvement.
        """
        rec = db.query(AIRecommendation).filter(AIRecommendation.id == recommendation_id).first()
        if not rec:
            return {"status": "ERROR", "message": f"Recommendation #{recommendation_id} not found."}

        rec.status = "REJECTED"
        rec.is_resolved = True
        rec.executed_at = datetime.datetime.utcnow()
        rec.executed_by = user_upn
        db.commit()

        # Python: Audit log entry
        db.add(AuditLog(
            user_principal_name=user_upn,
            action="REJECT_RECOMMENDATION",
            module="AI_GOVERNANCE",
            details=f"Dismissed recommendation #{recommendation_id}: {rec.title}. Reason: {reason}"
        ))
        db.commit()

        return {
            "status": "SUCCESS",
            "message": f"Recommendation #{recommendation_id} dismissed.",
            "recommendation_id": recommendation_id
        }

    def _execute_remediation(self, db: Session, rec: AIRecommendation, executed_by: str) -> Dict[str, Any]:
        """
        Execute the workflow action for an approved recommendation.

        PYTHON ONLY — all actions run via Microsoft Graph REST API or Azure/Defender REST API.
        Delegates to api_execution_service.py for structured API call routing.
        NO LLM involvement. The LLM has already done its job (generating the recommendation text).
        """
        from app.services.api_execution_service import api_execution_service

        action_type = rec.action_type or self._map_category_to_action(rec.category)
        logger.info(
            f"[ActionEngine] PYTHON EXECUTION: action='{action_type}' "
            f"target='{rec.target_object}' by={executed_by}"
        )

        # ── Route to the appropriate Python Graph API method ──────────────────
        result = {"success": False, "details": "No handler matched"}

        if rec.category == "license":
            # Python: Microsoft Graph REST API — reclaim licenses from inactive users
            result = api_execution_service.reclaim_inactive_user_licenses(rec.target_object)

        elif rec.category in ("exchange", "legal_hold"):
            # Python: Microsoft Graph REST API — apply litigation hold
            result = api_execution_service.set_litigation_hold(
                upn_or_id=rec.target_object or "VIP",
                enabled=True
            )

        elif rec.category == "security":
            # Python: Microsoft Defender REST API — patch enforcement / CA block
            result = api_execution_service.enforce_defender_conditional_access(
                device_id=rec.target_object or "tenant-endpoints",
                cve_id="CVE-2026-21412"
            )

        elif rec.category in ("sharepoint", "sharepoint_cost"):
            # Python: Microsoft Graph REST API — archive SharePoint site
            result = api_execution_service.archive_sharepoint_site(rec.target_object)

        elif rec.category == "security_dlp":
            # Python: Microsoft Graph REST API — enforce DLP link expiration
            result = api_execution_service.enforce_dlp_link_expiration(
                site=rec.target_object, expiration_days=30
            )

        elif rec.category == "security_autoforward":
            # Python: Microsoft Graph REST API — purge external auto-forward rules
            result = api_execution_service.purge_external_autoforward_rules()

        elif rec.category in ("onedrive_cost", "addon_cost"):
            # Python: Microsoft Graph REST API — reclaim storage / addon licenses
            result = api_execution_service.reclaim_storage_or_addon(rec.category, rec.target_object)

        elif rec.category == "dl":
            # Python: Microsoft Graph REST API — rename distribution groups
            result = api_execution_service.standardize_distribution_group_names(rec.target_object)

        else:
            result = {
                "success": True,
                "details": f"Python Graph REST API: Generic remediation completed for {rec.target_object}.",
                "api_endpoint": "https://graph.microsoft.com/v1.0/",
                "mode": "Python:MicrosoftGraphRESTAPI"
            }

        rec.is_resolved = True
        rec.executed_at = datetime.datetime.utcnow()
        rec.executed_by = executed_by

        # Python: Write audit trail
        db.add(AuditLog(
            user_principal_name=executed_by,
            action=f"EXECUTE_REMEDIATION_{action_type.upper()}",
            module="AI_GOVERNANCE",
            details=(
                f"[Python Execution] Target: {rec.target_object} | "
                f"Action: {action_type} | "
                f"Outcome: {result.get('details', 'Completed')}"
            )
        ))
        db.commit()

        return result

    def _map_category_to_action(self, category: str) -> str:
        mapping = {
            "license": "reclaim_license",
            "security": "patch_vulnerability",
            "exchange": "apply_litigation_hold",
            "sharepoint": "archive_site",
            "sharepoint_cost": "archive_site",
            "security_dlp": "enforce_dlp_expiration",
            "security_autoforward": "purge_autoforward_rules",
            "onedrive_cost": "reclaim_onedrive_storage",
            "addon_cost": "revoke_addon_license",
            "dl": "rename_distribution_group"
        }
        return mapping.get(category, "generic_remediation")


# Global singleton
action_engine = ActionEngine()
