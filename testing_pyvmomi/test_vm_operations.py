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

def select_source_vm(vms, custom_template_name=None):
    """Select the best VM to clone from with detailed explanation."""
    print(f"\n🎯 VM SELECTION LOGIC:")
    print("=" * 50)
    
    if custom_template_name:
        print(f"📋 Looking for specific template: '{custom_template_name}'")
        print()
        
        # First, try to find the exact template name
        for vm in vms:
            try:
                if vm.name.lower() == custom_template_name.lower():
                    print(f"✅ SELECTED: Custom template found")
                    print(f"   • Name: {vm.name}")
                    print(f"   • ID: {vm._moId}")
                    print(f"   • Power State: {vm.runtime.powerState}")
                    if hasattr(vm, 'config') and vm.config and hasattr(vm.config, 'template'):
                        print(f"   • Template: {vm.config.template}")
                    return vm
            except Exception:
                continue
        
        print(f"❌ Template '{custom_template_name}' not found")
        print(f"📋 Available VMs:")
        for vm in vms[:5]:  # Show first 5 VMs
            try:
                print(f"   • {vm.name}")
            except Exception:
                print(f"   • {vm._moId}")
        if len(vms) > 5:
            print(f"   ... and {len(vms) - 5} more")
        print()
        print(f"⚠️ Falling back to automatic selection...")
        print()
    
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

def gather_placement_resources(content, custom_datastore_name=None):
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
            # If custom datastore is specified, try to find it
            if custom_datastore_name:
                selected_datastore = None
                for ds in datastores:
                    if ds.name.lower() == custom_datastore_name.lower():
                        selected_datastore = ds
                        break
                
                if selected_datastore:
                    resources['datastore'] = selected_datastore
                    print(f"✅ Custom Datastore: {selected_datastore.name} (ID: {selected_datastore._moId})")
                    print(f"   • Type: {selected_datastore.summary.type}")
                    print(f"   • Capacity: {selected_datastore.summary.capacity / (1024**3):.1f} GB")
                    print(f"   • Free Space: {selected_datastore.summary.freeSpace / (1024**3):.1f} GB")
                else:
                    print(f"⚠️ Custom datastore '{custom_datastore_name}' not found, using first available")
                    resources['datastore'] = datastores[0]
                    print(f"✅ Datastore: {datastores[0].name} (ID: {datastores[0]._moId})")
                    print(f"   • Type: {datastores[0].summary.type}")
                    print(f"   • Capacity: {datastores[0].summary.capacity / (1024**3):.1f} GB")
                    print(f"   • Free Space: {datastores[0].summary.freeSpace / (1024**3):.1f} GB")
            else:
                # Use first available datastore
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

def simulate_vm_clone_with_customization(source_vm, resources, customization_params=None):
    """Simulate VM cloning with full customization parameters."""
    print(f"\n🧪 VM CLONING WITH CUSTOMIZATION SIMULATION (DRY RUN)")
    print("=" * 50)
    print("📋 This is a simulation - no actual VM will be created!")
    print()
    
    # Generate test VM name - use hostname if provided, otherwise use timestamp
    if customization_params and 'hostname' in customization_params:
        test_vm_name = customization_params['hostname']
    else:
        test_vm_name = f"test-clone-custom-{source_vm.name}-{int(time.time())}"
    
    print(f"📋 CLONE PARAMETERS:")
    print(f"   • Source VM: {source_vm.name} (ID: {source_vm._moId})")
    print(f"   • New VM Name: {test_vm_name}")
    print(f"   • Datastore: {resources['datastore'].name}")
    print(f"   • Resource Pool: {resources['resource_pool'].name}")
    print(f"   • Folder: {resources['folder'].name}")
    print()
    
    # Show customization parameters if provided
    if customization_params:
        print(f"📋 CUSTOMIZATION PARAMETERS:")
        
        # Template selection
        if 'template_name' in customization_params:
            print(f"   • Template: {customization_params['template_name']}")
        
        # Hardware customization
        if 'cpu_count' in customization_params:
            print(f"   • CPU Count: {customization_params['cpu_count']} cores")
        if 'memory_mb' in customization_params:
            print(f"   • Memory: {customization_params['memory_mb']} MB")
        
        # Network customization
        if 'hostname' in customization_params:
            print(f"   • Hostname: {customization_params['hostname']}")
        if 'ip_address' in customization_params:
            print(f"   • IP Address: {customization_params['ip_address']}")
        if 'netmask' in customization_params:
            print(f"   • Netmask: {customization_params['netmask']}")
        if 'gateway' in customization_params:
            print(f"   • Gateway: {customization_params['gateway']}")
        if 'network_name' in customization_params:
            print(f"   • Network: {customization_params['network_name']}")
        
        # Storage customization
        if 'datastore_name' in customization_params:
            print(f"   • Datastore: {customization_params['datastore_name']}")
        if 'disk_size_gb' in customization_params:
            print(f"   • Disk Size: {customization_params['disk_size_gb']} GB")
        
        print()
    
    print(f"📋 CLONE SPECIFICATION:")
    print(f"   • Power On: False (VM will be created powered off)")
    print(f"   • Template: False (VM will be a regular VM, not a template)")
    
    if customization_params:
        print(f"   • Hardware Customization: {'Yes' if any(k in customization_params for k in ['cpu_count', 'memory_mb']) else 'No'}")
        print(f"   • Network Customization: {'Yes' if any(k in customization_params for k in ['hostname', 'ip_address', 'netmask', 'gateway']) else 'No'}")
        print(f"   • Storage Customization: {'Yes' if any(k in customization_params for k in ['datastore_name', 'disk_size_gb']) else 'No'}")
        print(f"   • Guest Customization: {'Yes' if any(k in customization_params for k in ['hostname', 'ip_address']) else 'No'}")
    else:
        print(f"   • Hardware: Same as source VM")
        print(f"   • Customization: None (no guest customization)")
    
    print()
    
    print(f"📋 WHAT WOULD HAPPEN:")
    print(f"   1. Clone task would be created")
    print(f"   2. VM files would be copied to {resources['datastore'].name}")
    print(f"   3. New VM would be registered in {resources['folder'].name}")
    print(f"   4. VM would be placed in {resources['resource_pool'].name}")
    
    if customization_params:
        if 'cpu_count' in customization_params or 'memory_mb' in customization_params:
            print(f"   5. Hardware would be customized (CPU/Memory)")
        if any(k in customization_params for k in ['hostname', 'ip_address', 'netmask', 'gateway']):
            print(f"   6. Guest OS would be customized (Network/Hostname)")
        if 'disk_size_gb' in customization_params:
            print(f"   7. Disk size would be customized")
    
    print(f"   8. VM would be created powered off")
    print(f"   9. Task would complete successfully")
    print()
    
    print(f"✅ SIMULATION COMPLETE - No actual VM created!")
    print(f"💡 To actually create the VM, remove the simulation mode")

