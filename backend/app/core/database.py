import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings

logger = logging.getLogger("m365_admin.database")

# Database engine initialization with SQLite / MSSQL SQL Express compatibility options
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """FastAPI Dependency for managing DB sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize database tables on server launch and auto-migrate missing columns."""
    try:
        import app.db.models  # Ensure models are registered with Base.metadata
        Base.metadata.create_all(bind=engine)
        _auto_migrate_columns(engine)
        logger.info(f"Database initialized successfully using URL: {settings.DATABASE_URL}")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        # Fallback to local SQLite if SQL Express connection fails
        if not settings.DATABASE_URL.startswith("sqlite"):
            logger.warning("Falling back to local SQLite engine (m365_admin.db)...")
            fallback_engine = create_engine("sqlite:///./m365_admin.db", connect_args={"check_same_thread": False})
            SessionLocal.configure(bind=fallback_engine)
            Base.metadata.create_all(bind=fallback_engine)
            _auto_migrate_columns(fallback_engine)
            logger.info("Local SQLite database initialized successfully.")

def _auto_migrate_columns(target_engine=None):
    """Add missing columns to existing SQLite tables if schema evolved."""
    from sqlalchemy import inspect, text
    eng = target_engine or engine
    inspector = inspect(eng)
    try:
        if "ai_recommendations" in inspector.get_table_names():
            columns = [c["name"] for c in inspector.get_columns("ai_recommendations")]
            with eng.connect() as conn:
                if "recommendation_type" not in columns:
                    conn.execute(text("ALTER TABLE ai_recommendations ADD COLUMN recommendation_type VARCHAR(50) DEFAULT 'COST_SAVING'"))
                if "benefit_category" not in columns:
                    conn.execute(text("ALTER TABLE ai_recommendations ADD COLUMN benefit_category VARCHAR(100)"))
                if "security_benefit" not in columns:
                    conn.execute(text("ALTER TABLE ai_recommendations ADD COLUMN security_benefit TEXT"))
                if "automation_phase" not in columns:
                    conn.execute(text("ALTER TABLE ai_recommendations ADD COLUMN automation_phase VARCHAR(50) DEFAULT 'PHASE_1_REPORTING'"))
                if "status" not in columns:
                    conn.execute(text("ALTER TABLE ai_recommendations ADD COLUMN status VARCHAR(50) DEFAULT 'REPORTED'"))
                if "action_type" not in columns:
                    conn.execute(text("ALTER TABLE ai_recommendations ADD COLUMN action_type VARCHAR(100)"))
                if "action_payload" not in columns:
                    conn.execute(text("ALTER TABLE ai_recommendations ADD COLUMN action_payload TEXT"))
                if "executed_at" not in columns:
                    conn.execute(text("ALTER TABLE ai_recommendations ADD COLUMN executed_at DATETIME"))
                if "executed_by" not in columns:
                    conn.execute(text("ALTER TABLE ai_recommendations ADD COLUMN executed_by VARCHAR(255)"))
                conn.commit()

        if "automation_policies" in inspector.get_table_names():
            pol_cols = [c["name"] for c in inspector.get_columns("automation_policies")]
            with eng.connect() as conn:
                if "policy_type" not in pol_cols:
                    conn.execute(text("ALTER TABLE automation_policies ADD COLUMN policy_type VARCHAR(100) DEFAULT 'CUSTOM'"))
                if "criteria_json" not in pol_cols:
                    conn.execute(text("ALTER TABLE automation_policies ADD COLUMN criteria_json TEXT"))
                if "alert_email_enabled" not in pol_cols:
                    conn.execute(text("ALTER TABLE automation_policies ADD COLUMN alert_email_enabled BOOLEAN DEFAULT 1"))
                if "alert_email_recipients" not in pol_cols:
                    conn.execute(text("ALTER TABLE automation_policies ADD COLUMN alert_email_recipients TEXT"))
                if "alert_teams_enabled" not in pol_cols:
                    conn.execute(text("ALTER TABLE automation_policies ADD COLUMN alert_teams_enabled BOOLEAN DEFAULT 1"))
                if "alert_teams_webhook" not in pol_cols:
                    conn.execute(text("ALTER TABLE automation_policies ADD COLUMN alert_teams_webhook TEXT"))
                if "daily_summary_email" not in pol_cols:
                    conn.execute(text("ALTER TABLE automation_policies ADD COLUMN daily_summary_email BOOLEAN DEFAULT 1"))
                if "daily_summary_teams" not in pol_cols:
                    conn.execute(text("ALTER TABLE automation_policies ADD COLUMN daily_summary_teams BOOLEAN DEFAULT 1"))
                if "action_config_json" not in pol_cols:
                    conn.execute(text("ALTER TABLE automation_policies ADD COLUMN action_config_json TEXT"))
                conn.commit()
        if "legal_hold_cases" in inspector.get_table_names():
            lh_cols = [c["name"] for c in inspector.get_columns("legal_hold_cases")]
            with eng.connect() as conn:
                if "keywords" not in lh_cols:
                    conn.execute(text("ALTER TABLE legal_hold_cases ADD COLUMN keywords TEXT"))
                if "time_interval_start" not in lh_cols:
                    conn.execute(text("ALTER TABLE legal_hold_cases ADD COLUMN time_interval_start VARCHAR(50)"))
                if "time_interval_end" not in lh_cols:
                    conn.execute(text("ALTER TABLE legal_hold_cases ADD COLUMN time_interval_end VARCHAR(50)"))
                if "destination_folder_url" not in lh_cols:
                    conn.execute(text("ALTER TABLE legal_hold_cases ADD COLUMN destination_folder_url TEXT"))
                if "compliance_search_status" not in lh_cols:
                    conn.execute(text("ALTER TABLE legal_hold_cases ADD COLUMN compliance_search_status VARCHAR(100) DEFAULT 'Completed & Copied to Vault'"))
                conn.commit()
    except Exception as e:
        logger.warning(f"Auto-migration check note: {e}")

