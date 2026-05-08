# ============================================================
#  Schema Detector
#  Automatically classifies DataFrame columns and generates
#  a schema summary for LLM context.
# ============================================================

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List

import pandas as pd

from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ColumnInfo:
    """Metadata for a single column."""

    name: str
    dtype: str
    category: str  # numerical, categorical, datetime, id, currency
    unique_count: int = 0
    null_count: int = 0
    sample_values: List[Any] = field(default_factory=list)


@dataclass
class SchemaInfo:
    """Complete schema description of a DataFrame."""

    columns: List[ColumnInfo] = field(default_factory=list)
    row_count: int = 0
    column_count: int = 0

    @property
    def numerical_columns(self) -> List[str]:
        return [c.name for c in self.columns if c.category == "numerical"]

    @property
    def categorical_columns(self) -> List[str]:
        return [c.name for c in self.columns if c.category == "categorical"]

    @property
    def datetime_columns(self) -> List[str]:
        return [c.name for c in self.columns if c.category == "datetime"]

    @property
    def id_columns(self) -> List[str]:
        return [c.name for c in self.columns if c.category == "id"]

    @property
    def currency_columns(self) -> List[str]:
        return [c.name for c in self.columns if c.category == "currency"]

    def to_llm_string(self) -> str:
        """
        Format the schema as a concise string suitable for
        injection into LLM prompts.
        """
        lines = [f"DataFrame: {self.row_count} rows × {self.column_count} columns\n"]
        lines.append("Columns:")

        for col in self.columns:
            samples = ", ".join(str(v) for v in col.sample_values[:5])
            lines.append(
                f"  - {col.name} ({col.dtype}, {col.category}) "
                f"| {col.unique_count} unique | {col.null_count} nulls "
                f"| samples: [{samples}]"
            )

        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dictionary."""
        return {
            "row_count": self.row_count,
            "column_count": self.column_count,
            "columns": [
                {
                    "name": c.name,
                    "dtype": c.dtype,
                    "category": c.category,
                    "unique_count": c.unique_count,
                    "null_count": c.null_count,
                }
                for c in self.columns
            ],
        }


def detect_schema(df: pd.DataFrame) -> SchemaInfo:
    """
    Analyze a DataFrame and produce a detailed schema.

    Classification rules:
      - **datetime**: ``datetime64`` dtype
      - **id**: unique-value ratio > 0.95 and (integer or string)
      - **currency**: column name contains money-related keywords
      - **numerical**: numeric dtype
      - **categorical**: everything else (object, bool, etc.)

    Args:
        df: The DataFrame to analyze.

    Returns:
        A :class:`SchemaInfo` instance.
    """
    schema = SchemaInfo(row_count=len(df), column_count=len(df.columns))

    currency_keywords = {"price", "cost", "revenue", "amount", "salary", "fee",
                         "total", "profit", "income", "expense", "payment",
                         "balance", "budget", "tax", "discount"}

    for col in df.columns:
        series = df[col]
        dtype_str = str(series.dtype)
        unique_count = int(series.nunique())
        null_count = int(series.isna().sum())
        sample_values = series.dropna().head(5).tolist()

        # Classify
        category = _classify_column(
            series, str(col), unique_count, len(df), currency_keywords
        )

        schema.columns.append(
            ColumnInfo(
                name=str(col),
                dtype=dtype_str,
                category=category,
                unique_count=unique_count,
                null_count=null_count,
                sample_values=sample_values,
            )
        )

    logger.info(
        "Schema detected: %d numerical, %d categorical, %d datetime, %d id cols.",
        len(schema.numerical_columns),
        len(schema.categorical_columns),
        len(schema.datetime_columns),
        len(schema.id_columns),
    )

    return schema


def _classify_column(
    series: pd.Series,
    col_name: str,
    unique_count: int,
    total_rows: int,
    currency_keywords: set[str],
) -> str:
    """Classify a single column into a category."""

    # Datetime
    if pd.api.types.is_datetime64_any_dtype(series):
        return "datetime"

    # ID column: very high cardinality relative to row count
    if total_rows > 0 and unique_count / total_rows > 0.95:
        if pd.api.types.is_integer_dtype(series) or pd.api.types.is_string_dtype(series):
            return "id"

    # Currency: numeric + name contains money keyword
    name_lower = col_name.lower().replace("_", " ").replace("-", " ")
    if pd.api.types.is_numeric_dtype(series):
        if any(kw in name_lower for kw in currency_keywords):
            return "currency"
        return "numerical"

    # Categorical (object, bool, etc.)
    return "categorical"


def get_dtype_summary(df: pd.DataFrame) -> str:
    """Return a formatted string of column names and their dtypes."""
    lines = [f"{col}: {dtype}" for col, dtype in df.dtypes.items()]
    return "\n".join(lines)
