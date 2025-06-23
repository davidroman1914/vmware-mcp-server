#!/usr/bin/env python3
"""
VM Creation Debug Script
Hardcoded values to test VM creation and isolate issues
"""

import os
import ssl
import sys
from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim

def connect_to_vcenter():
    """Connect to vCenter using pyvmomi."""
    try:
        host = os.getenv('VCENTER_HOST')
        user = os.getenv('VCENTER_USER')
        password = os.getenv('VCENTER_PASSWORD')
        
        if not all([host, user, password]):
            print("❌ Error: Missing environment variables")
            return None
        
        print(f"🔗 Connecting to vCenter: {host}")
        
        # Create SSL context with optimizations
        context = ssl.SSLContext(ssl.PROTOCOL_TLS)
        context.verify_mode = ssl.CERT_NONE
        context.check_hostname = False
        
        service_instance = SmartConnect(
            host=host,
            user=user,
            pwd=password,
            sslContext=context
        )
        
        print("✅ Successfully connected to vCenter")
        return service_instance
        
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return None

def find_template(service_instance, template_name):
    """Find template by name."""
    try:
        content = service_instance.RetrieveContent()
        container = content.viewManager.CreateContainerView(
            content.rootFolder, [vim.VirtualMachine], True
        )
        
        for vm in container.view:
            if vm.config.template and vm.name == template_name:
                print(f"✅ Found template: {template_name}")
                return vm
        
        print(f"❌ Template '{template_name}' not found")
        return None
        
    except Exception as e:
        print(f"❌ Error finding template: {e}")
        return None

def find_datastore(service_instance, datastore_name):
    """Find datastore by name."""
    try:
        content = service_instance.RetrieveContent()
        container = content.viewManager.CreateContainerView(
            content.rootFolder, [vim.Datastore], True
        )
        
        for ds in container.view:
            if ds.name == datastore_name:
                print(f"✅ Found datastore: {datastore_name}")
                return ds
        
        print(f"❌ Datastore '{datastore_name}' not found")
        return None
        
    except Exception as e:
        print(f"❌ Error finding datastore: {e}")
        return None

def find_network(service_instance, network_name):
    """Find network by name."""
    try:
        content = service_instance.RetrieveContent()
        container = content.viewManager.CreateContainerView(
            content.rootFolder, [vim.dvs.DistributedVirtualPortgroup, vim.Network], True
        )
        
        for net in container.view:
            if net.name == network_name:
                print(f"✅ Found network: {network_name}")
                return net
        
        print(f"❌ Network '{network_name}' not found")
        return None
        
    except Exception as e:
        print(f"❌ Error finding network: {e}")
        return None

def find_resource_pool(service_instance):
    """Find the default resource pool."""
    try:
        content = service_instance.RetrieveContent()
        container = content.viewManager.CreateContainerView(
            content.rootFolder, [vim.ClusterComputeResource], True
        )
        
        for cluster in container.view:
            if cluster.resourcePool:
                print(f"✅ Found resource pool: {cluster.resourcePool.name}")
                return cluster.resourcePool
        
        print("❌ No resource pool found")
        return None
        
    except Exception as e:
        print(f"❌ Error finding resource pool: {e}")
        return None

def test_simple_clone(template, new_vm_name, resource_pool):
    """Test simple clone without any customizations."""
    print(f"\n🧪 Testing simple clone: {new_vm_name}")
    
    try:
        # Create relocation spec with resource pool (required)
        relospec = vim.vm.RelocateSpec()
        relospec.pool = resource_pool
        
        # Create clone spec
        clone_spec = vim.vm.CloneSpec()
        clone_spec.location = relospec
        clone_spec.powerOn = False
        clone_spec.template = False
        
        print("📋 Clone spec with resource pool created successfully")
        
        # Clone the VM
        task = template.Clone(folder=template.parent, name=new_vm_name, spec=clone_spec)
        print("🔄 Clone task started...")
        
        # Wait for task to complete
        while task.info.state not in [vim.TaskInfo.State.success, vim.TaskInfo.State.error]:
            pass
        
        if task.info.state == vim.TaskInfo.State.success:
            print(f"✅ Simple clone successful: {new_vm_name}")
            return True
        else:
            print(f"❌ Simple clone failed: {task.info.error.msg}")
            return False
            
    except Exception as e:
        print(f"❌ Simple clone error: {e}")
        return False