def test_vm_clone_with_customization_simulation():
    """Test VM cloning with full customization simulation."""
    print(f"\n🧪 VM CLONING WITH CUSTOMIZATION SIMULATION (pyvmomi)")
    print("=" * 50)
    print("📋 This will simulate VM cloning with full customization")
    
    try:
        service_instance = get_vsphere_client()
        content = service_instance.RetrieveContent()
        
        # Step 1: Define customization parameters
        print(f"\n📋 Step 1: Defining customization parameters...")
        customization_params = {
            'template_name': 'Ubuntu-Template-01-TMPL',  # Custom template selection!
            'hostname': 'test-vm-custom',
            'ip_address': '192.168.1.100',
            'netmask': '255.255.255.0',
            'gateway': '192.168.1.1',
            'network_name': 'VM Network',  # You can update this to match your network
            'datastore_name': 'ova-inf-vh03-ds-2',  # Custom datastore selection
            'cpu_count': 4,
            'memory_mb': 4096,
            'disk_size_gb': 50
        }
        
        print(f"📋 Customization parameters:")
        for key, value in customization_params.items():
            print(f"   • {key}: {value}")
        
        # Step 2: Find a VM to clone from
        print(f"\n📋 Step 2: Finding a VM to clone from...")
        container = content.viewManager.CreateContainerView(
            content.rootFolder, [vim.VirtualMachine], True
        )
        vms = container.view
        
        if not vms:
            print("❌ No VMs found to clone from")
            return
        
        # Step 3: Select source VM with custom template name
        source_vm = select_source_vm(vms, customization_params.get('template_name'))
        if not source_vm:
            print("❌ No suitable VM found to clone from")
            return
        
        # Step 4: Gather placement resources with custom datastore
        resources = gather_placement_resources(content, customization_params.get('datastore_name'))
        if not resources:
            print("❌ Failed to gather placement resources")
            return
        
        # Step 5: Simulate the clone with customization
        simulate_vm_clone_with_customization(source_vm, resources, customization_params)
        
    except Exception as e:
        print(f"❌ Error in VM cloning simulation: {str(e)}")
    finally:
        # Disconnect
        try:
            Disconnect(service_instance)
        except:
            pass

def power_on_and_wait_for_customization(vm, timeout_minutes=10):
    """Power on VM and wait for customization to complete."""
    print(f"\n🚀 POWERING ON VM AND WAITING FOR CUSTOMIZATION")
    print("=" * 50)
    
    try:
        # Power on the VM
        print(f"🔌 Powering on VM: {vm.name}")
        task = vm.PowerOn()
        
        # Wait for power on to complete
        while task.info.state not in [vim.TaskInfo.State.success, vim.TaskInfo.State.error]:
            time.sleep(2)
        
        if task.info.state == vim.TaskInfo.State.error:
            print(f"❌ Failed to power on VM: {task.info.error.msg}")
            return False
        
        print(f"✅ VM powered on successfully")
        
        # Wait for VMware Tools to start and customization to complete
        print(f"⏳ Waiting for VMware Tools and customization...")
        start_time = time.time()
        timeout_seconds = timeout_minutes * 60
        
        while time.time() - start_time < timeout_seconds:
            try:
                # Check tools status
                tools_status = vm.guest.toolsStatus if hasattr(vm, 'guest') else 'Unknown'
                print(f"   • Tools Status: {tools_status}")
                
                # Check if customization is complete
                if hasattr(vm, 'config') and vm.config and hasattr(vm.config, 'extraConfig'):
                    for config in vm.config.extraConfig:
                        if config.key == 'guestinfo.customization':
                            print(f"   • Customization Status: {config.value}")
                            if 'SUCCESS' in config.value.upper():
                                print(f"✅ Customization completed successfully!")
                                return True
                            elif 'FAILED' in config.value.upper():
                                print(f"❌ Customization failed!")
                                return False
                
                # Check if we can get guest info (indicates tools are working)
                if hasattr(vm, 'guest') and vm.guest and hasattr(vm.guest, 'ipAddress'):
                    ip_addresses = vm.guest.ipAddress
                    if ip_addresses:
                        print(f"   • IP Addresses: {', '.join(ip_addresses)}")
                        
                        # Check if the expected IP is in the list
                        if hasattr(vm, 'config') and vm.config and hasattr(vm.config, 'extraConfig'):
                            for config in vm.config.extraConfig:
                                if config.key == 'guestinfo.customization':
                                    print(f"   • Customization Status: {config.value}")
                        
                        print(f"✅ VM is responding with IP addresses!")
                        return True
                
                # Also check network adapters
                if hasattr(vm, 'config') and vm.config and hasattr(vm.config, 'hardware'):
                    for device in vm.config.hardware.device:
                        if isinstance(device, vim.vm.device.VirtualEthernetCard):
                            print(f"   • Network Adapter: {device.deviceInfo.label}")
                            if hasattr(device, 'backing') and device.backing:
                                if hasattr(device.backing, 'network'):
                                    print(f"   • Connected to: {device.backing.network.name}")
                                elif hasattr(device.backing, 'port'):
                                    print(f"   • Connected to: {device.backing.port.portgroupKey}")
                
                time.sleep(10)
                
            except Exception as e:
                print(f"   • Error checking status: {str(e)}")
                time.sleep(10)
        
        print(f"⚠️ Timeout waiting for customization (after {timeout_minutes} minutes)")
        return False
        
    except Exception as e:
        print(f"❌ Error powering on VM: {str(e)}")
        return False

