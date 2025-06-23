#!/usr/bin/env python3
"""
VM Creation Module using pyvmomi
Handles creating VMs from templates with customization.
"""

from typing import Dict, Any, Optional
from pyVmomi import vim
from vm_info import VMInfoManager
import time

class VMCreationManager:
    def __init__(self):
        self.vm_info = VMInfoManager()
    
    def create_vm_from_template(self, service_instance, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new VM from a template with customization."""
        try:
            template_name = arguments.get("template_name")
            vm_name = arguments.get("vm_name")
            hostname = arguments.get("hostname")
            ip_address = arguments.get("ip_address")
            netmask = arguments.get("netmask")
            gateway = arguments.get("gateway")
            network_name = arguments.get("network_name")
            cpu_count = arguments.get("cpu_count")
            memory_mb = arguments.get("memory_mb")
            disk_size_gb = arguments.get("disk_size_gb")
            datastore_name = arguments.get("datastore_name")
            
            # Get the template VM
            template_vm = self.vm_info.get_vm_by_name(service_instance, template_name)
            if not template_vm:
                return {"error": f"Template VM '{template_name}' not found"}
            
            # Get content and find required objects
            content = service_instance.RetrieveContent()
            
            # Find datastore
            datastore = None
            if datastore_name:
                datastore = self._find_datastore(content, datastore_name)
            if not datastore:
                # Use the first available datastore
                datastore = content.viewManager.CreateContainerView(
                    content.rootFolder, [vim.Datastore], True
                ).view[0]
            
            # Find network
            network = self._find_network(content, network_name)
            if not network:
                return {"error": f"Network '{network_name}' not found"}
            
            # Find resource pool
            resource_pool = template_vm.resourcePool
            
            # Find folder
            folder = template_vm.parent
            
            # Create relocation spec
            relospec = vim.vm.RelocateSpec()
            relospec.datastore = datastore
            relospec.pool = resource_pool
            
            # Create clone spec
            clonespec = vim.vm.CloneSpec()
            clonespec.location = relospec
            clonespec.powerOn = False
            clonespec.template = False
            
            # Create customization spec
            customizationspec = vim.vm.customization.Specification()
            
            # Identity
            identity = vim.vm.customization.LinuxPrep()
            identity.hostName = vim.vm.customization.FixedName(name=hostname)
            identity.domain = vim.vm.customization.FixedName(name="local")
            customizationspec.identity = identity
            
            # Network interface
            adapter_mapping = vim.vm.customization.AdapterMapping()
            adapter_mapping.adapter = vim.vm.customization.IPSettings()
            adapter_mapping.adapter.ip = vim.vm.customization.FixedIp(ipAddress=ip_address)
            adapter_mapping.adapter.subnetMask = netmask
            adapter_mapping.adapter.gateway = [gateway]
            adapter_mapping.adapter.dnsServerList = ["8.8.8.8", "8.8.4.4"]
            
            customizationspec.nicSettingMap = [adapter_mapping]
            customizationspec.globalIPSettings = vim.vm.customization.GlobalIPSettings()
            customizationspec.globalIPSettings.dnsServerList = ["8.8.8.8", "8.8.4.4"]
            
            clonespec.customization = customizationspec
            
            # Hardware customization if specified
            if cpu_count or memory_mb or disk_size_gb:
                config_spec = vim.vm.ConfigSpec()
                
                if cpu_count:
                    config_spec.numCPUs = cpu_count
                
                if memory_mb:
                    config_spec.memoryMB = memory_mb
                
                if disk_size_gb:
                    # Find the first disk and resize it
                    for device in template_vm.config.hardware.device:
                        if isinstance(device, vim.vm.device.VirtualDisk):
                            disk_spec = vim.vm.device.VirtualDeviceSpec()
                            disk_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.edit
                            disk_spec.device = device
                            disk_spec.device.capacityInKB = disk_size_gb * 1024 * 1024
                            config_spec.deviceChange = [disk_spec]
                            break
                
                clonespec.config = config_spec
            
            # Clone the VM
            task = template_vm.Clone(folder=folder, name=vm_name, spec=clonespec)
            
            # Wait for clone to complete
            while task.info.state not in [vim.TaskInfo.State.success, vim.TaskInfo.State.error]:
                time.sleep(1)
            
            if task.info.state == vim.TaskInfo.State.success:
                # Get the new VM
                new_vm = task.info.result
                
                # Power on the VM
                power_task = new_vm.PowerOn()
                while power_task.info.state not in [vim.TaskInfo.State.success, vim.TaskInfo.State.error]:
                    time.sleep(1)
                
                if power_task.info.state == vim.TaskInfo.State.success:
                    return {
                        "message": f"Successfully created and powered on VM '{vm_name}'",
                        "vm_name": vm_name,
                        "ip_address": ip_address,
                        "hostname": hostname
                    }
                else:
                    return {
                        "message": f"VM '{vm_name}' created but failed to power on",
                        "vm_name": vm_name,
                        "error": power_task.info.error.msg if power_task.info.error else "Unknown error"
                    }
            else:
                return {"error": f"Failed to create VM '{vm_name}': {task.info.error.msg if task.info.error else 'Unknown error'}"}
                
        except Exception as e:
            return {"error": f"Error creating VM: {str(e)}"}
    
    def _find_datastore(self, content, datastore_name: str):
        """Find a datastore by name."""
        container = content.viewManager.CreateContainerView(
            content.rootFolder, [vim.Datastore], True
        )
        
        for datastore in container.view:
            if datastore.name == datastore_name:
                container.Destroy()
                return datastore
        
        container.Destroy()
        return None
    
    def _find_network(self, content, network_name: str):
        """Find a network by name."""
        container = content.viewManager.CreateContainerView(
            content.rootFolder, [vim.dvs.DistributedVirtualPortgroup], True
        )
        
        for network in container.view:
            if network.name == network_name:
                container.Destroy()
                return network
        
        container.Destroy()
        
        # Try standard networks
        container = content.viewManager.CreateContainerView(
            content.rootFolder, [vim.Network], True
        )
        
        for network in container.view:
            if network.name == network_name:
                container.Destroy()
                return network
        
        container.Destroy()
        return None 