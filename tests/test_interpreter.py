from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from interpreter import execute_code, execute_file
from models import InvalidInputError


def test_execute_code_success() -> None:
    result = asyncio.run(execute_code("print('hello')"))

    assert result["exit_code"] == 0
    assert result["timed_out"] is False
    assert result["stdout"] == "hello\n"
    assert result["stderr"] == ""


def test_execute_code_reports_exception() -> None:
    result = asyncio.run(execute_code("raise RuntimeError('boom')"))

    assert result["exit_code"] != 0
    assert "RuntimeError: boom" in result["stderr"]


def test_execute_code_starts_fresh_process_each_time() -> None:
    first = asyncio.run(execute_code("x = 42\nprint(x)"))
    second = asyncio.run(execute_code("print('x' in globals())"))

    assert first["stdout"] == "42\n"
    assert second["stdout"] == "False\n"


def test_execute_code_allows_concurrent_runs() -> None:
    async def run_many() -> list[dict]:
        return await asyncio.gather(
            execute_code("import time; time.sleep(0.2); print('a')"),
            execute_code("import time; time.sleep(0.2); print('b')"),
        )

    results = asyncio.run(run_many())

    assert {item["stdout"] for item in results} == {"a\n", "b\n"}


def test_execute_code_timeout() -> None:
    result = asyncio.run(
        execute_code("import time; time.sleep(5)", timeout_seconds=0.1)
    )

    assert result["timed_out"] is True
    assert result["exit_code"] != 0


def test_execute_code_truncates_output() -> None:
    result = asyncio.run(execute_code("print('abcdef', end='')", max_output_bytes=3))

    assert result["stdout"] == "abc"
    assert result["stdout_truncated"] is True


def test_execute_python_file(tmp_path: Path) -> None:
    script = tmp_path / "script.py"
    script.write_text(
        "import sys\nprint('args=' + ','.join(sys.argv[1:]))\n",
        encoding="utf-8",
    )

    result = asyncio.run(execute_file(str(script), args=["one", "two"]))

    assert result["exit_code"] == 0
    assert result["stdout"] == "args=one,two\n"


def test_execute_file_rejects_missing_file() -> None:
    with pytest.raises(InvalidInputError):
        asyncio.run(execute_file("/does/not/exist.py"))
