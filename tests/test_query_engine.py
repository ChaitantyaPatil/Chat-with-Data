# ============================================================
#  Tests — Code Executor (Safety Validation)
# ============================================================

from __future__ import annotations

import pandas as pd
import pytest

from llm.code_executor import (
    CodeExecutionError,
    CodeValidationError,
    execute_code,
    validate_code,
)


class TestValidateCode:
    """Tests for the code validation / safety layer."""

    def test_valid_pandas_code(self) -> None:
        code = "result = df.head(10)"
        cleaned = validate_code(code)
        assert "result" in cleaned

    def test_blocks_os_import(self) -> None:
        with pytest.raises(CodeValidationError, match="Blocked unsafe pattern"):
            validate_code("import os\nos.listdir('.')")

    def test_blocks_subprocess(self) -> None:
        with pytest.raises(CodeValidationError, match="Blocked unsafe pattern"):
            validate_code("import subprocess\nsubprocess.run(['ls'])")

    def test_blocks_exec(self) -> None:
        with pytest.raises(CodeValidationError, match="Blocked unsafe pattern"):
            validate_code("exec('print(1)')")

    def test_blocks_eval(self) -> None:
        with pytest.raises(CodeValidationError, match="Blocked unsafe pattern"):
            validate_code("result = eval('1+1')")

    def test_blocks_open(self) -> None:
        with pytest.raises(CodeValidationError, match="Blocked unsafe pattern"):
            validate_code("f = open('/etc/passwd', 'r')")

    def test_blocks_sys(self) -> None:
        with pytest.raises(CodeValidationError, match="Blocked unsafe pattern"):
            validate_code("import sys\nsys.exit()")

    def test_blocks_dunder_import(self) -> None:
        with pytest.raises(CodeValidationError, match="Blocked unsafe pattern"):
            validate_code("__import__('os').system('rm -rf /')")

    def test_strips_markdown_fences(self) -> None:
        code = "```python\nresult = df.head(5)\n```"
        cleaned = validate_code(code)
        assert "```" not in cleaned
        assert "result" in cleaned

    def test_empty_code_raises(self) -> None:
        with pytest.raises(CodeValidationError, match="empty"):
            validate_code("")

    def test_blocks_unauthorized_import(self) -> None:
        with pytest.raises(CodeValidationError, match="Unauthorized import"):
            validate_code("import requests\nresult = requests.get('http://evil.com')")


class TestExecuteCode:
    """Tests for safe code execution."""

    def test_basic_pandas_operation(self) -> None:
        df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
        result = execute_code("result = df['a'].sum()", df)
        assert result == 6

    def test_returns_dataframe(self) -> None:
        df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
        result = execute_code("result = df[df['a'] > 1]", df)
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2

    def test_does_not_mutate_original(self) -> None:
        df = pd.DataFrame({"a": [1, 2, 3]})
        original_len = len(df)
        execute_code("df.drop(index=0, inplace=True)\nresult = df", df)
        assert len(df) == original_len  # Original is untouched

    def test_numpy_available(self) -> None:
        df = pd.DataFrame({"a": [1, 4, 9]})
        result = execute_code("result = np.sqrt(df['a']).tolist()", df)
        assert result == [1.0, 2.0, 3.0]

    def test_execution_error_raises(self) -> None:
        df = pd.DataFrame({"a": [1, 2, 3]})
        with pytest.raises(CodeExecutionError):
            execute_code("result = df['nonexistent_column'].sum()", df)