def create_vm_from_template_with_customization(source_vm, resources, customization_params=None):
    """Actually create a VM by cloning from template with full customization."""
    print(f"\n🚀 CREATING VM FROM TEMPLATE WITH CUSTOMIZATION")
    print("=" * 50)
    print("📋 This will actually create a new VM!")
    print()
    
    # Generate test VM name - use hostname if provided, otherwise use timestamp
    if customization_params and 'hostname' in customization_params:
        test_vm_name = customization_params['hostname']
    else:
        test_vm_name = f"test-clone-custom-{source_vm.name}-{int(time.time())}"
    
    print(f"📋 CLONE PARAMETERS:")
    print(f"   • Source VM: {source_vm.name} (ID: {source_vm._moId})")
    print(f"   • New VM Name: {test_vm_name}")
    print(f"   • Datastore: {resources['datastore'].name}")
    print(f"   • Resource Pool: {resources['resource_pool'].name}")
    print(f"   • Folder: {resources['folder'].name}")
    print()
    
    # Show customization parameters if provided
    if customization_params:
        print(f"📋 CUSTOMIZATION PARAMETERS:")
        
        # Template selection
        if 'template_name' in customization_params:
            print(f"   • Template: {customization_params['template_name']}")
        
        # Hardware customization
        if 'cpu_count' in customization_params:
            print(f"   • CPU Count: {customization_params['cpu_count']} cores")
        if 'memory_mb' in customization_params:
            print(f"   • Memory: {customization_params['memory_mb']} MB")
        
        # Network customization
        if 'hostname' in customization_params:
            print(f"   • Hostname: {customization_params['hostname']}")
        if 'ip_address' in customization_params:
            print(f"   • IP Address: {customization_params['ip_address']}")
        if 'netmask' in customization_params:
            print(f"   • Netmask: {customization_params['netmask']}")
        if 'gateway' in customization_params:
            print(f"   • Gateway: {customization_params['gateway']}")
        if 'network_name' in customization_params:
            print(f"   • Network: {customization_params['network_name']}")
        
        # Storage customization
        if 'datastore_name' in customization_params:
            print(f"   • Datastore: {customization_params['datastore_name']}")
        if 'disk_size_gb' in customization_params:
            print(f"   • Disk Size: {customization_params['disk_size_gb']} GB")
        
        print()
    
    try:
        # Create the clone specification
        clone_spec = vim.vm.CloneSpec()
        clone_spec.location = vim.vm.RelocateSpec()
        clone_spec.location.datastore = resources['datastore']
        clone_spec.location.pool = resources['resource_pool']
        clone_spec.location.folder = resources['folder']
        clone_spec.powerOn = False  # Keep powered off initially
        clone_spec.template = False
        
        # Configure hardware customization
        if any(k in customization_params for k in ['cpu_count', 'memory_mb', 'disk_size_gb', 'ip_address', 'netmask', 'gateway']):
            clone_spec.config = vim.vm.ConfigSpec()
            clone_spec.config.deviceChange = []
            
            # CPU customization
            if 'cpu_count' in customization_params:
                clone_spec.config.numCPUs = customization_params['cpu_count']
                print(f"🔧 Setting CPU count to {customization_params['cpu_count']}")
            
            # Memory customization
            if 'memory_mb' in customization_params:
                clone_spec.config.memoryMB = customization_params['memory_mb']
                print(f"🔧 Setting memory to {customization_params['memory_mb']} MB")
            
            # Network adapter configuration - Configure the hardware network adapter
            if any(k in customization_params for k in ['ip_address', 'netmask', 'gateway', 'network_name']):
                print(f"🔧 Configuring network adapter hardware...")
                
                # Find the network
                network_obj = None
                if 'network_name' in customization_params:
                    for network in resources.get('networks', []):
                        if network.name == customization_params['network_name']:
                            network_obj = network
                            break
                
                # If network not found, use the first available
                if not network_obj and resources.get('networks'):
                    network_obj = resources['networks'][0]
                
                if network_obj:
                    # Configure each network adapter in the source VM
                    for i, device in enumerate(source_vm.config.hardware.device):
                        if isinstance(device, vim.vm.device.VirtualEthernetCard):
                            print(f"   • Configuring network adapter {i}: {device.__class__.__name__}")
                            
                            # Create network adapter spec
                            nic_spec = vim.vm.device.VirtualDeviceSpec()
                            nic_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.edit
                            nic_spec.device = device
                            
                            # Ensure the adapter is connected to the right network
                            if hasattr(network_obj, 'portKeys'):
                                # Distributed virtual switch
                                print(f"     - Connecting to distributed port group: {network_obj.name}")
                                nic_spec.device.backing = vim.vm.device.VirtualEthernetCard.DistributedVirtualPortBackingInfo()
                                nic_spec.device.backing.port = vim.dvs.PortConnection()
                                nic_spec.device.backing.port.portgroupKey = network_obj.key
                                nic_spec.device.backing.port.switchUuid = network_obj.config.distributedVirtualSwitch.uuid
                            else:
                                # Standard switch
                                print(f"     - Connecting to standard switch: {network_obj.name}")
                                nic_spec.device.backing = vim.vm.device.VirtualEthernetCard.NetworkBackingInfo()
                                nic_spec.device.backing.network = network_obj
                                nic_spec.device.backing.deviceName = network_obj.name
                            
                            # Ensure the adapter is connected and starts connected
                            nic_spec.device.connectable.connected = True
                            nic_spec.device.connectable.startConnected = True
                            nic_spec.device.connectable.allowGuestControl = True
                            
                            clone_spec.config.deviceChange.append(nic_spec)
                            print(f"     - Network adapter {i} configured for {network_obj.name}")
            
            # Disk customization (if specified)
            if 'disk_size_gb' in customization_params:
                # Find the first disk and resize it
                for device in source_vm.config.hardware.device:
                    if isinstance(device, vim.vm.device.VirtualDisk):
                        disk_spec = vim.vm.device.VirtualDeviceSpec()
                        disk_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.edit
                        disk_spec.device = device
                        disk_spec.device.capacityInKB = customization_params['disk_size_gb'] * 1024 * 1024
                        clone_spec.config.deviceChange.append(disk_spec)
                        print(f"🔧 Setting disk size to {customization_params['disk_size_gb']} GB")
                        break
        
        # Add guest customization if network parameters are specified
        if customization_params and any(k in customization_params for k in ['hostname', 'ip_address', 'netmask', 'gateway']):
            clone_spec.customization = vim.vm.customization.Specification()
            
            # Global IP settings (required for Linux customization)
            clone_spec.customization.globalIPSettings = vim.vm.customization.GlobalIPSettings()
            if 'gateway' in customization_params:
                clone_spec.customization.globalIPSettings.dnsServerList = ['8.8.8.8', '8.8.4.4']
            
            # Linux customization - be explicit about Ubuntu
            clone_spec.customization.identity = vim.vm.customization.LinuxPrep()
            
            if 'hostname' in customization_params:
                clone_spec.customization.identity.hostName = vim.vm.customization.FixedName(name=customization_params['hostname'])
                print(f"🔧 Setting hostname to {customization_params['hostname']}")
            
            # Set domain if specified
            if 'domain' in customization_params:
                clone_spec.customization.identity.domain = customization_params['domain']
                print(f"🔧 Setting domain to {customization_params['domain']}")
            
            # Network configuration - Use Ansible's exact approach
            clone_spec.customization.nicSettingMap = []
            
            # Find the network
            network_obj = None
            if 'network_name' in customization_params:
                for network in resources.get('networks', []):
                    if network.name == customization_params['network_name']:
                        network_obj = network
                        break
            
            # If network not found, use the first available
            if not network_obj and resources.get('networks'):
                network_obj = resources['networks'][0]
            
            if network_obj:
                # Create adapter mapping exactly like Ansible does
                guest_map = vim.vm.customization.AdapterMapping()
                guest_map.adapter = vim.vm.customization.IPSettings()
                
                # IP assignment logic - exactly like Ansible
                if 'ip_address' in customization_params and 'netmask' in customization_params:
                    guest_map.adapter.ip = vim.vm.customization.FixedIp()
                    guest_map.adapter.ip.ipAddress = str(customization_params['ip_address'])
                    guest_map.adapter.subnetMask = str(customization_params['netmask'])
                    print(f"🔧 Setting fixed IP: {customization_params['ip_address']}/{customization_params['netmask']}")
                    
                    # For Ubuntu/Linux, we need to be more explicit about static IP
                    # Set DNS servers on the adapter level
                    guest_map.adapter.dnsServerList = ['8.8.8.8', '8.8.4.4']
                    print(f"🔧 Setting DNS servers on adapter: 8.8.8.8, 8.8.4.4")
                else:
                    # Use DHCP if no IP specified
                    guest_map.adapter.ip = vim.vm.customization.DhcpIpGenerator()
                    print(f"🔧 Using DHCP for IP assignment")
                
                # Gateway
                if 'gateway' in customization_params:
                    guest_map.adapter.gateway = [customization_params['gateway']]
                    print(f"🔧 Setting gateway to {customization_params['gateway']}")
                
                clone_spec.customization.nicSettingMap.append(guest_map)
                print(f"🔧 Network adapter configured for: {network_obj.name}")
                
                # Debug the customization spec
                print(f"🔧 Customization spec details:")
                print(f"   • Global IP Settings: {clone_spec.customization.globalIPSettings}")
                print(f"   • Identity: {clone_spec.customization.identity}")
                print(f"   • NIC Settings Count: {len(clone_spec.customization.nicSettingMap)}")
                for i, nic in enumerate(clone_spec.customization.nicSettingMap):
                    print(f"   • NIC {i}: {nic.adapter}")
                    if hasattr(nic.adapter, 'ip'):
                        print(f"     - IP: {nic.adapter.ip}")
                        if hasattr(nic.adapter.ip, 'ipAddress'):
                            print(f"       - IP Address: {nic.adapter.ip.ipAddress}")
                    if hasattr(nic.adapter, 'subnetMask'):
                        print(f"     - Netmask: {nic.adapter.subnetMask}")
                    if hasattr(nic.adapter, 'gateway'):
                        print(f"     - Gateway: {nic.adapter.gateway}")
                    if hasattr(nic.adapter, 'dnsServerList'):
                        print(f"     - DNS Servers: {nic.adapter.dnsServerList}")
                
                # Additional debugging - show the raw customization spec
                print(f"\n🔍 RAW CUSTOMIZATION SPECIFICATION:")
                print(f"   • Type: {type(clone_spec.customization)}")
                print(f"   • Identity Type: {type(clone_spec.customization.identity)}")
                print(f"   • Global IP Settings Type: {type(clone_spec.customization.globalIPSettings)}")
                print(f"   • NIC Setting Map Type: {type(clone_spec.customization.nicSettingMap)}")
                print(f"   • NIC Setting Map Length: {len(clone_spec.customization.nicSettingMap)}")
                
                # Check if we need to map to specific network adapters
                print(f"\n🔍 SOURCE VM NETWORK ADAPTERS:")
                if source_vm.config and source_vm.config.hardware and source_vm.config.hardware.device:
                    for i, device in enumerate(source_vm.config.hardware.device):
                        if isinstance(device, vim.vm.device.VirtualEthernetCard):
                            print(f"   • Adapter {i}: {device.__class__.__name__}")
                            print(f"     - MAC: {device.macAddress}")
                            print(f"     - Connected: {device.connectable.connected}")
                            if hasattr(device, 'backing') and device.backing:
                                if hasattr(device.backing, 'network'):
                                    print(f"     - Network: {device.backing.network.name}")
                                elif hasattr(device.backing, 'port'):
                                    print(f"     - Port Group: {device.backing.port.portgroupKey}")
                
                # Try a different approach - create one adapter mapping per network adapter
                print(f"\n🔧 TRYING ALTERNATIVE APPROACH: One adapter mapping per network adapter")
                clone_spec.customization.nicSettingMap = []
                
                # Create one adapter mapping for each network adapter in the source VM
                if source_vm.config and source_vm.config.hardware and source_vm.config.hardware.device:
                    for i, device in enumerate(source_vm.config.hardware.device):
                        if isinstance(device, vim.vm.device.VirtualEthernetCard):
                            print(f"   • Creating mapping for adapter {i}: {device.__class__.__name__}")
                            
                            guest_map = vim.vm.customization.AdapterMapping()
                            guest_map.adapter = vim.vm.customization.IPSettings()
                            
                            # IP assignment logic - exactly like Ansible
                            if 'ip_address' in customization_params and 'netmask' in customization_params:
                                guest_map.adapter.ip = vim.vm.customization.FixedIp()
                                guest_map.adapter.ip.ipAddress = str(customization_params['ip_address'])
                                guest_map.adapter.subnetMask = str(customization_params['netmask'])
                                print(f"     - Setting fixed IP: {customization_params['ip_address']}/{customization_params['netmask']}")
                                
                                # For Ubuntu/Linux, we need to be more explicit about static IP
                                # Set DNS servers on the adapter level
                                guest_map.adapter.dnsServerList = ['8.8.8.8', '8.8.4.4']
                                print(f"     - Setting DNS servers on adapter: 8.8.8.8, 8.8.4.4")
                            else:
                                # Use DHCP if no IP specified
                                guest_map.adapter.ip = vim.vm.customization.DhcpIpGenerator()
                                print(f"     - Using DHCP for IP assignment")
                            
                            # Gateway
                            if 'gateway' in customization_params:
                                guest_map.adapter.gateway = [customization_params['gateway']]
                                print(f"     - Setting gateway to {customization_params['gateway']}")
                            
                            clone_spec.customization.nicSettingMap.append(guest_map)
                            print(f"     - Added adapter mapping {i}")
                
                print(f"   • Final NIC Setting Map Count: {len(clone_spec.customization.nicSettingMap)}")
        
        print(f"\n🚀 Starting VM clone operation...")
        print(f"   • This may take several minutes depending on VM size")
        print(f"   • You can monitor progress in vCenter")
        
        # Start the clone operation
        task = source_vm.Clone(folder=resources['folder'], name=test_vm_name, spec=clone_spec)
        
        print(f"✅ Clone task started successfully!")
        print(f"   • Task ID: {task.info.key}")
        print(f"   • New VM will be named: {test_vm_name}")
        print(f"   • VM will be created powered off")
        
        # Wait for the task to complete
        print(f"\n⏳ Waiting for clone operation to complete...")
        while task.info.state not in [vim.TaskInfo.State.success, vim.TaskInfo.State.error]:
            time.sleep(5)
            print(f"   • Status: {task.info.state}")
        
        if task.info.state == vim.TaskInfo.State.success:
            print(f"✅ VM clone completed successfully!")
            print(f"   • New VM: {test_vm_name}")
            print(f"   • Location: {resources['folder'].name}")
            print(f"   • Datastore: {resources['datastore'].name}")
            print(f"   • Resource Pool: {resources['resource_pool'].name}")
            
            # Get the new VM object
            new_vm = task.info.result
            print(f"   • VM ID: {new_vm._moId}")
            
            # Check customization status
            print(f"\n🔍 Checking VM customization status...")
            try:
                if hasattr(new_vm, 'config') and new_vm.config:
                    print(f"   • Guest ID: {new_vm.config.guestId}")
                    print(f"   • Tools Status: {new_vm.guest.toolsStatus if hasattr(new_vm, 'guest') else 'Unknown'}")
                    print(f"   • Power State: {new_vm.runtime.powerState}")
                    
                    # Check hardware configuration
                    if hasattr(new_vm.config, 'hardware'):
                        print(f"\n🔧 HARDWARE CONFIGURATION:")
                        print(f"   • CPU Count: {new_vm.config.hardware.numCPU} cores")
                        print(f"   • Memory: {new_vm.config.hardware.memoryMB} MB")
                        
                        # Check disk configuration
                        for device in new_vm.config.hardware.device:
                            if isinstance(device, vim.vm.device.VirtualDisk):
                                disk_size_gb = device.capacityInKB / (1024 * 1024)
                                print(f"   • Disk Size: {disk_size_gb:.1f} GB")
                                break
                        
                        # Compare with requested configuration
                        if customization_params:
                            print(f"\n📋 REQUESTED vs ACTUAL CONFIGURATION:")
                            if 'cpu_count' in customization_params:
                                requested_cpu = customization_params['cpu_count']
                                actual_cpu = new_vm.config.hardware.numCPU
                                status = "✅" if requested_cpu == actual_cpu else "❌"
                                print(f"   • CPU: {status} Requested {requested_cpu}, Got {actual_cpu}")
                            
                            if 'memory_mb' in customization_params:
                                requested_memory = customization_params['memory_mb']
                                actual_memory = new_vm.config.hardware.memoryMB
                                status = "✅" if requested_memory == actual_memory else "❌"
                                print(f"   • Memory: {status} Requested {requested_memory} MB, Got {actual_memory} MB")
                            
                            if 'disk_size_gb' in customization_params:
                                requested_disk = customization_params['disk_size_gb']
                                for device in new_vm.config.hardware.device:
                                    if isinstance(device, vim.vm.device.VirtualDisk):
                                        actual_disk = device.capacityInKB / (1024 * 1024)
                                        status = "✅" if abs(requested_disk - actual_disk) < 0.1 else "❌"
                                        print(f"   • Disk: {status} Requested {requested_disk} GB, Got {actual_disk:.1f} GB")
                                        break
                    
                    # Check if customization was applied
                    if hasattr(new_vm, 'config') and new_vm.config and hasattr(new_vm.config, 'extraConfig'):
                        customization_applied = False
                        for config in new_vm.config.extraConfig:
                            if config.key == 'guestinfo.customization':
                                customization_applied = True
                                print(f"   • Customization Applied: {config.value}")
                                break
                        
                        if not customization_applied:
                            print(f"   • Customization Applied: Not detected")
                    
                    print(f"\n💡 Next steps:")
                    print(f"   1. Power on the VM: {new_vm.name}")
                    print(f"   2. Wait for VMware Tools to start")
                    print(f"   3. The customization should apply automatically")
                    print(f"   4. Check the VM's IP address after boot")
                    
            except Exception as e:
                print(f"   • Error checking customization status: {str(e)}")
            
            # Ask if user wants to power on the VM
            print(f"\n🚀 Would you like to power on the VM and wait for customization?")
            print(f"   • This will power on the VM and wait for customization to complete")
            print(f"   • The VM will get the IP address: {customization_params.get('ip_address', 'DHCP')}")
            
            # For now, let's power it on automatically
            if customization_params and any(k in customization_params for k in ['hostname', 'ip_address']):
                print(f"\n🚀 Powering on VM automatically to apply customization...")
                success = power_on_and_wait_for_customization(new_vm)
                if success:
                    print(f"🎉 VM is ready with customization applied!")
                else:
                    print(f"⚠️ VM powered on but customization may not have completed")
            
            return new_vm
        else:
            print(f"❌ VM clone failed!")
            if hasattr(task.info, 'error') and task.info.error:
                print(f"   • Error: {task.info.error.msg}")
            return None
            
    except Exception as e:
        print(f"❌ Error creating VM: {str(e)}")
        return None

