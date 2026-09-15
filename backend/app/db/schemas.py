import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, Field

# Base & Common Schemas
class SystemStatusSchema(BaseModel):
    app_name: str
    environment: str
    max_sync_objects: Optional[int]
    db_connected: bool
    version: str
    sql_last_updated: Optional[str] = None
    dashboard_last_updated: Optional[str] = None

# AI Settings Schema
class AIKeySaveSchema(BaseModel):
    provider: str = Field(..., example="openai")
    api_key: str = Field(..., example="sk-...")
    model_name: str = Field(default="gpt-4o")
    endpoint_url: Optional[str] = None

class AIKeyResponseSchema(BaseModel):
    provider: str
    model_name: str
    is_active: bool
    has_key: bool
    endpoint_url: Optional[str] = None

# AI Recommendation Schema
class AIRecommendationSchema(BaseModel):
    id: int
    category: str
    title: str
    description: str
    impact_level: str
    potential_savings_usd: float
    target_object: Optional[str]
    is_resolved: bool
    recommendation_type: Optional[str] = "COST_SAVING"
    benefit_category: Optional[str] = None
    security_benefit: Optional[str] = None
    automation_phase: Optional[str] = "PHASE_1_REPORTING"
    status: Optional[str] = "REPORTED"
    action_type: Optional[str] = None
    action_payload: Optional[str] = None
    executed_at: Optional[datetime.datetime] = None
    executed_by: Optional[str] = None
    created_at: datetime.datetime

    class Config:
        from_attributes = True

class ActionApprovalSchema(BaseModel):
    recommendation_id: int
    user_upn: Optional[str] = "admin@contoso.com"
    rejection_reason: Optional[str] = None

class AutomationPolicySchema(BaseModel):
    id: int
    category: str
    policy_type: str = "CUSTOM"
    policy_name: str
    phase_level: str
    is_enabled: bool
    description: Optional[str] = None
    criteria_json: Optional[str] = None
    alert_email_enabled: bool = True
    alert_email_recipients: Optional[str] = None
    alert_teams_enabled: bool = True
    alert_teams_webhook: Optional[str] = None
    daily_summary_email: bool = True
    daily_summary_teams: bool = True
    action_config_json: Optional[str] = None
    created_at: datetime.datetime

    class Config:
        from_attributes = True

class AutomationPolicyCreateSchema(BaseModel):
    category: str
    policy_type: str = "CUSTOM"
    policy_name: str
    phase_level: str = "PHASE_1_REPORTING"
    is_enabled: bool = True
    description: Optional[str] = None
    criteria_json: Optional[str] = None
    alert_email_enabled: bool = True
    alert_email_recipients: Optional[str] = "admin@contoso.com"
    alert_teams_enabled: bool = True
    alert_teams_webhook: Optional[str] = None
    daily_summary_email: bool = True
    daily_summary_teams: bool = True
    action_config_json: Optional[str] = None

class TeamsConfigSaveSchema(BaseModel):
    webhook_url: Optional[str] = None
    channel_name: Optional[str] = "General Admin Channel"
    daily_digest_enabled: bool = True
    daily_digest_time: str = "09:00"
    active_governance_phase: str = "PHASE_1_REPORTING"

class TeamsConfigSchema(TeamsConfigSaveSchema):
    id: int
    bot_app_id: Optional[str] = None
    updated_at: datetime.datetime

    class Config:
        from_attributes = True

class TeamsBotMessageSchema(BaseModel):
    text: str = Field(..., example="Show AI recommendations")
    user_principal_name: Optional[str] = "teams_user@contoso.com"
    user_name: Optional[str] = "Teams User"
    channel_id: Optional[str] = None

# Legal Hold Case Schema
class LegalHoldCreateSchema(BaseModel):
    case_name: str
    custodian_email: str
    hold_type: str = "LitigationHold"
    reason: str

class LegalHoldCaseSchema(BaseModel):
    id: int
    case_number: str
    case_name: str
    custodian_email: str
    hold_type: str
    status: str
    requested_by: str
    reason: str
    created_at: datetime.datetime

    class Config:
        from_attributes = True

# Mailbox Action Schema
class MailboxActionSchema(BaseModel):
    user_principal_name: str
    action_type: str  # convert_shared, enable_litigation_hold, set_retention, add_calendar_permission
    value: Optional[str] = None

# Distribution Group Management Schema
class DistributionGroupUpdateSchema(BaseModel):
    group_email: str
    action: str  # add_member, remove_member, update_department
    member_email: Optional[str] = None
    department_name: Optional[str] = None

# License Action Schema
class LicenseActionSchema(BaseModel):
    user_principal_name: str
    current_sku: str
    target_sku: str
    action: str  # UPGRADE, DOWNGRADE, REMOVE
    ai_recommendation_reason: Optional[str] = None

# Inbox Rule Management Schemas
class InboxRuleCreateSchema(BaseModel):
    user_principal_name: str
    rule_name: str
    forward_to: str
    stop_processing_more_rules: bool = True
    is_enabled: bool = True

class InboxRuleActionSchema(BaseModel):
    user_principal_name: Optional[str] = ""
    rule_name: Optional[str] = ""
    action: str  # TOGGLE, DELETE, PURGE_EXTERNAL


# Export Request Schema
class ExportRequestSchema(BaseModel):
    module: str
    days: int = Field(..., example=30, description="15, 30, or 365 days")
    format: str = Field(default="csv", example="csv")

# Extensible API Integration Registry Schemas
class APIIntegrationSaveSchema(BaseModel):
    api_category: str = Field(..., example="LLM", description="LLM, AZURE, MAPS, CUSTOM")
    provider_name: str = Field(..., example="openai", description="e.g. openai, gemini, claude, azure_openai, ollama, deepseek, groq, azure_ad, azure_maps")
    api_key: Optional[str] = Field(default=None, description="API Key or Secret Token (Encrypted on save)")
    endpoint_url: Optional[str] = None
    model_name: Optional[str] = Field(default="gpt-4o")
    priority: int = Field(default=1, description="Failover priority rank (1 = highest)")
    is_active: bool = Field(default=True)
    extra_headers_json: Optional[str] = Field(default=None, description="JSON string for custom headers/tokens for future API integrations")

class APIIntegrationResponseSchema(BaseModel):
    id: int
    api_category: str
    provider_name: str
    has_key: bool
    endpoint_url: Optional[str] = None
    model_name: Optional[str] = None
    priority: int
    is_active: bool
    last_error: Optional[str] = None
    error_count: int
    updated_at: datetime.datetime

    class Config:
        from_attributes = True

class LLMFailoverTestSchema(BaseModel):
    prompt: str = Field(default="Synthesize tenant security and license recommendations.", description="Test prompt for LLM failover engine")
    simulate_errors: Optional[List[str]] = Field(default=None, description="Optional list of provider names to simulate failure for testing failover")

class APITestConnectionSchema(BaseModel):
    provider_name: str = Field(..., example="openai")
    api_category: str = Field(default="LLM", example="LLM")
    api_key: Optional[str] = None
    endpoint_url: Optional[str] = None
    model_name: Optional[str] = None

