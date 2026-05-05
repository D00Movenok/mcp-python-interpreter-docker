from __future__ import annotations

import asyncio
import os
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def _run_live_checks() -> None:
    params = StdioServerParameters(
        command=sys.executable,
        args=["src/server.py"],
        env={
            "MCP_TRANSPORT": "stdio",
            "PYTHONPATH": os.environ.get("PYTHONPATH", ""),
        },
    )

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            init_result = await session.initialize()
            assert init_result.serverInfo.name == "python-interpreter-docker"

            tools = await session.list_tools()
            tool_names = {tool.name for tool in tools.tools}
            assert "execute_python" in tool_names
            assert "execute_python_file" in tool_names
            assert "install_packages" in tool_names
            assert "list_installed_packages" in tool_names
            assert "python_environment" in tool_names
            assert "reset_interpreter" not in tool_names

            result = await session.call_tool("execute_python", {"code": "print(2 + 2)"})
            structured = result.structuredContent
            assert isinstance(structured, dict)
            assert structured["exit_code"] == 0
            assert structured["stdout"] == "4\n"

            env_result = await session.call_tool("python_environment", {})
            env_structured = env_result.structuredContent
            assert isinstance(env_structured, dict)
            assert env_structured["mcp_port"] == 5556
            assert env_structured["mcp_path"] == "/mcp"
            assert env_structured["mcp_sse_path"] == "/sse"


def test_mcp_live_end_to_end() -> None:
    asyncio.run(_run_live_checks())
