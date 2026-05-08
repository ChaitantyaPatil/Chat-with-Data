# ============================================================
#  Safe Code Executor
#  Validates and executes AI-generated Pandas code in a
#  restricted sandbox. Blocks dangerous operations.
# ============================================================

from __future__ import annotations

import re
from typing import Any

import numpy as np
import pandas as pd

from utils.logger import get_logger

logger = get_logger(__name__)

# ── Blocked patterns ─────────────────────────────────────────
# These patterns are NEVER allowed in generated code.
BLOCKED_PATTERNS: list[str] = [
    r"\bimport\s+os\b",
    r"\bimport\s+sys\b",
    r"\bimport\s+subprocess\b",
    r"\bimport\s+shutil\b",
    r"\bfrom\s+os\b",
    r"\bfrom\s+sys\b",
    r"\bfrom\s+subprocess\b",
    r"\bfrom\s+shutil\b",
    r"\b__import__\s*\(",
    r"\bexec\s*\(",
    r"\beval\s*\(",
    r"\bopen\s*\(",
    r"\bglobals\s*\(",
    r"\blocals\s*\(",
    r"\bcompile\s*\(",
    r"\bgetattr\s*\(",
    r"\bsetattr\s*\(",
    r"\bdelattr\s*\(",
    r"\bbreakpoint\s*\(",
    r"\bos\.\w+",
    r"\bsys\.\w+",
    r"\bsubprocess\.\w+",
    r"\bshutil\.\w+",
    r"\b__builtins__",
    r"\b__class__",
    r"\b__subclasses__",
]

# Compiled regex for performance
_BLOCKED_RE = re.compile("|".join(BLOCKED_PATTERNS), re.IGNORECASE)


class CodeValidationError(Exception):
    """Raised when generated code fails safety validation."""

    pass


class CodeExecutionError(Exception):
    """Raised when validated code fails during execution."""

    pass


def validate_code(code: str) -> str:
    """
    Validate that AI-generated code is safe to execute.

    Args:
        code: The Python code string to validate.

    Returns:
        The cleaned code string if validation passes.

    Raises:
        CodeValidationError: If dangerous patterns are detected.
    """
    if not code or not code.strip():
        raise CodeValidationError("Generated code is empty.")

    # Strip markdown code fences if the LLM wrapped them
    cleaned = code.strip()
    if cleaned.startswith("```python"):
        cleaned = cleaned[len("```python") :]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()

    # Check for blocked patterns
    match = _BLOCKED_RE.search(cleaned)
    if match:
        raise CodeValidationError(
            f"Blocked unsafe pattern detected: '{match.group()}'. "
            "Only pandas and numpy operations are allowed."
        )

    # Block generic import statements (allow only pandas/numpy aliases already provided)
    import_lines = re.findall(r"^\s*(?:import|from)\s+\S+", cleaned, re.MULTILINE)
    for imp in import_lines:
        # Allow: import pandas, import numpy (though they shouldn't need to)
        if not re.search(r"\b(pandas|numpy|pd|np)\b", imp):
            raise CodeValidationError(
                f"Unauthorized import detected: '{imp.strip()}'. "
                "Only pandas (pd) and numpy (np) are available."
            )

    logger.info("Code validation passed (%d chars).", len(cleaned))
    return cleaned


def execute_code(code: str, df: pd.DataFrame) -> Any:
    """
    Execute validated code in a restricted sandbox.

    The sandbox provides:
      - ``df``: the user's DataFrame
      - ``pd``: pandas
      - ``np``: numpy

    Args:
        code: Validated Python code string.
        df: The DataFrame to operate on.

    Returns:
        The ``result`` variable from the executed code, or ``None``
        if no result variable was set.

    Raises:
        CodeExecutionError: If execution fails at runtime.
    """
    # First, validate
    clean_code = validate_code(code)

    # Prepare restricted namespace
    sandbox_globals: dict[str, Any] = {
        "__builtins__": {},  # Remove all builtins
        "pd": pd,
        "np": np,
        "df": df.copy(),  # Work on a copy to prevent mutation
    }

    # Re-add only safe builtins
    safe_builtins = [
        "len", "range", "enumerate", "zip", "map", "filter",
        "sorted", "reversed", "min", "max", "sum", "abs",
        "round", "int", "float", "str", "bool", "list",
        "dict", "tuple", "set", "type", "isinstance",
        "True", "False", "None", "print",
    ]
    import builtins
    for name in safe_builtins:
        if hasattr(builtins, name):
            sandbox_globals["__builtins__"][name] = getattr(builtins, name)

    sandbox_locals: dict[str, Any] = {}

    try:
        exec(clean_code, sandbox_globals, sandbox_locals)  # noqa: S102
    except Exception as exc:
        logger.error("Code execution failed: %s", exc)
        raise CodeExecutionError(f"Execution error: {exc}") from exc

    result = sandbox_locals.get("result")
    if result is None:
        logger.warning("No 'result' variable found in executed code.")

    return result
