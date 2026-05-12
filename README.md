# MCP Python Interpreter Docker

MCP server for running Python inside a Docker container.

> ⚠️ Be careful, completely vibe-coded ⚠️
>
> (but manually verified)

> ⚠️ Warning: this server is intentionally not sandboxed. ⚠️
>
> Python code runs with the normal permissions of the container process. Use it only with trusted clients and treat Docker as the isolation boundary.

## Tools

- `execute_python(code, timeout_seconds=None, max_output_bytes=200000)`
  - Runs Python code in a fresh interpreter process.
  - Returns exit code, timeout flag, duration, stdout, stderr, and truncation flags.
- `execute_python_file(path, args=None, timeout_seconds=None, max_output_bytes=200000)`
  - Runs a Python file in a fresh interpreter process.
  - Passes optional command-line arguments to the file.
  - Returns exit code, timeout flag, duration, stdout, stderr, and truncation flags.
- `install_packages(packages, timeout_seconds=300)`
  - Installs packages with `pip install --no-cache-dir` inside the running container.
- `list_installed_packages(max_results=10000)`
  - Lists installed packages using `pip list --format=json`.
- `python_environment()`
  - Returns Python executable/version, platform, cwd, MCP paths, and package environment.

Each Python execution starts a new interpreter. Multiple executions can run concurrently.

## Install

### Docker (recommended)

```bash
docker run --rm -p 5556:5556 \
  -e PYTHON_PACKAGES="numpy pandas requests" \
  ghcr.io/d00movenok/mcp-python-interpreter-docker:py-latest
```

SageMath image:

```bash
docker run --rm -p 5556:5556 \
  ghcr.io/d00movenok/mcp-python-interpreter-docker:sage-latest
```

The `latest` tag is kept as an alias for the pure Python image. Use `py-latest` or `sage-latest` when you want the variant to be explicit.

Endpoints:

- Streamable HTTP: `http://127.0.0.1:5556/mcp`
- SSE: `http://127.0.0.1:5556/sse`
- Healthcheck: `http://127.0.0.1:5556/health`

The container installs `PYTHON_PACKAGES` before starting the MCP HTTP/SSE service. Startup progress is written to stderr. If startup package installation fails, the process exits and the service never becomes healthy.

### Local

With pipx:

```bash
pipx install git+https://github.com/D00Movenok/mcp-python-interpreter-docker.git
```

With uv:

```bash
uv pip install git+https://github.com/D00Movenok/mcp-python-interpreter-docker.git
```

Or with a virtualenv:

```bash
git clone https://github.com/D00Movenok/mcp-python-interpreter-docker.git
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Configuration

Environment variables:

- `MCP_HOST` (default: `0.0.0.0`)
- `MCP_PORT` (default: `5556`)
- `MCP_PATH` (default: `/mcp`)
- `MCP_SSE_PATH` (default: `/sse`)
- `MCP_MESSAGE_PATH` (default: `/messages/`)
- `MCP_TRANSPORT` (default: `http-sse`, also supports `stdio`)
- `PYTHON_PACKAGES` (optional package specifiers installed at startup)
- `PYTHON_PACKAGES_INSTALL_TIMEOUT_SECONDS` (default: `300`)
- `PYTHON_EXEC_TIMEOUT_SECONDS` (default: `60`)

Package specs in `PYTHON_PACKAGES` are parsed with shell-like quoting:

```bash
PYTHON_PACKAGES="numpy 'git+https://github.com/org/repo.git'"
```

Use standard pip environment variables for private indexes:

- `PIP_INDEX_URL`
- `PIP_EXTRA_INDEX_URL`
- `PIP_TRUSTED_HOST`

## Claude Code MCP Config Example

Streamable HTTP:

```bash
claude mcp add --transport http python-docker http://127.0.0.1:5556/mcp
```

SSE:

```bash
claude mcp add --transport sse python-docker http://127.0.0.1:5556/sse
```

Stdio with pipx-installed command:

```bash
claude mcp add python-docker -- mcp-python-interpreter-docker
```

## Claude Desktop MCP Config Examples

Streamable HTTP, with the Docker container already running:

```json
{
  "mcpServers": {
    "python-docker": {
      "type": "http",
      "url": "http://127.0.0.1:5556/mcp"
    }
  }
}
```

Stdio with pipx-installed command:

```json
{
  "mcpServers": {
    "python-docker": {
      "command": "mcp-python-interpreter-docker",
      "env": {
        "MCP_TRANSPORT": "stdio",
        "PYTHON_PACKAGES": "numpy pandas requests"
      }
    }
  }
}
```
