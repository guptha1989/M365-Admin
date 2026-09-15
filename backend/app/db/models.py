import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float
from app.core.database import Base

class TenantPolicy(Base):
    __tablename__ = "tenant_policies"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(100), unique=True, index=True)
    rbi_user_type_default = Column(String(100), default="StandardEmployee")
    auto_license_reclaim = Column(Boolean, default=True)
    sync_interval_hours = Column(Integer, default=24)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)

class MailflowCache(Base):
    __tablename__ = "mailflow_cache"

    id = Column(Integer, primary_key=True, index=True)
    sender = Column(String(255), index=True)
    recipient = Column(String(255), index=True)
    domain = Column(String(100), index=True)
    bytes_transferred = Column(Integer, default=0)
    auto_forwarded = Column(Boolean, default=False)
    forward_target_domain = Column(String(100), nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)

class AIKeyConfig(Base):
    __tablename__ = "ai_key_configs"

    id = Column(Integer, primary_key=True, index=True)
    provider = Column(String(50), unique=True, index=True)  # openai, anthropic, local
    encrypted_key = Column(Text, nullable=True)
    endpoint_url = Column(String(255), nullable=True)
    model_name = Column(String(100), default="gpt-4o")
    is_active = Column(Boolean, default=True)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)

class AIRecommendation(Base):
    __tablename__ = "ai_recommendations"

    id = Column(Integer, primary_key=True, index=True)
    category = Column(String(50), index=True)  # license, security, exchange, sharepoint, dl
    title = Column(String(255))
    description = Column(Text)
    impact_level = Column(String(20), default="MEDIUM")  # HIGH, MEDIUM, LOW
    potential_savings_usd = Column(Float, default=0.0)
    target_object = Column(String(255), nullable=True)
    is_resolved = Column(Boolean, default=False)
    
    # Categorized Benefit & Security Fields
    recommendation_type = Column(String(50), default="COST_SAVING") # COST_SAVING, SECURITY
    benefit_category = Column(String(100), nullable=True) # e.g. License SKU Optimization, Data Loss Prevention
    security_benefit = Column(Text, nullable=True)

    # 3-Phase Automation Fields
    automation_phase = Column(String(50), default="PHASE_1_REPORTING") # PHASE_1_REPORTING, PHASE_2_SEMI_AUTOMATED, PHASE_3_FULLY_AUTOMATED
    status = Column(String(50), default="REPORTED")  # REPORTED, PENDING_APPROVAL, APPROVED, REJECTED, AUTOMATED_EXECUTED, MANUAL_EXECUTED
    action_type = Column(String(100), nullable=True) # e.g. reclaim_license, apply_litigation_hold, rename_group, archive_site
    action_payload = Column(Text, nullable=True)     # JSON parameters
    executed_at = Column(DateTime, nullable=True)
    executed_by = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class AutomationPolicy(Base):
    __tablename__ = "automation_policies"

    id = Column(Integer, primary_key=True, index=True)
    category = Column(String(50), index=True) # LICENSE_AUTOMATION, SHAREPOINT_CLEANUP, COMPLIANCE_SECURITY
    policy_type = Column(String(100), default="CUSTOM") # LICENSE_REMOVAL, LICENSE_DOWNGRADE, LICENSE_ASSIGNMENT, SHAREPOINT_CLEANUP, AZURE_SECURITY_ALERTS, SHAREPOINT_SENSITIVE_SHARING, EMAIL_FORWARDING_SENSITIVE
    policy_name = Column(String(255))
    phase_level = Column(String(50), default="PHASE_1_REPORTING") # PHASE_1_REPORTING, PHASE_2_SEMI_AUTOMATED, PHASE_3_FULLY_AUTOMATED
    is_enabled = Column(Boolean, default=True)
    description = Column(Text, nullable=True)
    criteria_json = Column(Text, nullable=True)
    
    # Alert Options
    alert_email_enabled = Column(Boolean, default=True)
    alert_email_recipients = Column(Text, nullable=True) # comma separated emails
    alert_teams_enabled = Column(Boolean, default=True)
    alert_teams_webhook = Column(Text, nullable=True)
    daily_summary_email = Column(Boolean, default=True)
    daily_summary_teams = Column(Boolean, default=True)

    # Execution Action Config (e.g. Delete, Move to SP/OneDrive/Azure Storage)
    action_config_json = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)

class SensitiveFileType(Base):
    __tablename__ = "sensitive_file_types"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True) # Credit Card Number, SSN, Passport, Financial Record, etc.
    description = Column(Text, nullable=True)
    extension_patterns = Column(String(255), default=".pdf,.docx,.xlsx,.csv,.doc,.xls") # file extensions
    regex_pattern = Column(Text, nullable=True)
    is_built_in = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class PolicyAlertFinding(Base):
    __tablename__ = "policy_alert_findings"

    id = Column(Integer, primary_key=True, index=True)
    policy_id = Column(Integer, index=True)
    policy_name = Column(String(255))
    category = Column(String(50), index=True)
    target_user_or_resource = Column(String(255), index=True) # UPN, Site URL, File Path, Email Address
    finding_description = Column(Text)
    severity = Column(String(20), default="MEDIUM") # HIGH, MEDIUM, LOW
    status = Column(String(50), default="TRIGGERED") # TRIGGERED, PENDING_ACTION, RESOLVED, IGNORED
    details_json = Column(Text, nullable=True)
    triggered_at = Column(DateTime, default=datetime.datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)


