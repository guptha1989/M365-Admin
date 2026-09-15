import sys
import os
import requests
import json

# Add backend directory to sys.path
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.config import settings

def test_all_apis():
    results = {}

    print("==========================================================================")
    print("LIVE API INTEGRATION & PERMISSIONS TEST HARNESS")
    print("==========================================================================")

    # 1. Test Entra ID (Azure AD) & Microsoft Graph REST API
    print("\n--- 1. Testing Microsoft Entra ID OAuth2 Client Credentials Flow ---")
    token_url = f"https://login.microsoftonline.com/{settings.ENTRA_TENANT_ID}/oauth2/v2.0/token"
    token_payload = {
        "grant_type": "client_credentials",
        "client_id": settings.ENTRA_CLIENT_ID,
        "client_secret": settings.ENTRA_CLIENT_SECRET,
        "scope": "https://graph.microsoft.com/.default"
    }

    try:
        r = requests.post(token_url, data=token_payload, timeout=10)
        token_res = r.json()
        if "access_token" in token_res:
            print("✅ SUCCESS: Microsoft Graph OAuth2 Access Token Acquired!")
            access_token = token_res["access_token"]
            results["entra_id_oauth2"] = {"status": "SUCCESS", "token_type": token_res.get("token_type"), "expires_in": token_res.get("expires_in")}
            
            # Test Graph API Endpoints with Read-Only Access
            headers = {"Authorization": f"Bearer {access_token}"}
            
            # Users Endpoint (/v1.0/users)
            u_res = requests.get("https://graph.microsoft.com/v1.0/users?$top=10", headers=headers, timeout=10)
            if u_res.status_code == 200:
                users_data = u_res.json().get("value", [])
                print(f"  └─ GET /v1.0/users: HTTP 200 OK (Retrieved {len(users_data)} live tenant users)")
                results["graph_users"] = {"status": "SUCCESS", "count": len(users_data), "sample_users": [u.get("userPrincipalName") for u in users_data[:3]]}
            else:
                print(f"  └─ GET /v1.0/users: HTTP {u_res.status_code} - {u_res.text[:200]}")
                results["graph_users"] = {"status": "FAILED", "code": u_res.status_code, "error": u_res.text[:200]}

            # Subscribed SKUs / Licenses Endpoint (/v1.0/subscribedSkus)
            sku_res = requests.get("https://graph.microsoft.com/v1.0/subscribedSkus", headers=headers, timeout=10)
            if sku_res.status_code == 200:
                skus = sku_res.json().get("value", [])
                print(f"  └─ GET /v1.0/subscribedSkus: HTTP 200 OK (Retrieved {len(skus)} active license SKUs)")
                results["graph_licenses"] = {"status": "SUCCESS", "count": len(skus), "skus": [s.get("skuPartNumber") for s in skus]}
            else:
                print(f"  └─ GET /v1.0/subscribedSkus: HTTP {sku_res.status_code} - {sku_res.text[:200]}")
                results["graph_licenses"] = {"status": "FAILED", "code": sku_res.status_code, "error": sku_res.text[:200]}

            # Service Health Announcements (/v1.0/admin/serviceAnnouncement/issues)
            health_res = requests.get("https://graph.microsoft.com/v1.0/admin/serviceAnnouncement/issues?$top=5", headers=headers, timeout=10)
            if health_res.status_code == 200:
                incidents = health_res.json().get("value", [])
                print(f"  └─ GET /v1.0/admin/serviceAnnouncement/issues: HTTP 200 OK (Retrieved {len(incidents)} active health incidents)")
                results["graph_service_health"] = {"status": "SUCCESS", "count": len(incidents)}
            else:
                print(f"  └─ GET /v1.0/admin/serviceAnnouncement/issues: HTTP {health_res.status_code} (Requires ServiceHealth.Read.All permission)")
                results["graph_service_health"] = {"status": "PERMISSION_REQUIRED", "code": health_res.status_code}

        else:
            print("❌ FAILURE: Unable to acquire Graph token.")
            print("  └─ Response:", token_res)
            results["entra_id_oauth2"] = {"status": "FAILED", "response": token_res}
    except Exception as e:
        print("❌ ERROR testing Entra ID:", e)
        results["entra_id_oauth2"] = {"status": "ERROR", "error": str(e)}

    # 2. Test OpenAI API
    print("\n--- 2. Testing OpenAI API Integration ---")
    try:
        o_res = requests.get("https://api.openai.com/v1/models", headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"}, timeout=10)
        if o_res.status_code == 200:
            models = o_res.json().get("data", [])
            print(f"✅ SUCCESS: OpenAI API Key Verified! ({len(models)} models available)")
            results["openai"] = {"status": "SUCCESS", "model_count": len(models)}
        else:
            print(f"❌ OpenAI API Error: HTTP {o_res.status_code} - {o_res.text[:200]}")
            results["openai"] = {"status": "FAILED", "code": o_res.status_code, "error": o_res.text[:200]}
    except Exception as e:
        print("❌ ERROR testing OpenAI:", e)
        results["openai"] = {"status": "ERROR", "error": str(e)}

    # 3. Test Google Gemini API
    print("\n--- 3. Testing Google Gemini API Integration ---")
    try:
        g_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={settings.GEMINI_API_KEY}"
        gem_res = requests.get(g_url, timeout=10)
        if gem_res.status_code == 200:
            g_models = gem_res.json().get("models", [])
            print(f"✅ SUCCESS: Google Gemini API Key Verified! ({len(g_models)} models available)")
            results["gemini"] = {"status": "SUCCESS", "model_count": len(g_models)}
        else:
            print(f"❌ Gemini API Error: HTTP {gem_res.status_code} - {gem_res.text[:200]}")
            results["gemini"] = {"status": "FAILED", "code": gem_res.status_code, "error": gem_res.text[:200]}
    except Exception as e:
        print("❌ ERROR testing Gemini:", e)
        results["gemini"] = {"status": "ERROR", "error": str(e)}

    # 4. Test Google Maps API
    print("\n--- 4. Testing Google Maps API Integration ---")
    try:
        m_url = f"https://maps.googleapis.com/maps/api/geocode/json?address=New+York&key={settings.GOOGLE_MAPS_KEY}"
        map_res = requests.get(m_url, timeout=10)
        if map_res.status_code == 200:
            m_j = map_res.json()
            status = m_j.get("status")
            print(f"✅ Google Maps API Endpoint Responded! (Status: {status})")
            results["google_maps"] = {"status": status}
        else:
            print(f"❌ Maps API Error: HTTP {map_res.status_code} - {map_res.text[:200]}")
            results["google_maps"] = {"status": "FAILED", "code": map_res.status_code, "error": map_res.text[:200]}
    except Exception as e:
        print("❌ ERROR testing Google Maps:", e)
        results["google_maps"] = {"status": "ERROR", "error": str(e)}

    print("\n==========================================================================")
    print("FINAL SUMMARY REPORT:")
    print(json.dumps(results, indent=2))
    print("==========================================================================")

if __name__ == "__main__":
    test_all_apis()
