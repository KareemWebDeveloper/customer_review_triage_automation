"""Data loader module for reading customer reviews from CSV files or Google Sheets URLs."""

import csv
from dataclasses import dataclass
import io
from pathlib import Path
import re
from typing import List, Tuple, Union
import urllib.request


@dataclass
class RawReview:
    review_id: str
    review_date: str
    brand: str
    product: str
    star_rating: int
    review_text: str
    is_empty: bool = False


@dataclass
class IngestionStats:
    total_rows_read: int = 0
    duplicates_skipped: int = 0
    empty_reviews_count: int = 0
    unique_reviews_to_process: int = 0


def fetch_csv_from_url(url: str) -> str:
    """Fetch CSV content text from a Google Sheets URL or HTTP CSV link.

    Args:
        url: Full URL string (e.g. Google Sheets link or direct CSV URL).

    Returns:
        CSV text content string.
    """
    if "docs.google.com/spreadsheets" in url:
        match = re.search(r"/d/([a-zA-Z0-9-_]+)", url)
        if not match:
            raise ValueError("Invalid Google Sheets URL. Could not extract spreadsheet ID.")
        sheet_id = match.group(1)

        gid_match = re.search(r"[#&?]gid=([0-9]+)", url)
        gid_param = f"&gid={gid_match.group(1)}" if gid_match else ""
        download_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv{gid_param}"
    else:
        download_url = url

    req = urllib.request.Request(
        download_url,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
    )
    with urllib.request.urlopen(req) as response:
        return response.read().decode("utf-8-sig")


def load_and_deduplicate_reviews(
    source: Union[str, Path]
) -> Tuple[List[RawReview], IngestionStats]:
    """Read reviews from a local CSV file or Google Sheets URL, deduplicate by Review ID, and track stats.

    Args:
        source: Local Path or URL string (Google Sheets / HTTP CSV).

    Returns:
        Tuple of (list of unique RawReview objects, IngestionStats summary).
    """
    stats = IngestionStats()
    seen_ids = set()
    unique_reviews: List[RawReview] = []

    source_str = str(source).strip()

    if source_str.startswith("http://") or source_str.startswith("https://"):
        csv_text = fetch_csv_from_url(source_str)
        f = io.StringIO(csv_text)
        reader = csv.DictReader(f)
        _process_rows(reader, seen_ids, unique_reviews, stats)
    else:
        csv_path = Path(source)
        if not csv_path.exists():
            raise FileNotFoundError(f"Input CSV file not found at: {csv_path}")

        with open(csv_path, mode="r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            _process_rows(reader, seen_ids, unique_reviews, stats)

    stats.unique_reviews_to_process = len(unique_reviews)
    return unique_reviews, stats


def _process_rows(
    reader: csv.DictReader,
    seen_ids: set,
    unique_reviews: List[RawReview],
    stats: IngestionStats,
) -> None:
    """Process CSV DictReader rows for deduplication and extraction."""
    for row in reader:
        if not row:
            continue
        stats.total_rows_read += 1
        review_id = (row.get("Review ID") or "").strip()
        review_text = (row.get("Review Text") or "").strip()

        if not review_id:
            continue

        if review_id in seen_ids:
            stats.duplicates_skipped += 1
            continue

        seen_ids.add(review_id)

        try:
            star_rating = int(row.get("Star Rating", 0) or 0)
        except (ValueError, TypeError):
            star_rating = 0

        is_empty = not bool(review_text)
        if is_empty:
            stats.empty_reviews_count += 1

        raw_review = RawReview(
            review_id=review_id,
            review_date=(row.get("Review Date") or "").strip(),
            brand=(row.get("Brand") or "").strip(),
            product=(row.get("Product") or "").strip(),
            star_rating=star_rating,
            review_text=review_text,
            is_empty=is_empty,
        )
        unique_reviews.append(raw_review)