class TeamsConfig(Base):
    __tablename__ = "teams_configs"

    id = Column(Integer, primary_key=True, index=True)
    webhook_url = Column(Text, nullable=True)
    bot_app_id = Column(String(100), nullable=True)
    channel_name = Column(String(100), default="General Admin Channel")
    daily_digest_enabled = Column(Boolean, default=True)
    daily_digest_time = Column(String(20), default="09:00")
    active_governance_phase = Column(String(50), default="PHASE_1_REPORTING")
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)

class JobQueue(Base):
    __tablename__ = "job_queue"

    id = Column(Integer, primary_key=True, index=True)
    job_type = Column(String(100), index=True)
    status = Column(String(20), default="QUEUED")  # QUEUED, RUNNING, COMPLETED, FAILED
    description = Column(String(255))
    payload = Column(Text, nullable=True)
    result = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_principal_name = Column(String(255), index=True)
    action = Column(String(100), index=True)
    module = Column(String(50))
    details = Column(Text)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

class LegalHoldCase(Base):
    __tablename__ = "legal_hold_cases"

    id = Column(Integer, primary_key=True, index=True)
    case_number = Column(String(100), unique=True, index=True)
    case_name = Column(String(255))
    custodian_email = Column(String(255), index=True)
    hold_type = Column(String(50), default="In-Place")  # LitigationHold, In-Place
    status = Column(String(50), default="Active")       # Requested, Active, Removed
    requested_by = Column(String(255))
    reason = Column(Text)
    keywords = Column(Text, nullable=True)
    time_interval_start = Column(String(50), nullable=True)
    time_interval_end = Column(String(50), nullable=True)
    destination_folder_url = Column(Text, nullable=True)
    compliance_search_status = Column(String(100), default="Completed & Copied to Vault")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class APIIntegrationConfig(Base):
    __tablename__ = "api_integration_configs"

    id = Column(Integer, primary_key=True, index=True)
    api_category = Column(String(50), index=True)  # LLM, AZURE, MAPS, MESSAGING, CUSTOM
    provider_name = Column(String(100), index=True) # e.g. openai, gemini, claude, azure_openai, ollama, deepseek, groq, azure_ad, azure_maps, google_maps
    encrypted_key = Column(Text, nullable=True)
    endpoint_url = Column(String(255), nullable=True)
    model_name = Column(String(100), nullable=True) # e.g. gpt-4o, gemini-1.5-pro, claude-3-5-sonnet
    priority = Column(Integer, default=1)           # Priority order for auto-switch failover (1 = highest)
    is_active = Column(Boolean, default=True)
    extra_headers_json = Column(Text, nullable=True)# JSON string for custom headers/tokens for future API integrations
    last_error = Column(Text, nullable=True)        # Records last failover exception message
    error_count = Column(Integer, default=0)        # Tracks consecutive failures
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)

class RegisteredTenant(Base):
    __tablename__ = "registered_tenants"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(100), unique=True, index=True)
    tenant_name = Column(String(255))
    primary_domain = Column(String(255), index=True)
    client_id = Column(String(255), nullable=True)
    encrypted_client_secret = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class AppUser(Base):
    __tablename__ = "app_users"

    id = Column(Integer, primary_key=True, index=True)
    user_principal_name = Column(String(255), unique=True, index=True)
    display_name = Column(String(255))
    tenant_id = Column(String(100), index=True)
    roles_json = Column(Text, default="[]") # JSON array of assigned roles: ExchangeAdmin, SharePointAdmin, etc.
    access_level = Column(String(50), default="Read-Only") # Read-Only, Member, Admin
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    last_login_at = Column(DateTime, default=datetime.datetime.utcnow)

class ModulePhaseConfig(Base):
    __tablename__ = "module_phase_configs"

    id = Column(Integer, primary_key=True, index=True)
    module_key = Column(String(50), unique=True, index=True) # exchange, sharepoint, teams, security, license, legal_hold
    module_name = Column(String(100))
    active_phase = Column(String(50), default="PHASE_1_REPORTING") # PHASE_1_REPORTING, PHASE_2_SEMI_AUTOMATED, PHASE_3_FULLY_AUTOMATED
    updated_by = Column(String(255), default="admin@contoso.com")
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)

class IntuneVulnerability(Base):
    __tablename__ = "intune_vulnerabilities"

    id = Column(Integer, primary_key=True, index=True)
    cve_id = Column(String(50), index=True)
    title = Column(String(255))
    severity = Column(String(20), default="HIGH") # CRITICAL, HIGH, MEDIUM, LOW
    cvss_score = Column(Float, default=7.5)
    affected_device_type = Column(String(100)) # Windows 11, iOS 17, Android 14
    affected_count = Column(Integer, default=1)
    remediation_steps = Column(Text)
    tenant_id = Column(String(100), default="contoso.com")
    is_remediated = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

