#!/usr/bin/env python3
"""
Test script for VMware vCenter operations using pyvmomi.
Tests VM listing and cloning functionality.
"""

import os
import sys
import time
from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim
import ssl

def get_vsphere_client():
    """Create and return a vSphere client with pyvmomi."""
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
        
        print("✅ Successfully connected to vCenter")
        return service_instance
        
    except Exception as e:
        print(f"❌ Failed to connect to vCenter: {str(e)}")
        raise

def test_list_vms():
    """Test listing all VMs with detailed information using pyvmomi."""
    print(f"\n🧪 VM LISTING TEST (pyvmomi)")
    print("=" * 50)
    
    try:
        service_instance = get_vsphere_client()
        content = service_instance.RetrieveContent()
        
        print(f"📋 Fetching all VMs...")
        
        # Get all VMs
        container = content.viewManager.CreateContainerView(
            content.rootFolder, [vim.VirtualMachine], True
        )
        vms = container.view
        
        if not vms:
            print("❌ No VMs found")
            return vms
        
        print(f"✅ Found {len(vms)} VMs:")
        print("-" * 80)
        
        for i, vm in enumerate(vms, 1):
            try:
                print(f"{i:2d}. {vm.name}")
                print(f"     ID: {vm._moId}")
                print(f"     Power State: {vm.runtime.powerState}")
                
                # Get CPU info
                if hasattr(vm, 'config') and vm.config and hasattr(vm.config, 'hardware'):
                    cpu_count = vm.config.hardware.numCPU
                    print(f"     CPU: {cpu_count} cores")
                
                # Get memory info
                if hasattr(vm, 'config') and vm.config and hasattr(vm.config, 'hardware'):
                    memory_mb = vm.config.hardware.memoryMB
                    print(f"     Memory: {memory_mb} MB")
                
                # Get guest OS info
                if hasattr(vm, 'config') and vm.config and hasattr(vm.config, 'guestId'):
                    guest_os = vm.config.guestId
                    print(f"     Guest OS: {guest_os}")
                
                # Check if it's a template
                if hasattr(vm, 'config') and vm.config and hasattr(vm.config, 'template'):
                    is_template = vm.config.template
                    print(f"     Template: {is_template}")
                
                print()
                
            except Exception as e:
                print(f"{i:2d}. {vm._moId} - Error getting details: {str(e)}")
                print()
        
        return vms
        
    except Exception as e:
        print(f"❌ Error listing VMs: {str(e)}")
        return None

def select_source_vm(vms):
    """Select the best VM to clone from with detailed explanation."""
    print(f"\n🎯 VM SELECTION LOGIC:")
    print("=" * 50)
    print("📋 Selection criteria (in order of preference):")
    print("   1. Powered-off VMs (safest for cloning)")
    print("   2. Templates (template=True)")
    print("   3. VMs with 'template' in the name")
    print("   4. First available VM")
    print()
    
    # Step 1: Look for powered-off VMs
    powered_off_vms = []
    for vm in vms:
        try:
            if vm.runtime.powerState == 'poweredOff':
                powered_off_vms.append(vm)
        except Exception:
            continue
    
    if powered_off_vms:
        selected_vm = powered_off_vms[0]
        print(f"✅ SELECTED: Powered-off VM")
        print(f"   • Name: {selected_vm.name}")
        print(f"   • ID: {selected_vm._moId}")
        print(f"   • Power State: {selected_vm.runtime.powerState}")
        return selected_vm
    
    # Step 2: Look for templates
    template_vms = []
    for vm in vms:
        try:
            if hasattr(vm, 'config') and vm.config and hasattr(vm.config, 'template') and vm.config.template:
                template_vms.append(vm)
        except Exception:
            continue
    
    if template_vms:
        selected_vm = template_vms[0]
        print(f"✅ SELECTED: Template VM")
        print(f"   • Name: {selected_vm.name}")
        print(f"   • ID: {selected_vm._moId}")
        print(f"   • Template: {selected_vm.config.template}")
        return selected_vm
    
    # Step 3: Look for VMs with 'template' in name
    template_name_vms = []
    for vm in vms:
        try:
            if 'template' in vm.name.lower():
                template_name_vms.append(vm)
        except Exception:
            continue
    
    if template_name_vms:
        selected_vm = template_name_vms[0]
        print(f"✅ SELECTED: VM with 'template' in name")
        print(f"   • Name: {selected_vm.name}")
        print(f"   • ID: {selected_vm._moId}")
        return selected_vm
    
    # Step 4: Use first available VM
    if vms:
        selected_vm = vms[0]
        print(f"⚠️ SELECTED: First available VM (fallback)")
        print(f"   • Name: {selected_vm.name}")
        print(f"   • ID: {selected_vm._moId}")
        print(f"   • Power State: {selected_vm.runtime.powerState}")
        return selected_vm
    
    return None

