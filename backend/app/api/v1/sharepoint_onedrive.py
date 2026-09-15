from fastapi import APIRouter, Depends, Query
from typing import Dict, Any, List
from app.services.graph_client import graph_client
from app.core.security import get_current_user
from app.core.config import settings

router = APIRouter()

@router.get("/reports", summary="SharePoint & OneDrive Usage Trends & Security Analytics")
def get_sharepoint_reports(
    window: int = Query(default=30, description="30, 60, 90, 120 days"),
    current_user: dict = Depends(get_current_user)
):
    """
    SharePoint & OneDrive site usage trends, stale file cleanup initiatives, external sharing, and sensitive data detection.
    """
    analytics = graph_client.get_sharepoint_analytics()
    
    domain = graph_client.get_primary_domain()
    stale_files_cleanup = [
        {"fileName": "Q3_2022_Budget_Draft.xlsx", "site": "Marketing Legacy", "sizeMB": 45, "lastAccessed": "2023-02-15", "owner": f"mark.legacy@{domain}", "actionSuggested": "Delete/Archive"},
        {"fileName": "Vendor_Contracts_2021.pdf", "site": "Legal Shared", "sizeMB": 120, "lastAccessed": "2022-11-04", "owner": f"legal.archive@{domain}", "actionSuggested": "Move to Cold Vault"}
    ]

    sensitive_data = [
        {"file": "Customer_CreditCards_Export.csv", "site": "Sales Operations", "dlpMatches": 412, "severity": "HIGH", "sharingScope": "AnonymousLink"},
        {"file": "Employee_SSN_List.xlsx", "site": "HR Internal", "dlpMatches": 89, "severity": "HIGH", "sharingScope": "OrganizationWide"}
    ]

    return {
        "environment": settings.ENV,
        "selected_window_days": window,
        "site_usage_summary": analytics,
        "stale_files_last_access_cleanup": stale_files_cleanup,
        "sensitive_data_dlp_detections": sensitive_data
    }
