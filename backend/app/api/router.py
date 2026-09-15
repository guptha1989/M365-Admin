from fastapi import APIRouter
from app.api.v1 import (
    health,
    reports,
    management,
    ai_engine,
    legal_hold,
    admin_reports,
    ai_governance,
    api_integrations,
    auditing,
    azure_ad,
    distribution_groups,
    exchange_mgmt,
    mailboxes,
    mailflow,
    outages,
    sharepoint_onedrive,
    teams_integration,
    policies,
    compliance_security,
    requests,
    auth_tenants,
    intune_vulnerabilities,
    api_audit
)

api_router = APIRouter()

# System Health Endpoint
api_router.include_router(health.router, tags=["System Health"])

# SSO Authentication, Tenants, & Per-Module Phase Management
api_router.include_router(auth_tenants.router, tags=["SSO Authentication & Multi-Tenant Management"])

# Intune Vulnerability Governance
api_router.include_router(intune_vulnerabilities.router, tags=["Intune Security Vulnerabilities"])

# API Scope & Permissions Audit Matrix
api_router.include_router(api_audit.router, tags=["API Permissions & Scope Audit"])

# Centralized Request Management Router
api_router.include_router(requests.router, prefix="/requests", tags=["Centralized Request Management Hub"])

# Core Module Routers
api_router.include_router(reports.router, prefix="/reports", tags=["Part 1: Reports Module"])
api_router.include_router(management.router, prefix="/management", tags=["Part 2: Management Module"])
api_router.include_router(ai_engine.router, prefix="/ai-engine", tags=["Part 3: AI Policy Engine & LLM Vault"])
api_router.include_router(legal_hold.router, prefix="/legal-hold", tags=["Part 4: Legal Hold Case Management (Isolated)"])
api_router.include_router(policies.router, prefix="/policies", tags=["Dedicated Policy Management Engine"])
api_router.include_router(compliance_security.router, prefix="/compliance", tags=["Compliance & Security Governance"])
api_router.include_router(compliance_security.router, prefix="/compliance-security", tags=["Compliance & Security Governance"])

# Feature & UI Module Routers
api_router.include_router(admin_reports.router, prefix="/admin-reports", tags=["Admin Reports"])
api_router.include_router(ai_governance.router, prefix="/ai-governance", tags=["AI Governance"])
api_router.include_router(api_integrations.router, prefix="/integrations", tags=["API Integrations"])
api_router.include_router(auditing.router, prefix="/auditing", tags=["App Auditing"])
api_router.include_router(azure_ad.router, prefix="/azure-ad", tags=["Azure Active Directory"])
api_router.include_router(distribution_groups.router, prefix="/distribution-groups", tags=["Distribution Groups"])
api_router.include_router(exchange_mgmt.router, prefix="/exchange", tags=["Exchange & License Management"])
api_router.include_router(mailboxes.router, prefix="/mailboxes", tags=["Mailbox Management"])
api_router.include_router(mailflow.router, prefix="/mailflow", tags=["Mailflow Report"])
api_router.include_router(outages.router, prefix="/outages", tags=["Outages Dashboard"])
api_router.include_router(sharepoint_onedrive.router, prefix="/sharepoint", tags=["SharePoint & OneDrive"])
api_router.include_router(teams_integration.router, prefix="/teams", tags=["Teams Integration"])



