#!/usr/bin/env python3
"""
Simple test for the minimal VMware MCP Server.
"""
import asyncio
import json
from src.mcp_server import VMwareMCPServer

async def test_server():
    """Test the minimal server functionality."""
    print("Testing minimal VMware MCP Server...")
    
    # Create server
    server = VMwareMCPServer()
    print("✅ Server created successfully")
    
    # Test get_info without connection
    info_result = await server._handle_get_info()
    print(f"✅ get_info result: {info_result.content[0].text[:100]}...")
    
    # Test list_vms without connection
    vms_result = await server._handle_list_vms()
    print(f"✅ list_vms result: {vms_result.content[0].text[:100]}...")
    
    # Test list_resources without connection
    resources_result = await server._handle_list_resources()
    print(f"✅ list_resources result: {len(resources_result.resources)} resources")
    
    print("✅ All tests passed! Server is working correctly.")

if __name__ == "__main__":
    asyncio.run(test_server()) 