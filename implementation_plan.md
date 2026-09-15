# 🚀 Implementation Plan: M365 Multi-Tenant SSO, Granular RBAC, Per-Module Phase Settings, Centralized Settings Tab, Intune Vulnerability Reporting & API Audit

This implementation plan details the technical architecture and step-by-step additions to empower the **Microsoft 365 Administration & AI Governance Platform** with multi-tenant SSO, granular role assignment, per-module phase overrides, centralized settings, Intune security vulnerability reporting, and an API permission scope audit hub.

---

## 📑 User Review Required

> [!IMPORTANT]
> **Key Architectural Enhancements for Review**:
> 1. **Multi-Tenant Data Segregation & Global Filter**: Data from 3 tenants (`Contoso Corp`, `Fabrikam Inc`, `Litware Inc`) will be aggregated, and a prominent **Global Tenant & Domain Filter** in the top navigation bar will dynamically scope all dashboards and reports.
> 2. **SSO Auto-Provisioning & Unassigned Role Rule**: Newly authenticated M365 SSO users are automatically provisioned in the user directory with **NO roles assigned** (`[]`) and `Read-Only` access level by default. Global Administrators must explicitly assign module-specific admin roles (`ExchangeAdmin`, `SharePointAdmin`, `TeamsAdmin`, `SecurityAdmin`, `LicenseAdmin`, `LegalHoldAdmin`, `LegalHoldReader`, `GlobalAdmin`) and access tiers (`Read-Only`, `Member`, `Admin`).
> 3. **Per-Module Phase Settings (Default Phase 1)**: All governance modules default to **Phase 1 (Report Only)**. A dedicated configuration interface allows manual overrides to Phase 2 (Semi-Automated) or Phase 3 (Fully Automated Guardrails) per module.
> 4. **New Sidebar Tabs**:
>    - **Platform & Tools $\rightarrow$ Settings & Configuration**: Centralizes AI/LLM keys, API secrets, SSO user role management, and module phase overrides.
>    - **Category 1: Reporting $\rightarrow$ Intune Vulnerability Report**: Detailed CVE vulnerability tracking, CVSS risk scores, affected device inventory, and step-by-step remediation plans integrated into AI Governance recommendations.
>    - **Platform & Tools $\rightarrow$ API Permissions & Scope Audit**: Audit matrix showing enabled vs disabled capabilities based on Graph API scopes, with exact remediation commands.

---

## 🛠️ Proposed Changes

### Database Models & Core Backend Architecture (`backend/app/db/` & `backend/app/core/`)

#### [MODIFY] [models.py](file:///d:/OneDrive%20-%20TECHFROST/Antigravity%20MS%20Laptop/M365%20Admin%20Bot/backend/app/db/models.py)
- **New Table `RegisteredTenant`**: Stores multi-tenant profiles (`tenant_id`, `tenant_name`, `primary_domain`, `client_id`, `encrypted_client_secret`, `is_active`).
- **New Table `AppUser`**: User directory tracking signed-up M365 SSO users (`user_principal_name`, `display_name`, `tenant_id`, `roles_json`, `access_level`, `is_active`).
- **New Table `ModulePhaseConfig`**: Tracks per-module phase overrides (`module_key`, `active_phase`, `updated_by`).
- **New Table `IntuneVulnerability`**: Tracks device security vulnerabilities, CVE IDs, CVSS scores, affected OS/devices, and remediation steps.

#### [MODIFY] [security.py](file:///d:/OneDrive%20-%20TECHFROST/Antigravity%20MS%20Laptop/M365%20Admin%20Bot/backend/app/core/security.py)
- Support SSO token validation and dynamic RBAC role checking for module access levels (`Read-Only`, `Member`, `Admin`).
- Validate user claims against assigned domain roles (`ExchangeAdmin`, `LegalHoldAdmin`, etc.).

---

### Backend API Routers (`backend/app/api/v1/`)

