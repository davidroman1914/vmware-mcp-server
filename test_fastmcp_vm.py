#!/usr/bin/env python3
"""
Test script to debug FastMCP VM creation
"""

import os
import sys
import json
import subprocess
import time

def test_fastmcp_vm_creation():
    """Test VM creation through FastMCP server"""
    
    print("🧪 Testing FastMCP VM Creation")
    print("=" * 50)
    
    # Test arguments for creating a VM via FastMCP
    test_args = {
        "template_name": "Ubuntu-Template-01",
        "new_vm_name": "fastmcp-test-vm-001",
        "ip_address": "10.60.132.107",
        "gateway": "10.60.132.1",
        "memory_gb": 4,
        "cpu_count": 2,
        "disk_gb": 50,
        "network_name": "PROD VMs"
    }
    
    print("📋 Test Arguments:")
    for key, value in test_args.items():
        print(f"   {key}: {value}")
    print()
    
    # Start the FastMCP server process
    print("🚀 Starting FastMCP server...")
    process = subprocess.Popen(
        ["python", "fastmcp_server.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=os.environ.copy()
    )
    
    try:
        # Wait a moment for server to start
        time.sleep(3)
        
        # Send a simple test request
        print("📡 Sending test request...")
        test_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "create_custom_vm",
                "arguments": test_args
            }
        }
        
        print(f"Sending: {json.dumps(test_request, indent=2)}")
        
        process.stdin.write(json.dumps(test_request) + "\n")
        process.stdin.flush()
        
        # Read response
        response = process.stdout.readline()
        print(f"✅ Response: {response.strip()}")
        
        # Check stderr for any errors
        stderr_output = process.stderr.read()
        if stderr_output:
            print(f"⚠️  Stderr: {stderr_output}")
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
    finally:
        # Clean up
        print("\n🔌 Terminating FastMCP server...")
        process.terminate()
        process.wait()

def test_direct_function_call():
    """Test the function directly without FastMCP"""
    print("\n🧪 Testing Direct Function Call")
    print("=" * 50)
    
    try:
        # Import the function directly
        sys.path.append('.')
        from fastmcp_server import create_custom_vm
        
        # Test the function
        result = create_custom_vm(
            template_name="Ubuntu-Template-01",
            new_vm_name="direct-test-vm-001",
            ip_address="10.60.132.108",
            gateway="10.60.132.1",
            memory_gb=4,
            cpu_count=2,
            disk_gb=50,
            network_name="PROD VMs"
        )
        
        print("✅ Direct function result:")
        print(result)
        
    except Exception as e:
        print(f"❌ Direct function error: {e}")

if __name__ == "__main__":
    test_fastmcp_vm_creation()
    test_direct_function_call() 