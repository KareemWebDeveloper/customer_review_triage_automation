"""Main entrypoint script for Review Triage Automation."""

import argparse
from datetime import datetime
import logging
from pathlib import Path
import sys
from typing import List, Union

from src import config
from src.agent.classifier import ReviewClassifier
from src.agent.schemas import TriageRow
from src.data.loader import load_and_deduplicate_reviews
from src.data.writer import write_triage_results
from src.notifications.emailer import EmailNotifier

# Reconfigure stdout/stderr to utf-8 for Windows console support
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def run_pipeline(input_source: Union[str, Path] = config.INPUT_CSV_PATH):
    """Execute the end-to-end review triage automation pipeline.

    Args:
        input_source: Path to local CSV file OR public Google Sheets URL / direct CSV link.
    """
    source_str = str(input_source).strip()
    print("=" * 60)
    print("Starting Pax Distribution — AI Review Triage Automation")
    print("=" * 60)

    # Step 1: Ingest & Deduplicate Data
    logger.info(f"Loading reviews from: {source_str}")
    raw_reviews, stats = load_and_deduplicate_reviews(source_str)
    logger.info(
        f"Ingestion complete: Total rows read={stats.total_rows_read}, "
        f"Duplicates skipped={stats.duplicates_skipped}, Unique to process={stats.unique_reviews_to_process}"
    )

    classifier = ReviewClassifier()
    notifier = EmailNotifier()

    triage_rows: List[TriageRow] = []
    ai_classified_count = 0
    manual_review_count = 0
    critical_alerts_triggered = 0
    critical_alerts_sent = 0

    # Step 2: Process each unique review
    for idx, review in enumerate(raw_reviews, start=1):
        timestamp_str = datetime.now().isoformat()
        logger.info(f"[{idx}/{len(raw_reviews)}] Processing Review ID: {review.review_id} ({review.brand} - {review.product})")

        # Step 3: Handle empty reviews
        if review.is_empty:
            logger.warning(f"  └─ Review ID {review.review_id} is EMPTY. Marking as 'Needs Manual Review'.")
            manual_review_count += 1
            triage_rows.append(
                TriageRow(
                    review_id=review.review_id,
                    brand=review.brand,
                    product=review.product,
                    star_rating=review.star_rating,
                    sentiment="",
                    category="",
                    urgency="",
                    english_summary="",
                    suggested_action="",
                    status="Needs Manual Review",
                    processed_at=timestamp_str,
                )
            )
            continue

        # Step 4: AI Classification with Gemini
        classification = None
        try:
            classification = classifier.classify(
                brand=review.brand,
                product=review.product,
                star_rating=review.star_rating,
                review_text=review.review_text,
            )
            ai_classified_count += 1
            logger.info(
                f"  └─ Classified: Sentiment={classification.sentiment.value}, "
                f"Category={classification.category.value}, Urgency={classification.urgency.value}"
            )

            triage_rows.append(
                TriageRow(
                    review_id=review.review_id,
                    brand=review.brand,
                    product=review.product,
                    star_rating=review.star_rating,
                    sentiment=classification.sentiment.value,
                    category=classification.category.value,
                    urgency=classification.urgency.value,
                    english_summary=classification.english_summary,
                    suggested_action=classification.suggested_action,
                    status="Classified",
                    processed_at=timestamp_str,
                )
            )

        except Exception as ce:
            logger.error(f"  ❌ Classification error for review {review.review_id}: {ce}")
            manual_review_count += 1
            triage_rows.append(
                TriageRow(
                    review_id=review.review_id,
                    brand=review.brand,
                    product=review.product,
                    star_rating=review.star_rating,
                    status="Needs Manual Review (Classification Error)",
                    processed_at=timestamp_str,
                )
            )
            continue

        # Step 5: Critical Safety Alert Notification (Decoupled from Classification)
        if classification and classification.urgency.value == "Critical":
            critical_alerts_triggered += 1
            logger.warning(f"  🚨 CRITICAL SAFETY ISSUE DETECTED for {review.review_id}! Dispatching email alert...")
            try:
                sent = notifier.send_critical_alert(
                    review_id=review.review_id,
                    brand=review.brand,
                    product=review.product,
                    star_rating=review.star_rating,
                    english_summary=classification.english_summary,
                    suggested_action=classification.suggested_action,
                )
                if sent:
                    critical_alerts_sent += 1
                else:
                    logger.error(f"  ⚠️ Critical alert email for {review.review_id} could not be delivered.")
            except Exception as ne:
                logger.error(f"  ❌ Notification error sending critical alert for review {review.review_id}: {ne}")

    # Step 6: Write output CSV
    logger.info(f"Writing triage results to: {config.OUTPUT_CSV_PATH}")
    write_triage_results(triage_rows, config.OUTPUT_CSV_PATH)
    logger.info("CSV export completed successfully.")

    # Step 7: Send Run Summary Email (Decoupled Error Handling with CSV Attachment)
    summary_stats = {
        "total_rows_read": stats.total_rows_read,
        "duplicates_skipped": stats.duplicates_skipped,
        "ai_classified_count": ai_classified_count,
        "manual_review_count": manual_review_count,
        "critical_alerts_triggered": critical_alerts_triggered,
        "critical_alerts_sent": critical_alerts_sent,
    }
    logger.info("Sending final run summary email with CSV attachment...")
    try:
        notifier.send_run_summary(summary_stats, attachment_path=config.OUTPUT_CSV_PATH)
    except Exception as se:
        logger.error(f"❌ Notification error sending run summary email: {se}")

    # Terminal Summary Output
    print("\n" + "=" * 60)
    print("📋 RUN SUMMARY REPORT")
    print("=" * 60)
    print(f"Total Rows Read:                      {stats.total_rows_read}")
    print(f"Duplicates Skipped:                   {stats.duplicates_skipped}")
    print(f"Reviews Classified by AI:             {ai_classified_count}")
    print(f"Reviews Marked 'Needs Manual Review': {manual_review_count}")
    print(f"Critical Alerts Triggered:            {critical_alerts_triggered}")
    print(f"Critical Email Alerts Delivered:      {critical_alerts_sent}")
    print(f"Output File:                          {config.OUTPUT_CSV_PATH}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Pax Distribution — AI Review Triage Automation"
    )
    parser.add_argument(
        "input_path",
        nargs="?",
        default=None,
        help="Optional path to local CSV file OR public Google Sheets URL. Defaults to input/reviews_sample.csv",
    )
    parser.add_argument(
        "--input",
        "-i",
        dest="input_flag",
        default=None,
        help="Alternative flag to specify input CSV file path or Google Sheets URL",
    )
    args = parser.parse_args()

    selected_source = args.input_flag or args.input_path
    if selected_source:
        run_pipeline(input_source=selected_source)
    else:
        run_pipeline(input_source=config.INPUT_CSV_PATH)
