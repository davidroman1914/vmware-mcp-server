#!/usr/bin/env python3
"""
Simple example: Get all VMs using vmware-vcenter package
Based on official PyPI documentation: https://pypi.org/project/vmware-vcenter/
"""

import os
import requests
import urllib3
from vmware.vapi.vsphere.client import create_vsphere_client

def get_vsphere_client():
    """Create vSphere client with environment variables."""
    host = os.getenv("VCENTER_SERVER")
    user = os.getenv("VCENTER_USERNAME")
    pwd = os.getenv("VCENTER_PASSWORD")
    insecure = os.getenv("VCENTER_INSECURE", "false").lower() == "true"

    if not all([host, user, pwd]):
        missing = [k for k, v in [("VCENTER_SERVER", host), ("VCENTER_USERNAME", user), ("VCENTER_PASSWORD", pwd)] if not v]
        raise EnvironmentError(f"Missing environment variables: {', '.join(missing)}")

    # Create session with SSL handling
    session = requests.Session()
    session.verify = not insecure
    
    # Disable SSL warnings for demo (not recommended in production)
    if insecure:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    # Create vSphere client (exactly as shown in PyPI docs)
    return create_vsphere_client(
        server=host, 
        username=user, 
        password=pwd, 
        session=session
    )

def get_all_vms():
    """Get all VMs from vCenter."""
    try:
        # Create client
        client = get_vsphere_client()
        
        # List all VMs (exactly as shown in PyPI docs)
        vms = client.vcenter.VM.list()
        
        print(f"Found {len(vms)} VMs:")
        print("-" * 50)
        
        for vm in vms:
            print(f"VM: {vm.name}")
            print(f"  ID: {vm.vm}")
            print(f"  Power State: {vm.power_state}")
            print(f"  CPU Count: {vm.cpu_count}")
            print(f"  Memory: {vm.memory_size_mib} MB")
            print()
        
        return vms
        
    except Exception as e:
        print(f"Error getting VMs: {str(e)}")
        return None

if __name__ == "__main__":
    print("Getting all VMs from vCenter...")
    vms = get_all_vms()
    
    if vms:
        print(f"Successfully retrieved {len(vms)} VMs")
    else:
        print("Failed to retrieve VMs") 