import os
from typing import Literal, Optional, List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    PROJECT_NAME: str = "M365 Administration & AI Governance Platform"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Environment Profiling (TEST vs PROD)
    ENV: Literal["TEST", "PROD"] = Field(default="TEST", description="Execution environment profile")
    
    # Database Configuration (SQL Express with SQLite fallback)
    # Default SQLite fallback for zero-config local runs
    DATABASE_URL: str = Field(
        default="sqlite:///./m365_admin.db",
        description="SQL Express URL (e.g. mssql+pyodbc://sa:password@localhost/M365AdminDB?driver=ODBC+Driver+17+for+SQL+Server) or SQLite"
    )
    
    # Security & Entra ID (Azure AD) OAuth2 Configuration
    SECRET_KEY: str = Field(default="SUPER_SECRET_KEY_CHANGE_IN_PRODUCTION_32BYTES_LONG!", description="JWT secret key")
    ENCRYPTION_KEY: str = Field(default="gAAAAABk_CHANGE_THIS_FERNET_KEY_IN_PROD_32_BYTES_=", description="Fernet encryption key for AI API keys")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day
    
    ENTRA_TENANT_ID: Optional[str] = Field(default="00000000-0000-0000-0000-000000000000", description="Microsoft 365 Tenant ID")
    ENTRA_CLIENT_ID: Optional[str] = Field(default="00000000-0000-0000-0000-000000000000", description="App Registration Client ID")
    ENTRA_CLIENT_SECRET: Optional[str] = Field(default="SECRET_PLACEHOLDER", description="App Registration Client Secret")
    M365_DEFENDER_API_KEY: Optional[str] = Field(default="sample_defender_key", description="M365 Defender API Key")
    
    # AI & LLM Provider API Keys & Failover Priority
    OPENAI_API_KEY: Optional[str] = Field(default=None, description="OpenAI API Key")
    GEMINI_API_KEY: Optional[str] = Field(default=None, description="Google Gemini API Key")
    CLAUDE_API_KEY: Optional[str] = Field(default=None, description="Anthropic Claude API Key")
    AZURE_OPENAI_KEY: Optional[str] = Field(default=None, description="Azure OpenAI Service Key")
    AZURE_OPENAI_ENDPOINT: Optional[str] = Field(default=None, description="Azure OpenAI Custom Endpoint URL")
    DEEPSEEK_API_KEY: Optional[str] = Field(default=None, description="DeepSeek LLM API Key")
    GROQ_API_KEY: Optional[str] = Field(default=None, description="Groq LPU API Key")
    COHERE_API_KEY: Optional[str] = Field(default=None, description="Cohere AI API Key")
    MISTRAL_API_KEY: Optional[str] = Field(default=None, description="Mistral AI API Key")
    HUGGINGFACE_API_KEY: Optional[str] = Field(default=None, description="HuggingFace API Key / Token")
    LOCAL_LLM_URL: Optional[str] = Field(default="http://localhost:11434/v1", description="Local Ollama/LLM Endpoint")
    LLM_FAILOVER_ORDER: str = Field(default="openai,gemini,claude,azure_openai,local,deepseek,groq,cohere,mistral,huggingface", description="Comma-separated LLM auto-switch failover priority order")
    
    # 3rd Party Integrations & Maps APIs
    MAPS_API_KEY: Optional[str] = Field(default=None, description="Maps API Key (Google or Azure Maps)")
    GOOGLE_MAPS_KEY: Optional[str] = Field(default=None, description="Google Maps API Key")
    AZURE_MAPS_KEY: Optional[str] = Field(default=None, description="Azure Maps Subscription Key")
    MAPBOX_ACCESS_TOKEN: Optional[str] = Field(default=None, description="Mapbox API Access Token")
    OSM_TILE_SERVER_URL: Optional[str] = Field(default=None, description="OpenStreetMap / Custom Tile Server URL")
    
    # Custom Enterprise & Future Integrations
    SERVICENOW_ENDPOINT: Optional[str] = Field(default=None, description="ServiceNow ITSM REST API Endpoint")
    SERVICENOW_API_KEY: Optional[str] = Field(default=None, description="ServiceNow Auth Token")
    SPLUNK_ENDPOINT: Optional[str] = Field(default=None, description="Splunk HEC API Endpoint")
    SPLUNK_HEC_TOKEN: Optional[str] = Field(default=None, description="Splunk HEC Token")
    DATADOG_API_KEY: Optional[str] = Field(default=None, description="Datadog API Key")
    
    SENDGRID_EMAIL_API_KEY: Optional[str] = Field(default=None, description="SendGrid Email API Key")
    TEAMS_WEBHOOK_URL: Optional[str] = Field(default=None, description="Microsoft Teams Incoming Webhook URL")
    TEAMS_DAILY_DIGEST_ENABLED: bool = Field(default=True, description="Enable daily proactive AI recommendations digest to Teams")
    TEAMS_DAILY_DIGEST_TIME: str = Field(default="09:00", description="Daily digest scheduled dispatch time (HH:MM)")
    DEFAULT_AUTOMATION_PHASE: str = Field(default="PHASE_1_REPORTING", description="Default tenant governance phase (PHASE_1_REPORTING, PHASE_2_SEMI_AUTOMATED, PHASE_3_FULLY_AUTOMATED)")
    SLACK_WEBHOOK_URL: Optional[str] = Field(default=None, description="Slack Incoming Webhook URL")
    
    # Execution Layer Limits derived from Environment Profile
    @property
    def max_sync_objects(self) -> Optional[int]:
        """Strict object cap in TEST environment (50 objects max), unconstrained in PROD."""
        if self.ENV.upper() == "TEST":
            return 50
        return None

    @property
    def limit_historical_payloads(self) -> bool:
        """Minimal payloads in TEST environment to accommodate SQL Express limits."""
        return self.ENV.upper() == "TEST"

    # Aggregation & Reporting Windows
    DASHBOARD_AGGREGATION_WINDOWS: List[int] = [30, 60, 90, 120]  # Days
    EXPORT_ALLOWED_WINDOWS: List[int] = [15, 30, 365]            # Days (15, 30, or 1-year locked)

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()

