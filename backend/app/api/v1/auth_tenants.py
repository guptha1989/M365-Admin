import json
import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.db.models import RegisteredTenant, AppUser, ModulePhaseConfig

router = APIRouter()

# Pydantic Schemas
class SsoLoginModel(BaseModel):
    user_principal_name: str
    display_name: str
    tenant_id: Optional[str] = "contoso.com"

class RoleAssignmentModel(BaseModel):
    user_principal_name: str
    roles: List[str] # ["ExchangeAdmin", "SecurityAdmin", etc.]
    access_level: Optional[str] = "Read-Only" # Read-Only, Member, Admin

class TenantRegisterModel(BaseModel):
    tenant_id: str
    tenant_name: str
    primary_domain: str
    client_id: Optional[str] = None
    client_secret: Optional[str] = None

class ModulePhaseUpdateModel(BaseModel):
    module_key: str
    active_phase: str

def seed_default_tenants_and_phases(db: Session):
    """Seed initial 3 multi-tenant profiles and default Phase 1 module settings."""
    # Seed Tenants
    if db.query(RegisteredTenant).count() == 0:
        tenants = [
            RegisteredTenant(tenant_id="contoso.com", tenant_name="Contoso Corporation", primary_domain="contoso.com"),
            RegisteredTenant(tenant_id="fabrikam.com", tenant_name="Fabrikam Inc", primary_domain="fabrikam.com"),
            RegisteredTenant(tenant_id="litware.com", tenant_name="Litware Ltd", primary_domain="litware.com")
        ]
        db.add_all(tenants)
        db.commit()

    # Seed Module Phase Defaults (All default to Phase 1: Reporting Only)
    if db.query(ModulePhaseConfig).count() == 0:
        modules = [
            ModulePhaseConfig(module_key="exchange", module_name="Exchange Mailbox Governance", active_phase="PHASE_1_REPORTING"),
            ModulePhaseConfig(module_key="sharepoint", module_name="SharePoint & OneDrive Governance", active_phase="PHASE_1_REPORTING"),
            ModulePhaseConfig(module_key="teams", module_name="Microsoft Teams Governance", active_phase="PHASE_1_REPORTING"),
            ModulePhaseConfig(module_key="security", module_name="Security & Threat Mitigation", active_phase="PHASE_1_REPORTING"),
            ModulePhaseConfig(module_key="license", module_name="License Cost Optimization", active_phase="PHASE_1_REPORTING"),
            ModulePhaseConfig(module_key="legal_hold", module_name="Legal Hold & Purview Compliance", active_phase="PHASE_1_REPORTING"),
        ]
        db.add_all(modules)
        db.commit()

@router.get("/tenants/list", summary="List Registered M365 Tenants")
def get_tenants(db: Session = Depends(get_db)):
    seed_default_tenants_and_phases(db)
    tenants = db.query(RegisteredTenant).filter(RegisteredTenant.is_active == True).all()
    return [{
        "tenant_id": t.tenant_id,
        "tenant_name": t.tenant_name,
        "primary_domain": t.primary_domain
    } for t in tenants]

