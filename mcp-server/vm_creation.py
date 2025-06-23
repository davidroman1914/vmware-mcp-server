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
    
    def create_custom_vm(self, service_instance, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new VM from template with comprehensive customization:
        - Memory, CPU, Disk size
        - IP address, hostname, network
        - Powered off by default
        """
        try:
            template_name = arguments.get("template_name")
            vm_name = arguments.get("vm_name")
            hostname = arguments.get("hostname", vm_name)
            ip_address = arguments.get("ip_address")
            netmask = arguments.get("netmask", "255.255.255.0")
            gateway = arguments.get("gateway")
            network_name = arguments.get("network_name")
            cpu_count = arguments.get("cpu_count", 2)
            memory_gb = arguments.get("memory_gb", 4)
            disk_size_gb = arguments.get("disk_size_gb", 50)
            datastore_name = arguments.get("datastore_name")
            
            # Validate required parameters
            if not template_name:
                return {"error": "template_name is required"}
            if not vm_name:
                return {"error": "vm_name is required"}
            if not network_name:
                return {"error": "network_name is required"}
            
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
            if not folder:
                return {"error": "Could not determine VM folder"}
            
            # Cast folder to proper type
            folder = folder if isinstance(folder, vim.Folder) else None
            if not folder:
                return {"error": "Parent is not a valid folder"}
            
            # Create relocation spec
            relospec = vim.vm.RelocateSpec()
            relospec.datastore = datastore
            relospec.pool = resource_pool
            
            # Create clone spec
            clonespec = vim.vm.CloneSpec()
            clonespec.location = relospec
            clonespec.powerOn = False  # Keep powered off
            clonespec.template = False
            
            # Create customization spec for IP and hostname
            if ip_address and gateway:
                customizationspec = vim.vm.customization.Specification()
                
                # Identity
                identity = vim.vm.customization.LinuxPrep()
                identity.hostName = vim.vm.customization.FixedName(name=hostname)
                identity.domain = "local"
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
            
            # Hardware customization
            config_spec = vim.vm.ConfigSpec()
            config_spec.numCPUs = cpu_count
            config_spec.memoryMB = memory_gb * 1024  # Convert GB to MB
            
            # Disk customization
            if template_vm.config and template_vm.config.hardware:
                for device in template_vm.config.hardware.device:
                    if isinstance(device, vim.vm.device.VirtualDisk):
                        disk_spec = vim.vm.device.VirtualDeviceSpec()
                        disk_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.edit
                        disk_spec.device = device
                        disk_spec.device.capacityInKB = disk_size_gb * 1024 * 1024  # Convert GB to KB
                        config_spec.deviceChange = [disk_spec]
                        break
            
            clonespec.config = config_spec
            
            # Clone the VM
            task = template_vm.Clone(folder=folder, name=vm_name, spec=clonespec)
            
            # Wait for clone to complete
            while task.info.state not in [vim.TaskInfo.State.success, vim.TaskInfo.State.error]:
                time.sleep(1)
            
            if task.info.state == vim.TaskInfo.State.success:
                new_vm = task.info.result
                return {
                    "message": f"Successfully created VM '{vm_name}' (powered off)",
                    "vm_name": vm_name,
                    "hostname": hostname,
                    "ip_address": ip_address,
                    "cpu_count": cpu_count,
                    "memory_gb": memory_gb,
                    "disk_size_gb": disk_size_gb,
                    "network": network_name,
                    "datastore": datastore.name
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