from __future__ import annotations

import contextlib
import os
from collections.abc import Awaitable
from typing import Any

import uvicorn
from mcp.server.fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route

from interpreter import DEFAULT_MAX_OUTPUT_BYTES, execute_code, execute_file, environment
from models import PythonInterpreterError
from packages import install_env_packages, install_packages as pip_install_packages
from packages import list_installed_packages as pip_list_installed_packages
from utils import log_startup


DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 5556
_startup_packages_ready = False
_startup_package_result: dict[str, Any] | None = None
_startup_package_error: str | None = None

mcp = FastMCP(
    "python-interpreter-docker",
    host=os.getenv("MCP_HOST", DEFAULT_HOST),
    port=int(os.getenv("MCP_PORT", str(DEFAULT_PORT))),
    streamable_http_path=os.getenv("MCP_PATH", "/mcp"),
    sse_path=os.getenv("MCP_SSE_PATH", "/sse"),
    message_path=os.getenv("MCP_MESSAGE_PATH", "/messages/"),
    stateless_http=True,
    json_response=True,
)


@mcp.tool()
async def execute_python(
    code: str,
    timeout_seconds: float | None = None,
    max_output_bytes: int = DEFAULT_MAX_OUTPUT_BYTES,
) -> dict[str, Any]:
    """Execute Python code in a fresh interpreter process.

    This is intentionally not sandboxed. Use only with trusted clients.

    Args:
        code: Python source code passed to python -c.
        timeout_seconds: Optional execution timeout. Defaults to env or 60.
        max_output_bytes: Maximum bytes returned for each output stream.
    """
    return await _tool_call(
        execute_code(
            code,
            timeout_seconds=timeout_seconds,
            max_output_bytes=max_output_bytes,
        )
    )


@mcp.tool()
async def execute_python_file(
    path: str,
    args: list[str] | None = None,
    timeout_seconds: float | None = None,
    max_output_bytes: int = DEFAULT_MAX_OUTPUT_BYTES,
) -> dict[str, Any]:
    """Execute a Python file in a fresh interpreter process.

    This is intentionally not sandboxed. Use only with trusted clients.

    Args:
        path: Path to a Python file inside the container.
        args: Optional command-line arguments passed to the file.
        timeout_seconds: Optional execution timeout. Defaults to env or 60.
        max_output_bytes: Maximum bytes returned for each output stream.
    """
    return await _tool_call(
        execute_file(
            path,
            args=args,
            timeout_seconds=timeout_seconds,
            max_output_bytes=max_output_bytes,
        )
    )


@mcp.tool()
async def install_packages(
    packages: list[str],
    timeout_seconds: float = 300,
) -> dict[str, Any]:
    """Install Python packages with pip inside the container.

    Args:
        packages: Package specifiers accepted by pip install.
        timeout_seconds: pip install timeout.
    """
    return await _tool_call(
        pip_install_packages(packages, timeout_seconds=timeout_seconds)
    )


@mcp.tool()
async def list_installed_packages(max_results: int = 10000) -> dict[str, Any]:
    """List installed Python packages from pip."""
    return await _tool_call(pip_list_installed_packages(max_results=max_results))


@mcp.tool()
def python_environment() -> dict[str, Any]:
    """Return Python and MCP server environment information."""
    data = environment()
    data.update(
        {
            "mcp_host": mcp.settings.host,
            "mcp_port": mcp.settings.port,
            "mcp_path": mcp.settings.streamable_http_path,
            "mcp_sse_path": mcp.settings.sse_path,
        }
    )
    return data


def create_app() -> Starlette:
    streamable_app = mcp.streamable_http_app()
    sse_app = mcp.sse_app("/")

    @contextlib.asynccontextmanager
    async def lifespan(app: Starlette):
        async with mcp.session_manager.run():
            yield

    return Starlette(
        debug=mcp.settings.debug,
        routes=[Route("/health", health_check), *streamable_app.routes, *sse_app.routes],
        lifespan=lifespan,
    )


async def _tool_call(operation: Awaitable[dict[str, Any]]) -> dict[str, Any]:
    try:
        return await operation
    except PythonInterpreterError as exc:
        raise ValueError(str(exc)) from exc


async def health_check(request) -> JSONResponse:
    if not _startup_packages_ready:
        return JSONResponse(
            {
                "status": "starting",
                "packages_ready": False,
                "error": _startup_package_error,
            },
            status_code=503,
        )

    package_count = len((_startup_package_result or {}).get("packages", []))
    return JSONResponse(
        {
            "status": "ok",
            "packages_ready": True,
            "startup_package_count": package_count,
        }
    )


def install_startup_packages() -> None:
    global _startup_package_error, _startup_package_result, _startup_packages_ready

    _startup_packages_ready = False
    _startup_package_error = None
    try:
        _startup_package_result = install_env_packages()
    except Exception as exc:
        _startup_package_result = None
        _startup_package_error = str(exc)
        log_startup(f"Exiting because startup package installation failed: {exc}")
        raise SystemExit(1) from exc

    _startup_packages_ready = True


def run_http_server() -> None:
    install_startup_packages()
    uvicorn.run(
        create_app(),
        host=mcp.settings.host,
        port=mcp.settings.port,
        log_level=mcp.settings.log_level.lower(),
    )


def main() -> None:
    transport = os.getenv("MCP_TRANSPORT", "http-sse")
    if transport == "stdio":
        install_startup_packages()
        mcp.run(transport="stdio")
        return
    if transport not in {"http-sse", "http", "streamable-http"}:
        raise ValueError(
            "MCP_TRANSPORT must be http-sse, http, streamable-http, or stdio"
        )
    run_http_server()


if __name__ == "__main__":
    main()
