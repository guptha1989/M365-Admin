import datetime
import logging
import time
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.db.models import JobQueue

logger = logging.getLogger("m365_admin.tasks")

def enqueue_db_job(job_type: str, payload: dict, description: str = "") -> str:
    """Add a heavy background job (e.g., 1-year mailflow sync) to the SQL Express DB queue."""
    db: Session = SessionLocal()
    try:
        job = JobQueue(
            job_type=job_type,
            status="QUEUED",
            description=description or f"Job {job_type}",
            payload=str(payload),
            created_at=datetime.datetime.utcnow()
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        logger.info(f"Enqueued DB background job #{job.id}: {job_type}")
        return str(job.id)
    finally:
        db.close()

def process_background_job_task(job_id: int):
    """Background task executor processing heavy jobs outside main HTTP request lifecycle."""
    db: Session = SessionLocal()
    try:
        job = db.query(JobQueue).filter(JobQueue.id == job_id).first()
        if not job:
            return
        
        job.status = "RUNNING"
        job.started_at = datetime.datetime.utcnow()
        db.commit()

        logger.info(f"Starting execution of background job #{job.id} ({job.job_type})")
        # Simulate background processing duration
        time.sleep(2)

        job.status = "COMPLETED"
        job.completed_at = datetime.datetime.utcnow()
        job.result = f"Successfully executed job '{job.job_type}' for payload {job.payload}"
        db.commit()
        logger.info(f"Finished background job #{job.id}")
    except Exception as e:
        logger.error(f"Error processing background job #{job_id}: {e}")
        if job:
            job.status = "FAILED"
            job.result = str(e)
            db.commit()
    finally:
        db.close()

def run_daily_teams_digest_task():
    """Daily proactive task that compiles AI recommendations and delivers digest card to Microsoft Teams."""
    db: Session = SessionLocal()
    try:
        from app.db.models import AIRecommendation, TeamsConfig
        from app.services.ai_orchestrator import ai_orchestrator
        from app.services.teams_service import teams_service
        from app.core.config import settings

        logger.info("Starting Daily AI Recommendations Teams Digest Dispatch Task...")
        
        # Ensure fresh recommendations
        recs = db.query(AIRecommendation).filter(AIRecommendation.is_resolved == False).all()
        if not recs:
            ai_orchestrator.generate_recommendations(db)
            recs = db.query(AIRecommendation).filter(AIRecommendation.is_resolved == False).all()

        teams_config = db.query(TeamsConfig).first()
        current_phase = teams_config.active_governance_phase if teams_config else settings.DEFAULT_AUTOMATION_PHASE
        webhook_url = teams_config.webhook_url if teams_config else settings.TEAMS_WEBHOOK_URL

        card_payload = teams_service.build_daily_digest_card(recs, current_phase=current_phase)
        result = teams_service.send_webhook_payload(card_payload, custom_webhook_url=webhook_url)

        logger.info(f"Daily Teams Digest Dispatch Completed: {result.get('status')}")
        return result
    except Exception as e:
        logger.error(f"Failed to execute Daily Teams Digest Task: {e}")
        return {"status": "FAILED", "error": str(e)}
    finally:
        db.close()
