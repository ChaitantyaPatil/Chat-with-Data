# ============================================================
#  Summary Cards Component
#  Beautiful KPI metric cards for the dashboard.
# ============================================================

from __future__ import annotations
import pandas as pd
import streamlit as st
from backend.schema_detector import SchemaInfo


def render_summary_cards(df: pd.DataFrame, schema: SchemaInfo) -> None:
    """Render KPI summary cards for the dataset."""

    # Row 1: Core metrics
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        _metric_card("📊", "Total Rows", f"{schema.row_count:,}", "#6366f1")
    with c2:
        _metric_card("📐", "Total Columns", str(schema.column_count), "#8b5cf6")
    with c3:
        missing = int(df.isna().sum().sum())
        pct = (missing / (len(df) * len(df.columns)) * 100) if len(df) > 0 else 0
        _metric_card("⚠️", "Missing Values", f"{missing:,} ({pct:.1f}%)", "#f59e0b")
    with c4:
        dups = int(df.duplicated().sum())
        _metric_card("♻️", "Duplicate Rows", f"{dups:,}", "#10b981")

    st.markdown("<div style='height: 12px'></div>", unsafe_allow_html=True)

    # Row 2: Column type breakdown
    c5, c6, c7, c8 = st.columns(4)

    with c5:
        _metric_card("🔢", "Numeric Cols", str(len(schema.numerical_columns)), "#06b6d4")
    with c6:
        _metric_card("🏷️", "Categorical", str(len(schema.categorical_columns)), "#f43f5e")
    with c7:
        _metric_card("📅", "Date Cols", str(len(schema.datetime_columns)), "#a78bfa")
    with c8:
        mem_mb = df.memory_usage(deep=True).sum() / (1024 * 1024)
        _metric_card("💾", "Memory", f"{mem_mb:.1f} MB", "#64748b")

    # Row 3: Top category & numeric summary
    st.markdown("<div style='height: 12px'></div>", unsafe_allow_html=True)

    col_left, col_right = st.columns(2)

    with col_left:
        if schema.numerical_columns:
            with st.expander("🔢 Numeric Summary", expanded=True):
                st.dataframe(
                    df[schema.numerical_columns].describe().T.round(2),
                    use_container_width=True,
                )

    with col_right:
        if schema.categorical_columns:
            with st.expander("🏷️ Top Categories", expanded=True):
                for col_name in schema.categorical_columns[:3]:
                    top3 = df[col_name].value_counts().head(3)
                    st.markdown(f"**{col_name}**")
                    for val, count in top3.items():
                        pct = count / len(df) * 100
                        st.markdown(f"&nbsp;&nbsp;`{val}` — {count:,} ({pct:.1f}%)")


def _metric_card(icon: str, label: str, value: str, color: str) -> None:
    """Render a single styled metric card."""
    st.markdown(
        f"""
        <div style="
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
            border: 1px solid #334155;
            border-left: 4px solid {color};
            border-radius: 12px;
            padding: 18px 16px;
            text-align: center;
        ">
            <div style="font-size: 24px; margin-bottom: 6px;">{icon}</div>
            <div style="
                font-size: 24px;
                font-weight: 800;
                color: {color};
                line-height: 1.2;
            ">{value}</div>
            <div style="
                font-size: 12px;
                color: #94a3b8;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                margin-top: 4px;
            ">{label}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