def test_with_datastore(template, new_vm_name, datastore, resource_pool):
    """Test clone with datastore specification."""
    print(f"\n🧪 Testing clone with datastore: {new_vm_name}")
    
    try:
        # Create relocation spec with both datastore and resource pool
        relospec = vim.vm.RelocateSpec()
        relospec.datastore = datastore
        relospec.pool = resource_pool
        
        # Create clone spec
        clone_spec = vim.vm.CloneSpec()
        clone_spec.location = relospec
        clone_spec.powerOn = False
        clone_spec.template = False
        
        print("📋 Clone spec with datastore and resource pool created successfully")
        
        # Clone the VM
        task = template.Clone(folder=template.parent, name=new_vm_name, spec=clone_spec)
        print("🔄 Clone task with datastore started...")
        
        # Wait for task to complete
        while task.info.state not in [vim.TaskInfo.State.success, vim.TaskInfo.State.error]:
            pass
        
        if task.info.state == vim.TaskInfo.State.success:
            print(f"✅ Clone with datastore successful: {new_vm_name}")
            return True
        else:
            print(f"❌ Clone with datastore failed: {task.info.error.msg}")
            return False
            
    except Exception as e:
        print(f"❌ Clone with datastore error: {e}")
        return False

def test_with_customizations(template, new_vm_name, datastore, network, resource_pool):
    """Test clone with customizations."""
    print(f"\n🧪 Testing clone with customizations: {new_vm_name}")
    
    try:
        # Create relocation spec with both datastore and resource pool
        relospec = vim.vm.RelocateSpec()
        relospec.datastore = datastore
        relospec.pool = resource_pool
        
        # Create clone spec
        clone_spec = vim.vm.CloneSpec()
        clone_spec.location = relospec
        clone_spec.powerOn = False
        clone_spec.template = False
        
        # Create config spec for customizations
        config_spec = vim.vm.ConfigSpec()
        config_spec.memoryMB = 2 * 1024  # 2GB
        config_spec.numCPUs = 2
        
        print("📋 Config spec with memory/CPU created successfully")
        
        # Add network customization
        if network:
            nic_spec = vim.vm.device.VirtualDeviceSpec()
            nic_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
            nic_spec.device = vim.vm.device.VirtualVmxnet3()
            nic_spec.device.key = -1
            nic_spec.device.deviceInfo = vim.Description()
            nic_spec.device.deviceInfo.label = "Network adapter 1"
            nic_spec.device.deviceInfo.summary = "PROD VMs"
            
            if isinstance(network, vim.dvs.DistributedVirtualPortgroup):
                nic_spec.device.backing = vim.vm.device.VirtualEthernetCard.DistributedVirtualPortBackingInfo()
                nic_spec.device.backing.port = vim.dvs.PortConnection()
                nic_spec.device.backing.port.portgroupKey = network.key
                nic_spec.device.backing.port.switchUuid = network.config.distributedVirtualSwitch.uuid
            else:
                nic_spec.device.backing = vim.vm.device.VirtualEthernetCard.NetworkBackingInfo()
                nic_spec.device.backing.network = network
                nic_spec.device.backing.deviceName = "PROD VMs"
            
            config_spec.deviceChange = [nic_spec]
            print("📋 Network adapter spec created successfully")
        
        # Attach config spec to clone spec
        clone_spec.config = config_spec
        
        # Clone the VM
        task = template.Clone(folder=template.parent, name=new_vm_name, spec=clone_spec)
        print("🔄 Clone task with customizations started...")
        
        # Wait for task to complete
        while task.info.state not in [vim.TaskInfo.State.success, vim.TaskInfo.State.error]:
            pass
        
        if task.info.state == vim.TaskInfo.State.success:
            print(f"✅ Clone with customizations successful: {new_vm_name}")
            return True
        else:
            print(f"❌ Clone with customizations failed: {task.info.error.msg}")
            return False
            
    except Exception as e:
        print(f"❌ Clone with customizations error: {e}")
        return False

