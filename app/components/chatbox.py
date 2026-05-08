# ============================================================
#  Chatbox Component
#  Conversational chat UI with message history, loading
#  indicators, and inline result rendering.
# ============================================================

from __future__ import annotations

from typing import List

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from backend.memory import ChatMessage


def render_chat_history(messages: List[ChatMessage]) -> None:
    """
    Render the full chat history in a conversational layout.

    Args:
        messages: List of ChatMessage objects to display.
    """
    for msg in messages:
        with st.chat_message(msg.role, avatar="🧑‍💻" if msg.role == "user" else "🤖"):
            # Text content
            if msg.content:
                st.markdown(msg.content)

            # Generated code (collapsible)
            if msg.code:
                with st.expander("🔧 Generated Code", expanded=False):
                    st.code(msg.code, language="python")

            # DataFrame result
            if msg.msg_type == "dataframe" and msg.data is not None:
                if isinstance(msg.data, pd.DataFrame):
                    st.dataframe(
                        msg.data,
                        use_container_width=True,
                        height=min(400, 35 * len(msg.data) + 38),
                    )

            # Chart result
            if msg.msg_type == "chart" and msg.data is not None:
                if isinstance(msg.data, go.Figure):
                    st.plotly_chart(msg.data, use_container_width=True)

            # Error
            if msg.msg_type == "error":
                st.error(msg.content, icon="❌")


def render_chat_input() -> str | None:
    """
    Render the chat input box.

    Returns:
        The user's query string, or None if no input.
    """
    return st.chat_input(
        placeholder="Ask a question about your data… e.g. 'Top 10 customers by revenue'",
        key="chat_input",
    )


def render_welcome_message() -> None:
    """Show an initial welcome message in the chat."""
    st.markdown(
        """
        <div style="
            text-align: center;
            padding: 60px 20px;
            color: #94a3b8;
        ">
            <div style="font-size: 56px; margin-bottom: 16px;">💬</div>
            <h2 style="
                color: #e2e8f0;
                font-weight: 700;
                margin-bottom: 8px;
            ">Ask anything about your data</h2>
            <p style="font-size: 15px; max-width: 500px; margin: 0 auto; line-height: 1.6;">
                Type a question in natural language and the AI will analyze your
                dataset, generate code, and return results with charts.
            </p>
            <div style="
                margin-top: 28px;
                display: flex;
                flex-wrap: wrap;
                justify-content: center;
                gap: 8px;
            ">
                <span style="
                    background: #1e293b;
                    border: 1px solid #334155;
                    border-radius: 20px;
                    padding: 8px 16px;
                    font-size: 13px;
                    color: #a5b4fc;
                ">📈 "Show monthly revenue trend"</span>
                <span style="
                    background: #1e293b;
                    border: 1px solid #334155;
                    border-radius: 20px;
                    padding: 8px 16px;
                    font-size: 13px;
                    color: #a5b4fc;
                ">🏆 "Top 10 customers by sales"</span>
                <span style="
                    background: #1e293b;
                    border: 1px solid #334155;
                    border-radius: 20px;
                    padding: 8px 16px;
                    font-size: 13px;
                    color: #a5b4fc;
                ">📊 "Average profit by region"</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_thinking_indicator() -> None:
    """Show a 'thinking' animation while the AI processes."""
    st.markdown(
        """
        <div style="
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 12px 16px;
            background: #1e293b;
            border-radius: 12px;
            border: 1px solid #334155;
            margin: 8px 0;
        ">
            <div class="thinking-dots">
                <span style="animation: blink 1.4s infinite 0s;">●</span>
                <span style="animation: blink 1.4s infinite 0.2s;">●</span>
                <span style="animation: blink 1.4s infinite 0.4s;">●</span>
            </div>
            <span style="color: #94a3b8; font-size: 14px;">Analyzing your data…</span>
        </div>
        <style>
            @keyframes blink {
                0%, 80%, 100% { opacity: 0.2; color: #6366f1; }
                40% { opacity: 1; color: #a78bfa; }
            }
            .thinking-dots span {
                font-size: 18px;
                margin: 0 2px;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )
