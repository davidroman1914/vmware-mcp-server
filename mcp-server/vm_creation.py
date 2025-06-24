#!/usr/bin/env python3
"""
VM Creation Module for VMware MCP Server
Handles VM creation from templates with customization
"""

from pyVmomi import vim
from .connection import get_service_instance


def find_template(service_instance, template_name):
    """Find template by name."""
    try:
        content = service_instance.RetrieveContent()
        container = content.viewManager.CreateContainerView(
            content.rootFolder, [vim.VirtualMachine], True
        )
        
        for vm in container.view:
            if vm.config.template and vm.name == template_name:
                return vm
        
        return None
        
    except Exception as e:
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
                return ds
        
        return None
        
    except Exception as e:
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
                return net
        
        return None
        
    except Exception as e:
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
                return cluster.resourcePool
        
        return None
        
    except Exception as e:
        return None


def create_relocation_spec(datastore, resource_pool):
    """Create relocation specification for VM placement."""
    relospec = vim.vm.RelocateSpec()
    relospec.datastore = datastore
    relospec.pool = resource_pool
    return relospec


def create_hardware_config_spec(memory_gb, cpu_count, template):
    """Create hardware configuration specification."""
    config_spec = vim.vm.ConfigSpec()
    config_spec.memoryMB = memory_gb * 1024  # Convert GB to MB
    config_spec.numCPUs = cpu_count
    return config_spec


def create_disk_spec(template, disk_gb):
    """Create disk specification for resizing."""
    for device in template.config.hardware.device:
        if isinstance(device, vim.vm.device.VirtualDisk):
            disk_spec = vim.vm.device.VirtualDeviceSpec()
            disk_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.edit
            disk_spec.device = device
            disk_spec.device.capacityInKB = disk_gb * 1024 * 1024  # Convert GB to KB
            return disk_spec
    return None


def create_network_spec(template, network):
    """Create network specification for network adapter configuration."""
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
            
            return nic_spec
    return None


def create_guest_customization_spec(new_vm_name, ip_address, netmask, gateway):
    """Create guest customization specification for IP configuration."""
    customizationspec = vim.vm.customization.Specification()
    
    # Identity
    identity = vim.vm.customization.LinuxPrep()
    identity.hostName = vim.vm.customization.FixedName(name=new_vm_name)
    identity.domain = "local"
    customizationspec.identity = identity
    
    # Network interface with IP
    adapter_mapping = vim.vm.customization.AdapterMapping()
    adapter_mapping.adapter = vim.vm.customization.IPSettings()
    adapter_mapping.adapter.ip = vim.vm.customization.FixedIp(ipAddress=ip_address)
    adapter_mapping.adapter.subnetMask = netmask
    adapter_mapping.adapter.gateway = [gateway]
    adapter_mapping.adapter.dnsServerList = ["8.8.8.8", "8.8.4.4"]
    
    customizationspec.nicSettingMap = [adapter_mapping]
    customizationspec.globalIPSettings = vim.vm.customization.GlobalIPSettings()
    customizationspec.globalIPSettings.dnsServerList = ["8.8.8.8", "8.8.4.4"]
    
    return customizationspec


def validate_resources(template, datastore, network, resource_pool, template_name, datastore_name, network_name):
    """Validate that all required resources exist."""
    if not template:
        return f"Template '{template_name}' not found. Use list_templates() to see available templates."
    
    if not datastore:
        return f"Datastore '{datastore_name}' not found. Use list_datastores() to see available datastores."
    
    if not network:
        return f"Network '{network_name}' not found. Use list_networks() to see available networks."
    
    if not resource_pool:
        return "Resource pool not found."
    
    return None  # All resources found


def create_vm_custom(template_name: str, new_vm_name: str, ip_address: str = "192.168.1.100", 
                    netmask: str = "255.255.255.0", gateway: str = "192.168.1.1", 
                    memory_gb: int = 4, cpu_count: int = 2, disk_gb: int = 50, 
                    network_name: str = "VM Network", datastore_name: str = "datastore1") -> str:
    """Create a new VM from template with comprehensive customization (memory, CPU, disk, IP) - powered off by default."""
    service_instance = get_service_instance()
    if not service_instance:
        return "Error: Could not connect to vCenter"
    
    try:
        # Find all required resources
        template = find_template(service_instance, template_name)
        datastore = find_datastore(service_instance, datastore_name)
        network = find_network(service_instance, network_name)
        resource_pool = find_resource_pool(service_instance)
        
        # Validate resources
        validation_error = validate_resources(template, datastore, network, resource_pool, 
                                            template_name, datastore_name, network_name)
        if validation_error:
            return validation_error
        
        # Create relocation spec
        relospec = create_relocation_spec(datastore, resource_pool)
        
        # Create clone spec
        clone_spec = vim.vm.CloneSpec()
        clone_spec.location = relospec
        clone_spec.powerOn = False  # Keep powered off
        clone_spec.template = False
        
        # Create hardware config spec
        config_spec = create_hardware_config_spec(memory_gb, cpu_count, template)
        
        # Add disk customization
        disk_spec = create_disk_spec(template, disk_gb)
        if disk_spec:
            config_spec.deviceChange = [disk_spec]
        
        # Add network customization
        if network:
            nic_spec = create_network_spec(template, network)
            if nic_spec:
                if config_spec.deviceChange:
                    config_spec.deviceChange.append(nic_spec)
                else:
                    config_spec.deviceChange = [nic_spec]
        
        # Create guest customization
        customizationspec = create_guest_customization_spec(new_vm_name, ip_address, netmask, gateway)
        clone_spec.customization = customizationspec
        
        # Attach config spec to clone spec
        clone_spec.config = config_spec
        
        # Clone the VM
        task = template.Clone(folder=template.parent, name=new_vm_name, spec=clone_spec)
        
        # Wait for task to complete
        while task.info.state not in [vim.TaskInfo.State.success, vim.TaskInfo.State.error]:
            pass
        
        if task.info.state == vim.TaskInfo.State.success:
            new_vm = task.info.result
            result = f"✅ Successfully created VM '{new_vm_name}' (powered off)"
            result += f"\n- Template: {template_name}"
            result += f"\n- Memory: {memory_gb} GB"
            result += f"\n- CPU: {cpu_count} cores"
            result += f"\n- Disk: {disk_gb} GB"
            result += f"\n- Network: {network_name}"
            result += f"\n- Datastore: {datastore.name}"
            result += f"\n- IP Address: {ip_address}"
            result += f"\n- Power State: Powered off"
            return result
        else:
            return f"❌ Failed to create VM: {task.info.error.msg}"
            
    except Exception as e:
        return f"Error: {e}" 