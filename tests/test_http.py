#!/usr/bin/env python3
"""Test the MCP server using streamable HTTP transport."""

import asyncio
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

PACKAGE_NAME = "bouncer"
SERVER_URL = "http://localhost:8000/mcp"


def get_project_root() -> Path:
    current = Path(__file__).parent.resolve()
    while current != current.parent:
        if (current / "pyproject.toml").exists():
            return current
        current = current.parent
    raise RuntimeError("Could not find project root (no pyproject.toml found)")


def load_env():
    root = get_project_root()
    env_file = root / ".env"
    if not env_file.exists():
        raise FileNotFoundError(
            f".env file not found at {env_file}\n"
            "Copy env.example to .env and fill in your credentials."
        )
    load_dotenv(env_file)
    return root


class ServerProcess:
    """Context manager that starts and stops the MCP server."""

    def __init__(self, root: Path, port: int = 8000):
        self.root = root
        self.port = port
        self.process: subprocess.Popen | None = None

    def __enter__(self):
        env = {**os.environ, "ENVIRONMENT": "local", "PORT": str(self.port)}
        self.process = subprocess.Popen(
            [sys.executable, "-m", f"{PACKAGE_NAME}.server"],
            cwd=str(self.root),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        time.sleep(3)
        return self

    def __exit__(self, *args):
        if self.process:
            self.process.send_signal(signal.SIGTERM)
            self.process.wait(timeout=5)


async def test_http():
    print("Connecting to server via streamable HTTP...")

    async with streamablehttp_client(SERVER_URL) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("Connected and initialized\n")

            tools_response = await session.list_tools()
            print("Available tools:")
            for tool in tools_response.tools:
                print(f"   - {tool.name}: {tool.description}")
            print()

            print("Testing verify_email...")
            result = await session.call_tool(
                "verify_email",
                {"email": "deliverable@sandbox.usebouncer.com"},
            )
            print(f"   Result: {result.content}")
            print()

            print("Testing check_credits...")
            result = await session.call_tool("check_credits", {})
            print(f"   Result: {result.content}")
            print()

            print("All tests passed!")


def main():
    root = load_env()
    with ServerProcess(root, port=8000):
        asyncio.run(test_http())


if __name__ == "__main__":
    main()