def test_actual_vm_creation():
    """Test actual VM creation with full customization."""
    print(f"\n🚀 ACTUAL VM CREATION WITH CUSTOMIZATION (pyvmomi)")
    print("=" * 50)
    print("📋 This will actually create a new VM!")
    
    try:
        service_instance = get_vsphere_client()
        content = service_instance.RetrieveContent()
        
        # Step 1: Define customization parameters
        print(f"\n📋 Step 1: Defining customization parameters...")
        customization_params = {
            'template_name': 'Ubuntu-Template-01-TMPL',  # Custom template selection!
            'hostname': 'test-vm-custom',
            'ip_address': '10.60.76.93',
            'netmask': '255.255.255.0',
            'gateway': '10.60.76.1',
            'network_name': 'PROD VMs',  # You can update this to match your network
            'datastore_name': 'ova-inf-vh03-ds-2',  # Custom datastore selection
            'cpu_count': 4,
            'memory_mb': 4096,
            'disk_size_gb': 65
        }
        
        print(f"📋 Customization parameters:")
        for key, value in customization_params.items():
            print(f"   • {key}: {value}")
        
        # Step 2: Find a VM to clone from
        print(f"\n📋 Step 2: Finding a VM to clone from...")
        container = content.viewManager.CreateContainerView(
            content.rootFolder, [vim.VirtualMachine], True
        )
        vms = container.view
        
        if not vms:
            print("❌ No VMs found to clone from")
            return
        
        # Step 3: Select source VM with custom template name
        source_vm = select_source_vm(vms, customization_params.get('template_name'))
        if not source_vm:
            print("❌ No suitable VM found to clone from")
            return
        
        # Step 4: Gather placement resources with custom datastore
        resources = gather_placement_resources(content, customization_params.get('datastore_name'))
        if not resources:
            print("❌ Failed to gather placement resources")
            return
        
        # Step 5: Actually create the VM with customization
        new_vm = create_vm_from_template_with_customization(source_vm, resources, customization_params)
        
        if new_vm:
            print(f"\n🎉 SUCCESS! New VM created:")
            print(f"   • Name: {new_vm.name}")
            print(f"   • ID: {new_vm._moId}")
            print(f"   • Power State: {new_vm.runtime.powerState}")
            print(f"   • You can now power it on in vCenter")
        else:
            print(f"\n❌ VM creation failed")
        
    except Exception as e:
        print(f"❌ Error in VM creation: {str(e)}")
    finally:
        # Disconnect
        try:
            Disconnect(service_instance)
        except:
            pass

