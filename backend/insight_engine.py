# ============================================================
#  Insight Engine
#  Generates business-friendly AI insights from data summaries.
# ============================================================

from __future__ import annotations

from typing import Optional

import pandas as pd

from backend.schema_detector import SchemaInfo
from llm.llm_client import get_llm
from llm.prompt_templates import INSIGHTS_PROMPT
from utils.logger import get_logger

logger = get_logger(__name__)


def generate_insights(
    df: pd.DataFrame,
    schema: SchemaInfo,
) -> str:
    """
    Generate AI-powered business insights from a DataFrame.

    Sends a statistical summary and schema to the LLM and
    returns formatted, human-readable insights.

    Args:
        df: The cleaned DataFrame.
        schema: The dataset schema.

    Returns:
        A formatted string of insights (markdown).
    """
    # Build statistical summary
    summary_parts = []

    # Basic info
    summary_parts.append(f"Dataset: {schema.row_count} rows × {schema.column_count} columns")

    # Numeric stats
    if schema.numerical_columns:
        num_stats = df[schema.numerical_columns].describe().to_string()
        summary_parts.append(f"\nNumerical Statistics:\n{num_stats}")

    # Categorical top values
    for col_name in schema.categorical_columns[:5]:
        top_vals = df[col_name].value_counts().head(5).to_dict()
        summary_parts.append(f"\nTop values in '{col_name}': {top_vals}")

    # Date range
    for col_name in schema.datetime_columns:
        try:
            date_min = df[col_name].min()
            date_max = df[col_name].max()
            summary_parts.append(f"\nDate range in '{col_name}': {date_min} to {date_max}")
        except Exception:
            pass

    # Missing data overview
    missing = df.isna().sum()
    missing = missing[missing > 0]
    if not missing.empty:
        summary_parts.append(f"\nMissing values:\n{missing.to_string()}")

    summary = "\n".join(summary_parts)

    # Build statistics string
    statistics = ""
    if schema.numerical_columns:
        statistics = df[schema.numerical_columns].describe().to_string()

    # Truncate for token limits (keep under ~3000 chars)
    if len(summary) > 3000:
        summary = summary[:3000] + "\n... (truncated)"

    logger.info("Generating AI insights (%d chars of context).", len(summary))

    try:
        llm = get_llm(temperature=0.3)

        prompt = INSIGHTS_PROMPT.format(
            summary=summary,
            statistics=statistics,
            schema=schema.to_llm_string(),
        )

        response = llm.invoke(prompt.to_messages())
        insights = response.content.strip()

        logger.info("Insights generated successfully (%d chars).", len(insights))
        return insights

    except Exception as exc:
        logger.error("Insight generation failed: %s", exc)
        return _generate_fallback_insights(df, schema)


def _generate_fallback_insights(df: pd.DataFrame, schema: SchemaInfo) -> str:
    """
    Generate basic statistical insights when the LLM is unavailable.
    """
    lines = ["## 📊 Data Insights (Auto-generated)\n"]

    # Row/column info
    lines.append(f"📋 **Dataset Size**: {len(df):,} rows × {len(df.columns)} columns\n")

    # Numeric summaries
    for col in schema.numerical_columns[:5]:
        mean_val = df[col].mean()
        median_val = df[col].median()
        std_val = df[col].std()
        lines.append(
            f"📈 **{col}**: Mean = {mean_val:,.2f}, "
            f"Median = {median_val:,.2f}, Std = {std_val:,.2f}"
        )

    # Top categories
    for col in schema.categorical_columns[:3]:
        top = df[col].value_counts().head(3)
        top_str = ", ".join(f"{k} ({v})" for k, v in top.items())
        lines.append(f"🏷️ **Top {col}**: {top_str}")

    # Missing data
    total_missing = df.isna().sum().sum()
    if total_missing > 0:
        pct = total_missing / (len(df) * len(df.columns)) * 100
        lines.append(f"\n⚠️ **Missing Data**: {total_missing:,} values ({pct:.1f}% of total)")

    return "\n\n".join(lines)