def gather_placement_resources(content):
    """Gather placement resources with detailed explanation."""
    print(f"\n🏗️ PLACEMENT RESOURCE SELECTION:")
    print("=" * 50)
    
    resources = {}
    
    # Get datastores
    try:
        datastores = content.viewManager.CreateContainerView(
            content.rootFolder, [vim.Datastore], True
        ).view
        if datastores:
            resources['datastore'] = datastores[0]
            print(f"✅ Datastore: {datastores[0].name} (ID: {datastores[0]._moId})")
            print(f"   • Type: {datastores[0].summary.type}")
            print(f"   • Capacity: {datastores[0].summary.capacity / (1024**3):.1f} GB")
            print(f"   • Free Space: {datastores[0].summary.freeSpace / (1024**3):.1f} GB")
        else:
            print("❌ No datastores found")
            return None
    except Exception as e:
        print(f"❌ Error getting datastores: {str(e)}")
        return None
    
    # Get resource pools
    try:
        resource_pools = content.viewManager.CreateContainerView(
            content.rootFolder, [vim.ResourcePool], True
        ).view
        if resource_pools:
            resources['resource_pool'] = resource_pools[0]
            print(f"✅ Resource Pool: {resource_pools[0].name} (ID: {resource_pools[0]._moId})")
        else:
            print("❌ No resource pools found")
            return None
    except Exception as e:
        print(f"❌ Error getting resource pools: {str(e)}")
        return None
    
    # Get folders
    try:
        folders = content.viewManager.CreateContainerView(
            content.rootFolder, [vim.Folder], True
        ).view
        if folders:
            resources['folder'] = folders[0]
            print(f"✅ Folder: {folders[0].name} (ID: {folders[0]._moId})")
        else:
            print("❌ No folders found")
            return None
    except Exception as e:
        print(f"❌ Error getting folders: {str(e)}")
        return None
    
    return resources

def simulate_vm_clone(source_vm, resources):
    """Simulate VM cloning without actually creating the VM."""
    print(f"\n🧪 VM CLONING SIMULATION (DRY RUN)")
    print("=" * 50)
    print("📋 This is a simulation - no actual VM will be created!")
    print()
    
    # Generate test VM name
    test_vm_name = f"test-clone-pyvmomi-{source_vm.name}-{int(time.time())}"
    
    print(f"📋 CLONE PARAMETERS:")
    print(f"   • Source VM: {source_vm.name} (ID: {source_vm._moId})")
    print(f"   • New VM Name: {test_vm_name}")
    print(f"   • Datastore: {resources['datastore'].name}")
    print(f"   • Resource Pool: {resources['resource_pool'].name}")
    print(f"   • Folder: {resources['folder'].name}")
    print()
    
    print(f"📋 CLONE SPECIFICATION:")
    print(f"   • Power On: False (VM will be created powered off)")
    print(f"   • Template: False (VM will be a regular VM, not a template)")
    print(f"   • Hardware: Same as source VM")
    print(f"   • Customization: None (no guest customization)")
    print()
    
    print(f"📋 WHAT WOULD HAPPEN:")
    print(f"   1. Clone task would be created")
    print(f"   2. VM files would be copied to {resources['datastore'].name}")
    print(f"   3. New VM would be registered in {resources['folder'].name}")
    print(f"   4. VM would be placed in {resources['resource_pool'].name}")
    print(f"   5. VM would be created powered off")
    print(f"   6. Task would complete successfully")
    print()
    
    print(f"✅ SIMULATION COMPLETE - No actual VM created!")
    print(f"💡 To actually create the VM, remove the simulation mode")

def test_simple_vm_clone_simulation():
    """Test VM cloning simulation without actually creating VMs."""
    print(f"\n🧪 SIMPLE VM CLONING SIMULATION (pyvmomi)")
    print("=" * 50)
    print("📋 This will simulate VM cloning without actually creating VMs")
    
    try:
        service_instance = get_vsphere_client()
        content = service_instance.RetrieveContent()
        
        # Step 1: Find a VM to clone from
        print(f"\n📋 Step 1: Finding a VM to clone from...")
        container = content.viewManager.CreateContainerView(
            content.rootFolder, [vim.VirtualMachine], True
        )
        vms = container.view
        
        if not vms:
            print("❌ No VMs found to clone from")
            return
        
        # Step 2: Select source VM with detailed explanation
        source_vm = select_source_vm(vms)
        if not source_vm:
            print("❌ No suitable VM found to clone from")
            return
        
        # Step 3: Gather placement resources with detailed explanation
        resources = gather_placement_resources(content)
        if not resources:
            print("❌ Failed to gather placement resources")
            return
        
        # Step 4: Simulate the clone
        simulate_vm_clone(source_vm, resources)
        
    except Exception as e:
        print(f"❌ Error in VM cloning simulation: {str(e)}")
    finally:
        # Disconnect
        try:
            Disconnect(service_instance)
        except:
            pass

if __name__ == "__main__":
    print("🚀 VMware vCenter VM Operations Test (pyvmomi)")
    print("=" * 60)
    print("This test will:")
    print("1. List all VMs with detailed information")
    print("2. Simulate VM cloning (no actual VM created)")
    print("=" * 60)
    
    # Test VM listing
    test_list_vms()
    
    # Test VM cloning simulation
    test_simple_vm_clone_simulation()
    
    print("\n✅ Test completed!") 