def show_expected_netplan_config(ip_address, netmask, gateway):
    """Show what the netplan configuration should look like for static IP"""
    print(f"\n📋 EXPECTED NETPLAN CONFIGURATION FOR STATIC IP:")
    print("=" * 60)
    print(f"# Expected netplan configuration for static IP: {ip_address}")
    print("# This is what VMware customization should generate:")
    print("network:")
    print("  version: 2")
    print("  renderer: networkd")
    print("  ethernets:")
    print("    ens33:")
    print("      dhcp4: no")
    print("      dhcp6: no")
    print(f"      addresses:")
    print(f"        - {ip_address}/{netmask}")
    print(f"      gateway4: {gateway}")
    print("      nameservers:")
    print("        addresses:")
    print("          - 8.8.8.8")
    print("          - 8.8.4.4")
    print("=" * 60)
    print(f"# ACTUAL NETPLAN CONFIGURATION (DHCP):")
    print("# This is what VMware actually generated:")
    print("network:")
    print("  version: 2")
    print("  renderer: networkd")
    print("  ethernets:")
    print("    ens33:")
    print("      dhcp4: yes")
    print("      dhcp4-overrides:")
    print("        use-dns: false")
    print("      dhcp6: yes")
    print("      dhcp6-overrides:")
    print("        use-dns: false")
    print("      nameservers:")
    print("        addresses:")
    print("          - 8.8.8.8")
    print("          - 8.8.4.4")
    print("=" * 60)
    print("🔍 ANALYSIS:")
    print("• VMware customization engine generated DHCP config instead of static IP")
    print("• DNS servers were applied correctly (8.8.8.8, 8.8.4.4)")
    print("• The issue is that VMware is not recognizing our static IP configuration")
    print("• This suggests a problem with the customization specification or guest OS detection")

def check_vm_network_config(si, vm_name):
    """Check the network configuration of a VM after it's powered on"""
    print(f"\n🔍 Checking network configuration for VM: {vm_name}")
    
    # Find the VM
    content = si.RetrieveContent()
    container = content.viewManager.CreateContainerView(content.rootFolder, [vim.VirtualMachine], True)
    vm = None
    for v in container.view:
        if v.name == vm_name:
            vm = v
            break
    container.Destroy()
    
    if not vm:
        print(f"❌ VM {vm_name} not found")
        return
    
    print(f"✅ Found VM: {vm.name}")
    print(f"   • Power State: {vm.runtime.powerState}")
    print(f"   • Guest ID: {vm.config.guestId}")
    
    # Check guest info
    if vm.guest:
        print(f"   • Guest Tools Status: {vm.guest.toolsRunningStatus}")
        print(f"   • Guest IP Addresses: {vm.guest.ipAddress}")
        
        # Check network interfaces
        if vm.guest.net:
            print(f"   • Network Interfaces:")
            for i, net in enumerate(vm.guest.net):
                print(f"     - Interface {i}: {net.network}")
                print(f"       • IP Addresses: {net.ipAddress}")
                print(f"       • MAC Address: {net.macAddress}")
                print(f"       • Connected: {net.connected}")
                print(f"       • Device Config Id: {net.deviceConfigId}")
        else:
            print(f"   • No network interfaces found in guest info")
    else:
        print(f"   • No guest info available")
    
    # Check hardware configuration
    if vm.config and vm.config.hardware:
        print(f"   • Hardware Configuration:")
        print(f"     - CPU Count: {vm.config.hardware.numCPU}")
        print(f"     - Memory MB: {vm.config.hardware.memoryMB}")
        
        # Check network adapters
        if vm.config.hardware.device:
            print(f"     - Network Adapters:")
            for device in vm.config.hardware.device:
                if isinstance(device, vim.vm.device.VirtualEthernetCard):
                    print(f"       • {device.__class__.__name__}")
                    print(f"         - MAC Address: {device.macAddress}")
                    print(f"         - Connected: {device.connectable.connected}")
                    print(f"         - Start Connected: {device.connectable.startConnected}")
                    if hasattr(device, 'backing') and device.backing:
                        if hasattr(device.backing, 'network'):
                            print(f"         - Network: {device.backing.network.name}")
                        elif hasattr(device.backing, 'port'):
                            print(f"         - Port Group: {device.backing.port.portgroupKey}")
    
    print(f"🔍 Network check complete for {vm_name}\n")

