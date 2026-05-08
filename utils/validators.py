# ============================================================
#  Validators
#  File and DataFrame validation utilities.
# ============================================================

from __future__ import annotations

from pathlib import Path
from typing import List

import pandas as pd

from utils.config import get_settings
from utils.logger import get_logger

logger = get_logger(__name__)

# ── Allowed file extensions ──────────────────────────────────
ALLOWED_EXTENSIONS: set[str] = {".csv", ".xlsx", ".xls"}


def validate_file_extension(filename: str) -> bool:
    """Check that the uploaded file has an allowed extension."""
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        logger.warning("Rejected file with unsupported extension: %s", ext)
        return False
    return True


def validate_file_size(size_bytes: int) -> bool:
    """Check that the file does not exceed the configured maximum size."""
    settings = get_settings()
    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    if size_bytes > max_bytes:
        logger.warning(
            "File size %d bytes exceeds limit of %d MB",
            size_bytes,
            settings.max_upload_size_mb,
        )
        return False
    return True


def validate_dataframe(df: pd.DataFrame) -> List[str]:
    """
    Run basic quality checks on a DataFrame.

    Returns:
        A list of warning messages (empty if everything looks good).
    """
    warnings: List[str] = []

    if df.empty:
        warnings.append("The uploaded file contains no data rows.")
        return warnings

    if len(df.columns) == 0:
        warnings.append("The uploaded file contains no columns.")
        return warnings

    # Check for completely empty columns
    empty_cols = [col for col in df.columns if df[col].isna().all()]
    if empty_cols:
        warnings.append(
            f"Columns with all missing values: {', '.join(str(c) for c in empty_cols)}"
        )

    # High missing-value ratio
    for col in df.columns:
        pct = df[col].isna().mean() * 100
        if pct > 50:
            warnings.append(f"Column '{col}' has {pct:.1f}% missing values.")

    # Duplicate rows
    dup_count = df.duplicated().sum()
    if dup_count > 0:
        warnings.append(f"Found {dup_count} duplicate rows.")

    return warnings
