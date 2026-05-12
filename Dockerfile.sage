FROM sagemath/sagemath:latest

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV MCP_HOST=0.0.0.0
ENV MCP_PORT=5556
ENV MCP_PATH=/mcp
ENV MCP_SSE_PATH=/sse

USER root
WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl git \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md LICENSE ./
COPY src ./src

RUN sage -pip install --no-cache-dir .

EXPOSE 5556

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -fsS http://127.0.0.1:5556/health || exit 1

CMD ["sage", "-python", "src/server.py"]
