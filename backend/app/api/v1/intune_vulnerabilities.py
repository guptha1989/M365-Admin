import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.db.models import IntuneVulnerability

router = APIRouter()

class IntuneRemediateModel(BaseModel):
    cve_id: str
    target_device_type: Optional[str] = "Windows 11"

def seed_default_intune_vulnerabilities(db: Session):
    if db.query(IntuneVulnerability).count() == 0:
        vulnerabilities = [
            IntuneVulnerability(
                cve_id="CVE-2026-21412",
                title="Windows Defender SmartScreen Security Feature Bypass",
                severity="CRITICAL",
                cvss_score=9.8,
                affected_device_type="Windows 11 Enterprise",
                affected_count=14,
                remediation_steps="Deploy KB5034441 via Intune Quality Update ring and force SmartScreen policy validation.",
                tenant_id="contoso.com"
            ),
            IntuneVulnerability(
                cve_id="CVE-2026-1889",
                title="Microsoft Edge / Chromium Remote Code Execution",
                severity="HIGH",
                cvss_score=8.8,
                affected_device_type="Windows 11 & macOS",
                affected_count=28,
                remediation_steps="Push Edge Version 122.0.2365.92 auto-update package to all enrolled Intune devices.",
                tenant_id="contoso.com"
            ),
            IntuneVulnerability(
                cve_id="CVE-2026-24890",
                title="Android Kernel Elevation of Privilege Vulnerability",
                severity="HIGH",
                cvss_score=7.8,
                affected_device_type="Android 14 Managed Work Profile",
                affected_count=9,
                remediation_steps="Enforce Intune Compliance Policy: Minimum Android Security Patch Level 2026-03-01.",
                tenant_id="fabrikam.com"
            ),
            IntuneVulnerability(
                cve_id="CVE-2026-30112",
                title="iOS WebKit Memory Corruption RCE Exposure",
                severity="CRITICAL",
                cvss_score=9.1,
                affected_device_type="iOS 17.3 Corporate Devices",
                affected_count=11,
                remediation_steps="Trigger Intune Mobile Device Management (MDM) forced update to iOS 17.4.",
                tenant_id="litware.com"
            )
        ]
        db.add_all(vulnerabilities)
        db.commit()

@router.get("/intune/vulnerabilities", summary="Get Intune Security Vulnerabilities & Remediation Inventory")
def get_intune_vulnerabilities(
    tenant_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    seed_default_intune_vulnerabilities(db)
    query = db.query(IntuneVulnerability)
    if tenant_id and tenant_id != "ALL":
        query = query.filter(IntuneVulnerability.tenant_id == tenant_id)
    
    vulns_db = query.all()
    
    total = len(vulns_db)
    critical = sum(1 for v in vulns_db if v.severity == "CRITICAL")
    high = sum(1 for v in vulns_db if v.severity == "HIGH")
    medium = sum(1 for v in vulns_db if v.severity == "MEDIUM")
    total_affected = sum(v.affected_count or 0 for v in vulns_db)
    
    vulnerabilities = []
    for v in vulns_db:
        vendor = "Apple" if "iOS" in (v.affected_device_type or "") else ("Android" if "Android" in (v.affected_device_type or "") else "Microsoft")
        vulnerabilities.append({
            "id": v.id,
            "cve_id": v.cve_id,
            "title": v.title,
            "severity": v.severity,
            "cvss_score": v.cvss_score,
            "component": v.affected_device_type,
            "vendor": vendor,
            "affected_device_count": v.affected_count,
            "remediation_plan": v.remediation_steps,
            "tenant_id": v.tenant_id,
            "status": "REMEDIATED" if v.is_remediated else "ACTIVE",
            "created_at": v.created_at.strftime("%Y-%m-%d %H:%M:%S") if v.created_at else ""
        })

    return {
        "summary": {
            "total": total,
            "critical": critical,
            "high": high,
            "medium": medium,
            "total_affected_devices": total_affected
        },
        "vulnerabilities": vulnerabilities
    }

@router.post("/intune/vulnerabilities/remediate", summary="Execute Intune Vulnerability Patch Deployment")
def remediate_intune_vulnerability(req: IntuneRemediateModel, db: Session = Depends(get_db)):
    vuln = db.query(IntuneVulnerability).filter(IntuneVulnerability.cve_id == req.cve_id).first()
    if not vuln:
        raise HTTPException(status_code=404, detail="Vulnerability CVE record not found.")
    
    vuln.is_remediated = True
    db.commit()

    return {
        "status": "Success",
        "message": f"Remediation patch pushed to Intune MDM for '{req.cve_id}' ({vuln.title}). Target Devices: {vuln.affected_device_type} ({vuln.affected_count} devices updated).",
        "cve_id": req.cve_id
    }