def check_vmware_customization_events(si, vm_name, timeout_minutes=5):
    """Check for VMware customization events and errors"""
    print(f"\n🔍 Checking VMware customization events for VM: {vm_name}")
    
    # Find the VM
    content = si.RetrieveContent()
    container = content.viewManager.CreateContainerView(content.rootFolder, [vim.VirtualMachine], True)
    vm = None
    for v in container.view:
        if v.name == vm_name:
            vm = v
            break
    container.Destroy()
    
    if not vm:
        print(f"❌ VM {vm_name} not found")
        return
    
    print(f"✅ Found VM: {vm.name}")
    
    # Check for customization events
    event_manager = content.eventManager
    event_filter = vim.event.EventFilterSpec()
    event_filter.entity = vim.event.EventFilterSpec.ByEntity()
    event_filter.entity.entity = vm
    event_filter.entity.recursion = vim.event.EventFilterSpec.RecursionOption.all
    
    # Look for customization-related events
    customization_events = []
    try:
        events = event_manager.QueryEvents(event_filter)
        for event in events:
            if hasattr(event, 'fullFormattedMessage'):
                message = event.fullFormattedMessage
                if any(keyword in message.lower() for keyword in ['customization', 'guest', 'network', 'ip', 'dhcp']):
                    customization_events.append({
                        'time': event.createdTime,
                        'message': message,
                        'type': event.__class__.__name__
                    })
    except Exception as e:
        print(f"⚠️ Error querying events: {str(e)}")
    
    if customization_events:
        print(f"📋 Found {len(customization_events)} customization-related events:")
        for event in customization_events[-5:]:  # Show last 5 events
            print(f"   • {event['time']}: {event['type']} - {event['message']}")
    else:
        print(f"📋 No customization-related events found")
    
    # Check guest tools status and customization status
    if vm.guest:
        print(f"🔧 Guest Tools Status: {vm.guest.toolsRunningStatus}")
        print(f"🔧 Guest Tools Version: {vm.guest.toolsVersion}")
        print(f"🔧 Guest OS: {vm.guest.guestFamily}")
        print(f"🔧 Guest ID: {vm.guest.guestId}")
        
        # Check for any guest tools errors
        if hasattr(vm.guest, 'toolsStatus'):
            print(f"🔧 Tools Status: {vm.guest.toolsStatus}")
        
        # Check for customization status
        if hasattr(vm.guest, 'customizationStatus'):
            print(f"🔧 Customization Status: {vm.guest.customizationStatus}")
    
    # Check VM configuration for guest OS
    if vm.config:
        print(f"🔧 VM Guest ID: {vm.config.guestId}")
        print(f"🔧 VM Version: {vm.config.version}")
        
        # Check for any advanced settings that might affect customization
        if hasattr(vm.config, 'extraConfig'):
            print(f"🔧 Extra Config Options:")
            for option in vm.config.extraConfig:
                if 'customization' in option.key.lower() or 'guest' in option.key.lower():
                    print(f"   • {option.key}: {option.value}")
    
    print(f"🔍 Customization event check complete for {vm_name}\n")

