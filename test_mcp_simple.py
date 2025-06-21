#!/usr/bin/env python3
"""
Simple MCP server test without VMware dependencies.
"""
import asyncio
import logging
import sys

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest, CallToolResult, ListToolsRequest, ListToolsResult,
    Tool, TextContent, ListResourcesRequest, ListResourcesResult, Resource
)

# Configure logging
logging.basicConfig(level=logging.INFO)

class SimpleMCPServer:
    """Simple MCP server for testing."""
    
    def __init__(self):
        self.server = Server("simple-test-server")
        self._setup_server()
    
    def _setup_server(self):
        """Set up the MCP server with basic tools."""
        
        @self.server.list_tools()
        async def handle_list_tools() -> ListToolsResult:
            return ListToolsResult(
                tools=[
                    Tool(
                        name="hello",
                        description="Say hello"
                    )
                ]
            )
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict) -> CallToolResult:
            if name == "hello":
                return CallToolResult(
                    content=[TextContent(type="text", text="Hello from simple MCP server!")]
                )
            else:
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Unknown tool: {name}")]
                )
        
        @self.server.list_resources()
        async def handle_list_resources() -> ListResourcesResult:
            return ListResourcesResult(
                resources=[Resource(id="test", name="Test Resource", status="running", uri="http://localhost/")],
                nextCursor=None
            )
    
    async def run(self):
        """Run the MCP server."""
        try:
            async with stdio_server() as (read_stream, write_stream):
                await self.server.run(read_stream, write_stream)
        except Exception as e:
            logging.error(f"Server error: {e}")
            import traceback
            logging.error(f"Traceback: {traceback.format_exc()}")
            sys.exit(1)

async def main():
    """Main entry point."""
    server = SimpleMCPServer()
    try:
        await server.run()
    except KeyboardInterrupt:
        logging.info("Server stopped by user")
    except Exception as e:
        logging.error(f"Server error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 