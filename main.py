#!/usr/bin/env python3
"""
Minimal VMware MCP Server entry point.
"""
import asyncio
import logging
import sys

from src.mcp_server import VMwareMCPServer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def main():
    """Main entry point."""
    server = VMwareMCPServer()
    try:
        await server.run()
    except KeyboardInterrupt:
        logging.info("Server stopped by user")
    except Exception as e:
        logging.error(f"Server error: {e}")
        sys.exit(1)
    finally:
        server.cleanup()

if __name__ == "__main__":
    asyncio.run(main()) 