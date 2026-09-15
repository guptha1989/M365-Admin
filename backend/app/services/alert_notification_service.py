"""
Alert & Notification Service — Pure Python & Graph API / Teams Webhook

Handles:
1. Instant Email alerts (Graph API sendMail) on policy findings
2. Instant Teams alerts (Webhooks / Graph chat messages) on policy findings
3. Daily summary report generation and delivery for triggered findings & pending action items
"""

import logging
import datetime
import requests
from typing import List, Dict, Any, Optional
from app.services.graph_client import graph_client

logger = logging.getLogger("m365_admin.alert_notification")

class AlertNotificationService:
    def send_finding_alert(
        self,
        policy_name: str,
        category: str,
        target_resource: str,
        description: str,
        severity: str = "MEDIUM",
        email_recipients: Optional[List[str]] = None,
        teams_webhook_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """Sends instant finding alert via Email and/or Teams Chat."""
        results = {"email_sent": False, "teams_sent": False, "details": []}

        # 1. Send Email Alert via Graph API sendMail if recipients provided
        if email_recipients:
            recipients = [e.strip() for e in email_recipients if e and "@" in e]
            if recipients:
                subject = f"🚨 [{severity}] Policy Finding Alert: {policy_name}"
                html_body = f"""
                <div style="font-family: 'Segoe UI', Arial, sans-serif; max-width: 600px; padding: 20px; border: 1px solid #e2e8f0; border-radius: 8px;">
                    <h2 style="color: #dc2626; margin-top: 0;">🚨 M365 Governance Policy Finding Alert</h2>
                    <table style="width: 100%; border-collapse: collapse; margin: 15px 0;">
                        <tr><td style="padding: 8px; font-weight: bold; background: #f8fafc; width: 30%;">Policy Name:</td><td style="padding: 8px;">{policy_name}</td></tr>
                        <tr><td style="padding: 8px; font-weight: bold; background: #f8fafc;">Category:</td><td style="padding: 8px;">{category}</td></tr>
                        <tr><td style="padding: 8px; font-weight: bold; background: #f8fafc;">Severity:</td><td style="padding: 8px;"><span style="background: {'#fee2e2' if severity == 'HIGH' else '#fef3c7'}; color: {'#991b1b' if severity == 'HIGH' else '#92400e'}; padding: 4px 8px; border-radius: 4px; font-weight: bold;">{severity}</span></td></tr>
                        <tr><td style="padding: 8px; font-weight: bold; background: #f8fafc;">Target:</td><td style="padding: 8px;"><code>{target_resource}</code></td></tr>
                    </table>
                    <div style="background: #f1f5f9; padding: 12px; border-left: 4px solid #3b82f6; margin-bottom: 15px;">
                        <strong>Finding Details:</strong><br/>{description}
                    </div>
                    <p style="color: #64748b; font-size: 0.85rem;">Generated automatically by M365 Administration & AI Governance Platform on {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}.</p>
                </div>
                """
                email_res = graph_client.send_mail(
                    to_recipients=recipients,
                    subject=subject,
                    body_html=html_body
                )
                results["email_sent"] = email_res.get("status") == "Success" or email_res.get("simulated", False)
                results["details"].append({"type": "email", "response": email_res})

        # 2. Send Teams Webhook Alert if webhook URL provided
        if teams_webhook_url and teams_webhook_url.startswith("http"):
            teams_card = {
                "@type": "MessageCard",
                "@context": "http://schema.org/extensions",
                "themeColor": "DC2626" if severity == "HIGH" else "F59E0B",
                "summary": f"Policy Finding: {policy_name}",
                "sections": [{
                    "activityTitle": f"🚨 Policy Finding Alert: {policy_name}",
                    "activitySubtitle": f"Category: {category} | Severity: {severity}",
                    "facts": [
                        {"name": "Target Resource", "value": target_resource},
                        {"name": "Severity", "value": severity},
                        {"name": "Time", "value": datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}
                    ],
                    "text": description
                }]
            }
            try:
                resp = requests.post(teams_webhook_url, json=teams_card, timeout=5)
                results["teams_sent"] = resp.status_code in [200, 202]
                results["details"].append({"type": "teams", "status_code": resp.status_code})
            except Exception as e:
                logger.warning(f"Failed to post Teams webhook alert: {e}")
                results["details"].append({"type": "teams", "error": str(e)})

        return results

    def generate_daily_summary(
        self,
        triggered_findings: List[Dict[str, Any]],
        pending_action_items: List[Dict[str, Any]],
        email_recipients: Optional[List[str]] = None,
        teams_webhook_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generates and dispatches daily summary report on triggered findings & pending actions."""
        summary_date = datetime.datetime.utcnow().strftime('%Y-%m-%d')
        total_triggered = len(triggered_findings)
        total_pending = len(pending_action_items)

        # Build HTML for Email
        html_rows = ""
        for f in triggered_findings[:10]:
            html_rows += f"""
            <tr>
                <td style="padding: 8px; border-bottom: 1px solid #e2e8f0;">{f.get('policy_name', 'N/A')}</td>
                <td style="padding: 8px; border-bottom: 1px solid #e2e8f0;"><code>{f.get('target_user_or_resource', 'N/A')}</code></td>
                <td style="padding: 8px; border-bottom: 1px solid #e2e8f0;">{f.get('severity', 'MEDIUM')}</td>
                <td style="padding: 8px; border-bottom: 1px solid #e2e8f0;">{f.get('finding_description', '')[:100]}</td>
            </tr>
            """
        if not html_rows:
            html_rows = "<tr><td colspan='4' style='padding: 12px; text-align: center; color: #64748b;'>No new findings triggered today.</td></tr>"

        pending_rows = ""
        for p in pending_action_items[:10]:
            pending_rows += f"""
            <tr>
                <td style="padding: 8px; border-bottom: 1px solid #e2e8f0;">{p.get('title', 'N/A')}</td>
                <td style="padding: 8px; border-bottom: 1px solid #e2e8f0;">{p.get('category', 'N/A')}</td>
                <td style="padding: 8px; border-bottom: 1px solid #e2e8f0;">{p.get('status', 'PENDING_APPROVAL')}</td>
            </tr>
            """
        if not pending_rows:
            pending_rows = "<tr><td colspan='3' style='padding: 12px; text-align: center; color: #64748b;'>No pending action items awaiting approval.</td></tr>"

        html_body = f"""
        <div style="font-family: 'Segoe UI', Arial, sans-serif; max-width: 700px; padding: 20px; border: 1px solid #cbd5e1; border-radius: 8px;">
            <div style="background: linear-gradient(135deg, #1e293b, #0f172a); color: white; padding: 15px; border-radius: 6px; margin-bottom: 20px;">
                <h2 style="margin: 0; font-size: 1.4rem;">📊 Daily Governance Summary Report ({summary_date})</h2>
                <p style="margin: 5px 0 0 0; opacity: 0.8; font-size: 0.9rem;">Microsoft 365 Policy Findings & Action Items Status</p>
            </div>
            
            <div style="display: flex; gap: 15px; margin-bottom: 20px;">
                <div style="flex: 1; background: #fee2e2; padding: 15px; border-radius: 6px; text-align: center;">
                    <div style="font-size: 1.8rem; font-weight: bold; color: #991b1b;">{total_triggered}</div>
                    <div style="font-size: 0.85rem; color: #7f1d1d; font-weight: 600;">Triggered Findings (24h)</div>
                </div>
                <div style="flex: 1; background: #e0f2fe; padding: 15px; border-radius: 6px; text-align: center;">
                    <div style="font-size: 1.8rem; font-weight: bold; color: #075985;">{total_pending}</div>
                    <div style="font-size: 0.85rem; color: #0c4a6e; font-weight: 600;">Pending Action Items</div>
                </div>
            </div>

            <h3 style="color: #1e293b; border-bottom: 2px solid #3b82f6; padding-bottom: 5px;">🔥 Recent Triggered Findings</h3>
            <table style="width: 100%; border-collapse: collapse; font-size: 0.88rem; margin-bottom: 20px;">
                <thead>
                    <tr style="background: #f1f5f9; text-align: left;">
                        <th style="padding: 8px;">Policy</th>
                        <th style="padding: 8px;">Target</th>
                        <th style="padding: 8px;">Severity</th>
                        <th style="padding: 8px;">Description</th>
                    </tr>
                </thead>
                <tbody>{html_rows}</tbody>
            </table>

            <h3 style="color: #1e293b; border-bottom: 2px solid #f59e0b; padding-bottom: 5px;">⏳ Pending Action Items</h3>
            <table style="width: 100%; border-collapse: collapse; font-size: 0.88rem; margin-bottom: 20px;">
                <thead>
                    <tr style="background: #f1f5f9; text-align: left;">
                        <th style="padding: 8px;">Action Title</th>
                        <th style="padding: 8px;">Category</th>
                        <th style="padding: 8px;">Status</th>
                    </tr>
                </thead>
                <tbody>{pending_rows}</tbody>
            </table>

            <p style="color: #64748b; font-size: 0.8rem; text-align: center;">M365 Admin Bot — Automated Daily Governance Summary</p>
        </div>
        """

        results = {"email_sent": False, "teams_sent": False, "summary_date": summary_date}

        if email_recipients:
            recipients = [e.strip() for e in email_recipients if e and "@" in e]
            if recipients:
                email_res = graph_client.send_mail(
                    to_recipients=recipients,
                    subject=f"📊 Daily M365 Governance Summary — {summary_date} ({total_triggered} findings, {total_pending} pending)",
                    body_html=html_body
                )
                results["email_sent"] = email_res.get("status") == "Success" or email_res.get("simulated", False)

        if teams_webhook_url and teams_webhook_url.startswith("http"):
            teams_card = {
                "@type": "MessageCard",
                "@context": "http://schema.org/extensions",
                "themeColor": "3B82F6",
                "summary": f"Daily Summary Report — {summary_date}",
                "sections": [{
                    "activityTitle": f"📊 Daily Governance Summary Report ({summary_date})",
                    "facts": [
                        {"name": "Triggered Findings (24h)", "value": str(total_triggered)},
                        {"name": "Pending Action Items", "value": str(total_pending)},
                        {"name": "Report Date", "value": summary_date}
                    ],
                    "text": f"Daily summary contains **{total_triggered}** policy findings and **{total_pending}** pending action items requiring admin review."
                }]
            }
            try:
                resp = requests.post(teams_webhook_url, json=teams_card, timeout=5)
                results["teams_sent"] = resp.status_code in [200, 202]
            except Exception as e:
                logger.warning(f"Failed to send Teams daily summary webhook: {e}")

        return results

alert_notification_service = AlertNotificationService()
