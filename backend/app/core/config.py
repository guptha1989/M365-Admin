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
    SECRET_KEY: str = Field(default="M365_ADMIN_JWT_SECRET_DEFAULT_KEY_32BYTES_MIN", description="JWT secret key")
    ENCRYPTION_KEY: Optional[str] = Field(default=None, description="Fernet encryption key for AI API keys")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day
    
    ENTRA_TENANT_ID: Optional[str] = Field(default=None, description="Microsoft 365 Tenant ID")
    ENTRA_CLIENT_ID: Optional[str] = Field(default=None, description="App Registration Client ID")
    ENTRA_CLIENT_SECRET: Optional[str] = Field(default=None, description="App Registration Client Secret")
    M365_DEFENDER_API_KEY: Optional[str] = Field(default=None, description="M365 Defender API Key")

    # Specific Service API Credentials (Azure, Teams RW, Exchange RW)
    AZURE_TENANT_ID: Optional[str] = Field(default=None, description="Azure Tenant ID")
    AZURE_CLIENT_ID: Optional[str] = Field(default=None, description="Azure Client ID")
    AZURE_CLIENT_SECRET: Optional[str] = Field(default=None, description="Azure Client Secret")
    AZURE_API_KEY: Optional[str] = Field(default=None, description="Azure API Key")
    AZURE_SUBSCRIPTION_ID: Optional[str] = Field(default=None, description="Azure Subscription ID")

    TEAMS_CLIENT_ID: Optional[str] = Field(default=None, description="Teams Read/Write Client ID")
    TEAMS_TENANT_ID: Optional[str] = Field(default=None, description="Teams Read/Write Tenant ID")
    TEAMS_CLIENT_SECRET: Optional[str] = Field(default=None, description="Teams Read/Write Client Secret")
    TEAMS_API_KEY: Optional[str] = Field(default=None, description="Teams Read/Write API Key")
    TEAMS_CHANNEL_NAME: str = Field(default="General", description="Teams Channel Name for daily reports")

    EXCHANGE_CLIENT_ID: Optional[str] = Field(default=None, description="Exchange Read/Write Client ID")
    EXCHANGE_TENANT_ID: Optional[str] = Field(default=None, description="Exchange Read/Write Tenant ID")
    EXCHANGE_CLIENT_SECRET: Optional[str] = Field(default=None, description="Exchange Read/Write Client Secret")
    EXCHANGE_API_KEY: Optional[str] = Field(default=None, description="Exchange Read/Write API Key")
    
    # Multi-LLM Provider API Keys & Auto-Switch Failover Priority
    LLM1_NAME: Optional[str] = Field(default="OpenAI GPT-4o", description="LLM Provider 1 Name")
    LLM1_MODEL: Optional[str] = Field(default="gpt-4o", description="LLM Provider 1 Model")
    LLM1_API_KEY: Optional[str] = Field(default=None, description="LLM Provider 1 API Key")
    LLM1_ENDPOINT: Optional[str] = Field(default=None, description="LLM Provider 1 Endpoint")

    LLM2_NAME: Optional[str] = Field(default="Google Gemini", description="LLM Provider 2 Name")
    LLM2_MODEL: Optional[str] = Field(default="gemini-1.5-flash", description="LLM Provider 2 Model")
    LLM2_API_KEY: Optional[str] = Field(default=None, description="LLM Provider 2 API Key")
    LLM2_ENDPOINT: Optional[str] = Field(default=None, description="LLM Provider 2 Endpoint")

    LLM3_NAME: Optional[str] = Field(default="Anthropic Claude 3.5", description="LLM Provider 3 Name")
    LLM3_MODEL: Optional[str] = Field(default="claude-3-5-sonnet", description="LLM Provider 3 Model")
    LLM3_API_KEY: Optional[str] = Field(default=None, description="LLM Provider 3 API Key")
    LLM3_ENDPOINT: Optional[str] = Field(default=None, description="LLM Provider 3 Endpoint")

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
    LLM_FAILOVER_ORDER: str = Field(default="llm1,llm2,llm3,openai,gemini,claude,azure_openai,local,deepseek,groq,cohere,mistral,huggingface", description="Comma-separated LLM auto-switch failover priority order")
    
    # 3rd Party Integrations & Maps APIs
    MAPS_API_KEY: Optional[str] = Field(default=None, description="Maps API Key (Google or Azure Maps)")
    GOOGLE_MAPS_KEY: Optional[str] = Field(default=None, description="Google Maps API Key")
    AZURE_MAPS_KEY: Optional[str] = Field(default=None, description="Azure Maps Subscription Key")
    MAPBOX_ACCESS_TOKEN: Optional[str] = Field(default=None, description="Mapbox API Access Token")
    OSM_TILE_SERVER_URL: Optional[str] = Field(default=None, description="OpenStreetMap / Custom Tile Server URL")
    
    # SNOW (ServiceNow) ITSM Integration
    SNOW_INSTANCE_URL: Optional[str] = Field(default=None, description="ServiceNow Instance URL")
    SNOW_CLIENT_ID: Optional[str] = Field(default=None, description="ServiceNow Client ID")
    SNOW_CLIENT_SECRET: Optional[str] = Field(default=None, description="ServiceNow Client Secret")
    SNOW_API_KEY: Optional[str] = Field(default=None, description="ServiceNow API Key")
    SNOW_USERNAME: Optional[str] = Field(default=None, description="ServiceNow Username")
    SNOW_PASSWORD: Optional[str] = Field(default=None, description="ServiceNow Password")
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

