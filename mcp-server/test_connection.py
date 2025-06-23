#!/usr/bin/env python3
"""
Simple vCenter connection test
Tests only the connection to vCenter with detailed debug output.
"""

import os
import sys
import ssl
import time
from pyVim import connect
from pyVim.connect import Disconnect
from pyVmomi import vim

def test_vcenter_connection():
    """Test vCenter connection with detailed debug output."""
    print("=== vCenter Connection Test ===")
    
    # Read environment variables
    print("[DEBUG] Reading environment variables...")
    host = os.getenv('VCENTER_HOST')
    user = os.getenv('VCENTER_USER')
    password = os.getenv('VCENTER_PASSWORD')
    insecure = os.getenv('VCENTER_INSECURE', 'false').lower() == 'true'
    
    print(f"[DEBUG] VCENTER_HOST: {host}")
    print(f"[DEBUG] VCENTER_USER: {user}")
    print(f"[DEBUG] VCENTER_INSECURE: {insecure}")
    print(f"[DEBUG] VCENTER_PASSWORD: {'***' if password else 'NOT SET'}")
    
    # Check if all required variables are set
    if not all([host, user, password]):
        print("[ERROR] Missing required environment variables:")
        if not host:
            print("  - VCENTER_HOST is not set")
        if not user:
            print("  - VCENTER_USER is not set")
        if not password:
            print("  - VCENTER_PASSWORD is not set")
        return False
    
    try:
        # Test SmartConnect with disabled SSL for faster connections
        print("[DEBUG] Testing SmartConnect with disabled SSL...")
        start_time = time.time()
        
        # Create a completely disabled SSL context
        context = ssl.SSLContext(ssl.PROTOCOL_TLS)
        context.verify_mode = ssl.CERT_NONE
        context.check_hostname = False
        
        service_instance = connect.SmartConnect(
            host=host,
            user=user,
            pwd=password,
            sslContext=context
        )
        
        connection_time = time.time() - start_time
        print(f"[SUCCESS] Connected to vCenter successfully in {connection_time:.2f} seconds!")
        
        # Get basic info
        print("[DEBUG] Getting vCenter information...")
        content = service_instance.RetrieveContent()
        about = content.about
        
        print(f"[INFO] vCenter version: {about.version}")
        print(f"[INFO] vCenter build: {about.build}")
        print(f"[INFO] vCenter name: {about.name}")
        print(f"[INFO] vCenter full name: {about.fullName}")
        
        # Test fast VM listing
        print("[DEBUG] Testing fast VM listing...")
        from vm_info import VMInfoManager
        vm_info = VMInfoManager()
        
        print("[DEBUG] Creating container view...")
        content = service_instance.RetrieveContent()
        container = content.viewManager.CreateContainerView(
            content.rootFolder, [vim.VirtualMachine], True
        )
        print(f"[DEBUG] Container view created, found {len(container.view)} VMs")
        
        print("[DEBUG] Starting VM iteration...")
        count = 0
        for vm in container.view:
            count += 1
            if count <= 3:  # Only process first 3 VMs for testing
                print(f"[DEBUG] Processing VM {count}: {vm.name}")
                vm_info_basic = {
                    "name": vm.name,
                    "power_state": vm.runtime.powerState,
                }
                print(f"[DEBUG] VM {count} info: {vm_info_basic}")
            else:
                break
        
        print(f"[DEBUG] Successfully processed {count} VMs")
        container.Destroy()
        print("[DEBUG] Container view destroyed")
        
        # Now test the actual method
        print("[DEBUG] Testing fast_list_vms method...")
        vms = vm_info.fast_list_vms(service_instance)
        print(f"[INFO] Found {len(vms)} VMs using fast listing")
        for vm in vms[:3]:  # Show first 3 VMs
            print(f"  - {vm['name']} ({vm['power_state']})")
        
        # Disconnect
        print("[DEBUG] Disconnecting from vCenter...")
        Disconnect(service_instance)
        print("[SUCCESS] Disconnected from vCenter")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to connect to vCenter: {e}")
        print(f"[ERROR] Exception type: {type(e).__name__}")
        return False

def main():
    """Main function."""
    print("vCenter Connection Test (SmartConnectNoSSL)")
    print("==========================================")
    
    success = test_vcenter_connection()
    
    if success:
        print("\n[SUCCESS] Connection test passed!")
        sys.exit(0)
    else:
        print("\n[FAILURE] Connection test failed!")
        sys.exit(1)

if __name__ == "__main__":
    main() 