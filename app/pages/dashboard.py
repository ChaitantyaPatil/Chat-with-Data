# ============================================================
#  Dashboard Page
#  Main overview with KPI cards, auto-generated charts,
#  and quick data insights.
# ============================================================

from __future__ import annotations
import pandas as pd
import streamlit as st
from backend.chart_engine import auto_generate_charts
from backend.schema_detector import SchemaInfo
from backend.export_engine import export_dataframe_csv
from app.components.summary_cards import render_summary_cards
from app.components.charts import render_auto_charts, render_chart_with_controls


def render_dashboard(df: pd.DataFrame, schema: SchemaInfo) -> None:
    """Render the main dashboard page."""

    st.markdown(
        '<h1 style="font-size:28px;font-weight:800;color:#e2e8f0;margin-bottom:4px;">'
        '🏠 Dashboard</h1>'
        '<p style="color:#94a3b8;font-size:14px;margin-bottom:24px;">'
        'Overview of your dataset at a glance</p>',
        unsafe_allow_html=True,
    )

    # ── KPI Summary Cards ────────────────────────────────
    render_summary_cards(df, schema)

    st.markdown("---")

    # ── Auto-Generated Charts ────────────────────────────
    tab1, tab2 = st.tabs(["📈 Auto Charts", "🎨 Custom Chart"])

    with tab1:
        with st.spinner("Generating charts…"):
            figures = auto_generate_charts(df, schema, max_charts=3)
            render_auto_charts(figures)

    with tab2:
        render_chart_with_controls(
            df,
            default_chart_type="bar",
            default_x=schema.categorical_columns[0] if schema.categorical_columns else df.columns[0],
            default_y=schema.numerical_columns[0] if schema.numerical_columns else None,
            key_prefix="dashboard_custom",
        )

    st.markdown("---")

    # ── Quick Data Preview ───────────────────────────────
    with st.expander("👀 Quick Data Preview (first 10 rows)", expanded=False):
        st.dataframe(df.head(10), use_container_width=True)

    # ── Export ────────────────────────────────────────────
    csv_bytes = export_dataframe_csv(df)
    st.download_button(
        "📥 Download Cleaned Data (CSV)",
        data=csv_bytes,
        file_name="cleaned_data.csv",
        mime="text/csv",
        key="dashboard_csv_dl",
    )
