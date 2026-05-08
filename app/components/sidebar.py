# ============================================================
#  Sidebar Component
#  Navigation, file info, schema summary, and controls.
# ============================================================

from __future__ import annotations

from typing import Optional

import streamlit as st

from backend.data_cleaner import CleaningReport
from backend.schema_detector import SchemaInfo


def render_sidebar(
    schema: Optional[SchemaInfo] = None,
    cleaning_report: Optional[CleaningReport] = None,
) -> str:
    """
    Render the application sidebar.

    Includes:
      - Logo / brand
      - Navigation
      - File / schema info (when data is loaded)
      - Reset button

    Args:
        schema: Schema info (shown when data is loaded).
        cleaning_report: Cleaning report (shown when data is loaded).

    Returns:
        The selected page name.
    """
    with st.sidebar:
        # ── Brand ────────────────────────────────────────
        st.markdown(
            """
            <div style="
                text-align: center;
                padding: 20px 0 10px 0;
            ">
                <div style="
                    font-size: 40px;
                    margin-bottom: 4px;
                ">💬📊</div>
                <div style="
                    font-size: 22px;
                    font-weight: 800;
                    background: linear-gradient(135deg, #818cf8, #c084fc);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    letter-spacing: -0.5px;
                ">Chat with Data</div>
                <div style="
                    font-size: 12px;
                    color: #94a3b8;
                    margin-top: 2px;
                ">AI-Powered Data Analysis</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("---")

        # ── Navigation ───────────────────────────────────
        st.markdown(
            '<p style="font-size: 11px; color: #64748b; text-transform: uppercase; '
            'letter-spacing: 1px; font-weight: 600; margin-bottom: 8px;">Navigation</p>',
            unsafe_allow_html=True,
        )

        page = st.radio(
            "Go to",
            options=["🏠 Dashboard", "🔍 Data Preview", "💡 Insights", "💬 Chat"],
            label_visibility="collapsed",
            key="nav_radio",
        )

        st.markdown("---")

        # ── Schema Info (if data loaded) ─────────────────
        if schema:
            st.markdown(
                '<p style="font-size: 11px; color: #64748b; text-transform: uppercase; '
                'letter-spacing: 1px; font-weight: 600; margin-bottom: 8px;">Dataset Info</p>',
                unsafe_allow_html=True,
            )

            col1, col2 = st.columns(2)
            col1.metric("Rows", f"{schema.row_count:,}")
            col2.metric("Columns", f"{schema.column_count}")

            # Column type breakdown
            with st.expander("📐 Column Types", expanded=False):
                if schema.numerical_columns:
                    st.markdown(f"**Numerical** ({len(schema.numerical_columns)})")
                    for col in schema.numerical_columns:
                        st.markdown(f"  `{col}`")
                if schema.categorical_columns:
                    st.markdown(f"**Categorical** ({len(schema.categorical_columns)})")
                    for col in schema.categorical_columns:
                        st.markdown(f"  `{col}`")
                if schema.datetime_columns:
                    st.markdown(f"**Datetime** ({len(schema.datetime_columns)})")
                    for col in schema.datetime_columns:
                        st.markdown(f"  `{col}`")
                if schema.id_columns:
                    st.markdown(f"**ID** ({len(schema.id_columns)})")
                    for col in schema.id_columns:
                        st.markdown(f"  `{col}`")
                if schema.currency_columns:
                    st.markdown(f"**Currency** ({len(schema.currency_columns)})")
                    for col in schema.currency_columns:
                        st.markdown(f"  `{col}`")

            st.markdown("---")

        # ── Cleaning Report ──────────────────────────────
        if cleaning_report:
            with st.expander("🧹 Cleaning Report", expanded=False):
                st.markdown(cleaning_report.summary)

            st.markdown("---")

        # ── Reset Button ─────────────────────────────────
        if st.button("🔄 Reset & Upload New File", use_container_width=True, type="secondary"):
            # Clear all session state
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

        # ── Footer ───────────────────────────────────────
        st.markdown(
            """
            <div style="
                position: fixed;
                bottom: 16px;
                left: 16px;
                font-size: 11px;
                color: #475569;
            ">
                Built with Streamlit + LangChain
            </div>
            """,
            unsafe_allow_html=True,
        )

    return page
