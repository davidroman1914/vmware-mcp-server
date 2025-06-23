#!/usr/bin/env python3
"""
Simple MCP client to test our VMware MCP server
"""

import json
import subprocess
import sys

def test_mcp_server():
    """Test the MCP server with basic protocol messages."""
    
    # Start the server process
    process = subprocess.Popen(
        ["python", "mcp-server/server.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    try:
        # Test 1: Initialize
        print("=== Testing Initialize ===")
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-03-26",
                "capabilities": {},
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        }
        
        print(f"Sending: {json.dumps(init_request)}")
        process.stdin.write(json.dumps(init_request) + "\n")
        process.stdin.flush()
        
        # Read response
        response = process.stdout.readline()
        print(f"Received: {response.strip()}")
        
        # Test 2: Tools List
        print("\n=== Testing Tools List ===")
        tools_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
        
        print(f"Sending: {json.dumps(tools_request)}")
        process.stdin.write(json.dumps(tools_request) + "\n")
        process.stdin.flush()
        
        # Read response
        response = process.stdout.readline()
        print(f"Received: {response.strip()}")
        
        print("\n=== Test Complete ===")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Clean up
        process.terminate()
        process.wait()

if __name__ == "__main__":
    test_mcp_server() 