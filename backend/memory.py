# ============================================================
#  Conversational Memory
#  Maintains chat history and context for follow-up queries
#  using Streamlit session state.
# ============================================================

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Optional


@dataclass
class ConversationTurn:
    """A single turn in the conversation."""

    query: str
    code: str = ""
    result_summary: str = ""
    success: bool = True


@dataclass
class ConversationMemory:
    """
    Manages conversational history for follow-up query support.

    Stores previous queries, generated code, and results so
    that the LLM can understand context for follow-up questions.
    """

    turns: List[ConversationTurn] = field(default_factory=list)
    max_turns: int = 20

    def add_turn(
        self,
        query: str,
        code: str = "",
        result_summary: str = "",
        success: bool = True,
    ) -> None:
        """Add a new conversation turn."""
        self.turns.append(
            ConversationTurn(
                query=query,
                code=code,
                result_summary=result_summary,
                success=success,
            )
        )
        # Keep only the latest turns to manage context window
        if len(self.turns) > self.max_turns:
            self.turns = self.turns[-self.max_turns :]

    def has_history(self) -> bool:
        """Check if there is any conversation history."""
        return len(self.turns) > 0

    @property
    def last_code(self) -> Optional[str]:
        """Return the most recently generated code, if any."""
        if self.turns:
            return self.turns[-1].code
        return None

    @property
    def last_query(self) -> Optional[str]:
        """Return the most recent query."""
        if self.turns:
            return self.turns[-1].query
        return None

    def get_history_string(self, max_recent: int = 5) -> str:
        """
        Format recent conversation turns as a string for LLM context.

        Args:
            max_recent: Number of recent turns to include.

        Returns:
            Formatted conversation history.
        """
        recent = self.turns[-max_recent:]
        lines = []
        for i, turn in enumerate(recent, 1):
            status = "✓" if turn.success else "✗"
            lines.append(f"Turn {i} [{status}]: {turn.query}")
            if turn.code:
                lines.append(f"  Code: {turn.code[:200]}...")
        return "\n".join(lines)

    def clear(self) -> None:
        """Clear all conversation history."""
        self.turns.clear()


# ── Chat Message Types ───────────────────────────────────────

@dataclass
class ChatMessage:
    """A display message in the chat UI."""

    role: str  # "user" | "assistant"
    content: str
    code: Optional[str] = None
    data: Any = None  # DataFrame, Figure, etc.
    msg_type: str = "text"  # text | dataframe | chart | error | insight
