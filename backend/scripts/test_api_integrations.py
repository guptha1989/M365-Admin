import sys
import os

# Add backend to python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import SessionLocal, init_db
from app.db.models import APIIntegrationConfig
from app.services.ai_orchestrator import ai_orchestrator
from app.core.security import encrypt_api_key, decrypt_api_key

def test_api_integrations_and_failover():
    print("==========================================================================")
    print("Testing Multi-API Integration Hub & LLM Auto-Switching Failover Engine")
    print("==========================================================================")

    init_db()
    db = SessionLocal()

    try:
        # Clear existing test integration configs
        db.query(APIIntegrationConfig).delete()
        db.commit()

        print("1. Seed API Integration Configurations across Categories...")
        # Add LLM Provider 1: OpenAI (Priority 1)
        llm1 = APIIntegrationConfig(
            api_category="LLM",
            provider_name="openai",
            encrypted_key=encrypt_api_key("sk-proj-testOpenAIKey123"),
            model_name="gpt-4o",
            priority=1,
            is_active=True
        )
        # Add LLM Provider 2: Gemini (Priority 2 - Backup)
        llm2 = APIIntegrationConfig(
            api_category="LLM",
            provider_name="gemini",
            encrypted_key=encrypt_api_key("AIzaSyTestGeminiKey456"),
            model_name="gemini-2.0-flash",
            priority=2,
            is_active=True
        )
        # Add LLM Provider 3: Claude (Priority 3 - Second Backup)
        llm3 = APIIntegrationConfig(
            api_category="LLM",
            provider_name="claude",
            encrypted_key=encrypt_api_key("sk-ant-testClaudeKey789"),
            model_name="claude-3-5-sonnet",
            priority=3,
            is_active=True
        )

        # Add Azure API Integration
        azure_ad = APIIntegrationConfig(
            api_category="AZURE",
            provider_name="azure_ad",
            encrypted_key=encrypt_api_key("sample_azure_client_secret"),
            endpoint_url="https://login.microsoftonline.com/00000000-0000-0000-0000-000000000000",
            model_name="11111111-1111-1111-1111-111111111111",
            priority=1,
            is_active=True
        )

        # Add Maps API Integration
        google_maps = APIIntegrationConfig(
            api_category="MAPS",
            provider_name="google_maps",
            encrypted_key=encrypt_api_key("AIzaSyTestGoogleMapsKey999"),
            priority=1,
            is_active=True
        )

        # Add Custom 3rd Party Integration
        servicenow = APIIntegrationConfig(
            api_category="ITSM_SIEM",
            provider_name="servicenow",
            encrypted_key=encrypt_api_key("sample_servicenow_auth_token"),
            endpoint_url="https://instance.service-now.com/api/now/table/",
            extra_headers_json='{"X-Custom-Auth": "Bearer XYZ"}',
            priority=1,
            is_active=True
        )

        db.add_all([llm1, llm2, llm3, azure_ad, google_maps, servicenow])
        db.commit()
        print("   [OK] Created 6 test API integration entries in SQL Express/SQLite DB.")

        print("\n2. Verify Decryption & Key Security...")
        decrypted_openai = decrypt_api_key(llm1.encrypted_key)
        assert decrypted_openai == "sk-proj-testOpenAIKey123", "Key decryption failed"
        print("   [OK] Key encryption & Fernet 32-byte AES decryption verified.")

        print("\n3. Execute LLM Request with No Errors (Normal Execution)...")
        res1 = ai_orchestrator.execute_llm_with_failover(db, prompt="Analyze licenses")
        print(f"   Active Provider Used: '{res1['active_provider'].upper()}' (Priority #{res1['priority_used']})")
        assert res1["active_provider"] == "openai", f"Expected openai but got {res1['active_provider']}"
        assert not res1["failover_occurred"], "Failover should not occur when primary works"
        print("   [OK] Primary LLM (OpenAI) served request cleanly.")

        print("\n4. Simulate Primary LLM (OpenAI) Failure & Test Auto-Switching...")
        res2 = ai_orchestrator.execute_llm_with_failover(
            db=db,
            prompt="Analyze licenses",
            simulate_errors=["openai"]
        )
        print(f"   Active Provider Used: '{res2['active_provider'].upper()}' (Priority #{res2['priority_used']})")
        print(f"   Failover Occurred: {res2['failover_occurred']}")
        assert res2["active_provider"] == "gemini", f"Expected auto-switch to gemini but got {res2['active_provider']}"
        assert res2["failover_occurred"], "Failover flag should be True"
        print("   [OK] Auto-switching engine successfully failed over from OpenAI -> Gemini!")

        print("\n5. Simulate Cascade Failure (OpenAI + Gemini) & Test 2nd Level Failover...")
        res3 = ai_orchestrator.execute_llm_with_failover(
            db=db,
            prompt="Analyze licenses",
            simulate_errors=["openai", "gemini"]
        )
        print(f"   Active Provider Used: '{res3['active_provider'].upper()}' (Priority #{res3['priority_used']})")
        assert res3["active_provider"] == "claude", f"Expected auto-switch to claude but got {res3['active_provider']}"
        print("   [OK] Multi-tier failover successfully auto-switched OpenAI -> Gemini -> Claude!")

        print("\n==========================================================================")
        print("ALL TESTS PASSED SUCCESSFULLY! Multi-API Hub and Auto-Switch Failover Ready.")
        print("==========================================================================")

    finally:
        db.close()

if __name__ == "__main__":
    test_api_integrations_and_failover()
