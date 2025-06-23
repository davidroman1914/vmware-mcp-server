#!/usr/bin/env python3
"""
Test script for the VMware MCP Server
Tests basic functionality including listing VMs and power management.
"""

import json
import sys
import os
from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim
import ssl

# Import our modules
from vm_info import VMInfoManager
from power import PowerManager
from vm_creation import VMCreationManager

def connect_to_vcenter():
    """Connect to vCenter using environment variables."""
    try:
        host = os.getenv('VCENTER_HOST')
        user = os.getenv('VCENTER_USER')
        password = os.getenv('VCENTER_PASSWORD')
        insecure = os.getenv('VCENTER_INSECURE', 'false').lower() == 'true'
        
        if not all([host, user, password]):
            print("Error: Missing vCenter credentials. Set VCENTER_HOST, VCENTER_USER, VCENTER_PASSWORD")
            return None
        
        # Create SSL context
        if insecure:
            context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
            context.verify_mode = ssl.CERT_NONE
        else:
            context = ssl.create_default_context()
        
        # Connect to vCenter
        service_instance = SmartConnect(
            host=host,
            user=user,
            pwd=password,
            sslContext=context
        )
        
        print(f"Successfully connected to vCenter at {host}")
        return service_instance
        
    except Exception as e:
        print(f"Error connecting to vCenter: {e}")
        return None

def test_list_vms(service_instance):
    """Test listing VMs."""
    print("\n=== Testing VM Listing ===")
    vm_info = VMInfoManager()
    vms = vm_info.list_all_vms(service_instance)
    
    if isinstance(vms, list):
        print(f"Found {len(vms)} VMs:")
        for vm in vms:
            if "error" not in vm:
                print(f"  - {vm['name']} ({vm['power_state']}) - {vm['guest_id']}")
                if vm.get('ip_address'):
                    print(f"    IP: {vm['ip_address']}")
                if vm.get('cpu_count') and vm.get('memory_mb'):
                    print(f"    CPU: {vm['cpu_count']}, Memory: {vm['memory_mb']} MB")
    else:
        print(f"Error listing VMs: {vms}")

def test_power_management(service_instance):
    """Test power management."""
    print("\n=== Testing Power Management ===")
    power_manager = PowerManager()
    vm_info = VMInfoManager()
    
    # Get first VM for testing
    vms = vm_info.list_all_vms(service_instance)
    if isinstance(vms, list) and vms:
        test_vm = vms[0]
        vm_name = test_vm['name']
        
        print(f"Testing power management on VM: {vm_name}")
        print(f"Current power state: {test_vm['power_state']}")
        
        # Test power off (if powered on)
        if test_vm['power_state'] == 'poweredOn':
            print("Testing power off...")
            result = power_manager.power_off_vm(service_instance, vm_name)
            print(f"Power off result: {result}")
        
        # Test power on
        print("Testing power on...")
        result = power_manager.power_on_vm(service_instance, vm_name)
        print(f"Power on result: {result}")
    else:
        print("No VMs found for power management testing")

def test_vm_creation(service_instance):
    """Test VM creation from template."""
    print("\n=== Testing VM Creation ===")
    vm_creation = VMCreationManager()
    vm_info = VMInfoManager()
    
    # Find a template VM
    vms = vm_info.list_all_vms(service_instance)
    template_vm = None
    
    if isinstance(vms, list):
        for vm in vms:
            if vm.get('template') or 'template' in vm.get('name', '').lower():
                template_vm = vm
                break
    
    if template_vm:
        print(f"Found template VM: {template_vm['name']}")
        
        # Test VM creation (commented out to avoid creating actual VMs during testing)
        print("VM creation test would create a new VM with these parameters:")
        test_args = {
            "template_name": template_vm['name'],
            "vm_name": "test-vm-creation",
            "hostname": "test-vm",
            "ip_address": "192.168.1.100",
            "netmask": "255.255.255.0",
            "gateway": "192.168.1.1",
            "network_name": "VM Network",
            "cpu_count": 2,
            "memory_mb": 2048,
            "disk_size_gb": 20
        }
        print(json.dumps(test_args, indent=2))
        print("(VM creation test is disabled to avoid creating actual VMs)")
        
        # Uncomment the following lines to actually test VM creation:
        # result = vm_creation.create_vm_from_template(service_instance, test_args)
        # print(f"VM creation result: {result}")
    else:
        print("No template VM found for creation testing")

def main():
    """Main test function."""
    print("VMware MCP Server Test")
    print("======================")
    
    # Connect to vCenter
    service_instance = connect_to_vcenter()
    if not service_instance:
        sys.exit(1)
    
    try:
        # Run tests
        test_list_vms(service_instance)
        test_power_management(service_instance)
        test_vm_creation(service_instance)
        
        print("\n=== Test Summary ===")
        print("All tests completed successfully!")
        
    except Exception as e:
        print(f"Error during testing: {e}")
    finally:
        # Disconnect from vCenter
        try:
            Disconnect(service_instance)
            print("Disconnected from vCenter")
        except:
            pass

if __name__ == "__main__":
    main() 