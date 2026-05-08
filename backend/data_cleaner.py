# ============================================================
#  Data Cleaner
#  Automatic data quality improvements with a detailed
#  cleaning report.
# ============================================================

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

import pandas as pd

from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class CleaningReport:
    """Summary of all cleaning operations performed."""

    rows_before: int = 0
    rows_after: int = 0
    cols_before: int = 0
    cols_after: int = 0
    duplicates_removed: int = 0
    empty_cols_removed: List[str] = field(default_factory=list)
    dtypes_fixed: dict[str, str] = field(default_factory=dict)
    missing_values_handled: dict[str, int] = field(default_factory=dict)
    currency_cols_cleaned: List[str] = field(default_factory=list)
    date_cols_parsed: List[str] = field(default_factory=list)

    @property
    def summary(self) -> str:
        """Human-readable cleaning summary."""
        lines = [
            f"📋 **Cleaning Report**",
            f"- Rows: {self.rows_before} → {self.rows_after}",
            f"- Columns: {self.cols_before} → {self.cols_after}",
        ]
        if self.duplicates_removed:
            lines.append(f"- Duplicates removed: {self.duplicates_removed}")
        if self.empty_cols_removed:
            lines.append(f"- Empty columns dropped: {', '.join(self.empty_cols_removed)}")
        if self.currency_cols_cleaned:
            lines.append(f"- Currency symbols stripped: {', '.join(self.currency_cols_cleaned)}")
        if self.date_cols_parsed:
            lines.append(f"- Date columns parsed: {', '.join(self.date_cols_parsed)}")
        if self.missing_values_handled:
            total = sum(self.missing_values_handled.values())
            lines.append(f"- Missing values handled: {total} across {len(self.missing_values_handled)} columns")
        return "\n".join(lines)


def clean_dataframe(df: pd.DataFrame) -> tuple[pd.DataFrame, CleaningReport]:
    """
    Run the full cleaning pipeline on a DataFrame.

    Operations (in order):
      1. Strip whitespace from column names
      2. Remove completely empty columns
      3. Remove duplicate rows
      4. Strip currency symbols from numeric-looking columns
      5. Parse date columns
      6. Fix incorrect dtypes
      7. Handle missing values

    Args:
        df: The raw DataFrame.

    Returns:
        Tuple of (cleaned DataFrame, CleaningReport).
    """
    report = CleaningReport(
        rows_before=len(df),
        cols_before=len(df.columns),
    )

    df = df.copy()

    # Handle empty DataFrame early
    if df.empty or len(df.columns) == 0:
        report.rows_after = len(df)
        report.cols_after = len(df.columns)
        return df, report

    # 1. Clean column names
    df.columns = df.columns.str.strip()

    # 2. Remove empty columns (all NaN)
    empty_cols = [col for col in df.columns if df[col].isna().all()]
    if empty_cols:
        df.drop(columns=empty_cols, inplace=True)
        report.empty_cols_removed = [str(c) for c in empty_cols]
        logger.info("Dropped %d empty columns: %s", len(empty_cols), empty_cols)

    # 3. Remove duplicate rows
    dup_count = df.duplicated().sum()
    if dup_count > 0:
        df.drop_duplicates(inplace=True)
        df.reset_index(drop=True, inplace=True)
        report.duplicates_removed = int(dup_count)
        logger.info("Removed %d duplicate rows.", dup_count)

    # 4. Strip currency symbols
    df, currency_cols = _strip_currency(df)
    report.currency_cols_cleaned = currency_cols

    # 5. Parse date columns
    df, date_cols = _parse_dates(df)
    report.date_cols_parsed = date_cols

    # 6. Fix dtypes (convert object columns that look numeric)
    df, fixed = _fix_dtypes(df)
    report.dtypes_fixed = fixed

    # 7. Handle missing values
    df, missing_handled = _handle_missing(df)
    report.missing_values_handled = missing_handled

    report.rows_after = len(df)
    report.cols_after = len(df.columns)

    logger.info(
        "Cleaning complete: %d→%d rows, %d→%d cols.",
        report.rows_before, report.rows_after,
        report.cols_before, report.cols_after,
    )
    return df, report


def _strip_currency(df: pd.DataFrame) -> tuple[pd.DataFrame, List[str]]:
    """Remove currency symbols ($, €, £, ₹, ¥) from string columns."""
    cleaned_cols: List[str] = []
    currency_pattern = r"[\$€£₹¥,]"

    for col in df.select_dtypes(include=["object", "str"]).columns:
        sample = df[col].dropna().head(100).astype(str)
        # Check if most values look like currency
        matches = sample.str.match(r"^\s*[\$€£₹¥]?\s*[\d,]+\.?\d*\s*$")
        if matches.mean() > 0.5:
            df[col] = (
                df[col]
                .astype(str)
                .str.replace(currency_pattern, "", regex=True)
                .str.strip()
            )
            df[col] = pd.to_numeric(df[col], errors="coerce")
            cleaned_cols.append(str(col))
            logger.debug("Stripped currency from column: %s", col)

    return df, cleaned_cols


def _parse_dates(df: pd.DataFrame) -> tuple[pd.DataFrame, List[str]]:
    """Attempt to parse object columns as datetime."""
    parsed_cols: List[str] = []

    for col in df.select_dtypes(include=["object", "str"]).columns:
        sample = df[col].dropna().head(50)
        if len(sample) == 0:
            continue

        try:
            parsed = pd.to_datetime(sample, infer_datetime_format=True, dayfirst=False)
            # If > 70% parsed successfully, convert the whole column
            if parsed.notna().mean() > 0.7:
                df[col] = pd.to_datetime(df[col], errors="coerce", infer_datetime_format=True)
                parsed_cols.append(str(col))
                logger.debug("Parsed date column: %s", col)
        except (ValueError, TypeError):
            continue

    return df, parsed_cols


def _fix_dtypes(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, str]]:
    """Convert object columns that look numeric to proper numeric types."""
    fixed: dict[str, str] = {}

    for col in df.select_dtypes(include=["object", "str"]).columns:
        try:
            converted = pd.to_numeric(df[col], errors="coerce")
            # If > 80% converted successfully, keep the conversion
            if converted.notna().mean() > 0.8 and df[col].notna().mean() > 0:
                original_dtype = str(df[col].dtype)
                df[col] = converted
                fixed[str(col)] = f"{original_dtype} → {df[col].dtype}"
                logger.debug("Fixed dtype for column %s: %s", col, fixed[str(col)])
        except (ValueError, TypeError):
            continue

    return df, fixed


def _handle_missing(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, int]]:
    """
    Handle missing values with type-appropriate strategies.

    - Numeric: fill with median
    - Categorical: fill with 'Unknown'
    - Datetime: leave as NaT
    """
    handled: dict[str, int] = {}

    for col in df.columns:
        missing_count = int(df[col].isna().sum())
        if missing_count == 0:
            continue

        if pd.api.types.is_numeric_dtype(df[col]):
            median_val = df[col].median()
            df[col] = df[col].fillna(median_val)
            handled[str(col)] = missing_count
        elif pd.api.types.is_datetime64_any_dtype(df[col]):
            # Leave datetime NaTs as-is
            pass
        else:
            df[col] = df[col].fillna("Unknown")
            handled[str(col)] = missing_count

    return df, handled
