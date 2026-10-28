"""Unit tests for EmailNotifier and attachments."""

from pathlib import Path
from unittest.mock import patch, MagicMock
from src.notifications.emailer import EmailNotifier


def test_send_run_summary_with_attachment(tmp_path: Path):
    # Create a temporary CSV file
    csv_file = tmp_path / "Triage Results.csv"
    csv_file.write_text("Review ID,Brand\nR-1001,Northvane", encoding="utf-8")

    notifier = EmailNotifier(
        api_key="re_test_key",
        recipient="test@example.com",
        sender="onboarding@resend.dev",
    )

    stats = {
        "total_rows_read": 12,
        "duplicates_skipped": 1,
        "ai_classified_count": 10,
        "manual_review_count": 1,
        "critical_alerts_triggered": 2,
        "critical_alerts_sent": 2,
    }

    with patch("resend.Emails.send") as mock_send:
        mock_send.return_value = {"id": "msg_12345"}
        success = notifier.send_run_summary(stats, attachment_path=csv_file)

        assert success is True
        assert mock_send.called
        call_params = mock_send.call_args[0][0]
        assert "attachments" in call_params
        assert len(call_params["attachments"]) == 1
        assert call_params["attachments"][0]["filename"] == "Triage Results.csv"
        assert isinstance(call_params["attachments"][0]["content"], str)
