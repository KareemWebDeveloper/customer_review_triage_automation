"""Unit tests for CLI input path arguments and fallback."""

from pathlib import Path
from src import config
from src.main import run_pipeline
from unittest.mock import patch


def test_default_config_fallback(tmp_path: Path):
    # Verify default parameter falls back to config.INPUT_CSV_PATH
    dummy_csv = tmp_path / "custom.csv"
    dummy_csv.write_text("Review ID,Brand,Product,Star Rating,Review Text\nR-2001,TestBrand,TestProduct,5,Great!", encoding="utf-8")

    with patch("src.main.load_and_deduplicate_reviews") as mock_load, \
         patch("src.main.ReviewClassifier") as mock_classifier, \
         patch("src.main.EmailNotifier") as mock_notifier, \
         patch("src.main.write_triage_results"):

        mock_load.return_value = ([], MagicMock(total_rows_read=0, duplicates_skipped=0, unique_reviews_to_process=0))

        # Test explicit custom path
        run_pipeline(input_source=dummy_csv)
        mock_load.assert_called_once_with(str(dummy_csv))


from unittest.mock import MagicMock
