#!/usr/bin/env python3
"""
Simple FastMCP Server for testing
"""

from fastmcp import FastMCP

# Create the MCP server instance
mcp = FastMCP(name="Simple MCP Server")

@mcp.tool()
def hello(name: str = "World") -> str:
    """Returns a greeting."""
    return f"Hello, {name}! Greetings from FastMCP."

@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b

@mcp.tool()
def echo(message: str) -> str:
    """Echo back the message."""
    return f"You said: {message}"

if __name__ == "__main__":
    # Run with stdio transport (default)
    mcp.run() 