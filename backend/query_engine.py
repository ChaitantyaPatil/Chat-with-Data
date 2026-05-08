# ============================================================
#  Query Engine — LangGraph Agent
#  Orchestrates: user query → LLM code gen → validation →
#  safe execution → result formatting.
# ============================================================

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Optional

import pandas as pd
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph import END, StateGraph

from backend.memory import ConversationMemory
from backend.schema_detector import SchemaInfo, get_dtype_summary
from llm.code_executor import (
    CodeExecutionError,
    CodeValidationError,
    execute_code,
)
from llm.llm_client import get_llm
from llm.prompt_templates import FOLLOWUP_QUERY_PROMPT, QUERY_TO_CODE_PROMPT
from utils.logger import get_logger

logger = get_logger(__name__)


# ── Result Container ─────────────────────────────────────────

@dataclass
class QueryResult:
    """Container for the result of a natural language query."""

    query: str
    generated_code: str = ""
    result_data: Any = None
    result_type: str = "text"  # text | dataframe | scalar
    error: Optional[str] = None
    success: bool = False

    @property
    def has_dataframe(self) -> bool:
        return isinstance(self.result_data, pd.DataFrame)


# ── LangGraph State ──────────────────────────────────────────

class QueryState(dict):
    """State dictionary for the LangGraph query pipeline."""
    pass


def _build_query_graph() -> StateGraph:
    """
    Build the LangGraph state graph for query processing.

    Flow:
        generate_code → validate_code → execute_code → format_result
    """
    graph = StateGraph(dict)

    # ── Nodes ─────────────────────────────────────────────
    graph.add_node("generate_code", _node_generate_code)
    graph.add_node("validate_and_execute", _node_validate_and_execute)
    graph.add_node("format_result", _node_format_result)
    graph.add_node("handle_error", _node_handle_error)

    # ── Edges ─────────────────────────────────────────────
    graph.set_entry_point("generate_code")
    graph.add_edge("generate_code", "validate_and_execute")
    graph.add_conditional_edges(
        "validate_and_execute",
        lambda state: "error" if state.get("error") else "success",
        {"error": "handle_error", "success": "format_result"},
    )
    graph.add_edge("format_result", END)
    graph.add_edge("handle_error", END)

    return graph


def _node_generate_code(state: dict) -> dict:
    """Generate Pandas code from the user's natural language query."""
    llm = get_llm()
    schema: SchemaInfo = state["schema"]
    query: str = state["query"]
    memory: ConversationMemory = state["memory"]

    # Choose prompt based on whether there is prior context
    if memory.has_history():
        prompt = FOLLOWUP_QUERY_PROMPT.format(
            schema=schema.to_llm_string(),
            history=memory.get_history_string(),
            previous_code=memory.last_code or "None",
            query=query,
        )
    else:
        prompt = QUERY_TO_CODE_PROMPT.format(
            schema=schema.to_llm_string(),
            sample=state.get("sample", ""),
            dtypes=state.get("dtypes", ""),
            query=query,
        )

    logger.info("Sending query to LLM: %s", query[:100])

    response = llm.invoke([HumanMessage(content=prompt)] if isinstance(prompt, str) else prompt.to_messages())
    code = response.content.strip()

    state["generated_code"] = code
    logger.info("LLM generated code (%d chars).", len(code))
    return state


def _node_validate_and_execute(state: dict) -> dict:
    """Validate and safely execute the generated code."""
    code: str = state["generated_code"]
    df: pd.DataFrame = state["df"]

    try:
        result = execute_code(code, df)
        state["result_data"] = result
        state["error"] = None
        logger.info("Code executed successfully.")
    except (CodeValidationError, CodeExecutionError) as exc:
        state["error"] = str(exc)
        state["result_data"] = None
        logger.warning("Code validation/execution failed: %s", exc)

    return state


def _node_format_result(state: dict) -> dict:
    """Determine the result type and format it."""
    result = state.get("result_data")

    if isinstance(result, pd.DataFrame):
        state["result_type"] = "dataframe"
    elif isinstance(result, (int, float, str, bool)):
        state["result_type"] = "scalar"
    elif isinstance(result, pd.Series):
        # Convert Series to DataFrame for display
        state["result_data"] = result.to_frame(name="Result")
        state["result_type"] = "dataframe"
    else:
        state["result_type"] = "text"
        if result is not None:
            state["result_data"] = str(result)

    return state


def _node_handle_error(state: dict) -> dict:
    """Package the error for user display."""
    state["result_type"] = "error"
    return state


# ── Public API ───────────────────────────────────────────────

# Build the graph once (module-level)
_query_graph = _build_query_graph().compile()


def run_query(
    query: str,
    df: pd.DataFrame,
    schema: SchemaInfo,
    memory: ConversationMemory,
) -> QueryResult:
    """
    Execute a natural language query against a DataFrame.

    Args:
        query: The user's question in natural language.
        df: The target DataFrame.
        schema: Pre-computed schema information.
        memory: Conversational memory for follow-up support.

    Returns:
        A :class:`QueryResult` with the answer.
    """
    initial_state = {
        "query": query,
        "df": df,
        "schema": schema,
        "memory": memory,
        "sample": df.head(3).to_string(),
        "dtypes": get_dtype_summary(df),
        "generated_code": "",
        "result_data": None,
        "result_type": "text",
        "error": None,
    }

    # Run the LangGraph pipeline
    final_state = _query_graph.invoke(initial_state)

    result = QueryResult(
        query=query,
        generated_code=final_state.get("generated_code", ""),
        result_data=final_state.get("result_data"),
        result_type=final_state.get("result_type", "text"),
        error=final_state.get("error"),
        success=final_state.get("error") is None,
    )

    # Update conversational memory
    memory.add_turn(
        query=query,
        code=result.generated_code,
        success=result.success,
    )

    return result
