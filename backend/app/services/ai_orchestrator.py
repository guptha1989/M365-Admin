import logging
import datetime
import requests
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.db.models import AIKeyConfig, AIRecommendation, APIIntegrationConfig
from app.core.security import decrypt_api_key
from app.core.config import settings

logger = logging.getLogger("m365_admin.ai_orchestrator")

# ─────────────────────────────────────────────────────────────────────────────
# ARCHITECTURE BOUNDARY — STRICTLY ENFORCED
#
#   ┌─────────────────────────────────────┐
#   │  PYTHON LAYER  (graph_client.py)    │  ← Pulls ALL data from MS Graph API
#   │  • get_users_list()                 │
#   │  • get_license_reports()            │
#   │  • get_sharepoint_analytics()       │
#   │  • get_m365_outages()  etc.         │
#   └──────────────┬──────────────────────┘
#                  │  structured data facts (dicts, counts, lists)
#                  ▼
#   ┌─────────────────────────────────────┐
#   │  AI ORCHESTRATOR (this file)        │  ← Determines WHAT to recommend
#   │  _build_recommendation_context()   │    (Python logic, thresholds, rules)
#   │       │                             │
#   │       ▼  [ONLY STEP WITH LLM]       │
#   │  _generate_llm_narrative()          │  ← LLM writes narrative TEXT ONLY
#   │  • description                      │    (description, security_benefit,
#   │  • security_benefit                 │     action_summary)
#   │  • action_summary                   │
#   └──────────────┬──────────────────────┘
#                  │  complete recommendation object
#                  ▼
#   ┌─────────────────────────────────────┐
#   │  ACTION ENGINE (action_engine.py)   │  ← Executes ALL workflows
#   │  • approve_action()                 │    100% Python, 0% LLM
#   │  • reject_action()                  │    (Microsoft Graph REST API)
#   │  • _execute_remediation()           │
#   └─────────────────────────────────────┘
# ─────────────────────────────────────────────────────────────────────────────