def create_custom_vm(template, new_vm_name, datastore, network, resource_pool):
    """Create a single VM with all customizations: memory, CPU, disk, and IP."""
    print(f"\n🚀 Creating custom VM: {new_vm_name}")
    print("📋 Specifications:")
    print("   - Memory: 4 GB")
    print("   - CPU: 2 cores")
    print("   - Disk: 50 GB")
    print("   - IP: 10.60.132.105")
    print("   - Network: PROD VMs")
    print("   - Powered off by default")
    
    try:
        # Create relocation spec with both datastore and resource pool
        relospec = vim.vm.RelocateSpec()
        relospec.datastore = datastore
        relospec.pool = resource_pool
        
        # Create clone spec
        clone_spec = vim.vm.CloneSpec()
        clone_spec.location = relospec
        clone_spec.powerOn = False  # Keep powered off
        clone_spec.template = False
        
        # Create config spec for hardware customizations
        config_spec = vim.vm.ConfigSpec()
        config_spec.memoryMB = 4 * 1024  # 4GB
        config_spec.numCPUs = 2
        
        # Disk customization - resize the first disk
        for device in template.config.hardware.device:
            if isinstance(device, vim.vm.device.VirtualDisk):
                disk_spec = vim.vm.device.VirtualDeviceSpec()
                disk_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.edit
                disk_spec.device = device
                disk_spec.device.capacityInKB = 50 * 1024 * 1024  # 50GB in KB
                config_spec.deviceChange = [disk_spec]
                print("📋 Disk customization: 50GB")
                break
        
        # Network customization
        if network:
            # Find existing network adapter and update it
            for device in template.config.hardware.device:
                if isinstance(device, vim.vm.device.VirtualEthernetCard):
                    nic_spec = vim.vm.device.VirtualDeviceSpec()
                    nic_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.edit
                    nic_spec.device = device
                    
                    if isinstance(network, vim.dvs.DistributedVirtualPortgroup):
                        nic_spec.device.backing = vim.vm.device.VirtualEthernetCard.DistributedVirtualPortBackingInfo()
                        nic_spec.device.backing.port = vim.dvs.PortConnection()
                        nic_spec.device.backing.port.portgroupKey = network.key
                        nic_spec.device.backing.port.switchUuid = network.config.distributedVirtualSwitch.uuid
                    else:
                        nic_spec.device.backing = vim.vm.device.VirtualEthernetCard.NetworkBackingInfo()
                        nic_spec.device.backing.network = network
                        nic_spec.device.backing.deviceName = network.name
                    
                    # Add to device changes
                    if config_spec.deviceChange:
                        config_spec.deviceChange.append(nic_spec)
                    else:
                        config_spec.deviceChange = [nic_spec]
                    print("📋 Network customization: PROD VMs")
                    break
        
        # IP customization
        customizationspec = vim.vm.customization.Specification()
        
        # Identity
        identity = vim.vm.customization.LinuxPrep()
        identity.hostName = vim.vm.customization.FixedName(name=new_vm_name)
        identity.domain = vim.vm.customization.FixedName(name="local")
        customizationspec.identity = identity
        
        # Network interface with IP
        adapter_mapping = vim.vm.customization.AdapterMapping()
        adapter_mapping.adapter = vim.vm.customization.IPSettings()
        adapter_mapping.adapter.ip = vim.vm.customization.FixedIp(ipAddress="10.60.132.105")
        adapter_mapping.adapter.subnetMask = "255.255.255.0"
        adapter_mapping.adapter.gateway = ["10.60.132.1"]
        adapter_mapping.adapter.dnsServerList = ["8.8.8.8", "8.8.4.4"]
        
        customizationspec.nicSettingMap = [adapter_mapping]
        customizationspec.globalIPSettings = vim.vm.customization.GlobalIPSettings()
        customizationspec.globalIPSettings.dnsServerList = ["8.8.8.8", "8.8.4.4"]
        
        clone_spec.customization = customizationspec
        print("📋 IP customization: 10.60.132.105")
        
        # Attach config spec to clone spec
        clone_spec.config = config_spec
        
        print("🔄 Starting VM creation...")
        
        # Clone the VM
        task = template.Clone(folder=template.parent, name=new_vm_name, spec=clone_spec)
        
        # Wait for task to complete
        while task.info.state not in [vim.TaskInfo.State.success, vim.TaskInfo.State.error]:
            pass
        
        if task.info.state == vim.TaskInfo.State.success:
            new_vm = task.info.result
            print(f"✅ VM created successfully: {new_vm_name}")
            print(f"📊 VM Details:")
            print(f"   - Name: {new_vm.name}")
            print(f"   - Power State: {new_vm.runtime.powerState}")
            print(f"   - Memory: {new_vm.config.hardware.memoryMB} MB")
            print(f"   - CPU: {new_vm.config.hardware.numCPU} cores")
            print(f"   - IP: 10.60.132.105")
            print(f"   - Network: PROD VMs")
            return True
        else:
            print(f"❌ VM creation failed: {task.info.error.msg}")
            return False
            
    except Exception as e:
        print(f"❌ VM creation error: {e}")
        return False

