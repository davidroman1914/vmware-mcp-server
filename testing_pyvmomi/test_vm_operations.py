#!/usr/bin/env python3
"""
Test script for VMware vCenter operations using pyvmomi.
Focuses on VM creation from templates with customization.
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

def list_vms():
    """List all VMs with basic information."""
    print(f"\n📋 Listing all VMs...")
    
    try:
        service_instance = get_vsphere_client()
        content = service_instance.RetrieveContent()
        
        # Get all VMs
        container = content.viewManager.CreateContainerView(
            content.rootFolder, [vim.VirtualMachine], True
        )
        vms = container.view
        
        if not vms:
            print("❌ No VMs found")
            return []
        
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
        return []

def get_available_resources(si):
    """Get available resources for VM placement."""
    print(f"🔍 Gathering available resources...")
    
    try:
        content = si.RetrieveContent()
        resources = {}
        
        # Get datacenters
        datacenters = []
        for dc in content.rootFolder.childEntity:
            if hasattr(dc, 'vmFolder'):
                datacenters.append(dc)
        
        if not datacenters:
            print("❌ No datacenters found")
            return None
        
        # Use first datacenter
        datacenter = datacenters[0]
        print(f"✅ Using datacenter: {datacenter.name}")
        
        # Get hosts
        hosts = []
        for host in datacenter.hostFolder.childEntity:
            if hasattr(host, 'host'):
                for h in host.host:
                    hosts.append(h)
        
        if hosts:
            resources['hosts'] = hosts
            print(f"✅ Found {len(hosts)} hosts")
        
        # Get resource pools
        resource_pools = []
        for host in hosts:
            if hasattr(host, 'parent') and hasattr(host.parent, 'resourcePool'):
                resource_pools.append(host.parent.resourcePool)
        
        if resource_pools:
            resources['resource_pools'] = resource_pools
            print(f"✅ Found {len(resource_pools)} resource pools")
        
        # Get datastores
        datastores = []
        for host in hosts:
            if hasattr(host, 'datastore'):
                datastores.extend(host.datastore)
        
        if datastores:
            resources['datastores'] = datastores
            print(f"✅ Found {len(datastores)} datastores")
        
        # Get networks
        networks = []
        for host in hosts:
            if hasattr(host, 'network'):
                networks.extend(host.network)
        
        if networks:
            resources['networks'] = networks
            print(f"✅ Found {len(networks)} networks")
        
        # Get VMs
        vms = []
        for dc in datacenters:
            if hasattr(dc, 'vmFolder'):
                container = content.viewManager.CreateContainerView(dc.vmFolder, [vim.VirtualMachine], True)
                vms.extend(container.view)
                container.Destroy()
        
        if vms:
            resources['vms'] = vms
            print(f"✅ Found {len(vms)} VMs")
        
        return resources
        
    except Exception as e:
        print(f"❌ Error gathering resources: {str(e)}")
        return None

def wait_for_task(task):
    """Wait for a VMware task to complete."""
    while task.info.state not in ['success', 'error']:
        time.sleep(1)
    return task

def create_vm_from_template(source_vm, resources, customization_params=None):
    """Create a VM from a template with customization."""
    print(f"🔧 Creating VM from template: {source_vm.name}")
    
    try:
        # Create clone specification
        clone_spec = vim.vm.CloneSpec()
        clone_spec.location = vim.vm.RelocateSpec()
        clone_spec.template = False
        
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
            
            # Network adapter configuration
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
            
            # Linux customization
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
            
            # Count actual network adapters in source VM
            network_adapters = []
            if source_vm.config and source_vm.config.hardware and source_vm.config.hardware.device:
                for device in source_vm.config.hardware.device:
                    if isinstance(device, vim.vm.device.VirtualEthernetCard):
                        network_adapters.append(device)
            
            print(f"🔍 Found {len(network_adapters)} network adapters in source VM")
            
            if not network_adapters:
                print(f"⚠️ No network adapters found in source VM, creating single DHCP mapping")
                # Create a single DHCP adapter mapping if no adapters found
                guest_map = vim.vm.customization.AdapterMapping()
                guest_map.adapter = vim.vm.customization.IPSettings()
                guest_map.adapter.ip = vim.vm.customization.DhcpIpGenerator()
                clone_spec.customization.nicSettingMap.append(guest_map)
            else:
                # Create one adapter mapping for each network adapter in the source VM
                for i, device in enumerate(network_adapters):
                    print(f"   • Creating mapping for adapter {i}: {device.__class__.__name__}")
                    
                    guest_map = vim.vm.customization.AdapterMapping()
                    guest_map.adapter = vim.vm.customization.IPSettings()
                    
                    # The adapter mapping is done by position/index, not by setting adapter to device
                    # VMware maps the first adapter mapping to the first network adapter, etc.
                    print(f"     - Mapping to adapter {i}: {device.__class__.__name__} (MAC: {device.macAddress})")
                    
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
            print(f"   • Network Adapters Count: {len(network_adapters)}")
            
            # Verify the counts match
            if len(clone_spec.customization.nicSettingMap) != len(network_adapters) and network_adapters:
                print(f"⚠️ WARNING: Adapter mapping count ({len(clone_spec.customization.nicSettingMap)}) doesn't match network adapter count ({len(network_adapters)})")
                print(f"   • This might cause VMware customization errors")
        
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
        task = source_vm.Clone(folder=source_vm.parent, name=customization_params.get('hostname', f"{source_vm.name}-clone"), spec=clone_spec)
        wait_for_task(task)
        
        if task.info.state == 'success':
            cloned_vm = task.info.result
            print(f"✅ VM cloned successfully: {cloned_vm.name}")
            
            # Power on the VM
            print(f"🔌 Powering on {cloned_vm.name}...")
            power_task = cloned_vm.PowerOn()
            wait_for_task(power_task)
            
            if power_task.info.state == 'success':
                print(f"✅ VM powered on successfully")
                
                # Wait for guest tools to be ready
                print("⏳ Waiting for guest tools to be ready...")
                max_wait = 120  # 2 minutes max wait
                wait_time = 0
                while wait_time < max_wait:
                    if cloned_vm.guest and cloned_vm.guest.toolsRunningStatus == 'guestToolsRunning':
                        print(f"✅ Guest tools are running")
                        break
                    time.sleep(5)
                    wait_time += 5
                    print(f"   • Waiting... ({wait_time}s)")
                
                if wait_time >= max_wait:
                    print(f"⚠️ Guest tools not ready after {max_wait}s, but VM is powered on")
                
                # Show final VM status
                print(f"\n🎉 VM Creation Complete!")
                print(f"   • Name: {cloned_vm.name}")
                print(f"   • ID: {cloned_vm._moId}")
                print(f"   • Power State: {cloned_vm.runtime.powerState}")
                if cloned_vm.guest:
                    print(f"   • Guest Tools: {cloned_vm.guest.toolsRunningStatus}")
                    print(f"   • IP Addresses: {cloned_vm.guest.ipAddress}")
                
            else:
                print(f"❌ Failed to power on VM: {power_task.info.error.msg}")
            
            return cloned_vm
        else:
            print(f"❌ Failed to clone VM: {task.info.error.msg}")
            return None
    
    except Exception as e:
        print(f"❌ Error cloning VM: {str(e)}")
        return None

def test_create_vm_from_template():
    """Test creating a VM from a template with customization."""
    print("🚀 Testing VM creation from template...")
    
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
            'hostname': 'test-vm-from-template',
            'ip_address': '192.168.1.100',
            'netmask': '255.255.255.0',
            'gateway': '192.168.1.1',
            'network_name': 'VM Network',  # Adjust to your network name
            'cpu_count': 2,
            'memory_mb': 2048,
            'disk_size_gb': 20
        }
        
        # Create the VM
        new_vm = create_vm_from_template(source_vm, resources, customization_params)
        
        if new_vm:
            print(f"✅ VM created successfully: {new_vm.name}")
            print(f"   • ID: {new_vm._moId}")
            print(f"   • Power State: {new_vm.runtime.powerState}")
            print(f"   • You can now power it on in vCenter")
        else:
            print("❌ Failed to create VM")
    
    finally:
        Disconnect(si)
        print("🔌 Disconnected from vCenter")

if __name__ == "__main__":
    print("🧪 VMware vCenter VM Creation Test (pyvmomi)")
    print("=" * 50)
    print("This test will create a VM from a template with customization")
    print("=" * 50)
    
    # Test VM creation from template
    test_create_vm_from_template()
    
    print("\n✅ Test completed!") 