@router.post("/tenants/register", summary="Register New M365 Tenant")
def register_tenant(req: TenantRegisterModel, db: Session = Depends(get_db)):
    existing = db.query(RegisteredTenant).filter(RegisteredTenant.tenant_id == req.tenant_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Tenant ID already registered.")
    
    new_t = RegisteredTenant(
        tenant_id=req.tenant_id,
        tenant_name=req.tenant_name,
        primary_domain=req.primary_domain,
        client_id=req.client_id
    )
    db.add(new_t)
    db.commit()
    return {"status": "Success", "message": f"Tenant '{req.tenant_name}' registered successfully."}

@router.post("/auth/sso-login", summary="M365 SSO Sign-In & User Auto-Provisioning")
def sso_login(req: SsoLoginModel, db: Session = Depends(get_db)):
    """Handles M365 SSO login. Auto-provisions new users with NO roles by default."""
    user = db.query(AppUser).filter(AppUser.user_principal_name == req.user_principal_name).first()
    
    if not user:
        # Create new user with NO roles assigned by default
        user = AppUser(
            user_principal_name=req.user_principal_name,
            display_name=req.display_name,
            tenant_id=req.tenant_id or "contoso.com",
            roles_json=json.dumps([]), # NO ROLES BY DEFAULT
            access_level="Read-Only"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        user.last_login_at = datetime.datetime.utcnow()
        db.commit()

    roles = json.loads(user.roles_json) if user.roles_json else []
    return {
        "status": "Success",
        "user_principal_name": user.user_principal_name,
        "display_name": user.display_name,
        "tenant_id": user.tenant_id,
        "roles": roles,
        "access_level": user.access_level,
        "is_role_unassigned": len(roles) == 0
    }

@router.get("/auth/users", summary="List Signed-up SSO Users and Assigned Roles")
def list_app_users(db: Session = Depends(get_db)):
    # Seed default Global Admin if empty
    if db.query(AppUser).count() == 0:
        admin_user = AppUser(
            user_principal_name="global_admin@contoso.com",
            display_name="Global Administrator",
            tenant_id="contoso.com",
            roles_json=json.dumps(["GlobalAdmin"]),
            access_level="Admin"
        )
        test_user = AppUser(
            user_principal_name="sso_user@contoso.com",
            display_name="Newly Signed-up User (Unassigned Roles)",
            tenant_id="contoso.com",
            roles_json=json.dumps([]),
            access_level="Read-Only"
        )
        db.add_all([admin_user, test_user])
        db.commit()

    users = db.query(AppUser).all()
    result = []
    for u in users:
        roles = json.loads(u.roles_json) if u.roles_json else []
        result.append({
            "id": u.id,
            "user_principal_name": u.user_principal_name,
            "display_name": u.display_name,
            "tenant_id": u.tenant_id,
            "roles": roles,
            "roles_display": ", ".join(roles) if roles else "⚠️ Unassigned (No Roles)",
            "access_level": u.access_level,
            "is_active": u.is_active,
            "created_at": u.created_at.strftime("%Y-%m-%d %H:%M:%S") if u.created_at else ""
        })
    return result

@router.post("/auth/users/assign-roles", summary="Assign Roles and Module Access Level to SSO User")
def assign_user_roles(req: RoleAssignmentModel, db: Session = Depends(get_db)):
    user = db.query(AppUser).filter(AppUser.user_principal_name == req.user_principal_name).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    
    user.roles_json = json.dumps(req.roles)
    user.access_level = req.access_level or "Read-Only"
    db.commit()
    
    return {
        "status": "Success",
        "message": f"Updated roles for '{user.user_principal_name}'. Assigned Roles: {req.roles}, Access Level: {user.access_level}"
    }

@router.get("/module-phases/get", summary="Get Per-Module Governance Automation Phases")
def get_module_phases(db: Session = Depends(get_db)):
    seed_default_tenants_and_phases(db)
    configs = db.query(ModulePhaseConfig).all()
    return [{
        "module_key": c.module_key,
        "module_name": c.module_name,
        "active_phase": c.active_phase,
        "phase_label": "Phase 1: Report Only" if c.active_phase == "PHASE_1_REPORTING" else ("Phase 2: Semi-Automated" if c.active_phase == "PHASE_2_SEMI_AUTOMATED" else "Phase 3: Fully Automated Guardrails"),
        "updated_by": c.updated_by,
        "updated_at": c.updated_at.strftime("%Y-%m-%d %H:%M:%S") if c.updated_at else ""
    } for c in configs]

@router.post("/module-phases/update", summary="Update Phase Level for a Specific Module")
def update_module_phase(req: ModulePhaseUpdateModel, db: Session = Depends(get_db)):
    config = db.query(ModulePhaseConfig).filter(ModulePhaseConfig.module_key == req.module_key).first()
    if not config:
        config = ModulePhaseConfig(module_key=req.module_key, module_name=req.module_key.capitalize())
        db.add(config)
    
    config.active_phase = req.active_phase
    config.updated_at = datetime.datetime.utcnow()
    db.commit()

    return {
        "status": "Success",
        "message": f"Module '{req.module_key}' updated to '{req.active_phase}'."
    }