def clone_vm_with_customization(si, source_vm, clone_name, customization_params=None):
    """Clone a VM with full customization using Ansible's approach"""
    print(f"🔧 Cloning {source_vm.name} to {clone_name} with customization...")
    
    try:
        content = si.RetrieveContent()
        
        # Get available resources
        resources = get_available_resources(si)
        if not resources:
            return None
        
        # Create clone specification
        clone_spec = vim.vm.CloneSpec()
        clone_spec.location = vim.vm.RelocateSpec()
        
        # Set datastore
        if 'datastore_name' in customization_params:
            datastore_name = customization_params['datastore_name']
            datastore_obj = None
            for ds in resources.get('datastores', []):
                if ds.name == datastore_name:
                    datastore_obj = ds
                    break
            if datastore_obj:
                clone_spec.location.datastore = datastore_obj
                print(f"🔧 Using specified datastore: {datastore_name}")
            else:
                print(f"⚠️ Specified datastore '{datastore_name}' not found, using first available")
                if resources.get('datastores'):
                    clone_spec.location.datastore = resources['datastores'][0]
        else:
            # Use first available datastore
            if resources.get('datastores'):
                clone_spec.location.datastore = resources['datastores'][0]
                print(f"🔧 Using datastore: {resources['datastores'][0].name}")
        
        # Set resource pool
        if resources.get('resource_pools'):
            clone_spec.location.pool = resources['resource_pools'][0]
            print(f"🔧 Using resource pool: {resources['resource_pools'][0].name}")
        
        # Set host
        if resources.get('hosts'):
            clone_spec.location.host = resources['hosts'][0]
            print(f"🔧 Using host: {resources['hosts'][0].name}")
        
        # Configure hardware customization
        if any(k in customization_params for k in ['cpu_count', 'memory_mb', 'disk_size_gb', 'ip_address', 'netmask', 'gateway']):
            clone_spec.config = vim.vm.ConfigSpec()
            clone_spec.config.deviceChange = []
            
            # CPU customization
            if 'cpu_count' in customization_params:
                clone_spec.config.numCPUs = customization_params['cpu_count']
                print(f"🔧 Setting CPU count to {customization_params['cpu_count']}")
            
            # Memory customization
            if 'memory_mb' in customization_params:
                clone_spec.config.memoryMB = customization_params['memory_mb']
                print(f"🔧 Setting memory to {customization_params['memory_mb']} MB")
            
            # Network adapter configuration - Configure the hardware network adapter
            if any(k in customization_params for k in ['ip_address', 'netmask', 'gateway', 'network_name']):
                print(f"🔧 Configuring network adapter hardware...")
                
                # Find the network
                network_obj = None
                if 'network_name' in customization_params:
                    for network in resources.get('networks', []):
                        if network.name == customization_params['network_name']:
                            network_obj = network
                            break
                
                # If network not found, use the first available
                if not network_obj and resources.get('networks'):
                    network_obj = resources['networks'][0]
                
                if network_obj:
                    # Configure each network adapter in the source VM
                    for i, device in enumerate(source_vm.config.hardware.device):
                        if isinstance(device, vim.vm.device.VirtualEthernetCard):
                            print(f"   • Configuring network adapter {i}: {device.__class__.__name__}")
                            
                            # Create network adapter spec
                            nic_spec = vim.vm.device.VirtualDeviceSpec()
                            nic_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.edit
                            nic_spec.device = device
                            
                            # Ensure the adapter is connected to the right network
                            if hasattr(network_obj, 'portKeys'):
                                # Distributed virtual switch
                                print(f"     - Connecting to distributed port group: {network_obj.name}")
                                nic_spec.device.backing = vim.vm.device.VirtualEthernetCard.DistributedVirtualPortBackingInfo()
                                nic_spec.device.backing.port = vim.dvs.PortConnection()
                                nic_spec.device.backing.port.portgroupKey = network_obj.key
                                nic_spec.device.backing.port.switchUuid = network_obj.config.distributedVirtualSwitch.uuid
                            else:
                                # Standard switch
                                print(f"     - Connecting to standard switch: {network_obj.name}")
                                nic_spec.device.backing = vim.vm.device.VirtualEthernetCard.NetworkBackingInfo()
                                nic_spec.device.backing.network = network_obj
                                nic_spec.device.backing.deviceName = network_obj.name
                            
                            # Ensure the adapter is connected and starts connected
                            nic_spec.device.connectable.connected = True
                            nic_spec.device.connectable.startConnected = True
                            nic_spec.device.connectable.allowGuestControl = True
                            
                            clone_spec.config.deviceChange.append(nic_spec)
                            print(f"     - Network adapter {i} configured for {network_obj.name}")
            
            # Disk customization (if specified)
            if 'disk_size_gb' in customization_params:
                # Find the first disk and resize it
                for device in source_vm.config.hardware.device:
                    if isinstance(device, vim.vm.device.VirtualDisk):
                        disk_spec = vim.vm.device.VirtualDeviceSpec()
                        disk_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.edit
                        disk_spec.device = device
                        disk_spec.device.capacityInKB = customization_params['disk_size_gb'] * 1024 * 1024
                        clone_spec.config.deviceChange.append(disk_spec)
                        print(f"🔧 Setting disk size to {customization_params['disk_size_gb']} GB")
                        break
        
        # Add guest customization if network parameters are specified
        if customization_params and any(k in customization_params for k in ['hostname', 'ip_address', 'netmask', 'gateway']):
            clone_spec.customization = vim.vm.customization.Specification()
            
            # Global IP settings (required for Linux customization)
            clone_spec.customization.globalIPSettings = vim.vm.customization.GlobalIPSettings()
            if 'gateway' in customization_params:
                clone_spec.customization.globalIPSettings.dnsServerList = ['8.8.8.8', '8.8.4.4']
            
            # Linux customization - be explicit about Ubuntu
            clone_spec.customization.identity = vim.vm.customization.LinuxPrep()
            
            if 'hostname' in customization_params:
                clone_spec.customization.identity.hostName = vim.vm.customization.FixedName(name=customization_params['hostname'])
                print(f"🔧 Setting hostname to {customization_params['hostname']}")
            
            # Set domain if specified
            if 'domain' in customization_params:
                clone_spec.customization.identity.domain = customization_params['domain']
                print(f"🔧 Setting domain to {customization_params['domain']}")
            
            # Network configuration - Use Ansible's exact approach
            clone_spec.customization.nicSettingMap = []
            
            # Find the network
            network_obj = None
            if 'network_name' in customization_params:
                for network in resources.get('networks', []):
                    if network.name == customization_params['network_name']:
                        network_obj = network
                        break
            
            # If network not found, use the first available
            if not network_obj and resources.get('networks'):
                network_obj = resources['networks'][0]
            
            if network_obj:
                # Create adapter mapping exactly like Ansible does
                guest_map = vim.vm.customization.AdapterMapping()
                guest_map.adapter = vim.vm.customization.IPSettings()
                
                # IP assignment logic - exactly like Ansible
                if 'ip_address' in customization_params and 'netmask' in customization_params:
                    guest_map.adapter.ip = vim.vm.customization.FixedIp()
                    guest_map.adapter.ip.ipAddress = str(customization_params['ip_address'])
                    guest_map.adapter.subnetMask = str(customization_params['netmask'])
                    print(f"🔧 Setting fixed IP: {customization_params['ip_address']}/{customization_params['netmask']}")
                    
                    # For Ubuntu/Linux, we need to be more explicit about static IP
                    # Set DNS servers on the adapter level
                    guest_map.adapter.dnsServerList = ['8.8.8.8', '8.8.4.4']
                    print(f"🔧 Setting DNS servers on adapter: 8.8.8.8, 8.8.4.4")
                else:
                    # Use DHCP if no IP specified
                    guest_map.adapter.ip = vim.vm.customization.DhcpIpGenerator()
                    print(f"🔧 Using DHCP for IP assignment")
                
                # Gateway
                if 'gateway' in customization_params:
                    guest_map.adapter.gateway = [customization_params['gateway']]
                    print(f"🔧 Setting gateway to {customization_params['gateway']}")
                
                clone_spec.customization.nicSettingMap.append(guest_map)
                print(f"🔧 Network adapter configured for: {network_obj.name}")
                
                # Debug the customization spec
                print(f"🔧 Customization spec details:")
                print(f"   • Global IP Settings: {clone_spec.customization.globalIPSettings}")
                print(f"   • Identity: {clone_spec.customization.identity}")
                print(f"   • NIC Settings Count: {len(clone_spec.customization.nicSettingMap)}")
                for i, nic in enumerate(clone_spec.customization.nicSettingMap):
                    print(f"   • NIC {i}: {nic.adapter}")
                    if hasattr(nic.adapter, 'ip'):
                        print(f"     - IP: {nic.adapter.ip}")
                        if hasattr(nic.adapter.ip, 'ipAddress'):
                            print(f"       - IP Address: {nic.adapter.ip.ipAddress}")
                    if hasattr(nic.adapter, 'subnetMask'):
                        print(f"     - Netmask: {nic.adapter.subnetMask}")
                    if hasattr(nic.adapter, 'gateway'):
                        print(f"     - Gateway: {nic.adapter.gateway}")
                    if hasattr(nic.adapter, 'dnsServerList'):
                        print(f"     - DNS Servers: {nic.adapter.dnsServerList}")
                
                # Additional debugging - show the raw customization spec
                print(f"\n🔍 RAW CUSTOMIZATION SPECIFICATION:")
                print(f"   • Type: {type(clone_spec.customization)}")
                print(f"   • Identity Type: {type(clone_spec.customization.identity)}")
                print(f"   • Global IP Settings Type: {type(clone_spec.customization.globalIPSettings)}")
                print(f"   • NIC Setting Map Type: {type(clone_spec.customization.nicSettingMap)}")
                print(f"   • NIC Setting Map Length: {len(clone_spec.customization.nicSettingMap)}")
                
                # Check if we need to map to specific network adapters
                print(f"\n🔍 SOURCE VM NETWORK ADAPTERS:")
                if source_vm.config and source_vm.config.hardware and source_vm.config.hardware.device:
                    for i, device in enumerate(source_vm.config.hardware.device):
                        if isinstance(device, vim.vm.device.VirtualEthernetCard):
                            print(f"   • Adapter {i}: {device.__class__.__name__}")
                            print(f"     - MAC: {device.macAddress}")
                            print(f"     - Connected: {device.connectable.connected}")
                            if hasattr(device, 'backing') and device.backing:
                                if hasattr(device.backing, 'network'):
                                    print(f"     - Network: {device.backing.network.name}")
                                elif hasattr(device.backing, 'port'):
                                    print(f"     - Port Group: {device.backing.port.portgroupKey}")
                
                # Try a different approach - create one adapter mapping per network adapter
                print(f"\n🔧 TRYING ALTERNATIVE APPROACH: One adapter mapping per network adapter")
                clone_spec.customization.nicSettingMap = []
                
                # Create one adapter mapping for each network adapter in the source VM
                if source_vm.config and source_vm.config.hardware and source_vm.config.hardware.device:
                    for i, device in enumerate(source_vm.config.hardware.device):
                        if isinstance(device, vim.vm.device.VirtualEthernetCard):
                            print(f"   • Creating mapping for adapter {i}: {device.__class__.__name__}")
                            
                            guest_map = vim.vm.customization.AdapterMapping()
                            guest_map.adapter = vim.vm.customization.IPSettings()
                            
                            # IP assignment logic - exactly like Ansible
                            if 'ip_address' in customization_params and 'netmask' in customization_params:
                                guest_map.adapter.ip = vim.vm.customization.FixedIp()
                                guest_map.adapter.ip.ipAddress = str(customization_params['ip_address'])
                                guest_map.adapter.subnetMask = str(customization_params['netmask'])
                                print(f"     - Setting fixed IP: {customization_params['ip_address']}/{customization_params['netmask']}")
                                
                                # For Ubuntu/Linux, we need to be more explicit about static IP
                                # Set DNS servers on the adapter level
                                guest_map.adapter.dnsServerList = ['8.8.8.8', '8.8.4.4']
                                print(f"     - Setting DNS servers on adapter: 8.8.8.8, 8.8.4.4")
                            else:
                                # Use DHCP if no IP specified
                                guest_map.adapter.ip = vim.vm.customization.DhcpIpGenerator()
                                print(f"     - Using DHCP for IP assignment")
                            
                            # Gateway
                            if 'gateway' in customization_params:
                                guest_map.adapter.gateway = [customization_params['gateway']]
                                print(f"     - Setting gateway to {customization_params['gateway']}")
                            
                            clone_spec.customization.nicSettingMap.append(guest_map)
                            print(f"     - Added adapter mapping {i}")
                
                print(f"   • Final NIC Setting Map Count: {len(clone_spec.customization.nicSettingMap)}")
        
        # Power off the VM before cloning
        if source_vm.runtime.powerState == 'poweredOn':
            print(f"🔌 Powering off source VM before cloning...")
            task = source_vm.PowerOff()
            wait_for_task(task)
            if task.info.state != 'success':
                print(f"❌ Failed to power off source VM: {task.info.error.msg}")
                return None
        
        # Clone the VM
        print(f"🚀 Starting VM clone...")
        task = source_vm.Clone(folder=source_vm.parent, name=clone_name, spec=clone_spec)
        wait_for_task(task)
        
        if task.info.state == 'success':
            cloned_vm = task.info.result
            print(f"✅ VM cloned successfully: {cloned_vm.name}")
            
            # Wait a bit for the clone to complete
            print("⏳ Waiting for clone to complete...")
            time.sleep(10)
            
            # Power on the VM
            print(f"🔌 Powering on {cloned_vm.name}...")
            task = cloned_vm.PowerOn()
            wait_for_task(task)
            
            if task.info.state == 'success':
                print(f"✅ VM powered on successfully")
                
                # Wait for guest tools and customization
                print("⏳ Waiting for guest tools and customization to complete...")
                time.sleep(30)
                
                # Check network configuration
                check_vm_network_config(si, cloned_vm.name)
                
                # Check VMware customization events
                check_vmware_customization_events(si, cloned_vm.name)
                
                # Show expected vs actual netplan configuration
                if 'ip_address' in customization_params and 'netmask' in customization_params and 'gateway' in customization_params:
                    show_expected_netplan_config(
                        customization_params['ip_address'],
                        customization_params['netmask'],
                        customization_params['gateway']
                    )
                
            else:
                print(f"❌ Failed to power on VM: {task.info.error.msg}")
        else:
            print(f"❌ Failed to clone VM: {task.info.error.msg}")
            return None
    
    except Exception as e:
        print(f"❌ Error cloning VM: {str(e)}")
        return None

