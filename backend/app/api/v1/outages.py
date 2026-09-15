from fastapi import APIRouter, Depends
from typing import Dict, Any
from app.services.graph_client import graph_client
from app.core.security import get_current_user

router = APIRouter()

@router.get("/service-health", summary="M365 Outage Dashboard & Service Health")
def get_service_health(current_user: dict = Depends(get_current_user)):
    """Parse and display live M365 Service Health and Outage APIs."""
    return graph_client.get_m365_outages()
