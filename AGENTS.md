# AGENTS.md

Guidance for LLM agents working on this repository.

## Project Overview

This is a Python MCP server for running Python inside Docker. It exposes Python execution and package-management tools through both streamable HTTP and SSE transports.

The server is intentionally not sandboxed. Do not add sandboxing, code restrictions, import restrictions, filesystem restrictions, or network restrictions unless explicitly requested.

## Repository Layout

- `src/server.py`: MCP tools, HTTP/SSE app creation, and entrypoint.
- `src/interpreter.py`: fresh-process Python execution helpers.
- `src/packages.py`: environment package install, runtime pip install, and package listing.
- `src/models.py`: project exception types.
- `src/utils.py`: shared validation and startup logging helpers.
- `tests/test_interpreter.py`: interpreter unit tests.
- `tests/test_packages.py`: package helper tests.
- `tests/test_mcp_live.py`: MCP stdio smoke test.
- `Dockerfile`: pure Python container image.
- `Dockerfile.sage`: SageMath container image that runs the server under Sage Python.
- `.github/workflows/docker-publish.yml`: test, build, and GHCR publish workflow.
- `README.md`: user-facing setup and tool documentation.
- `pyproject.toml`: package metadata and dependencies.

Keep the flat `src/*` module layout. Do not introduce a package directory unless explicitly requested.

## Development Commands

Use the project virtualenv when available:

```bash
.venv/bin/python -m pytest
.venv/bin/python -m compileall -q src tests
.venv/bin/mcp-python-interpreter-docker
```

If dependencies are missing, install with:

```bash
python -m venv .venv
.venv/bin/python -m pip install -e .[dev]
```

Avoid installing into the system Python environment.

## Behavior To Preserve

- Every `execute_python` call starts a fresh Python interpreter process.
- Every `execute_python_file` call starts a fresh Python interpreter process.
- Multiple executions may run concurrently.
- Package installation may be serialized to avoid concurrent pip mutations.
- Default Docker port is `5556`.
- HTTP endpoint is `/mcp` and SSE endpoint is `/sse`.
- Docker images are published to `ghcr.io/d00movenok/mcp-python-interpreter-docker` on every push to `main`.
- Pure Python image tags include `latest` and `py-latest`; SageMath image tags include `sage-latest`.

## Testing Expectations

Before finishing code changes, run:

```bash
.venv/bin/python -m compileall -q src tests
.venv/bin/python -m pytest
```

Docker build/run verification is useful but may require user approval depending on the environment.

## Coding Guidelines

- Prefer small, direct changes.
- Preserve structured MCP outputs (`dict[str, Any]`) from tools.
- Do not print to stdout from stdio mode; stdout is reserved for MCP JSON-RPC.
- Raise project exceptions from helpers and convert them to `ValueError` at MCP tool boundaries.
- Keep line lengths reasonable and code readable; no formatter is currently configured.
- Do not add backward compatibility shims unless explicitly needed.

## Git Safety

- Do not commit unless the user explicitly asks.
- Do not revert unrelated changes.
- Do not use destructive git commands unless explicitly approved.
