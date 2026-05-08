# ============================================================
#  Insights Page
#  AI-generated business insights with export.
# ============================================================

from __future__ import annotations
import pandas as pd
import streamlit as st
from backend.insight_engine import generate_insights
from backend.schema_detector import SchemaInfo
from backend.export_engine import export_insights_markdown


def render_insights_page(df: pd.DataFrame, schema: SchemaInfo) -> None:
    """Render the AI insights page."""

    st.markdown(
        '<h1 style="font-size:28px;font-weight:800;color:#e2e8f0;margin-bottom:4px;">'
        '💡 AI Insights</h1>'
        '<p style="color:#94a3b8;font-size:14px;margin-bottom:24px;">'
        'Intelligent, AI-generated analysis of your dataset</p>',
        unsafe_allow_html=True,
    )

    # Check for cached insights
    if "insights_text" not in st.session_state:
        st.session_state.insights_text = None

    col1, col2 = st.columns([1, 4])
    with col1:
        generate_btn = st.button(
            "🔍 Generate Insights",
            type="primary",
            use_container_width=True,
            key="gen_insights_btn",
        )
    with col2:
        if st.session_state.insights_text:
            md_bytes = export_insights_markdown(st.session_state.insights_text)
            st.download_button(
                "📥 Download Insights",
                data=md_bytes,
                file_name="ai_insights.md",
                mime="text/markdown",
                key="dl_insights_btn",
            )

    if generate_btn:
        with st.spinner("🤖 Generating AI insights… this may take a moment."):
            try:
                insights = generate_insights(df, schema)
                st.session_state.insights_text = insights
            except Exception as exc:
                st.error(f"Failed to generate insights: {exc}", icon="❌")

    # Display insights
    if st.session_state.insights_text:
        st.markdown(
            f"""
            <div style="
                background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
                border: 1px solid #334155;
                border-radius: 16px;
                padding: 28px;
                margin-top: 16px;
                line-height: 1.8;
            ">
            """,
            unsafe_allow_html=True,
        )
        st.markdown(st.session_state.insights_text)
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.markdown(
            """
            <div style="
                text-align: center;
                padding: 80px 20px;
                color: #64748b;
            ">
                <div style="font-size: 56px; margin-bottom: 16px;">💡</div>
                <h3 style="color: #94a3b8;">No insights generated yet</h3>
                <p>Click <b>Generate Insights</b> to let the AI analyze your data.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