def main():
    """Main debug function."""
    print("🚀 Starting VM Creation Debug Script")
    print("=" * 50)
    
    # Hardcoded values for testing
    TEMPLATE_NAME = "Ubuntu-Template-01"
    NEW_VM_NAME = "debug-test-vm-001"
    DATASTORE_NAME = "ova-inf-vh03-ds-1"
    NETWORK_NAME = "PROD VMs"
    
    print(f"📋 Test Configuration:")
    print(f"   Template: {TEMPLATE_NAME}")
    print(f"   New VM: {NEW_VM_NAME}")
    print(f"   Datastore: {DATASTORE_NAME}")
    print(f"   Network: {NETWORK_NAME}")
    print()
    
    # Connect to vCenter
    service_instance = connect_to_vcenter()
    if not service_instance:
        print("❌ Cannot proceed without vCenter connection")
        return
    
    try:
        # Find template
        template = find_template(service_instance, TEMPLATE_NAME)
        if not template:
            return
        
        # Find datastore
        datastore = find_datastore(service_instance, DATASTORE_NAME)
        if not datastore:
            return
        
        # Find network
        network = find_network(service_instance, NETWORK_NAME)
        if not network:
            return
        
        # Find resource pool
        resource_pool = find_resource_pool(service_instance)
        if not resource_pool:
            return
        
        print("\n" + "=" * 50)
        print("🚀 Creating Single Custom VM")
        print("=" * 50)
        
        # Create one VM with all customizations
        success = create_custom_vm(template, NEW_VM_NAME, datastore, network, resource_pool)
        
        print("\n" + "=" * 50)
        print("📊 Final Result")
        print("=" * 50)
        if success:
            print("🎉 VM creation successful!")
            print(f"✅ Created VM: {NEW_VM_NAME}")
            print("📋 Specifications applied:")
            print("   - Memory: 4 GB")
            print("   - CPU: 2 cores") 
            print("   - Disk: 50 GB")
            print("   - IP: 10.60.132.105")
            print("   - Network: PROD VMs")
            print("   - Powered off by default")
        else:
            print("❌ VM creation failed. Check the error messages above.")
        
    finally:
        # Disconnect
        Disconnect(service_instance)
        print("\n🔌 Disconnected from vCenter")

if __name__ == "__main__":
    main() 