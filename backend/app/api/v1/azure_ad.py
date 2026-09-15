from fastapi import APIRouter, Depends
from typing import Dict, Any
from app.services.graph_client import graph_client
from app.core.security import get_current_user
from app.core.config import settings

router = APIRouter()

@router.get("/summary", summary="Azure Active Directory Governance Summary")
def get_azure_ad_summary(current_user: dict = Depends(get_current_user)):
    """
    Azure Active Directory module: AD Connect sync errors, App registration summary, and Risky User detail report.
    """
    insights = graph_client.get_azure_ad_insights()
    return {
        "environment": settings.ENV,
        "azure_ad_governance": insights
    }
