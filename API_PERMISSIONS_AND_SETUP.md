# Microsoft 365 Admin & AI Governance Platform
## API Permissions, App Registration & Access Integration Guide

This guide provides step-by-step instructions on creating the required Azure AD (Entra ID) App Registration, assigning Microsoft Graph API permissions, generating Client Secrets, and configuring multi-LLM / 3rd-party integrations for this application.

---

## 📂 Table of Contents
1. [Overview](#1-overview)
2. [Step-by-Step Azure AD (Entra ID) App Registration](#2-step-by-step-azure-ad-entra-id-app-registration)
3. [Microsoft Graph & Azure API Permissions Matrix](#3-microsoft-graph--azure-api-permissions-matrix)
4. [Client Secret & Authentication Setup](#4-client-secret--authentication-setup)
5. [Multi-LLM, Maps & Webhook APIs](#5-multi-llm-maps--webhook-apis)
6. [Configuring Credentials in the Application](#6-configuring-credentials-in-the-application)
   - [Method A: Configuration File (.env)](#method-a-configuration-file-env)
   - [Method B: Multi-API Integration Hub UI](#method-b-multi-api-integration-hub-ui)
7. [Verification & Testing](#7-verification--testing)

---

## 1. Overview

The **M365 Administration & AI Governance Platform** interacts with Microsoft 365 services using the **Microsoft Graph REST API** and Azure APIs. Because the platform executes automated background governance, auditing, and telemetry sync, it uses the **OAuth 2.0 Client Credentials Grant Flow** (Application Permissions mode) rather than delegated user logins.

---

## 2. Step-by-Step Azure AD (Entra ID) App Registration

To connect the application to your Microsoft 365 tenant:

1. Sign in to the **[Microsoft Entra Admin Center](https://entra.microsoft.com)** or **[Azure Portal](https://portal.azure.com)** as a **Global Administrator** or **Application Administrator**.
2. In the left navigation menu, expand **Identity** $\rightarrow$ select **App registrations**.
3. Click **+ New registration** at the top of the pane.
4. Enter the registration details:
   - **Name**: `M365 Admin Governance Platform`
   - **Supported account types**: Select **Accounts in this organizational directory only (Single tenant)**.
   - **Redirect URI**: Leave blank (Daemon / API service).
5. Click **Register**.
6. On the **Overview** page, copy and save the following credentials:
   - **Application (client) ID**: *(e.g. `00000000-0000-0000-0000-000000000000`)*
   - **Directory (tenant) ID**: *(e.g. `00000000-0000-0000-0000-000000000000`)*

---

## 3. Microsoft Graph & Azure API Permissions Matrix (Phase-Wise)

Because the platform supports 3 progressive Tenant Governance Phases (**Phase 1: Reporting Only**, **Phase 2: Semi-Automated**, and **Phase 3: Fully Automated**), permissions can be granted incrementally following the **Principle of Least Privilege (PoLP)**.

### Adding Permissions in Azure Portal:
1. In your App Registration, click **API permissions** in the left menu.
2. Click **+ Add a permission**.
3. Select **Microsoft Graph** $\rightarrow$ click **Application permissions**.
4. Add the permissions corresponding to your active governance phase as detailed below.

---

### 📊 Phase 1: Reporting Only (Read-Only Telemetry)
In Phase 1, the platform reads telemetry, monitors inbox rules, tracks license usage, and scans vulnerabilities without making modifications.

| Module / Feature | Required Permission (Application) | Purpose in Phase 1 |
| :--- | :--- | :--- |
| **User & Mailbox Inventory** | `User.Read.All` | Read user principal names, departments, and custom attributes |
| **Inbox Rule Audit** | `MailboxSettings.Read` | Scan active/disabled inbox rules and external forwarding targets |
| **Mailflow Telemetry** | `AuditLog.Read.All` | Track external domain auto-forwarding and email volume counts |
| **Azure AD & License Audit** | `Directory.Read.All` | Audit inactive users (60/90/120 days) and SKU license usage |
| **Azure AD Risky Users** | `IdentityRiskEvent.Read.All` | Identity protection risk events and compromised user tracking |
| **SharePoint & OneDrive** | `Sites.Read.All` | Storage analytics, site inventory, and external sharing detection |
| **SharePoint File Types** | `Files.Read.All` | Read file extensions (.xlsx, .pdf) and last-accessed metadata |
| **Teams Call Quality** | `CallRecords.Read.All` | Telemetry for audio jitter, packet loss %, and network subnets |
| **Service Outages Map** | `ServiceHealth.Read.All` | Live M365 Service Announcements and regional outage map |
| **Defender Vulnerabilities** | `Vulnerability.Read.All` | Intune device vulnerability CVE matrix mapping |

---

### ⚡ Phase 2: Semi-Automated (Prompt Review & User Approval)
In Phase 2, administrators receive AI recommendations and manually trigger execution actions (e.g. license upgrades, mailbox setting toggles, individual inbox rule creation/deletion).

*Includes all Phase 1 Read permissions plus the following additional write/manage permissions:*

| Module / Action | Additional Permission Required | Purpose in Phase 2 |
| :--- | :--- | :--- |
| **License & User Mgmt** | `User.ReadWrite.All` | Execute license upgrades/downgrades and assign attributes |
| **Inbox Rule Actions** | `MailboxSettings.ReadWrite` | Create, toggle (enable/disable), and delete user inbox rules |
| **SharePoint Cleanup** | `Sites.ReadWrite.All` | Update site sharing permissions and archive stale files |
| **Teams Digest & Bot** | `ChannelMessage.Send` | Send proactive AI recommendation cards & interactive approval prompts |
| **Security Alerts** | `SecurityEvents.ReadWrite.All` | Acknowledge and resolve security alerts in Defender |

---

### 🤖 Phase 3: Fully Automated (Policy-Driven Zero-Touch Remediation)
In Phase 3, background policy engines automatically enforce security rules (e.g. auto-purging external email forwarding rules, auto-converting shared mailboxes, auto-enforcing retention holds).

*Includes all Phase 1 & Phase 2 permissions plus the following advanced enforcement permissions:*

| Module / Automation | Additional Permission Required | Purpose in Phase 3 |
| :--- | :--- | :--- |
| **Exchange Online App Access** | `Exchange.ManageAsApp` | Exchange PowerShell/REST app-only access for Litigation Hold, shared mailbox conversions, and tenant-wide rule purges |
| **Distribution Groups** | `Group.ReadWrite.All` | Automated DL membership updates based on department naming conventions (`GRP_<DEPT>_`) |
| **Risky User Auto-Isolation** | `Policy.ReadWrite.ConditionalAccess` | Trigger automatic Conditional Access sign-in blocks for compromised high-risk users |
| **Zero-Touch External Purge** | `MailboxSettings.ReadWrite` | Background automated purging of external forwarding rules across all tenant mailboxes |

---

> [!IMPORTANT]
> **Granting Admin Consent**: After adding permissions for your desired phase, click **Grant admin consent for [Your Tenant Name]** at the top of the API permissions page in Azure Portal. Confirm with **Yes**. All permissions must display a green checkmark under **Status**.

---

## 4. Client Secret & Authentication Setup

1. In your App Registration left sidebar, click **Certificates & secrets**.
2. Select the **Client secrets** tab $\rightarrow$ click **+ New client secret**.
3. Configure the secret:
   - **Description**: `M365 Admin Bot Client Secret`
   - **Expires**: Select `180 days (6 months)` or `24 months`.
4. Click **Add**.
5. ⚠️ **Copy the secret `Value` immediately** from the list. (This value will be masked permanently once you leave the page).

---

## 5. Multi-LLM, Maps & Webhook APIs

The platform features an extensible Multi-API Integration Hub supporting multiple AI models with automatic failover, interactive maps, and webhooks.

### A. Multi-LLM Provider API Keys
- **OpenAI (GPT-4o)**: Obtain key from [OpenAI API Portal](https://platform.openai.com/).
- **Google Gemini**: Obtain key from [Google AI Studio](https://aistudio.google.com/).
- **Anthropic Claude**: Obtain key from [Anthropic Console](https://console.anthropic.com/).
- **Azure OpenAI**: Obtain Endpoint URL and Key from Azure OpenAI Resource in Azure Portal.
- **Local Ollama / vLLM**: Point to local server (Default: `http://localhost:11434/v1`).

### B. Maps APIs (Outage & Call Quality Mapping)
- **Google Maps**: Enable Maps JavaScript API in Google Cloud Console.
- **Azure Maps**: Copy Primary Key from Azure Maps Account in Azure Portal.
- **OpenStreetMap**: Uses open tile server (`https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png`).

### C. Microsoft Teams Daily Digest Webhook
1. Open Microsoft Teams $\rightarrow$ navigate to target Channel.
2. Click **... (More Options)** $\rightarrow$ **Connectors** or **Workflows**.
3. Select **Incoming Webhook** $\rightarrow$ click **Add** / **Configure**.
4. Name the webhook `M365 Admin Bot` and click **Create**.
5. Copy the generated Webhook URL.

---

## 6. Configuring Credentials in the Application

### Method A: Configuration File (`.env`)

Create or edit the `.env` file in the application root directory (`M365 Admin Bot/.env`):

```ini
# ==============================================================================
# M365 Administration & AI Governance Platform Configuration
# ==============================================================================

# 1. Execution Profile Mode ('TEST' caps at 50 objects max, 'PROD' runs full tenant)
ENV=PROD

# 2. Database Tier (SQLite local default or SQL Express connection string)
DATABASE_URL=sqlite:///./m365_admin.db
# DATABASE_URL=mssql+pyodbc://sa:YourPassword@localhost/M365AdminDB?driver=ODBC+Driver+17+for+SQL+Server

# 3. Security Credentials
SECRET_KEY=Your32ByteJWTSecretKeyHere!
ENCRYPTION_KEY=gAAAAABk_YourFernetEncryptionKeyHere=

# 4. Microsoft Entra ID (Azure AD) Credentials
ENTRA_TENANT_ID=00000000-0000-0000-0000-000000000000
ENTRA_CLIENT_ID=00000000-0000-0000-0000-000000000000
ENTRA_CLIENT_SECRET=your_entra_client_secret_here
M365_DEFENDER_API_KEY=your_defender_key_here

# 5. Multi-LLM Provider API Keys & Auto-Switch Failover
LLM_FAILOVER_ORDER=openai,gemini,claude,azure_openai,local,deepseek,groq,cohere,mistral,huggingface
OPENAI_API_KEY=your_openai_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
CLAUDE_API_KEY=your_claude_api_key_here
AZURE_OPENAI_KEY=your_azure_openai_key_here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
LOCAL_LLM_URL=http://localhost:11434/v1

# 6. Maps & Messaging Webhooks
GOOGLE_MAPS_KEY=your_google_maps_key_here
MAPS_API_KEY=your_maps_api_key_here
TEAMS_WEBHOOK_URL=https://outlook.office.com/webhook/your-teams-webhook-url
```

---

### Method B: Multi-API Integration Hub UI

You can also manage and test all API integration credentials directly from the web interface without restarting the server:

1. Launch the application (`python run_server.py`) and navigate to [`http://127.0.0.1:8000`](http://127.0.0.1:8000).
2. Click **🌐 API Integration Hub & LLM Auto-Switch** in the bottom-left sidebar.
3. Use the interactive tabs:
   - **🤖 Multi-LLM & Failover**: Add keys for OpenAI, Gemini, Claude, etc., and specify their priority rank.
   - **☁️ Azure APIs**: Input Entra ID Tenant ID, Client ID, Client Secret, and Azure Subscription details.
   - **🗺️ Maps APIs**: Add Google Maps, Azure Maps, or Mapbox tokens.
   - **🔌 Future / Custom APIs**: Connect ITSM/SIEM services like ServiceNow or Splunk.
   - **⚡ Live Failover Simulator**: Run real-time simulation tests to verify automatic failover when a provider rate-limits or fails.

---

## 7. Verification & Testing

To verify API credentials and permissions:

1. Open the interactive API documentation at **[`http://127.0.0.1:8000/api/v1/docs`](http://127.0.0.1:8000/api/v1/docs)**.
2. Execute a test call to GET `/api/v1/health`.
3. Check the response status and ensure `db_connected: true` and `environment` profile load cleanly.
4. Navigate to **Mailbox Reports** or **Exchange Inbox Rule Report** in the web dashboard to inspect live data rendering.
