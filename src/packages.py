from __future__ import annotations

import asyncio
import json
import os
import shlex
import subprocess
import sys
from typing import Any

from models import InvalidInputError, PackageInstallError
from utils import env_positive_float, log_startup, validate_positive_float
from utils import validate_positive_int


_install_lock = asyncio.Lock()


def packages_from_env() -> list[str]:
    raw = os.getenv("PYTHON_PACKAGES", "")
    if not raw.strip():
        return []
    return shlex.split(raw)


def install_env_packages() -> dict[str, Any]:
    packages = packages_from_env()
    if not packages:
        log_startup("PYTHON_PACKAGES is empty; skipping startup package install")
        return {"installed": False, "packages": [], "stdout": "", "stderr": ""}

    log_startup(f"Installing {len(packages)} startup package(s) from PYTHON_PACKAGES")
    try:
        result = _install_packages_sync(packages, timeout_seconds=_env_install_timeout())
    except Exception:
        log_startup("Startup package installation failed")
        raise

    log_startup("Startup package installation completed")
    return result


async def install_packages(
    packages: list[str],
    *,
    timeout_seconds: float = 300.0,
) -> dict[str, Any]:
    packages = _validate_packages(packages)
    timeout_seconds = validate_positive_float(timeout_seconds, "timeout_seconds")

    async with _install_lock:
        process = await asyncio.create_subprocess_exec(
            *_pip_install_command(packages),
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout_seconds,
            )
        except asyncio.TimeoutError as exc:
            process.kill()
            stdout, stderr = await process.communicate()
            raise PackageInstallError(
                "pip install timed out\n"
                + stderr.decode("utf-8", errors="replace")[:4000]
            ) from exc

    stdout_text = stdout.decode("utf-8", errors="replace")
    stderr_text = stderr.decode("utf-8", errors="replace")
    if process.returncode != 0:
        raise PackageInstallError("pip install failed\n" + stderr_text[:4000])

    return _install_result(
        packages=packages,
        exit_code=process.returncode,
        stdout=stdout_text,
        stderr=stderr_text,
    )


async def list_installed_packages(max_results: int = 10000) -> dict[str, Any]:
    max_results = validate_positive_int(max_results, "max_results")
    process = await asyncio.create_subprocess_exec(
        sys.executable,
        "-m",
        "pip",
        "list",
        "--format=json",
        stdin=asyncio.subprocess.DEVNULL,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()
    if process.returncode != 0:
        raise PackageInstallError(
            "pip list failed\n" + stderr.decode("utf-8", errors="replace")[:4000]
        )

    parsed = json.loads(stdout.decode("utf-8"))
    if not isinstance(parsed, list):
        raise PackageInstallError("pip list returned unexpected JSON")

    return {
        "count": len(parsed),
        "packages": parsed[:max_results],
        "truncated": len(parsed) > max_results,
    }


def _install_packages_sync(packages: list[str], *, timeout_seconds: float) -> dict[str, Any]:
    completed = subprocess.run(
        _pip_install_command(packages),
        check=False,
        capture_output=True,
        stdin=subprocess.DEVNULL,
        text=True,
        timeout=timeout_seconds,
    )
    if completed.returncode != 0:
        raise PackageInstallError("pip install failed\n" + completed.stderr[:4000])
    return _install_result(
        packages=packages,
        exit_code=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )


def _pip_install_command(packages: list[str]) -> list[str]:
    return [sys.executable, "-m", "pip", "install", "--no-cache-dir", *packages]


def _install_result(
    *,
    packages: list[str],
    exit_code: int,
    stdout: str,
    stderr: str,
) -> dict[str, Any]:
    return {
        "installed": True,
        "packages": packages,
        "exit_code": exit_code,
        "stdout": stdout,
        "stderr": stderr,
    }


def _env_install_timeout() -> float:
    return env_positive_float("PYTHON_PACKAGES_INSTALL_TIMEOUT_SECONDS", 300.0)


def _validate_packages(value: list[str]) -> list[str]:
    if not isinstance(value, list):
        raise InvalidInputError("packages must be a list of package specifiers")
    packages = [str(item).strip() for item in value if str(item).strip()]
    if not packages:
        raise InvalidInputError("packages must not be empty")
    return packages
