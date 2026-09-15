from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from app.core.security import get_current_user, require_roles
from app.core.config import settings
from app.services.graph_client import graph_client

router = APIRouter()

@router.get("/outages", summary="M365 Outage Dashboard with Geographic Region Map")
def get_outage_dashboard(user: dict = Depends(get_current_user)):
    """Connects to Service Announcement issues endpoint with Geographical Region Map formatting."""
    return graph_client.get_m365_outages()

@router.get("/exchange-mailflow", summary="Exchange & Mailflow Telemetry (1-Year Cache)")
def get_exchange_mailflow(
    window_days: int = Query(30, description="Reporting window: 15, 30, or 365 days"),
    user: dict = Depends(get_current_user)
):
    """Fetch license reports, mailbox settings, and 1-year historical mailflow telemetry."""
    if window_days not in settings.EXPORT_ALLOWED_WINDOWS:
        raise HTTPException(status_code=400, detail=f"Export/download window must be one of {settings.EXPORT_ALLOWED_WINDOWS} days.")
    
    licenses = graph_client.get_license_reports()
    mailflow = graph_client.get_mailflow_analytics(window_days=window_days)
    return {
        "licenses": licenses,
        "mailflow_analytics": mailflow
    }

@router.get("/security-identity", summary="Security & Identity Audits & CVE Vulnerability Mapping")
def get_security_identity(user: dict = Depends(require_roles(["SecurityAdmin", "GlobalAdmin"]))):
    """Intune device inventory cross-referenced with M365 Defender CVE vulnerabilities, Azure AD sync errors, and app registrations."""
    cve_report = graph_client.get_intune_defender_vulnerability_report()
    azure_ad_data = graph_client.get_azure_ad_insights()
    return {
        "intune_defender_cve_mapping": cve_report,
        "azure_ad_insights": azure_ad_data
    }

@router.get("/collaboration", summary="Collaboration (Teams Call Quality & SharePoint Usage)")
def get_collaboration_reports(user: dict = Depends(get_current_user)):
    """Teams call quality drops audit, SharePoint usage drill-down, and external sensitive data sharing detection."""
    teams_cqd = graph_client.get_teams_call_quality()
    sp_analytics = graph_client.get_sharepoint_analytics()
    return {
        "teams_call_quality": teams_cqd,
        "sharepoint_analytics": sp_analytics
    }

@router.get("/mailbox-reports", summary="Mailbox Reports (Inbox rules, Retention policies, Litigation hold)")
def get_mailbox_reports_endpoint(user: dict = Depends(get_current_user)):
    return graph_client.get_mailbox_reports()

@router.get("/azure-ad/inactive", summary="Azure AD Inactive Users by 60, 90, 120 days")
def get_azure_ad_inactive_endpoint(days: int = Query(90, description="Inactivity threshold days (60, 90, 120)"), user: dict = Depends(get_current_user)):
    return graph_client.get_azure_ad_inactive_users(inactivity_days=days)

@router.get("/azure-ad/licenses-summary", summary="Azure AD Licenses Breakdown (Trial vs Paid, Used vs Available)")
def get_azure_ad_licenses_endpoint(user: dict = Depends(get_current_user)):
    return graph_client.get_azure_ad_licenses_breakdown()

@router.get("/mailflow/volume", summary="Email Volume Sent/Received (30, 90, 120 days)")
def get_mailflow_volume_endpoint(window_days: int = Query(30, description="Reporting window (30, 90, 120)"), user: dict = Depends(get_current_user)):
    return graph_client.get_mailflow_detailed_volume(window_days=window_days)

@router.get("/collaboration/file-types-and-inactive", summary="SharePoint/OneDrive File Types Breakdown & Inactive Libraries with File URLs")
def get_collaboration_file_types_endpoint(user: dict = Depends(get_current_user)):
    return graph_client.get_sharepoint_file_types_and_inactive()

@router.get("/management/distribution-groups", summary="Distribution Groups Management by Department/Team Naming Convention")
def get_mgmt_dl_endpoint(user: dict = Depends(get_current_user)):
    return graph_client.get_distribution_groups_management()

@router.get("/management/shared-mailboxes", summary="Shared Mailboxes Management & Categorization")
def get_mgmt_shared_mb_endpoint(user: dict = Depends(get_current_user)):
    return graph_client.get_shared_mailboxes_management()

@router.get("/management/room-mailboxes", summary="Room Mailboxes Management & Booking Schedules")
def get_mgmt_room_mb_endpoint(user: dict = Depends(get_current_user)):
    return graph_client.get_room_mailboxes_management()

@router.get("/failed-updates", summary="M365 Apps, Windows OS, Defender & Intune Failed Updates Telemetry Report")
def get_failed_updates_endpoint(user: dict = Depends(get_current_user)):
    return graph_client.get_failed_updates_report()

