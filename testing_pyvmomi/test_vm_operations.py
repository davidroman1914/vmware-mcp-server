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
        
        # Add hardware customization if specified
        if customization_params and ('cpu_count' in customization_params or 'memory_mb' in customization_params or 'disk_size_gb' in customization_params):
            clone_spec.config = vim.vm.ConfigSpec()
            
            if 'cpu_count' in customization_params:
                clone_spec.config.numCPUs = customization_params['cpu_count']
                print(f"🔧 Setting CPU count to {customization_params['cpu_count']} cores")
            
            if 'memory_mb' in customization_params:
                clone_spec.config.memoryMB = customization_params['memory_mb']
                print(f"🔧 Setting memory to {customization_params['memory_mb']} MB")
            
            # Add disk customization if specified
            if 'disk_size_gb' in customization_params:
                # Get the first disk and resize it
                if hasattr(source_vm, 'config') and source_vm.config and hasattr(source_vm.config, 'hardware'):
                    for device in source_vm.config.hardware.device:
                        if isinstance(device, vim.vm.device.VirtualDisk):
                            # Create a device change spec for the disk
                            disk_spec = vim.vm.device.VirtualDeviceSpec()
                            disk_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.edit
                            disk_spec.device = device
                            
                            # Set the new size in KB (convert GB to KB)
                            new_size_kb = customization_params['disk_size_gb'] * 1024 * 1024
                            disk_spec.device.capacityInKB = new_size_kb
                            
                            print(f"🔧 Setting disk size to {customization_params['disk_size_gb']} GB ({new_size_kb} KB)")
                            
                            # Add the device change to the config spec
                            if not hasattr(clone_spec.config, 'deviceChange'):
                                clone_spec.config.deviceChange = []
                            clone_spec.config.deviceChange.append(disk_spec)
                            break
        
        # Add guest customization if network parameters are specified
        if customization_params and any(k in customization_params for k in ['hostname', 'ip_address', 'netmask', 'gateway']):
            clone_spec.customization = vim.vm.customization.Specification()
            
            # Add global IP settings (required for Linux customization)
            clone_spec.customization.globalIPSettings = vim.vm.customization.GlobalIPSettings()
            if 'gateway' in customization_params:
                clone_spec.customization.globalIPSettings.dnsServerList = ['8.8.8.8', '8.8.4.4']  # Default DNS servers
            
            # Linux customization
            clone_spec.customization.identity = vim.vm.customization.LinuxPrep()
            
            if 'hostname' in customization_params:
                clone_spec.customization.identity.hostName = vim.vm.customization.FixedName(name=customization_params['hostname'])
                print(f"🔧 Setting hostname to {customization_params['hostname']}")
            
            # Network configuration
            if any(k in customization_params for k in ['ip_address', 'netmask', 'gateway']):
                clone_spec.customization.nicSettingMap = []
                
                # Find the network
                network_obj = None
                if 'network_name' in customization_params:
                    # Try to find the network by name
                    for network in resources.get('networks', []):
                        if network.name == customization_params['network_name']:
                            network_obj = network
                            break
                
                # If network not found, use the first available
                if not network_obj and resources.get('networks'):
                    network_obj = resources['networks'][0]
                
                if network_obj:
                    nic_setting = vim.vm.customization.AdapterMapping()
                    nic_setting.adapter = vim.vm.customization.IPSettings()
                    
                    # Try FixedIp first, fallback to DHCP if it fails
                    if 'ip_address' in customization_params:
                        try:
                            nic_setting.adapter.ip = vim.vm.customization.FixedIp(ipAddress=customization_params['ip_address'])
                            print(f"🔧 Setting fixed IP address to {customization_params['ip_address']}")
                        except Exception as e:
                            print(f"⚠️ Failed to set fixed IP, using DHCP: {str(e)}")
                            nic_setting.adapter.ip = vim.vm.customization.DhcpIpGenerator()
                            print(f"🔧 Using DHCP for IP assignment")
                    else:
                        # Use DHCP if no IP specified
                        nic_setting.adapter.ip = vim.vm.customization.DhcpIpGenerator()
                        print(f"🔧 Using DHCP for IP address")
                    
                    if 'netmask' in customization_params:
                        nic_setting.adapter.subnetMask = customization_params['netmask']
                        print(f"🔧 Setting netmask to {customization_params['netmask']}")
                    
                    if 'gateway' in customization_params:
                        nic_setting.adapter.gateway = [customization_params['gateway']]
                        print(f"🔧 Setting gateway to {customization_params['gateway']}")
                    
                    # Set DNS servers if gateway is provided
                    if 'gateway' in customization_params:
                        nic_setting.adapter.dnsServerList = ['8.8.8.8', '8.8.4.4']
                        print(f"🔧 Setting DNS servers to 8.8.8.8, 8.8.4.4")
                    
                    clone_spec.customization.nicSettingMap.append(nic_setting)
                    print(f"🔧 Network adapter configured for: {network_obj.name}")
                    
                    # Add debugging info
                    print(f"🔧 Network customization details:")
                    print(f"   • Network: {network_obj.name}")
                    print(f"   • IP Method: {'Fixed IP' if 'ip_address' in customization_params else 'DHCP'}")
                    if 'ip_address' in customization_params:
                        print(f"   • Requested IP: {customization_params['ip_address']}")
                    if 'netmask' in customization_params:
                        print(f"   • Netmask: {customization_params['netmask']}")
                    if 'gateway' in customization_params:
                        print(f"   • Gateway: {customization_params['gateway']}")
                else:
                    print(f"⚠️ No network found, using DHCP for all adapters")
                    # Create a DHCP adapter mapping if no specific network found
                    nic_setting = vim.vm.customization.AdapterMapping()
                    nic_setting.adapter = vim.vm.customization.IPSettings()
                    nic_setting.adapter.ip = vim.vm.customization.DhcpIpGenerator()
                    clone_spec.customization.nicSettingMap.append(nic_setting)
        
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
    
    print("\n✅ Test completed!") 