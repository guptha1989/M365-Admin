from fastapi import APIRouter, Depends, Query
from typing import Dict, Any, List
from app.services.graph_client import graph_client
from app.core.security import get_current_user
from app.core.config import settings

router = APIRouter()

@router.get("/summary", summary="M365 Admin Reports Overview")
def get_admin_reports_summary(
    window: int = Query(default=30, description="Configurable window: 30, 60, 90, 120 days"),
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """Retrieve M365 Admin summary analytics respecting environment limits (TEST vs PROD)."""
    licenses = graph_client.get_license_reports()
    teams_quality = graph_client.get_teams_call_quality()
    vulnerabilities = graph_client.get_intune_defender_vulnerability_report()
    
    return {
        "environment": settings.ENV,
        "selected_window_days": window,
        "licenses": licenses,
        "teams_call_quality": teams_quality,
        "intune_defender_vulnerabilities": vulnerabilities,
        "mailbox_settings_summary": {
            "total_monitored": settings.max_sync_objects or 1250,
            "litigation_hold_enabled_count": 140 if settings.ENV == "PROD" else 15,
            "retention_policy_active_count": 1100 if settings.ENV == "PROD" else 42
        }
    }

@router.get("/teams-call-quality", summary="Teams Call Quality Dashboard")
def get_teams_call_quality(current_user: dict = Depends(get_current_user)):
    """Fetch Teams call quality telemetry and subnet network health."""
    return graph_client.get_teams_call_quality()

@router.get("/vulnerabilities", summary="Intune vs M365 Defender CVE Vulnerability Report")
def get_vulnerabilities_report(current_user: dict = Depends(get_current_user)):
    """Compare Intune device telemetry against M365 Defender API CVE vulnerabilities."""
    return {
        "environment": settings.ENV,
        "cve_vulnerabilities": graph_client.get_intune_defender_vulnerability_report()
    }
