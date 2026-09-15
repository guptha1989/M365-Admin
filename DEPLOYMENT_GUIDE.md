# M365 Administration & AI Governance Platform - Deployment & User Guide

Welcome to the **M365 Administration & AI Governance Platform**. This document provides a complete, step-by-step guide designed for beginners to set up, run, and deploy this application both on your local machine and on another Windows VM / Windows Server environment with SQL Express.

---

## 📂 1. Application Folder & Installation Directory Structure

All application files are located in your project root folder:
`d:\OneDrive - TECHFROST\Antigravity MS Laptop\M365 Admin Bot\`

Below is the complete file tree and file locations:

```text
M365 Admin Bot/
│
├── run_server.py                       <-- One-click Python launcher script
├── requirements.txt                    <-- Python package dependencies list
├── DEPLOYMENT_GUIDE.md                 <-- (This file) Complete deployment manual
├── ARCHITECTURE.md                     <-- Architectural blueprint & security flow
│
├── backend/                            <-- FastAPI Backend Server
│   ├── app/
│   │   ├── main.py                     <-- Main FastAPI server entry point & static file hosting
│   │   │
│   │   ├── core/                       <-- Core System Architecture
│   │   │   ├── config.py               <-- Environment Profiler (ENV=TEST vs PROD, SQL connection, limits)
│   │   │   ├── database.py             <-- SQL Express engine setup + local SQLite fallback
│   │   │   ├── security.py             <-- OAuth2 JWT authentication & key encryption
│   │   │   └── tasks.py                <-- Non-blocking FastAPI background tasks & DB job queue
│   │   │
│   │   ├── db/                         <-- Data Tier & Schemas
│   │   │   ├── models.py               <-- SQLAlchemy ORM models (TenantPolicy, MailflowCache, AIKeyConfig, etc.)
│   │   │   └── schemas.py              <-- Pydantic API data validation models
│   │   │
│   │   ├── services/                   <-- Execution Layer Engines
│   │   │   ├── graph_client.py         <-- Microsoft Graph REST API client (80% core execution)
│   │   │   ├── powershell_service.py   <-- PowerShell microservice wrapper (20% Exchange Online edge cases)
│   │   │   ├── ai_orchestrator.py      <-- AI & LLM Governance orchestrator (OpenAI / Anthropic / Local)
│   │   │   └── export_service.py       <-- Data export generator (15-day, 30-day, 1-year CSV/JSON)
│   │   │
│   │   └── api/                        <-- API Gateway Routers
│   │       ├── router.py               <-- Master router uniting all feature modules
│   │       └── v1/                     <-- Feature Module API Routers
│   │           ├── health.py           <-- System health check & environment mode endpoint
│   │           ├── admin_reports.py    <-- Licenses, Teams Call Quality, Intune vs Defender CVEs
│   │           ├── exchange_mgmt.py    <-- Automated License actions & Retention by RBIusertype
│   │           ├── distribution_groups.py <-- Department DL categorization & member management
│   │           ├── mailboxes.py        <-- User, Shared, Room mailboxes & calendar permissions
│   │           ├── mailflow.py         <-- 1-Year mailflow store & auto-forwarding risk domains
│   │           ├── sharepoint_onedrive.py <-- SPO/ODB usage, file last access cleanup, DLP detections
│   │           ├── azure_ad.py         <-- AD Sync errors, App registrations expiry, Risky users
│   │           ├── outages.py          # M365 Service Health API parser
│   │           ├── legal_hold.py       <-- Legal hold case creation & In-Place hold details
│   │           └── ai_governance.py    <-- AI recommendation dashboard & encrypted LLM key management
│   │
│   └── scripts/
│       └── powershell/
│           └── ExchangeManagementHelper.ps1 <-- PowerShell helper script for Exchange cmdlets
│
└── frontend/                           <-- Modern Enterprise Glassmorphism UI
    ├── index.html                      <-- Single Page Application (SPA) HTML layout
    ├── css/
    │   └── styles.css                  <-- Dark theme CSS grid layout & glassmorphism styles
    └── js/
        └── app.js                      <-- SPA routing, REST API connector, export handlers
