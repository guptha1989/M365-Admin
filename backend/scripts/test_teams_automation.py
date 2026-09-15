import os
import sys
import unittest

# Add backend directory to PYTHONPATH
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.core.database import SessionLocal, init_db
from app.db.models import AIRecommendation, TeamsConfig, AuditLog, AutomationPolicy
from app.services.teams_service import teams_service
from app.services.action_engine import action_engine
from app.services.ai_orchestrator import ai_orchestrator

class TestTeamsIntegrationAndGovernancePhases(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        init_db()

    def setUp(self):
        self.db = SessionLocal()
        # Seed fresh AI recommendations
        ai_orchestrator.generate_recommendations(self.db)

    def tearDown(self):
        self.db.close()

    def test_01_teams_command_parsing(self):
        """Test Teams Bot interactive command parser."""
        # 1. Help command
        help_res = teams_service.parse_teams_command(self.db, "help", "admin@contoso.com")
        self.assertIn("M365 Admin AI Bot", help_res["text"])

        # 2. Recommendations command
        rec_res = teams_service.parse_teams_command(self.db, "recommendations", "admin@contoso.com")
        self.assertEqual(rec_res["response_type"], "adaptive_card")
        self.assertIn("card", rec_res)

        # 3. License command
        lic_res = teams_service.parse_teams_command(self.db, "licenses", "admin@contoso.com")
        self.assertIn("License Summary", lic_res["text"])

        # 4. Service Health command
        outage_res = teams_service.parse_teams_command(self.db, "health", "admin@contoso.com")
        self.assertIn("Service Health", outage_res["text"])

    def test_02_daily_digest_card_generation(self):
        """Test daily proactive Adaptive Card digest construction."""
        recs = self.db.query(AIRecommendation).all()
        card_payload = teams_service.build_daily_digest_card(recs, current_phase="PHASE_1_REPORTING")
        self.assertEqual(card_payload["type"], "message")
        self.assertIn("attachments", card_payload)
        card_content = card_payload["attachments"][0]["content"]
        self.assertEqual(card_content["type"], "AdaptiveCard")

    def test_03_phase_1_reporting_flow(self):
        """Test Phase 1 Reporting mode (informational recommendations, manual actions)."""
        config = self.db.query(TeamsConfig).first()
        if not config:
            config = TeamsConfig()
            self.db.add(config)
        config.active_governance_phase = "PHASE_1_REPORTING"
        self.db.commit()

        recs = ai_orchestrator.generate_recommendations(self.db)
        first_rec = self.db.query(AIRecommendation).first()
        self.assertEqual(first_rec.status, "REPORTED")
        self.assertEqual(first_rec.automation_phase, "PHASE_1_REPORTING")

    def test_04_phase_2_semi_automated_approval_flow(self):
        """Test Phase 2 Semi-Automated review & approval flow."""
        config = self.db.query(TeamsConfig).first()
        config.active_governance_phase = "PHASE_2_SEMI_AUTOMATED"
        self.db.commit()

        ai_orchestrator.generate_recommendations(self.db)
        pending_rec = self.db.query(AIRecommendation).first()
        self.assertEqual(pending_rec.status, "PENDING_APPROVAL")

        # Approve recommendation
        result = action_engine.approve_action(self.db, pending_rec.id, user_upn="admin@contoso.com")
        self.assertEqual(result["status"], "SUCCESS")

        updated_rec = self.db.query(AIRecommendation).filter(AIRecommendation.id == pending_rec.id).first()
        self.assertTrue(updated_rec.is_resolved)
        self.assertEqual(updated_rec.status, "APPROVED")
        self.assertEqual(updated_rec.executed_by, "admin@contoso.com")

        # Check Audit Log
        audit = self.db.query(AuditLog).filter(AuditLog.user_principal_name == "admin@contoso.com").first()
        self.assertIsNotNone(audit)

    def test_05_phase_3_fully_automated_policy_flow(self):
        """Test Phase 3 Policy-Driven Fully Automated execution flow."""
        config = self.db.query(TeamsConfig).first()
        config.active_governance_phase = "PHASE_3_FULLY_AUTOMATED"
        self.db.commit()

        # Add active automation policy for license
        policy = self.db.query(AutomationPolicy).filter(AutomationPolicy.category == "license").first()
        if not policy:
            policy = AutomationPolicy(
                category="license",
                policy_name="Auto-Downgrade Inactive E5",
                phase_level="PHASE_3_FULLY_AUTOMATED",
                is_enabled=True
            )
            self.db.add(policy)
            self.db.commit()
        else:
            policy.is_enabled = True
            self.db.commit()

        ai_orchestrator.generate_recommendations(self.db)

        license_rec = self.db.query(AIRecommendation).filter(AIRecommendation.category == "license").first()
        self.assertEqual(license_rec.status, "AUTOMATED_EXECUTED")
        self.assertTrue(license_rec.is_resolved)
        self.assertEqual(license_rec.executed_by, "AutoPolicyEngine:Phase3")

if __name__ == "__main__":
    unittest.main()
