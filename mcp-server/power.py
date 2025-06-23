#!/usr/bin/env python3
"""
Power Management Module using pyvmomi
Handles powering VMs on and off.
"""

from typing import Dict, Any, Optional
from pyVmomi import vim
from vm_info import VMInfoManager

class PowerManager:
    def __init__(self):
        self.vm_info = VMInfoManager()
    
    def power_on_vm(self, service_instance, vm_name: str) -> Dict[str, Any]:
        """Power on a VM by name."""
        try:
            vm = self.vm_info.get_vm_by_name(service_instance, vm_name)
            if not vm:
                return {"error": f"VM '{vm_name}' not found"}
            
            if vm.runtime.powerState == vim.VirtualMachinePowerState.poweredOn:
                return {"message": f"VM '{vm_name}' is already powered on"}
            
            task = vm.PowerOn()
            # Wait for task to complete
            while task.info.state not in [vim.TaskInfo.State.success, vim.TaskInfo.State.error]:
                pass
            
            if task.info.state == vim.TaskInfo.State.success:
                return {"message": f"Successfully powered on VM '{vm_name}'"}
            else:
                return {"error": f"Failed to power on VM '{vm_name}': {task.info.error.msg}"}
                
        except Exception as e:
            return {"error": f"Error powering on VM '{vm_name}': {str(e)}"}
    
    def power_off_vm(self, service_instance, vm_name: str) -> Dict[str, Any]:
        """Power off a VM by name."""
        try:
            vm = self.vm_info.get_vm_by_name(service_instance, vm_name)
            if not vm:
                return {"error": f"VM '{vm_name}' not found"}
            
            if vm.runtime.powerState == vim.VirtualMachinePowerState.poweredOff:
                return {"message": f"VM '{vm_name}' is already powered off"}
            
            task = vm.PowerOff()
            # Wait for task to complete
            while task.info.state not in [vim.TaskInfo.State.success, vim.TaskInfo.State.error]:
                pass
            
            if task.info.state == vim.TaskInfo.State.success:
                return {"message": f"Successfully powered off VM '{vm_name}'"}
            else:
                return {"error": f"Failed to power off VM '{vm_name}': {task.info.error.msg}"}
                
        except Exception as e:
            return {"error": f"Error powering off VM '{vm_name}': {str(e)}"}
    
    def shutdown_vm(self, service_instance, vm_name: str) -> Dict[str, Any]:
        """Gracefully shutdown a VM by name."""
        try:
            vm = self.vm_info.get_vm_by_name(service_instance, vm_name)
            if not vm:
                return {"error": f"VM '{vm_name}' not found"}
            
            if vm.runtime.powerState == vim.VirtualMachinePowerState.poweredOff:
                return {"message": f"VM '{vm_name}' is already powered off"}
            
            task = vm.ShutdownGuest()
            # Wait for task to complete
            while task.info.state not in [vim.TaskInfo.State.success, vim.TaskInfo.State.error]:
                pass
            
            if task.info.state == vim.TaskInfo.State.success:
                return {"message": f"Successfully shutdown VM '{vm_name}'"}
            else:
                return {"error": f"Failed to shutdown VM '{vm_name}': {task.info.error.msg}"}
                
        except Exception as e:
            return {"error": f"Error shutting down VM '{vm_name}': {str(e)}"}
    
    def reset_vm(self, service_instance, vm_name: str) -> Dict[str, Any]:
        """Reset a VM by name."""
        try:
            vm = self.vm_info.get_vm_by_name(service_instance, vm_name)
            if not vm:
                return {"error": f"VM '{vm_name}' not found"}
            
            if vm.runtime.powerState == vim.VirtualMachinePowerState.poweredOff:
                return {"error": f"Cannot reset VM '{vm_name}' - it is powered off"}
            
            task = vm.Reset()
            # Wait for task to complete
            while task.info.state not in [vim.TaskInfo.State.success, vim.TaskInfo.State.error]:
                pass
            
            if task.info.state == vim.TaskInfo.State.success:
                return {"message": f"Successfully reset VM '{vm_name}'"}
            else:
                return {"error": f"Failed to reset VM '{vm_name}': {task.info.error.msg}"}
                
        except Exception as e:
            return {"error": f"Error resetting VM '{vm_name}': {str(e)}"} 