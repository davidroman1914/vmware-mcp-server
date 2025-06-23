#!/usr/bin/env python3
"""
Test script to verify MCP server VM creation integration
"""

import os
import sys
import json
import subprocess
import time

def test_mcp_vm_creation():
    """Test VM creation through MCP server"""
    
    # Test arguments for creating a VM via MCP
    vm_creation_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "create_custom_vm",
            "arguments": {
                "template_name": "Ubuntu-Template-01",
                "vm_name": "mcp-test-vm-001",
                "hostname": "mcp-test-vm-001",
                "ip_address": "10.60.132.106",
                "netmask": "255.255.255.0",
                "gateway": "10.60.132.1",
                "network_name": "PROD VMs",
                "cpu_count": 2,
                "memory_gb": 4,
                "disk_size_gb": 50
            }
        }
    }
    
    print("🧪 Testing MCP Server VM Creation")
    print("=" * 50)
    print("📋 VM Creation Request:")
    print(f"   Template: Ubuntu-Template-01")
    print(f"   VM Name: mcp-test-vm-001")
    print(f"   IP: 10.60.132.106")
    print(f"   Memory: 4 GB")
    print(f"   CPU: 2 cores")
    print(f"   Disk: 50 GB")
    print(f"   Network: PROD VMs")
    print()
    
    # Start the MCP server process
    print("🚀 Starting MCP server...")
    process = subprocess.Popen(
        ["python", "mcp-server/server.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=os.environ.copy()
    )
    
    try:
        # Wait a moment for server to start
        time.sleep(2)
        
        # Send initialize request
        print("📡 Sending initialize request...")
        init_request = {
            "jsonrpc": "2.0",
            "id": 0,
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
        
        # Read initialize response
        init_response = process.stdout.readline()
        print(f"✅ Initialize response: {init_response.strip()}")
        
        # Send tools/list request
        print("📡 Sending tools/list request...")
        tools_list_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
        
        process.stdin.write(json.dumps(tools_list_request) + "\n")
        process.stdin.flush()
        
        # Read tools/list response
        tools_response = process.stdout.readline()
        print(f"✅ Tools list response: {tools_response.strip()}")
        
        # Send VM creation request
        print("📡 Sending VM creation request...")
        process.stdin.write(json.dumps(vm_creation_request) + "\n")
        process.stdin.flush()
        
        # Read VM creation response
        vm_response = process.stdout.readline()
        print(f"✅ VM creation response: {vm_response.strip()}")
        
        # Parse the response
        try:
            response_data = json.loads(vm_response)
            if "result" in response_data:
                print("\n🎉 MCP VM creation successful!")
                print("📊 Response details:")
                result_content = response_data["result"]["content"][0]["text"]
                result_data = json.loads(result_content)
                print(json.dumps(result_data, indent=2))
            else:
                print("\n❌ MCP VM creation failed!")
                print("📊 Error details:")
                print(json.dumps(response_data, indent=2))
        except json.JSONDecodeError:
            print(f"\n❌ Failed to parse response: {vm_response}")
        
    except Exception as e:
        print(f"❌ Error during MCP test: {e}")
    finally:
        # Clean up
        print("\n🔌 Terminating MCP server...")
        process.terminate()
        process.wait()

if __name__ == "__main__":
    test_mcp_vm_creation() 