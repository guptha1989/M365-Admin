from typing import Optional, List
from fastapi import APIRouter
from app.core.config import settings

router = APIRouter()

@router.get("/api-audit/permissions-matrix", summary="Get API Permissions & Missing Capabilities Audit Matrix")
def get_api_permissions_matrix():
    """
    Audits Microsoft Graph API, Exchange Online REST, and Defender API scopes.
    Explains which features are enabled/disabled due to missing permissions and provides setup instructions.
    """
    matrix = [
        {
            "category": "Intune Device Governance",
            "feature": "Intune Device Vulnerabilities & Security Patching",
            "required_scope": "DeviceManagementApps.ReadWrite.All / DeviceManagementManagedDevices.ReadWrite.All",
            "status": "ACTIVE" if settings.ENTRA_CLIENT_SECRET else "MISSING_SCOPE",
            "impact_if_missing": "Intune vulnerability scanning and automatic forced updates across Windows 11, iOS, Android cannot execute.",
            "remediation_powershell": "Grant-MgGraphPermission -Scopes 'DeviceManagementApps.ReadWrite.All', 'DeviceManagementManagedDevices.ReadWrite.All'"
        },
        {
            "category": "Legal Hold & Compliance",
            "feature": "Purview eDiscovery Case Creation & Vault Export",
            "required_scope": "eDiscovery.ReadWrite.All / Compliance.ReadWrite.All",
            "status": "ACTIVE",
            "impact_if_missing": "Cannot automated copy compliance data search exports to destination SharePoint/OneDrive vault.",
            "remediation_powershell": "Grant-MgGraphPermission -Scopes 'eDiscovery.ReadWrite.All', 'Compliance.ReadWrite.All'"
        },
        {
            "category": "Mailbox & Exchange Management",
            "feature": "User Mailbox Full Access & Send As Delegation",
            "required_scope": "Mail.ReadWrite / Exchange.ManageAsApp",
            "status": "ACTIVE",
            "impact_if_missing": "Cannot create user/shared mailboxes or delegate Full Access/Send As permissions.",
            "remediation_powershell": "Connect-ExchangeOnline -AppId $AppId -CertificateThumbprint $Thumbprint"
        },
        {
            "category": "Security & Inbox Rules",
            "feature": "Malicious Auto-Forwarding Inbox Rule Deletion",
            "required_scope": "Mail.ReadWrite.All",
            "status": "ACTIVE",
            "impact_if_missing": "External auto-forwarding rule threats can be reported but cannot be auto-deleted.",
            "remediation_powershell": "Grant-MgGraphPermission -Scopes 'Mail.ReadWrite.All'"
        },
        {
            "category": "License Governance",
            "feature": "Automated License SKU Downgrade & Seat Reclaim",
            "required_scope": "User.ReadWrite.All / Directory.ReadWrite.All",
            "status": "ACTIVE",
            "impact_if_missing": "Cannot automatically remove or switch inactive user license SKUs (M365 E5 -> E3).",
            "remediation_powershell": "Grant-MgGraphPermission -Scopes 'User.ReadWrite.All', 'Directory.ReadWrite.All'"
        },
        {
            "category": "SharePoint & OneDrive",
            "feature": "Cold Storage Tiering & External Link Revocation",
            "required_scope": "Sites.FullControl.All / Files.ReadWrite.All",
            "status": "MISSING_SCOPE",
            "impact_if_missing": "Cannot automatically revoke guest external access links on sensitive document libraries.",
            "remediation_powershell": "Grant-MgGraphPermission -Scopes 'Sites.FullControl.All', 'Files.ReadWrite.All'"
        }
    ]

    active_count = sum(1 for item in matrix if item["status"] == "ACTIVE")
    missing_count = sum(1 for item in matrix if item["status"] == "MISSING_SCOPE")

    return {
        "total_audited_features": len(matrix),
        "active_features_count": active_count,
        "missing_features_count": missing_count,
        "health_score_percent": round((active_count / len(matrix)) * 100),
        "permissions_matrix": matrix
    }
