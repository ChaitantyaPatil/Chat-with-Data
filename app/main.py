# ============================================================
#  Chat with Data — Main Streamlit Application
#  Entry point: streamlit run app/main.py
# ============================================================

from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is on sys.path for package imports
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import pandas as pd
import streamlit as st

from app.components.chatbox import (
    render_chat_history,
    render_chat_input,
    render_welcome_message,
)
from app.components.sidebar import render_sidebar
from app.components.uploader import render_uploader
from app.pages.dashboard import render_dashboard
from app.pages.data_preview import render_data_preview
from app.pages.insights import render_insights_page
from backend.chart_engine import render_chart, suggest_chart
from backend.memory import ChatMessage, ConversationMemory
from backend.query_engine import run_query
from backend.schema_detector import SchemaInfo


# ── Page Configuration ───────────────────────────────────────

st.set_page_config(
    page_title="Chat with Data — AI Data Analysis",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": "# Chat with Data\nAI-powered data analysis app built with Streamlit & LangChain.",
    },
)


# ── Custom CSS ───────────────────────────────────────────────

st.markdown(
    """
    <style>
        /* ── Global ──────────────────────────────────── */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
        }

        .stApp {
            background: linear-gradient(180deg, #0f172a 0%, #020617 100%);
        }

        /* ── Sidebar ─────────────────────────────────── */
        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0f172a 0%, #1e1b4b 100%);
            border-right: 1px solid #1e293b;
        }

        section[data-testid="stSidebar"] .stRadio label {
            color: #cbd5e1;
            font-weight: 500;
            padding: 8px 12px;
            border-radius: 8px;
            transition: all 0.2s ease;
        }

        section[data-testid="stSidebar"] .stRadio label:hover {
            background: rgba(99, 102, 241, 0.15);
            color: #e2e8f0;
        }

        /* ── Metrics ─────────────────────────────────── */
        [data-testid="stMetric"] {
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
            border: 1px solid #334155;
            border-radius: 12px;
            padding: 16px;
        }

        [data-testid="stMetricValue"] {
            color: #a78bfa;
            font-weight: 700;
        }

        /* ── Buttons ─────────────────────────────────── */
        .stButton button[kind="primary"] {
            background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
            border: none;
            border-radius: 10px;
            font-weight: 600;
            transition: all 0.3s ease;
        }

        .stButton button[kind="primary"]:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 20px rgba(99, 102, 241, 0.4);
        }

        /* ── Tabs ────────────────────────────────────── */
        .stTabs [data-baseweb="tab"] {
            color: #94a3b8;
            font-weight: 500;
        }

        .stTabs [aria-selected="true"] {
            color: #a78bfa;
            border-bottom-color: #8b5cf6;
        }

        /* ── Chat ────────────────────────────────────── */
        .stChatMessage {
            background: #1e293b;
            border: 1px solid #334155;
            border-radius: 12px;
            padding: 12px 16px;
        }

        /* ── Dataframe ───────────────────────────────── */
        .stDataFrame {
            border: 1px solid #334155;
            border-radius: 12px;
        }

        /* ── File Uploader ───────────────────────────── */
        [data-testid="stFileUploader"] {
            border: 2px dashed #4338ca;
            border-radius: 16px;
            padding: 20px;
            background: rgba(67, 56, 202, 0.05);
        }

        /* ── Expanders ───────────────────────────────── */
        .streamlit-expanderHeader {
            font-weight: 600;
            color: #e2e8f0;
        }

        /* ── Scrollbar ───────────────────────────────── */
        ::-webkit-scrollbar {
            width: 6px;
            height: 6px;
        }
        ::-webkit-scrollbar-track {
            background: #0f172a;
        }
        ::-webkit-scrollbar-thumb {
            background: #334155;
            border-radius: 3px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: #475569;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ── Session State Initialization ─────────────────────────────

def _init_session_state() -> None:
    """Initialize all session state keys with defaults."""
    defaults = {
        "raw_df": None,
        "cleaned_df": None,
        "schema": None,
        "cleaning_report": None,
        "memory": ConversationMemory(),
        "chat_messages": [],
        "insights_text": None,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


_init_session_state()


# ── Sidebar ──────────────────────────────────────────────────

selected_page = render_sidebar(
    schema=st.session_state.schema,
    cleaning_report=st.session_state.cleaning_report,
)


# ── Main Content ─────────────────────────────────────────────

def _handle_upload() -> None:
    """Process a new file upload and store results in session state."""
    result = render_uploader()
    if result is not None:
        raw_df, cleaned_df, schema, cleaning_report = result
        st.session_state.raw_df = raw_df
        st.session_state.cleaned_df = cleaned_df
        st.session_state.schema = schema
        st.session_state.cleaning_report = cleaning_report


# If no data loaded yet, show upload screen
if st.session_state.cleaned_df is None:
    st.markdown(
        """
        <div style="
            text-align: center;
            padding: 80px 20px 40px 20px;
        ">
            <div style="font-size: 72px; margin-bottom: 16px;">💬📊</div>
            <h1 style="
                font-size: 42px;
                font-weight: 800;
                background: linear-gradient(135deg, #818cf8, #c084fc, #f0abfc);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                margin-bottom: 12px;
            ">Chat with Data</h1>
            <p style="
                color: #94a3b8;
                font-size: 18px;
                max-width: 600px;
                margin: 0 auto 40px auto;
                line-height: 1.6;
            ">
                Upload a CSV or Excel file and start exploring your data
                with AI-powered natural language queries, auto-generated charts,
                and intelligent insights.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    _handle_upload()

else:
    # Data is loaded — show selected page
    df: pd.DataFrame = st.session_state.cleaned_df
    schema: SchemaInfo = st.session_state.schema

    if selected_page == "🏠 Dashboard":
        render_dashboard(df, schema)

    elif selected_page == "🔍 Data Preview":
        render_data_preview(df, schema)

    elif selected_page == "💡 Insights":
        render_insights_page(df, schema)

    elif selected_page == "💬 Chat":
        # ── Chat Page ────────────────────────────────────
        st.markdown(
            '<h1 style="font-size:28px;font-weight:800;color:#e2e8f0;margin-bottom:4px;">'
            '💬 Chat with Your Data</h1>'
            '<p style="color:#94a3b8;font-size:14px;margin-bottom:24px;">'
            'Ask questions in natural language</p>',
            unsafe_allow_html=True,
        )

        # Render existing messages
        if not st.session_state.chat_messages:
            render_welcome_message()
        else:
            render_chat_history(st.session_state.chat_messages)

        # Chat input
        user_query = render_chat_input()

        if user_query:
            # Add user message
            st.session_state.chat_messages.append(
                ChatMessage(role="user", content=user_query)
            )

            with st.chat_message("user", avatar="🧑‍💻"):
                st.markdown(user_query)

            # Process query
            with st.chat_message("assistant", avatar="🤖"):
                with st.spinner("🔄 Analyzing…"):
                    try:
                        result = run_query(
                            query=user_query,
                            df=df,
                            schema=schema,
                            memory=st.session_state.memory,
                        )

                        if result.success:
                            # Show generated code
                            with st.expander("🔧 Generated Code", expanded=False):
                                st.code(result.generated_code, language="python")

                            # Show result based on type
                            if result.result_type == "dataframe" and result.has_dataframe:
                                st.dataframe(
                                    result.result_data,
                                    use_container_width=True,
                                )
                                msg_content = f"Here are the results for: *{user_query}*"
                                msg_type = "dataframe"

                                # Try to suggest a chart
                                try:
                                    suggestion = suggest_chart(user_query, schema)
                                    chart_fig = render_chart(
                                        result.result_data,
                                        chart_type=suggestion.get("chart_type", "bar"),
                                        x_column=suggestion.get("x_column", result.result_data.columns[0]),
                                        y_column=suggestion.get("y_column"),
                                        title=suggestion.get("title", "Query Result"),
                                    )
                                    st.plotly_chart(chart_fig, use_container_width=True)
                                except Exception:
                                    pass  # Chart suggestion is optional

                            elif result.result_type == "scalar":
                                st.markdown(f"### {result.result_data}")
                                msg_content = str(result.result_data)
                                msg_type = "text"
                            else:
                                st.markdown(str(result.result_data) if result.result_data else "No result returned.")
                                msg_content = str(result.result_data) if result.result_data else "No result."
                                msg_type = "text"
                        else:
                            st.error(f"❌ {result.error}", icon="🚫")
                            msg_content = f"Error: {result.error}"
                            msg_type = "error"

                    except Exception as exc:
                        st.error(f"❌ Unexpected error: {exc}", icon="🚫")
                        msg_content = f"Error: {exc}"
                        msg_type = "error"
                        result = None

                    # Store assistant message
                    st.session_state.chat_messages.append(
                        ChatMessage(
                            role="assistant",
                            content=msg_content,
                            code=result.generated_code if result else "",
                            data=result.result_data if result else None,
                            msg_type=msg_type,
                        )
                    )