```

---

## 📦 2. Prerequisites & Software Installed

The application requires Python 3.9+ and pip. The backend dependencies listed in [`requirements.txt`](file:///d:/OneDrive%20-%20TECHFROST/Antigravity%20MS%20Laptop/M365%20Admin%20Bot/requirements.txt) include:

1. **`fastapi` & `uvicorn`**: High-performance API Gateway server.
2. **`sqlalchemy` & `pyodbc`**: SQL Express database ORM and driver.
3. **`pydantic-settings`**: Environment profiling (`ENV=TEST` or `ENV=PROD`).
4. **`pyjwt` & `cryptography`**: Security, OAuth2 token handling, and Fernet encryption for AI API keys.
5. **`httpx` & `requests`**: Async HTTP client for Graph REST API and LLM endpoints.

---

## ⚡ 3. How to Run & Start the Application on THIS Machine

### Step 1: Open Terminal in Project Directory
Open PowerShell or Command Prompt in the project folder:
```powershell
cd "d:\OneDrive - TECHFROST\Antigravity MS Laptop\M365 Admin Bot"
```

### Step 2: Install Python Dependencies
Run the pip install command:
```powershell
pip install -r requirements.txt
```

### Step 3: Launch the Server
Start the backend server using the included `run_server.py` script:
```powershell
python run_server.py
```

### Step 4: Access the Enterprise Dashboard
Open your web browser and navigate to:
- **Web Dashboard**: [`http://127.0.0.1:8000`](http://127.0.0.1:8000)
- **Interactive API Documentation (Swagger)**: [`http://127.0.0.1:8000/api/v1/docs`](http://127.0.0.1:8000/api/v1/docs)

*(Note: The server runs on `0.0.0.0:8000`, so any device on your local network—such as an Android phone, Windows 11 laptop, or iPad—can access the dashboard by visiting `http://<YOUR_COMPUTER_IP>:8000`)*

---

## ⚙️ 4. How to Configure Environment Profiling (`ENV=TEST` vs `ENV=PROD`)

The platform includes strict environment profiling built into Pydantic BaseSettings:

### 1. Test Environment (`ENV=TEST`) - *Default*
- **Object Limit**: Automatically caps synchronized users, mailboxes, and distribution lists to **50 objects maximum** to avoid overloading SQL Express resource limits.
- **Historical Data**: Restricts historical data fetching to lightweight minimal payloads.

### 2. Production Environment (`ENV=PROD`)
- **Object Limit**: No artificial pagination limits; fetches and processes all tenant users and objects.
- **Dashboard Windows**: Aggregates metrics in configurable windows of **30 days, 60 days, 90 days, and 120 days**.

### How to Change Environment Mode:
Create or edit a `.env` file in the project root:
```ini
ENV=PROD
DATABASE_URL=sqlite:///./m365_admin.db
```
*(To switch back to test mode, set `ENV=TEST`)*

---

## 🛢️ 5. Database Setup (SQL Express vs. SQLite Local Fallback)

By default, if SQL Express is not installed on the machine, the system **automatically defaults to a zero-configuration SQLite database** (`m365_admin.db`) created in the project folder.

### Connecting to Microsoft SQL Express:
When deploying to a Windows Server or VM with SQL Express installed:
1. Ensure **ODBC Driver 17 for SQL Server** (or Driver 18) is installed on Windows.
2. Set your `DATABASE_URL` in the `.env` file:
```ini
DATABASE_URL=mssql+pyodbc://sa:YourStrongPassword@localhost/M365AdminDB?driver=ODBC+Driver+17+for+SQL+Server
```

---

## 🖥️ 6. PowerShell Microservice Setup (20% Exchange Online Edge Cases)

For full execution of Exchange Online tasks (such as Litigation Hold toggles, Mailbox type conversions, and Calendar folder permissions):
1. Install **PowerShell Core** (`pwsh`) or use Windows PowerShell.
2. Install the Exchange Online module:
```powershell
Install-Module -Name ExchangeOnlineManagement -Force -AllowClobber
```
*(Note: If PowerShell or the module is not present, the system seamlessly uses a simulated fallback execution mode, ensuring the API and UI never break.)*

---

## 🌐 7. Step-by-Step Guide: Deploying & Running on ANOTHER Machine (Windows Server / VM)

To move this application to another Windows machine or Server:

1. **Copy the Folder**:
   Copy the entire `M365 Admin Bot` folder to the target machine (e.g., `C:\M365AdminBot`).

2. **Install Python**:
   Download and install Python 3.9+ from [python.org](https://www.python.org/downloads/) on the new machine. (Make sure to check *"Add Python to PATH"* during installation).

3. **Install Requirements**:
   Open PowerShell on the new machine and run:
   ```powershell
   cd C:\M365AdminBot
   pip install -r requirements.txt
   ```

4. **(Optional) Configure SQL Express & Entra ID**:
   Create a `.env` file in `C:\M365AdminBot\.env`:
   ```ini
   ENV=PROD
   DATABASE_URL=mssql+pyodbc://sa:YourPassword@localhost/M365AdminDB?driver=ODBC+Driver+17+for+SQL+Server
   ENTRA_TENANT_ID=your-azure-tenant-id
   ENTRA_CLIENT_ID=your-azure-client-id
   ENTRA_CLIENT_SECRET=your-azure-client-secret
   ```

5. **Start Server**:
   Run:
   ```powershell
   python run_server.py
   ```

6. **Access Dashboard from Anywhere**:
   From any browser on the server or on your local network/Android device, access:
   `http://<SERVER_IP_ADDRESS>:8000`

---

## 💡 8. Key Features Overview

1. **AI Governance & LLM Orchestrator**: Click **⚙️ AI API Keys Config** in the sidebar to securely enter your OpenAI, Anthropic, or Local LLM keys (encrypted in SQL Express). View cost-saving recommendations across all 10 modules.
2. **Dedicated Data Exports**: Click **📥 Export Data** in the top right to download CSV or JSON reports strictly filtered to **15 days, 30 days, or 1 year**.
3. **1-Year Mailflow Store**: View top recipients, external auto-forwarding risk domains, and trigger 1-year background aggregation jobs.
4. **Retention Dashboard**: Dynamic filtering by `RBIusertype` (`VIP`, `StandardEmployee`, `Frontline`).
5. **Intune vs Defender CVE Reports**: Compare device telemetry against vulnerability CVEs.
6. **Legal Hold Case Management**: Complete workflow for Litigation Hold and In-Place hold requests.
