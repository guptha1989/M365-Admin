# Architecture Blueprint & Security Flow

## 1. System Topology & Decoupled Model

```text
+-----------------------------------------------------------------------------------+
|                              Frontend Client Layer                                |
|        Flet UI (Python / Flutter) - Single Codebase for Android (.apk),           |
|            Windows 11 (.msix), & Web Browser connecting over IP                   |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                             API Gateway (FastAPI)                                 |
|    - OAuth2 / Entra ID JWT Authentication & Granular RBAC Claims Scoping          |
|    - Environment Profiler (Pydantic BaseSettings: ENV=TEST vs ENV=PROD)           |
+----+--------------------+--------------------+--------------------+---------------+
     |                    |                    |                    |
     v                    v                    v                    v
+---------------+  +---------------+  +---------------+  +------------------+
| Part 1:       |  | Part 2:       |  | Part 3: AI    |  | Part 4: Legal    |
| Reports       |  | Management    |  | Engine & LLM  |  | Hold (Isolated)  |
| Module        |  | Module        |  | Orchestrator  |  | Module           |
+-------+-------+  +-------+-------+  +-------+-------+  +--------+---------+
        |                  |                  |                   |
        +------------------+------------------+-------------------+
                                           |
                                           v
+-----------------------------------------------------------------------------------+
|                        Execution Layer (100% Pure REST APIs)                       |
|   - Microsoft Graph REST API (v1.0 & beta) for Exchange, SharePoint, Teams, Identity |
|   - Azure REST API for Intune Telemetry & Resource Management                     |
|   - M365 Defender API for App Inventory & CVE Vulnerability Mapping               |
|   * Strictly 0% PowerShell - Pure Cross-Platform Python & REST execution          |
+------------------------------------------+----------------------------------------+
                                           |
                                           v
+-----------------------------------------------------------------------------------+
|               Data Tier (SQL Express with AES-256 Vault / SQLAlchemy)             |
|   - AES-256 Fernet Key Vault for 3rd Party API & LLM Keys                         |
|   - Config, Local Tenant Policies, 1-Year Historical Mailflow Cache               |
|   - Background Job Queues & Audit Logs                                            |
+-----------------------------------------------------------------------------------+
```

## 2. Core Components

1. **Frontend (Flet / Python UI)**:
   - Single Python codebase compiling natively to Android (.apk), Windows 11 (.msix), and Web Browsers.
   - Enterprise-grade dark/light mode responsive grid UI.

2. **API Gateway (FastAPI)**:
   - Central nervous system routing requests with Entra ID OAuth2 / JWT authentication and strict granular RBAC claims (`GlobalAdmin`, `ExchangeAdmin`, `SecurityAdmin`, `LegalHoldAdmin`, `Viewer`).

3. **Execution Layer (100% Pure REST APIs - 0% PowerShell)**:
   - Purely API-driven using Microsoft Graph REST APIs, Azure APIs, and M365 Defender APIs for seamless cross-platform execution.

4. **Data Tier (SQL Express & AES-256 Vault)**:
   - Stores configuration, local tenant policies, cached reports (1-year mailflow), AI API keys, and job queues.
   - Built-in AES-256 Fernet vault for encrypting third-party API and LLM keys.

5. **Environment Profiling (`ENV=TEST` vs `ENV=PROD`)**:
   - `ENV=TEST`: Hard-limits data synchronization to a maximum of 50 objects to respect SQL Express constraints.
   - `ENV=PROD`: Full object syncs with 30, 60, 90, and 120-day dashboard aggregation views.
   - All export/download routes locked to strict 15-day, 30-day, or 365-day (1-year) parameters.

6. **4 Decoupled Module Categories**:
   - **Part 1: Reports Module**: Outage Dashboard with Geographic Region Map, Exchange & 1-Year Mailflow Cache, Security & Identity (Intune CVE vulnerability map via Defender API, AD Connect sync errors, app registrations, risky users), Teams call quality drops & SharePoint sensitive sharing audits.
   - **Part 2: Management Module**: Automated license management, Retention policy dashboards mapped to `RBIusertype` with dynamic UI toggles, Mailboxes/DLs with department auto-categorization, SharePoint/OneDrive site & cleanup manager.
   - **Part 3: AI Recommendations & Policy Engine**: Multi-LLM orchestrator (OpenAI, Anthropic, local models), interactive `If/Then` Policy Builder, AI recommendation feed with Manual, Semi-automated, and Autonomous modes.
   - **Part 4: Legal Hold Case Management**: Physically decoupled router isolated with `LegalHoldAdmin` RBAC claim for hold requests, approval workflows, and In-Place hold case detail dashboards.
