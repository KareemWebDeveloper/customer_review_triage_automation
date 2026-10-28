"""Email notification service using Resend API."""

import base64
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import resend

from src import config

logger = logging.getLogger(__name__)


class EmailNotifier:
    """Service for sending Critical review alert emails and run summaries."""

    def __init__(
        self,
        api_key: str = config.RESEND_API_KEY,
        recipient: str = config.ALERT_EMAIL_RECIPIENT,
        sender: str = config.SENDER_EMAIL,
    ):
        self.api_key = api_key
        self.recipient = recipient
        self.sender = sender
        if self.api_key:
            resend.api_key = self.api_key

    def send_critical_alert(
        self,
        review_id: str,
        brand: str,
        product: str,
        star_rating: int,
        english_summary: str,
        suggested_action: str,
    ) -> bool:
        """Send an urgent email alert for a Critical safety review.

        Subject format: [CRITICAL REVIEW] <Review ID>

        Returns:
            True if sent successfully, False otherwise.
        """
        if not self.api_key or not self.recipient:
            logger.warning("Resend API key or recipient email not configured. Skipping Critical alert email.")
            return False

        subject = f"[CRITICAL REVIEW] {review_id}"
        html_content = f"""
        <h2>⚠️ CRITICAL SAFETY REVIEW ALERT</h2>
        <p><strong>Review ID:</strong> {review_id}</p>
        <p><strong>Brand:</strong> {brand}</p>
        <p><strong>Product:</strong> {product}</p>
        <p><strong>Star Rating:</strong> ⭐ {star_rating}/5</p>
        <hr>
        <p><strong>English Summary:</strong> {english_summary}</p>
        <p><strong>Suggested Next Step:</strong> {suggested_action}</p>
        <hr>
        <p><em>This is an automated critical safety alert from Pax Distribution Review Triage System.</em></p>
        """

        try:
            params: resend.Emails.SendParams = {
                "from": self.sender,
                "to": [self.recipient],
                "subject": subject,
                "html": html_content,
            }
            response = resend.Emails.send(params)
            logger.info(f"Critical alert email sent for {review_id}. Response ID: {response.get('id')}")
            return True
        except Exception as e:
            logger.error(f"Failed to send Critical alert email for {review_id}: {e}")
            return False

    def send_run_summary(
        self,
        summary_stats: Dict[str, Any],
        attachment_path: Optional[Path] = None,
    ) -> bool:
        """Send a single run-summary email after processing all reviews, optionally attaching the results CSV file.

        Returns:
            True if sent successfully, False otherwise.
        """
        if not self.api_key or not self.recipient:
            logger.warning("Resend API key or recipient email not configured. Skipping run summary email.")
            return False

        subject = "Pax Distribution — Review Triage Automation Run Summary"
        html_content = f"""
        <h2>📊 Pax Distribution Review Triage Run Summary</h2>
        <ul>
            <li><strong>Total Rows Read:</strong> {summary_stats.get('total_rows_read', 0)}</li>
            <li><strong>Duplicates Skipped:</strong> {summary_stats.get('duplicates_skipped', 0)}</li>
            <li><strong>Reviews Classified by AI:</strong> {summary_stats.get('ai_classified_count', 0)}</li>
            <li><strong>Reviews Marked 'Needs Manual Review':</strong> {summary_stats.get('manual_review_count', 0)}</li>
            <li><strong>Critical Safety Alerts Triggered:</strong> {summary_stats.get('critical_alerts_triggered', 0)}</li>
            <li><strong>Critical Alert Emails Sent:</strong> {summary_stats.get('critical_alerts_sent', 0)}</li>
        </ul>
        <hr>
        <p><em>Processing finished successfully. Detailed output is attached as <strong>Triage Results.csv</strong>.</em></p>
        """

        attachments = []
        if attachment_path and attachment_path.exists():
            try:
                with open(attachment_path, "rb") as f:
                    encoded_content = base64.b64encode(f.read()).decode("utf-8")
                attachments.append({
                    "filename": attachment_path.name,
                    "content": encoded_content,
                })
                logger.info(f"Attached CSV result file '{attachment_path.name}' (Base64 encoded) to run summary email.")
            except Exception as ae:
                logger.warning(f"Could not attach CSV file '{attachment_path}': {ae}")

        try:
            params: resend.Emails.SendParams = {
                "from": self.sender,
                "to": [self.recipient],
                "subject": subject,
                "html": html_content,
            }
            if attachments:
                params["attachments"] = attachments

            response = resend.Emails.send(params)
            logger.info(f"Run summary email sent. Response ID: {response.get('id')}")
            return True
        except Exception as e:
            logger.error(f"Failed to send run summary email: {e}")
            return False
