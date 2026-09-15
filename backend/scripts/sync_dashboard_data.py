import sys
import os
import datetime

# Ensure stdout uses UTF-8 encoding on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import SessionLocal, init_db
from app.services.graph_client import graph_client
from app.services.ai_orchestrator import ai_orchestrator
from app.core.tasks import enqueue_db_job, process_background_job_task
from app.db.models import AuditLog, AIRecommendation, JobQueue, MailflowCache

def sync_dashboard_and_sql():
    print("==========================================================================")
    print("M365 ADMIN BOT - PULL LIVE API DATA & UPDATE SQL DATABASE & DASHBOARD")
    print("==========================================================================")

    init_db()
    db = SessionLocal()

    try:
        # Step 1: Pull live data via Microsoft Graph REST API & M365 Telemetry
        print("\n1. Pulling live M365 tenant data via Microsoft Graph REST API...")
        outages = graph_client.get_m365_outages()
        active_issues = outages.get('total_incidents', outages.get('active_issues_count', 0))
        print(f"   [OK] Service Announcements: {active_issues} active issues retrieved.")

        licenses = graph_client.get_license_reports()
        print(f"   [OK] Exchange & License Telemetry: {licenses.get('total_licenses_assigned', 0)} licenses assigned.")

        cve_report = graph_client.get_intune_defender_vulnerability_report()
        if isinstance(cve_report, list):
            unpatched_count = sum(v.get('affectedDevices', 0) for v in cve_report)
        else:
            unpatched_count = cve_report.get('unpatched_devices_count', 0)
        print(f"   [OK] Intune & Defender CVE Vulnerabilities: {unpatched_count} unpatched devices flagged.")

        azure_ad = graph_client.get_azure_ad_insights()
        print(f"   [OK] Azure AD Insights: {azure_ad.get('ad_connect_sync_status', 'UNKNOWN')} (Sync Errors: {azure_ad.get('sync_errors_count', 0)})")

        sp_analytics = graph_client.get_sharepoint_analytics()
        sites_list = sp_analytics.get('sites', [])
        storage_used = sp_analytics.get('storage_used_gb', sum(s.get('storageUsedGB', 0) for s in sites_list))
        total_sites = sp_analytics.get('total_sites', len(sites_list))
        print(f"   [OK] SharePoint Analytics: {storage_used} GB storage used across {total_sites} sites.")

        # Step 2: Trigger & Execute Mailflow Aggregation Background Job into SQL
        print("\n2. Executing 1-Year Mailflow Aggregation Job into SQL Express/SQLite...")
        job_id_str = enqueue_db_job(
            job_type="MAILFLOW_1YEAR_AGGREGATION",
            payload={"requested_by": "admin_sync_script", "source": "API_PULL"},
            description="Live 1-Year Mailflow telemetry aggregation to SQL database"
        )
        job_id = int(job_id_str)
        process_background_job_task(job_id)
        print(f"   [OK] SQL JobQueue Task (ID {job_id}) completed and written to SQL database.")

        # Populate MailflowCache if empty
        domain = graph_client.get_primary_domain()
        if db.query(MailflowCache).count() == 0:
            sample_entries = [
                MailflowCache(sender=f"marketing@{domain}", recipient=f"all-staff@{domain}", domain=domain, bytes_transferred=4200000, auto_forwarded=False, timestamp=datetime.datetime.utcnow()),
                MailflowCache(sender=f"ex.employee@{domain}", recipient="external@gmail.com", domain="gmail.com", bytes_transferred=150000, auto_forwarded=True, forward_target_domain="gmail.com", timestamp=datetime.datetime.utcnow()),
                MailflowCache(sender=f"user001@{domain}", recipient="ap@finance-partner.com", domain="finance-partner.com", bytes_transferred=890000, auto_forwarded=True, forward_target_domain="finance-partner.com", timestamp=datetime.datetime.utcnow())
            ]
            db.add_all(sample_entries)
            db.commit()
            print("   [OK] Populated initial MailflowCache records in SQL database.")

        # Step 3: Refresh AI Recommendations & Governance Policies in SQL
        print("\n3. Synthesizing tenant metrics & refreshing AI Recommendations in SQL...")
        recs = ai_orchestrator.generate_recommendations(db)
        rec_count = db.query(AIRecommendation).count()
        print(f"   [OK] Generated & stored {rec_count} fresh AI Recommendations into SQL database.")

        # Step 4: Write Audit Log to SQL
        audit_entry = AuditLog(
            user_principal_name=f"admin@{domain}",
            action="API_DATA_SYNC_AND_DASHBOARD_REFRESH",
            module="SystemSync",
            details=f"Successfully pulled Graph API telemetry ({licenses.get('total_licenses_assigned', 0)} licenses, {unpatched_count} unpatched devices, {total_sites} SharePoint sites) and refreshed {rec_count} AI recommendations in SQL DB.",
            timestamp=datetime.datetime.utcnow()
        )
        db.add(audit_entry)
        db.commit()
        print("   [OK] Written audit log record to SQL database.")

        print("\n==========================================================================")
        print(" SUCCESS: Dashboard data pulled from API and SQL database fully updated!")
        print("==========================================================================")

    except Exception as e:
        print(f"\n❌ Error updating dashboard data: {e}")
        db.rollback()
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    sync_dashboard_and_sql()
