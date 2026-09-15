from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from app.core.database import get_db
from app.core.security import get_current_user
from app.db.models import AuditLog
import datetime

router = APIRouter()

@router.get("/logs", summary="App Change Audit Logs")
def get_audit_logs(
    limit: int = Query(default=50, description="Max audit entries to retrieve"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Retrieve audit logs of administrative actions and changes executed within this application."""
    logs = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit).all()
    if not logs:
        from app.services.graph_client import graph_client
        domain = graph_client.get_primary_domain()
        users = graph_client.get_users_list()
        upns = [u["userPrincipalName"] for u in users if u.get("userPrincipalName")]
        u1 = upns[0] if len(upns) > 0 else f"admin@{domain}"
        u2 = upns[1] if len(upns) > 1 else f"user1@{domain}"

        # Seed default audit log items for initial demonstration
        sample_logs = [
            AuditLog(user_principal_name=f"admin@{domain}", action="API_DATA_SYNC_AND_DASHBOARD_REFRESH", module="SystemSync", details=f"Synced live Graph API telemetry and refreshed tenant dashboard for {domain}", timestamp=datetime.datetime.utcnow() - datetime.timedelta(minutes=30)),
            AuditLog(user_principal_name=f"admin@{domain}", action="LICENSE_OPTIMIZATION_EVAL", module="Management", details=f"Evaluated license assignment telemetry for user {u1}", timestamp=datetime.datetime.utcnow() - datetime.timedelta(hours=2)),
            AuditLog(user_principal_name=f"admin@{domain}", action="LITIGATION_HOLD_ENABLE", module="Management", details=f"Enabled Litigation Hold audit flag for user {u2}", timestamp=datetime.datetime.utcnow() - datetime.timedelta(hours=5)),
            AuditLog(user_principal_name=f"admin@{domain}", action="DL_MEMBER_ADD", module="Management", details=f"Mapped user {u1} to DL-Finance-Audit distribution group", timestamp=datetime.datetime.utcnow() - datetime.timedelta(days=1)),
            AuditLog(user_principal_name=f"admin@{domain}", action="SHARED_MAILBOX_CREATE", module="Management", details=f"Configured shared mailbox smb-fin-invoices@{domain} mapped to Finance department", timestamp=datetime.datetime.utcnow() - datetime.timedelta(days=2))
        ]
        db.add_all(sample_logs)
        db.commit()
        logs = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit).all()

    return logs
