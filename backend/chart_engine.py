# ============================================================
#  Chart Engine
#  Auto-suggests and renders Plotly charts based on query
#  intent and data characteristics.
# ============================================================

from __future__ import annotations

import json
from typing import Any, Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from backend.schema_detector import SchemaInfo, get_dtype_summary
from llm.llm_client import get_llm
from llm.prompt_templates import CHART_SUGGESTION_PROMPT
from utils.logger import get_logger

logger = get_logger(__name__)


# ── Chart Configuration ──────────────────────────────────────

CHART_COLORS = [
    "#6366f1", "#8b5cf6", "#a78bfa", "#c4b5fd",  # Purple palette
    "#06b6d4", "#22d3ee", "#67e8f9",              # Cyan palette
    "#f43f5e", "#fb7185", "#fda4af",              # Rose palette
    "#10b981", "#34d399", "#6ee7b7",              # Emerald palette
]

CHART_TEMPLATE = "plotly_dark"


def suggest_chart(
    query: str,
    schema: SchemaInfo,
) -> dict[str, Any]:
    """
    Use the LLM to suggest the best chart type for a query.

    Args:
        query: The user's natural language query.
        schema: The dataset schema.

    Returns:
        Dict with chart_type, x_column, y_column, color_column,
        title, and explanation.
    """
    llm = get_llm()

    prompt = CHART_SUGGESTION_PROMPT.format(
        schema=schema.to_llm_string(),
        dtypes="\n".join(f"{c.name}: {c.dtype}" for c in schema.columns),
        query=query,
    )

    try:
        response = llm.invoke(prompt.to_messages())
        content = response.content.strip()

        # Parse JSON from the response (handle markdown wrapping)
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        suggestion = json.loads(content)
        logger.info("Chart suggestion: %s", suggestion.get("chart_type", "unknown"))
        return suggestion

    except (json.JSONDecodeError, IndexError, Exception) as exc:
        logger.warning("Chart suggestion failed, using fallback: %s", exc)
        return _fallback_suggestion(schema)


def _fallback_suggestion(schema: SchemaInfo) -> dict[str, Any]:
    """Generate a sensible default chart when LLM suggestion fails."""
    num_cols = schema.numerical_columns
    cat_cols = schema.categorical_columns

    if cat_cols and num_cols:
        return {
            "chart_type": "bar",
            "x_column": cat_cols[0],
            "y_column": num_cols[0],
            "color_column": None,
            "title": f"{num_cols[0]} by {cat_cols[0]}",
            "explanation": "Default bar chart showing the first numeric column grouped by the first categorical column.",
        }
    elif len(num_cols) >= 2:
        return {
            "chart_type": "scatter",
            "x_column": num_cols[0],
            "y_column": num_cols[1],
            "color_column": None,
            "title": f"{num_cols[1]} vs {num_cols[0]}",
            "explanation": "Default scatter plot of the first two numeric columns.",
        }
    elif num_cols:
        return {
            "chart_type": "histogram",
            "x_column": num_cols[0],
            "y_column": None,
            "color_column": None,
            "title": f"Distribution of {num_cols[0]}",
            "explanation": "Default histogram of the first numeric column.",
        }
    else:
        return {
            "chart_type": "bar",
            "x_column": schema.columns[0].name if schema.columns else "",
            "y_column": None,
            "color_column": None,
            "title": "Data Overview",
            "explanation": "Fallback chart.",
        }


