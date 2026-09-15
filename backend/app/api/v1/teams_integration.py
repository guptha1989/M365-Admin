from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from app.core.database import get_db
from app.core.security import get_current_user
from app.core.config import settings
from app.db.models import TeamsConfig
from app.db.schemas import TeamsConfigSaveSchema, TeamsConfigSchema, TeamsBotMessageSchema
from app.services.teams_service import teams_service
from app.core.tasks import run_daily_teams_digest_task

router = APIRouter()

@router.post("/webhook", summary="Microsoft Teams Bot Webhook & Interactive Command Handler")
def handle_teams_bot_message(
    payload: TeamsBotMessageSchema,
    db: Session = Depends(get_db)
):
    """
    Endpoint receiving interactive questions and commands from Microsoft Teams users.
    Supports queries for recommendations, license usage, service health, and Phase 2 action approvals.
    """
    response_data = teams_service.parse_teams_command(
        db=db,
        user_query=payload.text,
        user_upn=payload.user_principal_name or "teams_user@contoso.com"
    )
    return {
        "status": "SUCCESS",
        "user_query": payload.text,
        "result": response_data
    }

@router.post("/daily-digest/trigger", summary="Trigger Daily AI Recommendation Digest to Teams")
def trigger_daily_teams_digest(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Manually or programmatically trigger the proactive Daily AI Recommendation Digest dispatch to Teams.
    """
    background_tasks.add_task(run_daily_teams_digest_task)
    return {
        "status": "QUEUED",
        "message": "Daily AI Recommendation Digest dispatch task queued in background for Teams delivery."
    }

@router.get("/config", response_model=TeamsConfigSchema, summary="Get Teams Integration Settings")
def get_teams_config(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Fetch Microsoft Teams webhook and proactive daily digest configuration."""
    config = db.query(TeamsConfig).first()
    if not config:
        config = TeamsConfig(
            webhook_url=settings.TEAMS_WEBHOOK_URL,
            daily_digest_enabled=settings.TEAMS_DAILY_DIGEST_ENABLED,
            daily_digest_time=settings.TEAMS_DAILY_DIGEST_TIME,
            active_governance_phase=settings.DEFAULT_AUTOMATION_PHASE
        )
        db.add(config)
        db.commit()
        db.refresh(config)
    return config

@router.post("/config", response_model=TeamsConfigSchema, summary="Save Teams Integration Settings")
def save_teams_config(
    payload: TeamsConfigSaveSchema,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Save or update Microsoft Teams webhook URL, daily digest parameters, and active governance phase."""
    config = db.query(TeamsConfig).first()
    if not config:
        config = TeamsConfig()
        db.add(config)

    config.webhook_url = payload.webhook_url
    config.channel_name = payload.channel_name or "General Admin Channel"
    config.daily_digest_enabled = payload.daily_digest_enabled
    config.daily_digest_time = payload.daily_digest_time
    config.active_governance_phase = payload.active_governance_phase
    db.commit()
    db.refresh(config)

    return config
