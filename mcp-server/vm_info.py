#!/usr/bin/env python3
"""
VM Info Management Module using pyvmomi
Handles listing VMs and getting VM details.
"""

from typing import Dict, Any, List, Optional
from pyVmomi import vim

class VMInfoManager:
    def __init__(self):
        pass
    
    def list_all_vms(self, service_instance) -> List[Dict[str, Any]]:
        """List all VMs in vCenter with detailed information."""
        try:
            content = service_instance.RetrieveContent()
            container = content.viewManager.CreateContainerView(
                content.rootFolder, [vim.VirtualMachine], True
            )
            
            vms = []
            for vm in container.view:
                vm_info = {
                    "name": vm.name,
                    "power_state": vm.runtime.powerState,
                    "guest_id": getattr(vm.config, 'guestId', 'Unknown'),
                    "template": getattr(vm.config, 'template', False),
                    "cpu_count": vm.config.hardware.numCPU if hasattr(vm.config, 'hardware') and vm.config.hardware else 0,
                    "memory_mb": vm.config.hardware.memoryMB if hasattr(vm.config, 'hardware') and vm.config.hardware else 0,
                    "ip_address": vm.guest.ipAddress if vm.guest else None,
                    "hostname": vm.guest.hostName if vm.guest else None,
                    "tools_status": vm.guest.toolsStatus if vm.guest else None,
                    "tools_running_status": vm.guest.toolsRunningStatus if vm.guest else None,
                    "folder": vm.parent.name if vm.parent else None,
                    "resource_pool": vm.resourcePool.name if vm.resourcePool else None,
                    "datastore": vm.datastore[0].name if vm.datastore else None,
                    "network_adapters": []
                }
                
                # Get network adapter information
                if hasattr(vm.config, 'hardware') and vm.config.hardware and vm.config.hardware.device:
                    for device in vm.config.hardware.device:
                        if isinstance(device, vim.vm.device.VirtualEthernetCard):
                            network_info = {
                                "mac_address": device.macAddress,
                                "network_name": device.backing.network.name if hasattr(device.backing, 'network') and device.backing.network else None,
                                "port_group": device.backing.port.portgroupKey if hasattr(device.backing, 'port') and device.backing.port else None,
                                "connected": device.connectable.connected if device.connectable else None,
                                "start_connected": device.connectable.startConnected if device.connectable else None
                            }
                            vm_info["network_adapters"].append(network_info)
                
                vms.append(vm_info)
            
            container.Destroy()
            return vms
            
        except Exception as e:
            return [{"error": f"Failed to list VMs: {str(e)}"}]
    
    def get_vm_by_name(self, service_instance, vm_name: str) -> Optional[vim.VirtualMachine]:
        """Get a specific VM by name."""
        try:
            content = service_instance.RetrieveContent()
            container = content.viewManager.CreateContainerView(
                content.rootFolder, [vim.VirtualMachine], True
            )
            
            for vm in container.view:
                if vm.name == vm_name:
                    container.Destroy()
                    return vm
            
            container.Destroy()
            return None
            
        except Exception as e:
            return None
    
    def fast_list_vms(self, service_instance) -> List[Dict[str, Any]]:
        """List all VMs with basic information only (fast version)."""
        try:
            content = service_instance.RetrieveContent()
            container = content.viewManager.CreateContainerView(
                content.rootFolder, [vim.VirtualMachine], True
            )
            
            vms = []
            for vm in container.view:
                # Only get basic properties that are fast to access
                vm_info = {
                    "name": vm.name,
                    "power_state": vm.runtime.powerState,
                    "guest_id": getattr(vm.config, 'guestId', 'Unknown'),
                    "template": getattr(vm.config, 'template', False),
                }
                
                # Only get hardware info if it's safe
                try:
                    if hasattr(vm.config, 'hardware') and vm.config.hardware:
                        vm_info["cpu_count"] = vm.config.hardware.numCPU
                        vm_info["memory_mb"] = vm.config.hardware.memoryMB
                    else:
                        vm_info["cpu_count"] = 0
                        vm_info["memory_mb"] = 0
                except:
                    vm_info["cpu_count"] = 0
                    vm_info["memory_mb"] = 0
                
                # Only get guest info if it's available and fast
                try:
                    if vm.guest and vm.guest.ipAddress:
                        vm_info["ip_address"] = vm.guest.ipAddress
                    else:
                        vm_info["ip_address"] = None
                except:
                    vm_info["ip_address"] = None
                
                vms.append(vm_info)
            
            container.Destroy()
            return vms
            
        except Exception as e:
            return [{"error": f"Failed to list VMs: {str(e)}"}] 