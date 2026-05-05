from __future__ import annotations

import asyncio
import os
import platform
import sys
import time
from pathlib import Path
from typing import Any

from models import InvalidInputError
from utils import decode_limited, env_positive_float, validate_positive_float
from utils import validate_positive_int


DEFAULT_TIMEOUT_SECONDS = 60.0
DEFAULT_MAX_OUTPUT_BYTES = 20000


async def execute_code(
    code: str,
    *,
    timeout_seconds: float | None = None,
    max_output_bytes: int = DEFAULT_MAX_OUTPUT_BYTES,
) -> dict[str, Any]:
    code = _validate_code(code)
    timeout_seconds = _validate_timeout(timeout_seconds)
    max_output_bytes = validate_positive_int(max_output_bytes, "max_output_bytes")

    return await _run_python(
        ["-c", code],
        timeout_seconds=timeout_seconds,
        max_output_bytes=max_output_bytes,
    )


async def execute_file(
    path: str,
    *,
    args: list[str] | None = None,
    timeout_seconds: float | None = None,
    max_output_bytes: int = DEFAULT_MAX_OUTPUT_BYTES,
) -> dict[str, Any]:
    path = _validate_file_path(path)
    args = _validate_args(args)
    timeout_seconds = _validate_timeout(timeout_seconds)
    max_output_bytes = validate_positive_int(max_output_bytes, "max_output_bytes")

    return await _run_python(
        [path, *args],
        timeout_seconds=timeout_seconds,
        max_output_bytes=max_output_bytes,
    )


def environment() -> dict[str, Any]:
    return {
        "python_version": sys.version,
        "python_executable": sys.executable,
        "platform": platform.platform(),
        "cwd": os.getcwd(),
        "pid": os.getpid(),
        "default_timeout_seconds": DEFAULT_TIMEOUT_SECONDS,
        "default_max_output_bytes": DEFAULT_MAX_OUTPUT_BYTES,
        "packages_env": os.getenv("PYTHON_PACKAGES", ""),
    }


async def _run_python(
    python_args: list[str],
    *,
    timeout_seconds: float,
    max_output_bytes: int,
) -> dict[str, Any]:
    started = time.monotonic()
    process = await asyncio.create_subprocess_exec(
        sys.executable,
        *python_args,
        stdin=asyncio.subprocess.DEVNULL,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    timed_out = False
    try:
        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=timeout_seconds,
        )
    except asyncio.TimeoutError:
        timed_out = True
        process.kill()
        stdout, stderr = await process.communicate()

    duration_seconds = time.monotonic() - started
    stdout_text, stdout_truncated = decode_limited(stdout, max_output_bytes)
    stderr_text, stderr_truncated = decode_limited(stderr, max_output_bytes)

    return {
        "exit_code": process.returncode,
        "timed_out": timed_out,
        "duration_seconds": duration_seconds,
        "stdout": stdout_text,
        "stderr": stderr_text,
        "stdout_truncated": stdout_truncated,
        "stderr_truncated": stderr_truncated,
    }


def _validate_code(value: str) -> str:
    if not isinstance(value, str) or not value:
        raise InvalidInputError("code must be a non-empty string")
    return value


def _validate_file_path(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise InvalidInputError("path must be a non-empty string")

    path = Path(value).expanduser()
    if not path.is_file():
        raise InvalidInputError(f"Python file does not exist: {value}")
    return str(path)


def _validate_args(value: list[str] | None) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise InvalidInputError("args must be a list of strings")
    return [str(item) for item in value]


def _validate_timeout(value: float | None) -> float:
    if value is None:
        return env_positive_float("PYTHON_EXEC_TIMEOUT_SECONDS", DEFAULT_TIMEOUT_SECONDS)
    return validate_positive_float(value, "timeout_seconds")