def render_chart(
    df: pd.DataFrame,
    chart_type: str,
    x_column: str,
    y_column: Optional[str] = None,
    color_column: Optional[str] = None,
    title: str = "Chart",
) -> go.Figure:
    """
    Render a Plotly chart based on the specified configuration.

    Args:
        df: Source DataFrame.
        chart_type: One of line, bar, histogram, scatter, pie, area, box.
        x_column: Column for the x-axis.
        y_column: Column for the y-axis (optional for some chart types).
        color_column: Column for color encoding (optional).
        title: Chart title.

    Returns:
        A :class:`plotly.graph_objects.Figure`.
    """
    # Validate columns exist
    available = set(df.columns)
    if x_column not in available:
        logger.warning("x_column '%s' not found. Using first column.", x_column)
        x_column = df.columns[0]
    if y_column and y_column not in available:
        logger.warning("y_column '%s' not found. Setting to None.", y_column)
        y_column = None
    if color_column and color_column not in available:
        color_column = None

    chart_builders = {
        "line": _build_line,
        "bar": _build_bar,
        "histogram": _build_histogram,
        "scatter": _build_scatter,
        "pie": _build_pie,
        "area": _build_area,
        "box": _build_box,
    }

    builder = chart_builders.get(chart_type, _build_bar)
    fig = builder(df, x_column, y_column, color_column, title)

    # Apply consistent styling
    fig.update_layout(
        template=CHART_TEMPLATE,
        title=dict(text=title, font=dict(size=18, color="#e2e8f0")),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#94a3b8"),
        margin=dict(l=40, r=40, t=60, b=40),
        colorway=CHART_COLORS,
        hoverlabel=dict(
            bgcolor="#1e293b",
            font_color="#e2e8f0",
            bordercolor="#475569",
        ),
    )

    return fig


# ── Chart Builders ───────────────────────────────────────────

def _build_line(df, x, y, color, title) -> go.Figure:
    return px.line(df, x=x, y=y, color=color, title=title, markers=True)


def _build_bar(df, x, y, color, title) -> go.Figure:
    return px.bar(df, x=x, y=y, color=color, title=title)


def _build_histogram(df, x, y, color, title) -> go.Figure:
    return px.histogram(df, x=x, color=color, title=title, nbins=30)


def _build_scatter(df, x, y, color, title) -> go.Figure:
    return px.scatter(df, x=x, y=y, color=color, title=title, opacity=0.7)


def _build_pie(df, x, y, color, title) -> go.Figure:
    if y:
        return px.pie(df, names=x, values=y, title=title)
    return px.pie(df, names=x, title=title)


def _build_area(df, x, y, color, title) -> go.Figure:
    return px.area(df, x=x, y=y, color=color, title=title)


def _build_box(df, x, y, color, title) -> go.Figure:
    return px.box(df, x=x, y=y, color=color, title=title)


def auto_generate_charts(
    df: pd.DataFrame,
    schema: SchemaInfo,
    max_charts: int = 3,
) -> list[go.Figure]:
    """
    Automatically generate a set of exploratory charts.

    Creates up to ``max_charts`` charts based on the schema:
      - Distribution of the first numeric column
      - Top categories bar chart
      - Time series if a datetime column exists

    Args:
        df: Source DataFrame.
        schema: Schema information.
        max_charts: Maximum number of charts to generate.

    Returns:
        List of Plotly figures.
    """
    figures: list[go.Figure] = []

    # 1. Distribution of first numeric column
    if schema.numerical_columns:
        col = schema.numerical_columns[0]
        fig = render_chart(df, "histogram", x_column=col, title=f"Distribution of {col}")
        figures.append(fig)

    # 2. Bar chart: first categorical × first numeric
    if schema.categorical_columns and schema.numerical_columns and len(figures) < max_charts:
        cat_col = schema.categorical_columns[0]
        num_col = schema.numerical_columns[0]
        # Aggregate for bar chart
        agg_df = df.groupby(cat_col)[num_col].sum().reset_index()
        agg_df = agg_df.nlargest(10, num_col)
        fig = render_chart(agg_df, "bar", x_column=cat_col, y_column=num_col, title=f"Top {cat_col} by {num_col}")
        figures.append(fig)

    # 3. Time series if datetime exists
    if schema.datetime_columns and schema.numerical_columns and len(figures) < max_charts:
        dt_col = schema.datetime_columns[0]
        num_col = schema.numerical_columns[0]
        ts_df = df.sort_values(dt_col)
        fig = render_chart(ts_df, "line", x_column=dt_col, y_column=num_col, title=f"{num_col} over Time")
        figures.append(fig)

    return figures
