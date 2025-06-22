"""
VM Power Management Module

Provides functions to power on, power off, and restart VMware VMs with proper state checking.
"""

import logging
from helpers import (
    get_vsphere_client,
    get_vm_by_id,
    safe_api_call
)

logger = logging.getLogger(__name__)

def get_vm_power_state(client, vm_id):
    """Get the current power state of a VM."""
    try:
        power_info = client.vcenter.vm.Power.get(vm_id)
        return power_info.state
    except Exception as e:
        logger.error(f"Failed to get power state for {vm_id}: {str(e)}")
        return None

def power_on_vm(vm_id: str) -> str:
    """Power on a VM if it's not already powered on."""
    try:
        client = get_vsphere_client()
        
        # Get VM details
        vm, error = safe_api_call(
            lambda: get_vm_by_id(client, vm_id),
            f"Failed to get VM details for {vm_id}"
        )
        if error:
            return error
        
        if not vm:
            return f"❌ VM with ID {vm_id} not found"
        
        # Check current power state
        current_state = get_vm_power_state(client, vm.vm)
        if current_state is None:
            return f"❌ Could not determine power state for {vm.name}"
        
        if current_state == "POWERED_ON":
            return f"✅ {vm.name} is already powered on"
        
        # Power on the VM
        _, error = safe_api_call(
            lambda: client.vcenter.vm.Power.start(vm.vm),
            f"Failed to power on {vm.name}"
        )
        
        if error:
            return error
        
        return f"✅ Successfully powered on {vm.name}"
        
    except Exception as e:
        logger.error(f"Error powering on VM: {str(e)}")
        return f"❌ Error powering on VM: {str(e)}"

def power_off_vm(vm_id: str) -> str:
    """Power off a VM if it's not already powered off."""
    try:
        client = get_vsphere_client()
        
        # Get VM details
        vm, error = safe_api_call(
            lambda: get_vm_by_id(client, vm_id),
            f"Failed to get VM details for {vm_id}"
        )
        if error:
            return error
        
        if not vm:
            return f"❌ VM with ID {vm_id} not found"
        
        # Check current power state
        current_state = get_vm_power_state(client, vm.vm)
        if current_state is None:
            return f"❌ Could not determine power state for {vm.name}"
        
        if current_state == "POWERED_OFF":
            return f"✅ {vm.name} is already powered off"
        
        # Power off the VM
        _, error = safe_api_call(
            lambda: client.vcenter.vm.Power.stop(vm.vm),
            f"Failed to power off {vm.name}"
        )
        
        if error:
            return error
        
        return f"✅ Successfully powered off {vm.name}"
        
    except Exception as e:
        logger.error(f"Error powering off VM: {str(e)}")
        return f"❌ Error powering off VM: {str(e)}"

def restart_vm(vm_id: str) -> str:
    """Restart a VM if it's powered on."""
    try:
        client = get_vsphere_client()
        
        # Get VM details
        vm, error = safe_api_call(
            lambda: get_vm_by_id(client, vm_id),
            f"Failed to get VM details for {vm_id}"
        )
        if error:
            return error
        
        if not vm:
            return f"❌ VM with ID {vm_id} not found"
        
        # Check current power state
        current_state = get_vm_power_state(client, vm.vm)
        if current_state is None:
            return f"❌ Could not determine power state for {vm.name}"
        
        if current_state == "POWERED_OFF":
            return f"❌ Cannot restart {vm.name} - it is powered off"
        
        # Restart the VM
        _, error = safe_api_call(
            lambda: client.vcenter.vm.Power.reset(vm.vm),
            f"Failed to restart {vm.name}"
        )
        
        if error:
            return error
        
        return f"✅ Successfully restarted {vm.name}"
        
    except Exception as e:
        logger.error(f"Error restarting VM: {str(e)}")
        return f"❌ Error restarting VM: {str(e)}"

def get_power_state_text(vm_id: str) -> str:
    """Get the current power state of a VM as formatted text."""
    try:
        client = get_vsphere_client()
        
        # Get VM details
        vm, error = safe_api_call(
            lambda: get_vm_by_id(client, vm_id),
            f"Failed to get VM details for {vm_id}"
        )
        if error:
            return error
        
        if not vm:
            return f"❌ VM with ID {vm_id} not found"
        
        # Get power state
        current_state = get_vm_power_state(client, vm.vm)
        if current_state is None:
            return f"❌ Could not determine power state for {vm.name}"
        
        return f"🔌 **Power State for {vm.name}:** {current_state}"
        
    except Exception as e:
        logger.error(f"Error getting power state: {str(e)}")
        return f"❌ Error getting power state: {str(e)}" 