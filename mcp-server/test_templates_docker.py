#!/usr/bin/env python3
"""
Test script for VMware vCenter VM operations.
Tests VM listing and cloning functionality.
"""

import os
import sys
import time
from vmware.vapi.vsphere.client import create_vsphere_client
from vmware.vapi.lib.connect import get_requests_connector
from vmware.vapi.security.session import create_session_security_context
from vmware.vapi.stdlib.client.factories import StubConfigurationFactory

def get_vsphere_client():
    """Create and return a vSphere client with session authentication."""
    try:
        # Get credentials from environment
        host = os.getenv('VCENTER_HOST')
        user = os.getenv('VCENTER_USER')
        password = os.getenv('VCENTER_PASSWORD')
        insecure = os.getenv('VCENTER_INSECURE', 'false').lower() == 'true'
        
        if not all([host, user, password]):
            raise ValueError("Missing vCenter credentials in environment variables")
        
        print(f"🔌 Connecting to vCenter: {host}")
        print(f"👤 User: {user}")
        print(f"🔓 Insecure: {insecure}")
        
        # Create session with SSL handling
        import requests
        import urllib3
        
        session = requests.Session()
        session.verify = not insecure
        
        # Disable SSL warnings for demo (not recommended in production)
        if insecure:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        # Create vSphere client (exactly as shown in PyPI docs)
        client = create_vsphere_client(
            server=host, 
            username=user, 
            password=password, 
            session=session
        )
        
        print("✅ Successfully connected to vCenter")
        return client
        
    except Exception as e:
        print(f"❌ Failed to connect to vCenter: {str(e)}")
        raise

def test_list_vms():
    """Test listing all VMs with detailed information."""
    print(f"\n🧪 VM LISTING TEST")
    print("=" * 50)
    
    try:
        client = get_vsphere_client()
        
        print(f"📋 Fetching all VMs...")
        vms = client.vcenter.VM.list()
        
        if not vms:
            print("❌ No VMs found")
            return
        
        print(f"✅ Found {len(vms)} VMs:")
        print("-" * 80)
        
        for i, vm in enumerate(vms, 1):
            try:
                vm_info = client.vcenter.VM.get(vm.vm)
                
                print(f"{i:2d}. {vm_info.name}")
                print(f"     ID: {vm.vm}")
                print(f"     Power State: {getattr(vm_info, 'power_state', 'Unknown')}")
                
                # Get CPU info
                if hasattr(vm_info, 'cpu') and vm_info.cpu:
                    cpu_count = getattr(vm_info.cpu, 'count', 'Unknown')
                    print(f"     CPU: {cpu_count} cores")
                
                # Get memory info
                if hasattr(vm_info, 'memory') and vm_info.memory:
                    memory_mb = getattr(vm_info.memory, 'size_MiB', 'Unknown')
                    print(f"     Memory: {memory_mb} MB")
                
                # Get guest OS info
                if hasattr(vm_info, 'guest_OS') and vm_info.guest_OS:
                    guest_os = getattr(vm_info.guest_OS, 'family', 'Unknown')
                    print(f"     Guest OS: {guest_os}")
                
                print()
                
            except Exception as e:
                print(f"{i:2d}. {vm.vm} - Error getting details: {str(e)}")
                print()
        
        return vms
        
    except Exception as e:
        print(f"❌ Error listing VMs: {str(e)}")
        return None

