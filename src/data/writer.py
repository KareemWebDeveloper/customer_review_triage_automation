"""Data writer module for writing triaged results to CSV."""

import csv
from pathlib import Path
from typing import List

from src.agent.schemas import TriageRow

FIELDNAMES = [
    "Review ID",
    "Brand",
    "Product",
    "Star Rating",
    "Sentiment",
    "Category",
    "Urgency",
    "English Summary",
    "Suggested Action",
    "Status",
    "Processed At",
]


def write_triage_results(rows: List[TriageRow], output_path: Path) -> None:
    """Write triage rows to CSV with exact 11 mandatory column headers.

    Args:
        rows: List of TriageRow objects.
        output_path: Target CSV file path.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for row in rows:
            writer.writerow(row.to_csv_dict())
