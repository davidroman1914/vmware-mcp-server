#!/usr/bin/env python3
"""
Main entry point for ESXi MCP Server.
This is a simple wrapper around the src module.
"""
import sys
import asyncio

if __name__ == "__main__":
    # Import and run the main module
    from src.__main__ import main
    asyncio.run(main()) 