def test_vm_cloning_with_customization():
    """Test cloning a VM with full customization (IP, CPU, memory, hostname)."""
    print(f"\n🧪 VM CLONING WITH CUSTOMIZATION TEST")
    print("=" * 50)
    print("📋 This will test cloning a VM with full customization:")
    print("   - IP address, netmask, gateway")
    print("   - CPU count and memory")
    print("   - Custom hostname")
    print("   - Datastore placement")
    
    try:
        client = get_vsphere_client()
        
        # Step 1: Find a VM to clone from
        print(f"\n📋 Step 1: Finding a VM to clone from...")
        vms = client.vcenter.VM.list()
        
        if not vms:
            print("❌ No VMs found to clone from")
            return
        
        # Look for a good candidate VM (preferably powered off)
        source_vm = None
        for vm in vms:
            try:
                vm_info = client.vcenter.VM.get(vm.vm)
                # Prefer powered off VMs for cloning
                if getattr(vm_info, 'power_state', '') == 'POWERED_OFF':
                    source_vm = vm_info
                    print(f"✅ Found powered-off VM: {vm_info.name} (ID: {vm.vm})")
                    break
            except Exception:
                continue
        
        # If no powered-off VM, use the first one
        if not source_vm and vms:
            try:
                source_vm = client.vcenter.VM.get(vms[0].vm)
                print(f"✅ Using VM: {source_vm.name} (ID: {vms[0].vm})")
            except Exception as e:
                print(f"❌ Error getting VM info: {str(e)}")
                return
        
        if not source_vm:
            print("❌ No VMs found to clone from")
            return
        
        # Step 2: Gather resources for placement
        print(f"\n📋 Step 2: Gathering placement resources...")
        
        # Get datastore
        try:
            datastores = client.vcenter.Datastore.list()
            if datastores:
                datastore = datastores[0]
                datastore_info = client.vcenter.Datastore.get(datastore.datastore)
                print(f"   ✅ Datastore: {datastore_info.name}")
            else:
                print("   ❌ No datastores found")
                return
        except Exception as e:
            print(f"   ❌ Error getting datastores: {str(e)}")
            return
        
        # Get resource pool
        try:
            resource_pools = client.vcenter.ResourcePool.list()
            if resource_pools:
                resource_pool = resource_pools[0]
                resource_pool_info = client.vcenter.ResourcePool.get(resource_pool.resource_pool)
                print(f"   ✅ Resource Pool: {resource_pool_info.name}")
            else:
                print("   ❌ No resource pools found")
                return
        except Exception as e:
            print(f"   ❌ Error getting resource pools: {str(e)}")
            return
        
        # Get folder
        try:
            folders = client.vcenter.Folder.list()
            if folders:
                folder = folders[0]
                folder_info = client.vcenter.Folder.get(folder.folder)
                print(f"   ✅ Folder: {folder_info.name}")
            else:
                print("   ❌ No folders found")
                return
        except Exception as e:
            print(f"   ❌ Error getting folders: {str(e)}")
            return
        
        # Step 3: Test cloning with full customization
        print(f"\n📋 Step 3: Testing VM cloning with customization...")
        test_vm_name = f"test-clone-{source_vm.name}-{int(time.time())}"
        
        # Customization parameters
        clone_params = {
            'source_vm_id': source_vm.vm if hasattr(source_vm, 'vm') else source_vm._moId,
            'new_vm_name': test_vm_name,
            'datastore_id': datastore.datastore,
            'resource_pool_id': resource_pool.resource_pool,
            'folder_id': folder.folder,
            'cpu_count': 2,
            'memory_mb': 4096,
            'hostname': test_vm_name,
            'ip_address': '192.168.1.100',
            'netmask': '255.255.255.0',
            'gateway': '192.168.1.1'
        }
        
        print(f"📋 Clone parameters:")
        print(f"   • Source VM: {source_vm.name}")
        print(f"   • New VM Name: {test_vm_name}")
        print(f"   • CPU: {clone_params['cpu_count']} cores")
        print(f"   • Memory: {clone_params['memory_mb']} MB")
        print(f"   • IP: {clone_params['ip_address']}")
        print(f"   • Datastore: {datastore_info.name}")
        print(f"   • Resource Pool: {resource_pool_info.name}")
        print(f"   • Folder: {folder_info.name}")
        
        # Step 4: Attempt the clone
        print(f"\n📋 Step 4: Attempting VM clone...")
        try:
            from vm_creation import clone_vm_text
            
            # Perform the clone
            result = clone_vm_text(**clone_params)
            
            print(f"✅ Clone test successful!")
            print(f"   Result: {result}")
            
            # Check if the new VM was created
            print(f"\n📋 Step 5: Verifying new VM creation...")
            time.sleep(3)  # Give it a moment to appear
            
            new_vms = client.vcenter.VM.list()
            new_vm_found = False
            for vm in new_vms:
                try:
                    vm_info = client.vcenter.VM.get(vm.vm)
                    if vm_info.name == test_vm_name:
                        new_vm_found = True
                        print(f"✅ New VM found: {vm_info.name}")
                        print(f"   • VM ID: {vm.vm}")
                        print(f"   • Power State: {getattr(vm_info, 'power_state', 'Unknown')}")
                        
                        # Check hardware customization
                        if hasattr(vm_info, 'cpu') and vm_info.cpu:
                            print(f"   • CPU Count: {getattr(vm_info.cpu, 'count', 'Unknown')}")
                        if hasattr(vm_info, 'memory') and vm_info.memory:
                            print(f"   • Memory: {getattr(vm_info.memory, 'size_MiB', 'Unknown')} MB")
                        break
                except Exception:
                    continue
            
            if not new_vm_found:
                print(f"⚠️ New VM '{test_vm_name}' not found in VM list")
                print(f"   This might be normal if the clone is still in progress")
            
        except Exception as e:
            print(f"❌ Clone test failed: {str(e)}")
            print(f"   Source VM ID: {clone_params['source_vm_id']}")
            print(f"   Source VM Name: {source_vm.name}")
            
            # Try simpler clone without customization
            print(f"\n🔄 Trying simpler clone without customization...")
            try:
                simple_result = clone_vm_text(
                    source_vm_id=clone_params['source_vm_id'],
                    new_vm_name=f"{test_vm_name}-simple",
                    datastore_id=datastore.datastore
                )
                print(f"✅ Simple clone successful: {simple_result}")
            except Exception as simple_error:
                print(f"❌ Simple clone also failed: {str(simple_error)}")
        
    except Exception as e:
        print(f"❌ Error in VM cloning test: {str(e)}")

if __name__ == "__main__":
    print("🚀 VMware vCenter VM Operations Test")
    print("=" * 60)
    print("This test will:")
    print("1. List all VMs with detailed information")
    print("2. Test VM cloning with full customization")
    print("=" * 60)
    
    # Test VM listing
    test_list_vms()
    
    # Test VM cloning with customization
    test_vm_cloning_with_customization()
    
    print("\n✅ Test completed!") 