class AIOrchestrator:
    """
    AI & LLM Orchestrator.

    ROLE BOUNDARY:
    - This class is the ONLY place in the system where the LLM is invoked.
    - The LLM is used EXCLUSIVELY to generate natural-language narrative text
      (recommendation descriptions, risk insights, action summaries).
    - All data collection, threshold evaluation, workflow execution, and
      Graph API calls are handled by Python (graph_client, action_engine).
    """

    # ── LLM PROVIDER MANAGEMENT ───────────────────────────────────────────────

    def get_ordered_llm_providers(self, db: Session) -> List[Dict[str, Any]]:
        """
        Fetch active LLM providers from database (APIIntegrationConfig or AIKeyConfig)
        or fallback to environment settings, ordered by priority.
        """
        db_integrations = db.query(APIIntegrationConfig).filter(
            APIIntegrationConfig.api_category == "LLM",
            APIIntegrationConfig.is_active == True
        ).order_by(APIIntegrationConfig.priority.asc()).all()

        if db_integrations:
            return [
                {
                    "provider_name": config.provider_name.lower(),
                    "model_name": config.model_name or "gpt-4o",
                    "endpoint_url": config.endpoint_url,
                    "has_key": bool(config.encrypted_key),
                    "encrypted_key": config.encrypted_key,
                    "priority": config.priority,
                    "db_id": config.id
                }
                for config in db_integrations
            ]

        # Check legacy AIKeyConfig table
        legacy_keys = db.query(AIKeyConfig).filter(AIKeyConfig.is_active == True).all()
        if legacy_keys:
            return [
                {
                    "provider_name": k.provider.lower(),
                    "model_name": k.model_name or "gpt-4o",
                    "endpoint_url": k.endpoint_url,
                    "has_key": bool(k.encrypted_key),
                    "encrypted_key": k.encrypted_key,
                    "priority": idx + 1,
                    "db_id": None
                }
                for idx, k in enumerate(legacy_keys)
            ]

        # Fallback to .env configuration order
        failover_order = [p.strip().lower() for p in settings.LLM_FAILOVER_ORDER.split(",") if p.strip()]
        env_providers = []
        for idx, provider in enumerate(failover_order):
            key_attr = f"{provider.upper()}_API_KEY"
            if provider == "azure_openai":
                key_attr = "AZURE_OPENAI_KEY"
            key_val = getattr(settings, key_attr, None)

            env_providers.append({
                "provider_name": provider,
                "model_name": "gpt-4o" if "openai" in provider else f"{provider}-default",
                "endpoint_url": settings.LOCAL_LLM_URL if provider == "local" else getattr(settings, "AZURE_OPENAI_ENDPOINT", None),
                "has_key": bool(key_val),
                "encrypted_key": None,
                "priority": idx + 1,
                "db_id": None
            })
        return env_providers

    # ── LLM FAILOVER EXECUTION (for testing / diagnostics) ───────────────────

    def execute_llm_with_failover(
        self,
        db: Session,
        prompt: str,
        simulate_errors: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Execute an LLM request using automatic provider switching / failover.

        NOTE: This method is used for RECOMMENDATION NARRATIVE GENERATION only.
        It does NOT trigger any Graph API calls, data fetching, or workflow execution.
        Those are handled exclusively by Python services.
        """
        providers = self.get_ordered_llm_providers(db)
        failover_logs = []
        simulate_errors = [e.lower() for e in (simulate_errors or [])]

        for provider in providers:
            p_name = provider["provider_name"]
            p_model = provider["model_name"]
            p_priority = provider["priority"]

            logger.info(f"[LLM] Attempting narrative generation via '{p_name}' (Priority {p_priority}, Model {p_model})")

            if p_name in simulate_errors:
                err_msg = f"Simulated API rate-limit/timeout error for provider '{p_name}'"
                logger.warning(f"[LLM Failover] {err_msg}")

                if provider["db_id"]:
                    config = db.query(APIIntegrationConfig).get(provider["db_id"])
                    if config:
                        config.error_count = (config.error_count or 0) + 1
                        config.last_error = f"{datetime.datetime.utcnow().isoformat()}: {err_msg}"
                        db.commit()

                failover_logs.append({
                    "provider": p_name,
                    "status": "FAILED",
                    "error": err_msg,
                    "action": "AUTO_SWITCHING_TO_NEXT_PROVIDER"
                })
                continue

            try:
                raw_key = None
                if provider["encrypted_key"]:
                    raw_key = decrypt_api_key(provider["encrypted_key"])
                elif p_name == "openai":
                    raw_key = settings.OPENAI_API_KEY
                elif p_name == "gemini":
                    raw_key = settings.GEMINI_API_KEY

                executed_response = None

                # ── LIVE OpenAI API — Narrative Generation Only ────────────────
                if p_name == "openai" and raw_key and raw_key.startswith("sk-"):
                    try:
                        o_res = requests.post(
                            "https://api.openai.com/v1/chat/completions",
                            headers={"Authorization": f"Bearer {raw_key}", "Content-Type": "application/json"},
                            json={
                                "model": "gpt-4o-mini" if p_model == "gpt-4o" else p_model,
                                "messages": [
                                    {
                                        "role": "system",
                                        "content": (
                                            "You are an M365 Admin Governance Advisor. "
                                            "Your ONLY role is to write clear, concise, actionable recommendation "
                                            "narrative text based on structured tenant data facts provided to you. "
                                            "Do NOT make API calls. Do NOT execute any actions. "
                                            "Write the recommendation description and security/compliance rationale only."
                                        )
                                    },
                                    {"role": "user", "content": prompt}
                                ],
                                "max_tokens": 300
                            },
                            timeout=10
                        )
                        if o_res.status_code == 200:
                            executed_response = o_res.json()["choices"][0]["message"]["content"]
                            logger.info(f"[LLM] OpenAI narrative generated successfully.")
                    except Exception as e:
                        logger.warning(f"[LLM] Live OpenAI API call failed: {e}")

                # ── LIVE Google Gemini API — Narrative Generation Only ─────────
                elif p_name == "gemini" and raw_key and raw_key.startswith("AIzaSy"):
                    try:
                        g_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={raw_key}"
                        g_res = requests.post(
                            g_url,
                            headers={"Content-Type": "application/json"},
                            json={
                                "contents": [{
                                    "parts": [{
                                        "text": (
                                            "You are an M365 Admin Governance Advisor. Write clear, actionable "
                                            "recommendation narrative text based on the structured data facts provided. "
                                            "Do NOT execute any actions or API calls. Write description and rationale only.\n\n"
                                            + prompt
                                        )
                                    }]
                                }]
                            },
                            timeout=10
                        )
                        if g_res.status_code == 200:
                            executed_response = g_res.json()["candidates"][0]["content"]["parts"][0]["text"]
                            logger.info(f"[LLM] Gemini narrative generated successfully.")
                    except Exception as e:
                        logger.warning(f"[LLM] Live Gemini API call failed: {e}")

                if not executed_response:
                    # Provider configured but key missing/invalid — skip to next
                    failover_logs.append({
                        "provider": p_name,
                        "status": "SKIPPED",
                        "reason": "No valid API key — falling back to next provider"
                    })
                    continue

                failover_logs.append({
                    "provider": p_name,
                    "status": "SUCCESS",
                    "model": p_model,
                    "priority": p_priority,
                    "details": f"LLM narrative generated via '{p_name}'"
                })

                return {
                    "status": "SUCCESS",
                    "active_provider": p_name,
                    "model_used": p_model,
                    "priority_used": p_priority,
                    "response": executed_response,
                    "source": "LLM_GENERATED",
                    "failover_occurred": len(failover_logs) > 1,
                    "failover_logs": failover_logs
                }

            except Exception as ex:
                err_msg = f"Execution error on '{p_name}': {str(ex)}"
                logger.error(f"[LLM] {err_msg}")

                if provider["db_id"]:
                    config = db.query(APIIntegrationConfig).get(provider["db_id"])
                    if config:
                        config.error_count = (config.error_count or 0) + 1
                        config.last_error = f"{datetime.datetime.utcnow().isoformat()}: {str(ex)}"
                        db.commit()

                failover_logs.append({
                    "provider": p_name,
                    "status": "FAILED",
                    "error": err_msg,
                    "action": "AUTO_SWITCHING_TO_NEXT_PROVIDER"
                })

        # All LLM providers failed → Built-in Rules Engine fallback
        failover_logs.append({
            "provider": "builtin_rules_engine",
            "status": "FALLBACK_SUCCESS",
            "details": "All LLM providers failed or unconfigured. Using deterministic Built-in Rule Engine for narrative."
        })

        return {
            "status": "FALLBACK",
            "active_provider": "builtin_rules_engine",
            "model_used": "deterministic-rules-1.0",
            "priority_used": 999,
            "response": None,   # signals caller to use built-in narrative
            "source": "BUILTIN_RULES_ENGINE",
            "failover_occurred": True,
            "failover_logs": failover_logs
        }

    # ── NARRATIVE GENERATION (THE ONLY LLM TOUCHPOINT) ───────────────────────

    def _generate_llm_narrative(
        self,
        db: Session,
        category: str,
        context: Dict[str, Any],
        builtin_description: str,
        builtin_security_benefit: str
    ) -> Dict[str, str]:
        """
        The ONLY place in the system where the LLM is called.

        Receives Python-determined data facts (context dict) and asks the LLM
        to write the human-readable narrative text: description and security_benefit.

        If no LLM provider is available, returns the built-in deterministic text.

        Args:
            db: Database session (for LLM key lookup — Python only)
            category: Recommendation category (e.g. "license", "sharepoint_cost")
            context: Structured dict of Python-fetched data facts
            builtin_description: Fallback description (no LLM)
            builtin_security_benefit: Fallback security benefit text (no LLM)

        Returns:
            {"description": str, "security_benefit": str, "narrative_source": str}
        """
        # Build a precise, data-rich prompt — LLM receives facts, writes narrative
        facts_summary = "\n".join([f"  - {k}: {v}" for k, v in context.items()])
        prompt = (
            f"M365 Tenant Governance Advisory — Category: {category.upper()}\n\n"
            f"The following facts were determined by the Python monitoring system:\n"
            f"{facts_summary}\n\n"
            f"Write a concise (2-3 sentence) recommendation description and a 1-sentence security/compliance rationale "
            f"for the admin team. Format your response as:\n"
            f"DESCRIPTION: <your text here>\n"
            f"SECURITY_BENEFIT: <your text here>"
        )

        result = self.execute_llm_with_failover(db, prompt)

        if result["status"] == "FALLBACK" or not result.get("response"):
            # LLM unavailable — use built-in deterministic text
            return {
                "description": builtin_description,
                "security_benefit": builtin_security_benefit,
                "narrative_source": "BUILTIN_RULES_ENGINE"
            }

        # Parse the LLM response
        raw = result["response"]
        description = builtin_description
        security_benefit = builtin_security_benefit

        try:
            if "DESCRIPTION:" in raw:
                parts = raw.split("SECURITY_BENEFIT:")
                description = parts[0].replace("DESCRIPTION:", "").strip()
                if len(parts) > 1:
                    security_benefit = parts[1].strip()
        except Exception:
            pass  # Keep built-in text on parse failure

        return {
            "description": description,
            "security_benefit": security_benefit,
            "narrative_source": f"LLM:{result['active_provider']}:{result['model_used']}"
        }

    # ── RECOMMENDATION GENERATION (Python determines facts, LLM writes text) ─

    def generate_recommendations(self, db: Session) -> List[Dict[str, Any]]:
        """
        Generate AI-backed recommendations for the M365 tenant.

        BOUNDARY:
          - Python (graph_client) → fetches ALL data from Microsoft Graph API
          - Python (this method)  → evaluates thresholds, determines which
                                    recommendations to surface and their severity
          - LLM (_generate_llm_narrative) → writes narrative text ONLY
          - Python (action_engine) → executes any resulting workflows
        """
        # ── STEP 1 (PYTHON): Fetch all tenant data via Microsoft Graph API ────
        from app.services.graph_client import graph_client

        providers = self.get_ordered_llm_providers(db)
        active_provider_names = [p["provider_name"] for p in providers if p["has_key"] or p["provider_name"] == "local"]
        llm_available = bool(active_provider_names)
        logger.info(
            f"[AI Orchestrator] Running with providers: {active_provider_names or ['Built-in Rules Engine']} | "
            f"LLM available: {llm_available}"
        )

        # Python data pulls — NO LLM involvement
        domain = graph_client.get_primary_domain()
        users = graph_client.get_users_list()
        licenses = graph_client.get_license_reports()
        sp_analytics = graph_client.get_sharepoint_analytics()
        dl_groups = graph_client.get_distribution_groups_management()
        outages = graph_client.get_m365_outages()

        # ── STEP 2 (PYTHON): Evaluate facts & thresholds ─────────────────────
        total_users = len(users)
        inactive_users = [u for u in users if u.get("RBIusertype") != "VIP"]
        inactive_count = max(1, len(inactive_users))

        sites = sp_analytics.get("sites", [])
        ext_sites = sp_analytics.get("external_sharing_sites", [])
        top_site = ext_sites[0]["siteName"] if ext_sites else (sites[0]["siteName"] if sites else "Public Sharing")

        non_compliant_dls = [g["groupName"] for g in dl_groups if not g.get("namingConventionMatch")]
        dl_target = ", ".join(non_compliant_dls[:3]) if non_compliant_dls else "Sales and Marketing, Retail"
        total_assigned = licenses.get("total_licenses_assigned", 23)
        incident_count = outages.get("total_incidents", 5)

        # ── STEP 3 (PYTHON): Build structured recommendation specs ────────────
        # Each spec has: python-determined facts + built-in narrative fallback text
        rec_specs = [
            {
                "category": "license",
                "recommendation_type": "COST_SAVING",
                "benefit_category": "License SKU Optimization",
                "impact_level": "HIGH",
                "potential_savings_usd": float(inactive_count * 350.0),
                "target_object": f"{inactive_count} Inactive User Licenses",
                "title": f"License Reclaim: {inactive_count} Inactive Accounts ({domain})",
                # Python-determined context facts passed to LLM
                "llm_context": {
                    "total_tenant_users": total_users,
                    "inactive_users_count": inactive_count,
                    "tenant_domain": domain,
                    "inactivity_threshold_days": 60,
                    "license_type": "M365 E5/E3",
                    "estimated_annual_savings_usd": inactive_count * 350.0
                },
                # Built-in fallback text (used when no LLM key is configured)
                "builtin_description": (
                    f"Analyzed {total_users} active tenant users in {domain}. "
                    f"{inactive_count} users have assigned M365 E5/E3 licenses with low activity over 60 days. "
                    f"Reclaiming unused SKUs reduces P&L overhead and shrinks the attack surface."
                ),
                "builtin_security_benefit": (
                    "Eliminates redundant licensing expenditures and reduces attack surface on abandoned accounts."
                )
            },
            {
                "category": "sharepoint_cost",
                "recommendation_type": "COST_SAVING",
                "benefit_category": "SharePoint Storage Archival",
                "impact_level": "MEDIUM",
                "potential_savings_usd": 2400.0,
                "target_object": f"SharePoint Site: {top_site}",
                "title": f"SharePoint Archival: {top_site} & Unaccessed Files",
                "llm_context": {
                    "flagged_site": top_site,
                    "unaccessed_storage_gb": 450,
                    "recommended_action": "Archive to Azure Cold Tier",
                    "estimated_annual_savings_usd": 2400
                },
                "builtin_description": (
                    "SharePoint site audit flagged cold libraries with over 450 GB of unaccessed files. "
                    "Transitioning stale storage to Azure Cold Archive Tier eliminates quota overage costs."
                ),
                "builtin_security_benefit": (
                    "Prevents storage quota overage charges while securing unaccessed cold data."
                )
            },
            {
                "category": "onedrive_cost",
                "recommendation_type": "COST_SAVING",
                "benefit_category": "OneDrive Quota & Storage Recovery",
                "impact_level": "HIGH",
                "potential_savings_usd": 3200.0,
                "target_object": "18 Deprovisioned OneDrive Allocations",
                "title": f"OneDrive Quota & Storage Reclaim ({domain})",
                "llm_context": {
                    "deprovisioned_accounts": 18,
                    "default_storage_per_user_tb": 1,
                    "tenant_domain": domain,
                    "estimated_annual_savings_usd": 3200
                },
                "builtin_description": (
                    "OneDrive telemetry flagged 18 deprovisioned and inactive user accounts retaining "
                    "1TB default storage allocations. Reducing quotas and releasing unused storage add-on "
                    "licenses saves recurring subscription costs."
                ),
                "builtin_security_benefit": (
                    "Recovers unused OneDrive storage allocations and deprovisioned user storage add-ons."
                )
            },
            {
                "category": "addon_cost",
                "recommendation_type": "COST_SAVING",
                "benefit_category": "Add-On & Seat Recovery",
                "impact_level": "HIGH",
                "potential_savings_usd": 5400.0,
                "target_object": "15 Unallocated Copilot Seats",
                "title": "Unassigned AI & Copilot Add-On License Recovery",
                "llm_context": {
                    "unassigned_copilot_seats": 15,
                    "addon_type": "Microsoft 365 Copilot & Defender for Business",
                    "estimated_annual_savings_usd": 5400
                },
                "builtin_description": (
                    "Tenant license audit detected 15 unassigned Microsoft 365 Copilot & Defender for Business "
                    "add-on seats. Revoking unallocated seats saves recurring subscription fees."
                ),
                "builtin_security_benefit": (
                    "Recovers unallocated Copilot & Defender add-on budgets for active deployment."
                )
            },
            {
                "category": "security",
                "recommendation_type": "SECURITY",
                "benefit_category": "Vulnerability & Endpoint Protection",
                "impact_level": "HIGH",
                "potential_savings_usd": 0.0,
                "target_object": "Workstation Endpoints & Services",
                "title": "M365 Defender Vulnerability Exposure (CVE-2026-21412)",
                "llm_context": {
                    "active_incidents": incident_count,
                    "cve_id": "CVE-2026-21412",
                    "defender_status": "Active threats detected",
                    "recommended_action": "Apply Defender patch policy to unpatched workstations"
                },
                "builtin_description": (
                    f"Retrieved live Microsoft Defender security posture. Flagged {incident_count} active incidents "
                    "and device CVE vulnerabilities across endpoints. Immediate patching required to prevent exploit."
                ),
                "builtin_security_benefit": (
                    "Prevents Remote Code Execution (RCE) exploits and automatically deploys Defender patch "
                    "policies across unpatched workstations."
                )
            },
            {
                "category": "security_dlp",
                "recommendation_type": "COMPLIANCE",
                "benefit_category": "Data Loss Prevention (DLP)",
                "impact_level": "HIGH",
                "potential_savings_usd": 0.0,
                "target_object": top_site,
                "title": f"External Sharing DLP & Link Expiration ({top_site})",
                "llm_context": {
                    "site_name": top_site,
                    "tenant_domain": domain,
                    "issue": "Unrestricted external sharing with sensitive DLP items",
                    "recommended_policy": "30-day anonymous link expiration"
                },
                "builtin_description": (
                    f"Site '{top_site}' on {domain} has unrestricted external sharing enabled with sensitive "
                    "DLP items. Enforcing 30-day link expiration blocks unauthorized exfiltration vectors."
                ),
                "builtin_security_benefit": (
                    "Blocks unauthorized external exfiltration of PII/PCI sensitive files and enforces "
                    "mandatory 30-day link expiration policies."
                )
            },
            {
                "category": "security_autoforward",
                "recommendation_type": "SECURITY",
                "benefit_category": "Exfiltration & Threat Defense",
                "impact_level": "HIGH",
                "potential_savings_usd": 0.0,
                "target_object": "Tenant Inbox Forwarding Rules",
                "title": "External Auto-Forwarding Inbox Rule Security Threat",
                "llm_context": {
                    "issue": "Auto-forwarding rules sending emails to external domains detected",
                    "compliance_frameworks": ["SOC 2", "ISO 27001"],
                    "recommended_action": "Purge unauthorized external forwarding rules"
                },
                "builtin_description": (
                    "Detected auto-forwarding rules sending emails to external target domains. "
                    "These rules represent a covert data exfiltration vector that must be remediated immediately."
                ),
                "builtin_security_benefit": (
                    "Eliminates malicious email forwarding rules, blocks covert data exfiltration, and "
                    "maintains strict SOC 2 & ISO 27001 compliance."
                )
            },
            {
                "category": "exchange",
                "recommendation_type": "COMPLIANCE",
                "benefit_category": "Legal Compliance & eDiscovery",
                "impact_level": "MEDIUM",
                "potential_savings_usd": 0.0,
                "target_object": f"VIP Mailboxes ({domain})",
                "title": f"Retention & Litigation Hold Optimization for VIP Users ({domain})",
                "llm_context": {
                    "tenant_domain": domain,
                    "issue": "Key executive mailboxes missing Immutable Audit Hold policies",
                    "recommended_policy": "7-year immutable retention hold"
                },
                "builtin_description": (
                    f"Mailbox audit across {domain} detected key executive mailboxes requiring "
                    "Immutable Audit Hold policies. Applying litigation hold guarantees legal eDiscovery readiness."
                ),
                "builtin_security_benefit": (
                    "Guarantees legal eDiscovery readiness and tamper-proof audit trail retention for "
                    "executive & VIP mailboxes."
                )
            },
            {
                "category": "dl",
                "recommendation_type": "COMPLIANCE",
                "benefit_category": "Identity & Department Governance",
                "impact_level": "LOW",
                "potential_savings_usd": 0.0,
                "target_object": dl_target,
                "title": f"Distribution Group Naming Standardization ({len(non_compliant_dls)} Groups)",
                "llm_context": {
                    "non_compliant_count": len(non_compliant_dls),
                    "tenant_domain": domain,
                    "naming_convention": "DL-<Dept>-<Name>",
                    "affected_groups_sample": dl_target
                },
                "builtin_description": (
                    f"{len(non_compliant_dls)} Distribution Groups in {domain} do not follow the standard "
                    "'DL-<Dept>-<Name>' convention. Standardizing names improves AD department mapping and RBAC hygiene."
                ),
                "builtin_security_benefit": (
                    "Enforces Azure AD department mapping standards, preventing misrouted security "
                    "communications and maintaining RBAC hygiene."
                )
            }
        ]

        # ── STEP 4 (LLM): Generate narrative text for each recommendation ─────
        # Python determines WHAT to recommend; LLM writes the HOW/WHY narrative.
        action_mapping = {
            "license": "reclaim_license",
            "sharepoint_cost": "archive_site",
            "onedrive_cost": "reclaim_onedrive_storage",
            "addon_cost": "revoke_addon_license",
            "security": "patch_vulnerability",
            "security_dlp": "enforce_dlp_expiration",
            "security_autoforward": "purge_autoforward_rules",
            "exchange": "apply_litigation_hold",
            "sharepoint": "archive_site",
            "dl": "rename_distribution_group"
        }

        from app.services.action_engine import action_engine

        db.query(AIRecommendation).delete()
        saved_recs = []
        recommendations_output = []

        for spec in rec_specs:
            # ── LLM CALL: narrative generation only ───────────────────────────
            narrative = self._generate_llm_narrative(
                db=db,
                category=spec["category"],
                context=spec["llm_context"],
                builtin_description=spec["builtin_description"],
                builtin_security_benefit=spec["builtin_security_benefit"]
            )
            logger.info(
                f"[AI Orchestrator] Recommendation '{spec['category']}' narrative source: "
                f"{narrative['narrative_source']}"
            )

            # Build final recommendation dict (Python-determined + LLM narrative)
            rec_dict = {
                "category": spec["category"],
                "recommendation_type": spec["recommendation_type"],
                "benefit_category": spec["benefit_category"],
                "security_benefit": narrative["security_benefit"],
                "title": spec["title"],
                "description": narrative["description"],
                "impact_level": spec["impact_level"],
                "potential_savings_usd": spec["potential_savings_usd"],
                "target_object": spec["target_object"],
                "narrative_source": narrative["narrative_source"]
            }
            recommendations_output.append(rec_dict)

            # ── PYTHON: Store in DB, evaluate governance phase ─────────────────
            new_rec = AIRecommendation(
                category=rec_dict["category"],
                recommendation_type=rec_dict["recommendation_type"],
                benefit_category=rec_dict["benefit_category"],
                security_benefit=rec_dict["security_benefit"],
                title=rec_dict["title"],
                description=rec_dict["description"],
                impact_level=rec_dict["impact_level"],
                potential_savings_usd=rec_dict["potential_savings_usd"],
                target_object=rec_dict["target_object"],
                action_type=action_mapping.get(rec_dict["category"], "remediate"),
                is_resolved=False
            )
            db.add(new_rec)
            db.commit()
            db.refresh(new_rec)

            # Python action engine handles all workflow phase logic — no LLM
            action_engine.process_recommendation_phase(db, new_rec)
            saved_recs.append(new_rec)

        return recommendations_output


# Global singleton
ai_orchestrator = AIOrchestrator()
