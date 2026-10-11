#!/usr/bin/env python3
"""Minimal MCP server test"""
from mcp.server import MCPServer

# Create server
mcp = MCPServer("Test Server")

@mcp.tool()
def hello(name: str) -> str:
    """Say hello"""
    return f"Hello, {name}!"

if __name__ == "__main__":
    mcp.run()