def test_clone_vm_with_customization():
    """Test cloning a VM with full customization"""
    print("🚀 Testing VM cloning with customization...")
    
    # Connect to vCenter
    si = get_vsphere_client()
    if not si:
        return
    
    try:
        # Get available resources
        resources = get_available_resources(si)
        if not resources:
            return
        
        # Find a source VM to clone from
        source_vm = None
        for vm in resources.get('vms', []):
            if vm.runtime.powerState == 'poweredOff':
                source_vm = vm
                break
        
        if not source_vm:
            print("❌ No powered-off VM found to clone from")
            return
        
        print(f"✅ Found source VM: {source_vm.name}")
        
        # Customization parameters
        customization_params = {
            'hostname': 'test-clone-custom',
            'ip_address': '192.168.1.100',
            'netmask': '255.255.255.0',
            'gateway': '192.168.1.1',
            'network_name': 'VM Network',  # Adjust to your network name
            'cpu_count': 2,
            'memory_mb': 2048,
            'disk_size_gb': 20
        }
        
        # Clone the VM
        clone_name = f"{source_vm.name}-clone-custom"
        print(f"🔧 Cloning {source_vm.name} to {clone_name} with customization...")
        
        cloned_vm = clone_vm_with_customization(
            si, source_vm, clone_name, customization_params
        )
        
        if cloned_vm:
            print(f"✅ VM cloned successfully: {cloned_vm.name}")
            
            # Wait a bit for the clone to complete
            print("⏳ Waiting for clone to complete...")
            time.sleep(10)
            
            # Power on the VM
            print(f"🔌 Powering on {cloned_vm.name}...")
            task = cloned_vm.PowerOn()
            wait_for_task(task)
            
            if task.info.state == 'success':
                print(f"✅ VM powered on successfully")
                
                # Wait for guest tools and customization
                print("⏳ Waiting for guest tools and customization to complete...")
                time.sleep(30)
                
                # Check network configuration
                check_vm_network_config(si, cloned_vm.name)
                
                # Check VMware customization events
                check_vmware_customization_events(si, cloned_vm.name)
                
                # Show expected vs actual netplan configuration
                if 'ip_address' in customization_params and 'netmask' in customization_params and 'gateway' in customization_params:
                    show_expected_netplan_config(
                        customization_params['ip_address'],
                        customization_params['netmask'],
                        customization_params['gateway']
                    )
                
            else:
                print(f"❌ Failed to power on VM: {task.info.error.msg}")
        else:
            print("❌ Failed to clone VM")
    
    finally:
        si.Disconnect()
        print("🔌 Disconnected from vCenter")

if __name__ == "__main__":
    print("🧪 VMware vCenter VM Operations Test (pyvmomi)")
    print("=" * 50)
    print("This test will:")
    print("1. List all VMs with detailed information")
    print("2. Simulate VM cloning (no actual VM created)")
    print("3. Simulate VM cloning with full customization")
    print("4. Actually create a VM with customization")
    print("=" * 50)
    
    # Test 1: List VMs
    test_list_vms()
    
    # Test 2: Simple clone simulation
    test_simple_vm_clone_simulation()
    
    # Test 3: Clone with customization simulation
    test_vm_clone_with_customization_simulation()
    
    # Test 4: Actual VM creation
    test_actual_vm_creation()
    
    # Test 5: Clone VM with customization
    test_clone_vm_with_customization()
    
    print("\n✅ Test completed!") 