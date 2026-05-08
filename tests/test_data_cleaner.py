# ============================================================
#  Tests — Data Cleaner
# ============================================================

from __future__ import annotations

import pandas as pd
import pytest

from backend.data_cleaner import clean_dataframe


class TestCleanDataframe:
    """Tests for the data cleaning pipeline."""

    def test_removes_duplicate_rows(self) -> None:
        df = pd.DataFrame({"a": [1, 1, 2, 3], "b": ["x", "x", "y", "z"]})
        cleaned, report = clean_dataframe(df)
        assert report.duplicates_removed == 1
        assert len(cleaned) == 3

    def test_removes_empty_columns(self) -> None:
        df = pd.DataFrame({
            "good": [1, 2, 3],
            "empty": [None, None, None],
        })
        cleaned, report = clean_dataframe(df)
        assert "empty" in report.empty_cols_removed
        assert "empty" not in cleaned.columns

    def test_strips_currency_symbols(self) -> None:
        df = pd.DataFrame({"price": ["$100", "$200.50", "$300"]})
        cleaned, report = clean_dataframe(df)
        assert pd.api.types.is_numeric_dtype(cleaned["price"])
        assert cleaned["price"].iloc[0] == 100.0

    def test_handles_missing_values_numeric(self) -> None:
        df = pd.DataFrame({"val": [10.0, None, 30.0]})
        cleaned, report = clean_dataframe(df)
        assert cleaned["val"].isna().sum() == 0
        # Median of [10, 30] = 20
        assert cleaned["val"].iloc[1] == 20.0

    def test_handles_missing_values_categorical(self) -> None:
        df = pd.DataFrame({"cat": ["a", None, "b"]})
        cleaned, report = clean_dataframe(df)
        assert cleaned["cat"].iloc[1] == "Unknown"

    def test_preserves_valid_data(self) -> None:
        df = pd.DataFrame({
            "id": [1, 2, 3],
            "name": ["Alice", "Bob", "Charlie"],
            "score": [90.5, 85.0, 92.3],
        })
        cleaned, report = clean_dataframe(df)
        assert len(cleaned) == 3
        assert report.duplicates_removed == 0
        assert len(report.empty_cols_removed) == 0

    def test_cleaning_report_row_counts(self) -> None:
        df = pd.DataFrame({"a": [1, 1, 2], "b": [None, None, None]})
        cleaned, report = clean_dataframe(df)
        assert report.rows_before == 3
        assert report.rows_after == 2  # 1 duplicate removed
        assert report.cols_before == 2
        assert report.cols_after == 1  # 1 empty column removed

    def test_empty_dataframe(self) -> None:
        df = pd.DataFrame()
        cleaned, report = clean_dataframe(df)
        assert len(cleaned) == 0

    def test_whitespace_column_names(self) -> None:
        df = pd.DataFrame({" name ": ["a", "b"], " value ": [1, 2]})
        cleaned, report = clean_dataframe(df)
        assert "name" in cleaned.columns
        assert "value" in cleaned.columns
