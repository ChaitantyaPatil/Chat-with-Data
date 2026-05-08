# ============================================================
#  Export Engine
#  Provides download functionality for data, charts, and
#  insights from the Streamlit UI.
# ============================================================

from __future__ import annotations

import io
from typing import Optional

import pandas as pd
import plotly.graph_objects as go

from utils.logger import get_logger

logger = get_logger(__name__)


def export_dataframe_csv(df: pd.DataFrame) -> bytes:
    """
    Export a DataFrame as CSV bytes.

    Args:
        df: The DataFrame to export.

    Returns:
        UTF-8 encoded CSV bytes.
    """
    buffer = io.StringIO()
    df.to_csv(buffer, index=False)
    csv_bytes = buffer.getvalue().encode("utf-8")
    logger.info("Exported CSV: %d bytes.", len(csv_bytes))
    return csv_bytes


def export_dataframe_excel(df: pd.DataFrame) -> bytes:
    """
    Export a DataFrame as Excel bytes.

    Args:
        df: The DataFrame to export.

    Returns:
        XLSX file bytes.
    """
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Data")
    xlsx_bytes = buffer.getvalue()
    logger.info("Exported Excel: %d bytes.", len(xlsx_bytes))
    return xlsx_bytes


def export_chart_png(fig: go.Figure, width: int = 1200, height: int = 600) -> Optional[bytes]:
    """
    Export a Plotly figure as PNG bytes.

    Requires the ``kaleido`` package for static image export.

    Args:
        fig: The Plotly figure to export.
        width: Image width in pixels.
        height: Image height in pixels.

    Returns:
        PNG bytes, or None if export fails.
    """
    try:
        png_bytes = fig.to_image(format="png", width=width, height=height, engine="kaleido")
        logger.info("Exported chart PNG: %d bytes.", len(png_bytes))
        return png_bytes
    except Exception as exc:
        logger.error("Chart PNG export failed: %s", exc)
        return None


def export_insights_markdown(insights: str) -> bytes:
    """
    Export insights as a Markdown file.

    Args:
        insights: The insights text (markdown formatted).

    Returns:
        UTF-8 encoded markdown bytes.
    """
    header = "# AI-Generated Data Insights\n\n"
    md_content = header + insights
    md_bytes = md_content.encode("utf-8")
    logger.info("Exported insights MD: %d bytes.", len(md_bytes))
    return md_bytes
