"""Unit tests for data loader and deduplication."""

from pathlib import Path
from unittest.mock import patch
from src.data.loader import load_and_deduplicate_reviews, fetch_csv_from_url


def test_sample_reviews_deduplication():
    csv_path = Path("input/reviews_sample.csv")
    reviews, stats = load_and_deduplicate_reviews(csv_path)

    # Total rows in CSV = 12
    assert stats.total_rows_read == 12
    # R-1003 is repeated once => 1 duplicate skipped
    assert stats.duplicates_skipped == 1
    # 11 unique reviews total
    assert stats.unique_reviews_to_process == 11
    assert len(reviews) == 11

    # R-1006 has empty review text
    empty_reviews = [r for r in reviews if r.is_empty]
    assert len(empty_reviews) == 1
    assert empty_reviews[0].review_id == "R-1006"


def test_google_sheet_url_ingestion():
    mock_csv_text = "Review ID,Brand,Product,Star Rating,Review Text\nR-3001,GoogleBrand,Widget,5,Great product!"
    sheet_url = "https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/edit#gid=0"

    with patch("src.data.loader.fetch_csv_from_url") as mock_fetch:
        mock_fetch.return_value = mock_csv_text
        reviews, stats = load_and_deduplicate_reviews(sheet_url)

        assert stats.total_rows_read == 1
        assert len(reviews) == 1
        assert reviews[0].review_id == "R-3001"
        assert reviews[0].brand == "GoogleBrand"


def test_whitespace_review_text_flagged_as_empty():
    """Edge Case: Review text containing only whitespace or newlines is flagged as empty."""
    mock_csv_text = "Review ID,Brand,Product,Star Rating,Review Text\nR-4001,BrandX,ItemY,1,   \n\t  "
    with patch("src.data.loader.fetch_csv_from_url") as mock_fetch:
        mock_fetch.return_value = mock_csv_text
        reviews, stats = load_and_deduplicate_reviews("https://example.com/data.csv")

        assert len(reviews) == 1
        assert reviews[0].is_empty is True
        assert stats.empty_reviews_count == 1


def test_non_numeric_star_rating_handled_gracefully():
    """Edge Case: Invalid or missing star rating in CSV defaults to 0 without throwing error."""
    mock_csv_text = "Review ID,Brand,Product,Star Rating,Review Text\nR-5001,BrandZ,ItemZ,INVALID_RATING,Nice!"
    with patch("src.data.loader.fetch_csv_from_url") as mock_fetch:
        mock_fetch.return_value = mock_csv_text
        reviews, stats = load_and_deduplicate_reviews("https://example.com/data.csv")

        assert len(reviews) == 1
        assert reviews[0].star_rating == 0
        assert reviews[0].is_empty is False
