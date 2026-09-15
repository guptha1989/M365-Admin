import sys
import os
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_all():
    print("\n--- Testing Part 1: Reports Module ---")
    res = client.get("/api/v1/reports/outages")
    assert res.status_code == 200, res.text
    print("[OK] Outages Endpoint:", res.json()["status"])

    res = client.get("/api/v1/reports/exchange-mailflow?window_days=30")
    assert res.status_code == 200, res.text
    print("[OK] Exchange & Mailflow (1-Yr Cache):", res.json()["mailflow_analytics"]["window_days"], "days window")

    res = client.get("/api/v1/reports/failed-updates")
    assert res.status_code == 200, res.text
    print("[OK] Failed Updates Report Endpoint:", len(res.json()["failed_updates"]), "update failure items found")

    res = client.get("/api/v1/reports/security-identity")
    assert res.status_code == 200, res.text
    print("[OK] Security & Identity (CVE Map):", len(res.json()["intune_defender_cve_mapping"]), "vulnerabilities found")

    res = client.get("/api/v1/reports/collaboration")
    assert res.status_code == 200, res.text
    print("[OK] Collaboration (Teams & SharePoint): Audio Quality Score:", res.json()["teams_call_quality"]["overall_audio_quality_score"])

    print("\n--- Testing Part 2: Management Module ---")
    res = client.post("/api/v1/management/exchange-identity/licenses?upn=user1@lzwm.onmicrosoft.com&action=upgrade")
    assert res.status_code == 200, res.text
    print("[OK] Automated License Management:", res.json()["mode"])

    res = client.post("/api/v1/management/exchange-identity/retention-policies", json={
        "rbi_user_type": "VIP",
        "enabled_filter_attributes": ["Executive", "Legal"],
        "retention_days": 365
    })
    assert res.status_code == 200, res.text
    print("[OK] Retention Policy RBI Toggle Engine:", res.json()["mode"])

    res = client.post("/api/v1/management/mailboxes/create", json={
        "display_name": "Finance Shared",
        "upn": "fin-shared@lzwm.onmicrosoft.com",
        "department": "Finance",
        "mailbox_type": "Shared"
    })
    assert res.status_code == 200, res.text
    print("[OK] Mailbox Creator & Department Categorization:", res.json()["auto_assigned_category"])

    print("\n--- Testing Part 3: AI Recommendations & Policy Engine ---")
    res = client.post("/api/v1/ai-engine/keys", json={
        "provider": "openai",
        "api_key": "sk-proj-test1234567890secretkey",
        "model_name": "gpt-4o"
    })
    assert res.status_code == 200, res.text
    print("[OK] AES-256 Fernet Vault Store:", res.json()["status"])

    res = client.get("/api/v1/ai-engine/recommendations")
    assert res.status_code == 200, res.text
    print("[OK] AI Recommendations Feed:", len(res.json()), "items aggregated")

    res = client.post("/api/v1/ai-engine/execute-recommendation/101?execution_mode=AUTONOMOUS")
    assert res.status_code == 200, res.text
    print("[OK] AI Autonomous Execution via Defender API:", res.json()["mode"])

    print("\n--- Testing Part 4: Legal Hold Case Management (Isolated) ---")
    res = client.get("/api/v1/legal-hold/cases")
    assert res.status_code == 200, res.text
    print("[OK] Isolated Legal Hold Case Manager:", len(res.json()), "cases listed")

    res = client.post("/api/v1/legal-hold/request", json={
        "case_name": "Q3 Patent Hold",
        "custodian_email": "inventor@lzwm.onmicrosoft.com",
        "reason": "Preserve all lab notebook notes and email threads."
    })
    assert res.status_code == 200, res.text
    print("[OK] Legal Hold Request Form:", res.json()["case_number"], res.json()["status"])

    print("\n=========================================================")
    print(" ALL 4 MODULE CATEGORIES VERIFIED WITH 100% PURE REST APIs!")
    print("=========================================================")

if __name__ == "__main__":
    test_all()
