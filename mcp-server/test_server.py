#!/usr/bin/env python3
"""
Test script for the VMware MCP server
"""

import subprocess
import json
import sys
from typing import Optional

def test_mcp_server():
    """Test the MCP server by sending a tool call."""
    
    # Start the MCP server process
    process = subprocess.Popen(
        [sys.executable, "server.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    try:
        # Check if process started successfully
        if process.stdin is None or process.stdout is None:
            print("Failed to start MCP server process")
            return
        
        # Send initialization
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        }
        
        process.stdin.write(json.dumps(init_request) + "\n")
        process.stdin.flush()
        
        # Read response
        response = process.stdout.readline()
        print("Init response:", response.strip())
        
        # Send list tools request
        list_tools_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list"
        }
        
        process.stdin.write(json.dumps(list_tools_request) + "\n")
        process.stdin.flush()
        
        # Read response
        response = process.stdout.readline()
        print("List tools response:", response.strip())
        
        # Send tool call
        tool_call_request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "list_vms",
                "arguments": {}
            }
        }
        
        process.stdin.write(json.dumps(tool_call_request) + "\n")
        process.stdin.flush()
        
        # Read response
        response = process.stdout.readline()
        print("Tool call response:", response.strip())
        
    except Exception as e:
        print(f"Error testing server: {e}")
    finally:
        # Clean up
        process.terminate()
        process.wait()

if __name__ == "__main__":
    print("Testing VMware MCP server...")
    test_mcp_server() 