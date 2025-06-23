#!/usr/bin/env python3
"""
Test script for creating a custom VM with all specifications
"""

import os
import sys
import json
import ssl
from pyVim.connect import SmartConnect

# Add the mcp-server directory to the path
sys.path.append('mcp-server')
from vm_creation import VMCreationManager
from vm_info import VMInfoManager

def test_create_custom_vm():
    """Test creating a VM with custom memory, CPU, disk, and IP"""
    
    # Get vCenter connection details from environment
    host = os.getenv('VCENTER_HOST')
    user = os.getenv('VCENTER_USER')
    password = os.getenv('VCENTER_PASSWORD')
    
    if not all([host, user, password]):
        print("Missing vCenter environment variables")
        return
    
    try:
        # Connect to vCenter
        context = ssl.SSLContext(ssl.PROTOCOL_TLS)
        context.verify_mode = ssl.CERT_NONE
        context.check_hostname = False
        
        service_instance = SmartConnect(
            host=host,  # type: ignore
            user=user,  # type: ignore
            pwd=password,  # type: ignore
            sslContext=context
        )
        
        print("Connected to vCenter successfully!")
        
        # Create VM creation manager
        vm_creation = VMCreationManager()
        
        # Test arguments for creating a custom VM
        arguments = {
            "template_name": "ubuntu-template",  # Replace with your template name
            "vm_name": "test-custom-vm-001",
            "hostname": "test-custom-vm-001",
            "ip_address": "192.168.1.100",
            "netmask": "255.255.255.0",
            "gateway": "192.168.1.1",
            "network_name": "VM Network",  # Replace with your network name
            "cpu_count": 4,
            "memory_gb": 8,
            "disk_size_gb": 100,
            "datastore_name": None  # Will use first available
        }
        
        print("Creating custom VM with specifications:")
        print(f"  VM Name: {arguments['vm_name']}")
        print(f"  Hostname: {arguments['hostname']}")
        print(f"  IP Address: {arguments['ip_address']}")
        print(f"  CPU Count: {arguments['cpu_count']}")
        print(f"  Memory: {arguments['memory_gb']} GB")
        print(f"  Disk Size: {arguments['disk_size_gb']} GB")
        print(f"  Network: {arguments['network_name']}")
        print()
        
        # Create the VM
        result = vm_creation.create_custom_vm(service_instance, arguments)
        
        print("Result:")
        print(json.dumps(result, indent=2))
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Disconnect
        if 'service_instance' in locals():
            from pyVim.connect import Disconnect
            Disconnect(service_instance)

if __name__ == "__main__":
    test_create_custom_vm() 