#### [NEW] [auth_tenants.py](file:///d:/OneDrive%20-%20TECHFROST/Antigravity%20MS%20Laptop/M365%20Admin%20Bot/backend/app/api/v1/auth_tenants.py)
- `GET /api/v1/auth/me`: Fetches current SSO user profile and assigned roles.
- `POST /api/v1/auth/sso-login`: Handles M365 SSO sign-in and auto-provisions new users with no roles.
- `GET /api/v1/auth/users`: Lists registered SSO users.
- `POST /api/v1/auth/users/assign-roles`: Updates user assigned roles (`GlobalAdmin`, `LegalHoldAdmin`, etc.) and access level (`Read-Only`, `Member`, `Admin`).
- `GET /api/v1/tenants/list`: Lists registered tenants for global filter bar.
- `POST /api/v1/tenants/register`: Adds new tenant profile to platform.

#### [NEW] [intune_vulnerabilities.py](file:///d:/OneDrive%20-%20TECHFROST/Antigravity%20MS%20Laptop/M365%20Admin%20Bot/backend/app/api/v1/intune_vulnerabilities.py)
- `GET /api/v1/intune/vulnerabilities`: Returns CVE inventory, CVSS scores, affected device breakdown (Windows 11, iOS, Android), and remediation steps.
- `POST /api/v1/intune/vulnerabilities/remediate`: Triggers automated Intune security patch deployment or device remediation.

#### [NEW] [api_audit.py](file:///d:/OneDrive%20-%20TECHFROST/Antigravity%20MS%20Laptop/M365%20Admin%20Bot/backend/app/api/v1/api_audit.py)
- `GET /api/v1/api-audit/permissions-matrix`: Compares granted Graph/Exchange API scopes against required scopes, returning missing capabilities and PowerShell setup commands.

#### [MODIFY] [ai_governance.py](file:///d:/OneDrive%20-%20TECHFROST/Antigravity%20MS%20Laptop/M365%20Admin%20Bot/backend/app/api/v1/ai_governance.py)
- Inject Intune CVE security vulnerabilities into the AI recommendations feed.

---

### Frontend SPA UI System (`frontend/`)

#### [MODIFY] [index.html](file:///d:/OneDrive%20-%20TECHFROST/Antigravity%20MS%20Laptop/M365%20Admin%20Bot/frontend/index.html)
- Add **Global Tenant & Domain Filter Selector** in the top navigation ribbon.
- Add **Intune Vulnerability Report** item under `Category 1: Reporting`.
- Add **Settings & Configuration** item under `Platform & Tools`.
- Add **API Permissions & Scope Audit** item under `Platform & Tools`.

#### [MODIFY] [app.js](file:///d:/OneDrive%20-%20TECHFROST/Antigravity%20MS%20Laptop/M365%20Admin%20Bot/frontend/js/app.js)
- Global `window.currentTenantFilter` state to filter telemetry by selected tenant across all modules.
- New module render function `renderIntuneVulnerabilities(container)`.
- New module render function `renderSettingsPage(container)` with 4 tabs:
  1. *AI & LLM Configuration*
  2. *API & Service Credentials*
  3. *Per-Module Phase Settings (Phase 1, 2, 3)*
  4. *User & RBAC Role Management*
- New module render function `renderApiAuditPage(container)`.

---

## 🔍 Verification Plan

### Automated Verification
1. **Node.js Syntax Check**: `node --check frontend/js/app.js` to ensure zero frontend syntax regressions.
2. **Python Backend Test**: Run test script validating endpoints `/api/v1/auth/users`, `/api/v1/tenants/list`, `/api/v1/intune/vulnerabilities`, `/api/v1/api-audit/permissions-matrix`.

### Manual Verification
1. Open http://127.0.0.1:8000 in browser.
2. Verify **Global Tenant Selector** in top ribbon filters data across dashboards.
3. Test **Intune Vulnerability Report** under Reporting.
4. Test **Settings & Configuration** tab under Platform & Tools.
5. Test **API Permissions & Scope Audit** tab under Platform & Tools.
