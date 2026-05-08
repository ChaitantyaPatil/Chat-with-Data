# ============================================================
#  Charts Component
#  Reusable chart rendering with controls and download.
# ============================================================

from __future__ import annotations
from typing import List, Optional
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from backend.chart_engine import render_chart
from backend.export_engine import export_chart_png


def render_chart_with_controls(
    df: pd.DataFrame,
    default_chart_type: str = "bar",
    default_x: Optional[str] = None,
    default_y: Optional[str] = None,
    key_prefix: str = "chart",
) -> Optional[go.Figure]:
    """Render an interactive chart with user controls."""
    columns = list(df.columns)
    numeric_cols = list(df.select_dtypes(include=["number"]).columns)
    if not columns:
        st.info("No columns available for charting.", icon="ℹ️")
        return None

    col1, col2, col3, col4 = st.columns([1.5, 1.5, 1.5, 1])
    chart_types = ["bar", "line", "scatter", "histogram", "pie", "area", "box"]

    with col1:
        chart_type = st.selectbox(
            "Chart Type", options=chart_types,
            index=chart_types.index(default_chart_type) if default_chart_type in chart_types else 0,
            key=f"{key_prefix}_type",
        )
    with col2:
        x_col = st.selectbox(
            "X-Axis", options=columns,
            index=columns.index(default_x) if default_x and default_x in columns else 0,
            key=f"{key_prefix}_x",
        )
    with col3:
        y_options = ["(none)"] + numeric_cols
        y_col = st.selectbox("Y-Axis", options=y_options,
            index=y_options.index(default_y) if default_y and default_y in y_options else (1 if len(y_options) > 1 else 0),
            key=f"{key_prefix}_y")
        y_col = None if y_col == "(none)" else y_col
    with col4:
        color_options = ["(none)"] + [c for c in columns if df[c].nunique() <= 20]
        color_col = st.selectbox("Color By", options=color_options, key=f"{key_prefix}_color")
        color_col = None if color_col == "(none)" else color_col

    try:
        title = f"{y_col or x_col} by {x_col}" if y_col else f"Distribution of {x_col}"
        fig = render_chart(df, chart_type, x_col, y_col, color_col, title)
        st.plotly_chart(fig, use_container_width=True, key=f"{key_prefix}_plot")
        png_bytes = export_chart_png(fig)
        if png_bytes:
            st.download_button("📥 Download Chart (PNG)", data=png_bytes,
                file_name=f"{key_prefix}_chart.png", mime="image/png", key=f"{key_prefix}_dl")
        return fig
    except Exception as exc:
        st.error(f"Could not render chart: {exc}", icon="📊")
        return None


def render_auto_charts(figures: List[go.Figure]) -> None:
    """Display a list of auto-generated charts."""
    if not figures:
        return
    st.markdown('<p style="font-size:11px;color:#64748b;text-transform:uppercase;'
        'letter-spacing:1px;font-weight:600;margin-bottom:16px;">📈 Auto-Generated Charts</p>',
        unsafe_allow_html=True)
    for i, fig in enumerate(figures):
        st.plotly_chart(fig, use_container_width=True, key=f"auto_chart_{i}")
