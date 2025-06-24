#!/usr/bin/env python3
"""
Power Management Module for VMware MCP Server
Handles VM power operations (power on, power off)
"""

import sys
from pyVmomi import vim
from .connection import get_service_instance


def power_on_vm(vm_name: str) -> str:
    """Power on a VM by name."""
    service_instance = get_service_instance()
    if not service_instance:
        return "Error: Could not connect to vCenter"
    
    try:
        content = service_instance.RetrieveContent()
        container = content.viewManager.CreateContainerView(
            content.rootFolder, [vim.VirtualMachine], True
        )
        
        vm = None
        for v in container.view:
            if v.name == vm_name:
                vm = v
                break
        
        if not vm:
            return f"VM '{vm_name}' not found"
        
        if vm.runtime.powerState == vim.VirtualMachinePowerState.poweredOn:
            return f"VM '{vm_name}' is already powered on"
        
        task = vm.PowerOn()
        while task.info.state not in [vim.TaskInfo.State.success, vim.TaskInfo.State.error]:
            pass
        
        if task.info.state == vim.TaskInfo.State.success:
            return f"✅ Successfully powered on VM '{vm_name}'"
        else:
            return f"❌ Failed to power on VM '{vm_name}': {task.info.error.msg}"
            
    except Exception as e:
        return f"Error: {e}"


def power_off_vm(vm_name: str) -> str:
    """Power off a VM by name."""
    service_instance = get_service_instance()
    if not service_instance:
        return "Error: Could not connect to vCenter"
    
    try:
        content = service_instance.RetrieveContent()
        container = content.viewManager.CreateContainerView(
            content.rootFolder, [vim.VirtualMachine], True
        )
        
        vm = None
        for v in container.view:
            if v.name == vm_name:
                vm = v
                break
        
        if not vm:
            return f"VM '{vm_name}' not found"
        
        if vm.runtime.powerState == vim.VirtualMachinePowerState.poweredOff:
            return f"VM '{vm_name}' is already powered off"
        
        task = vm.PowerOff()
        while task.info.state not in [vim.TaskInfo.State.success, vim.TaskInfo.State.error]:
            pass
        
        if task.info.state == vim.TaskInfo.State.success:
            return f"✅ Successfully powered off VM '{vm_name}'"
        else:
            return f"❌ Failed to power off VM '{vm_name}': {task.info.error.msg}"
            
    except Exception as e:
        return f"Error: {e}" 