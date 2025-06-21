#!/usr/bin/env python3
"""
VMware MCP Server Entry Point

Run this to start the VMware MCP server for vCenter management.
"""

import asyncio
import subprocess
import sys
import os

def main():
    """Run the MCP server."""
    server_path = os.path.join(os.path.dirname(__file__), 'mcp-server', 'server.py')
    if not os.path.exists(server_path):
        print(f"Error: Server file not found at {server_path}")
        sys.exit(1)
    
    # Run the server directly
    subprocess.run([sys.executable, server_path])

if __name__ == "__main__":
    main()
