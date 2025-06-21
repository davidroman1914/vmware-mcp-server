#!/usr/bin/env python3
"""
Minimal VMware MCP Server entry point.
"""
import asyncio
import logging
import sys

from src.mcp_server import run_server

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def main():
    """Main entry point."""
    await run_server()

if __name__ == "__main__":
    asyncio.run(main()) 