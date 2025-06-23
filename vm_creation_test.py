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
        print("🧪 Starting VM Creation Tests")
        print("=" * 50)
        
        # Test 1: Simple clone
        success1 = test_simple_clone(template, f"{NEW_VM_NAME}-simple", resource_pool)
        
        # Test 2: Clone with datastore
        success2 = test_with_datastore(template, f"{NEW_VM_NAME}-datastore", datastore, resource_pool)
        
        # Test 3: Clone with customizations
        success3 = test_with_customizations(template, f"{NEW_VM_NAME}-custom", datastore, network, resource_pool)
        
        print("\n" + "=" * 50)
        print("📊 Test Results Summary")
        print("=" * 50)
        print(f"Simple Clone: {'✅ PASS' if success1 else '❌ FAIL'}")
        print(f"With Datastore: {'✅ PASS' if success2 else '❌ FAIL'}")
        print(f"With Customizations: {'✅ PASS' if success3 else '❌ FAIL'}")
        
        if success1 and success2 and success3:
            print("\n🎉 All tests passed! VM creation is working.")
        else:
            print("\n🔍 Some tests failed. Check the error messages above.")
        
    finally:
        # Disconnect
        Disconnect(service_instance)
        print("\n🔌 Disconnected from vCenter")

if __name__ == "__main__":
    main() 