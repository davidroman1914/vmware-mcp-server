"""
VM Info Module

Provides functions to get detailed information about VMware VMs.
"""

import logging
from .helpers import (
    get_vsphere_client,
    safe_get_attr,
    format_bytes,
    get_vm_by_id,
    get_network_name,
    safe_api_call
)

logger = logging.getLogger(__name__)

def get_vm_info_text(vm_id: str) -> str:
    """Get detailed information about a specific VM as formatted text."""
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
        power_state, error = safe_api_call(
            lambda: client.vcenter.vm.Power.get(vm.vm),
            f"Failed to get power state for {vm_id}"
        )
        if error:
            power_state = None
        
        # Get guest info
        guest_info, error = safe_api_call(
            lambda: client.vcenter.vm.guest.Identity.get(vm.vm),
            f"Failed to get guest info for {vm_id}"
        )
        
        # Get hardware info
        hardware_info, error = safe_api_call(
            lambda: client.vcenter.vm.hardware.Cpu.get(vm.vm),
            f"Failed to get CPU info for {vm_id}"
        )
        
        # Get memory info
        memory_info, error = safe_api_call(
            lambda: client.vcenter.vm.hardware.Memory.get(vm.vm),
            f"Failed to get memory info for {vm_id}"
        )
        
        # Get disk info
        disks, error = safe_api_call(
            lambda: client.vcenter.vm.hardware.Disk.list(vm.vm),
            f"Failed to get disk info for {vm_id}"
        )
        
        # Get network adapters
        nics, error = safe_api_call(
            lambda: client.vcenter.vm.hardware.Ethernet.list(vm.vm),
            f"Failed to get network adapters for {vm_id}"
        )
        
        # Build output
        output = []
        output.append(f"📋 **VM Information: {vm.name}**")
        output.append(f"**ID:** {vm.vm}")
        output.append(f"**Power State:** {power_state.state if power_state else 'Unknown'}")
        
        # Guest OS info
        if guest_info:
            output.append(f"**Guest OS:** {safe_get_attr(guest_info, 'full_name', 'Unknown')}")
            output.append(f"**Guest Family:** {safe_get_attr(guest_info, 'family', 'Unknown')}")
            output.append(f"**Guest Version:** {safe_get_attr(guest_info, 'version', 'Unknown')}")
        
        # Hardware info
        if hardware_info:
            output.append(f"**CPU Cores:** {safe_get_attr(hardware_info, 'cores_per_socket', 'Unknown')}")
            output.append(f"**CPU Sockets:** {safe_get_attr(hardware_info, 'count', 'Unknown')}")
        
        if memory_info:
            size_mib = safe_get_attr(memory_info, 'size_mib', 'Unknown')
            if size_mib != 'Unknown':
                try:
                    size_bytes = int(size_mib) * 1024 * 1024
                    output.append(f"**Memory:** {format_bytes(size_bytes)}")
                except (ValueError, TypeError):
                    output.append(f"**Memory:** {size_mib} MiB")
        
        # Disk info
        if disks:
            output.append("\n💾 **Disks:**")
            for disk in disks:
                capacity = safe_get_attr(disk, 'capacity', 'Unknown')
                disk_type = safe_get_attr(disk, 'type', 'Unknown')
                if capacity != 'Unknown':
                    output.append(f"  • {format_bytes(capacity)} ({disk_type})")
                else:
                    output.append(f"  • {disk_type}")
        
        # Network adapters
        if nics:
            output.append("\n🌐 **Network Adapters:**")
            for nic in nics:
                backing = safe_get_attr(nic, 'backing', 'Unknown')
                if isinstance(backing, dict):
                    network_id = backing.get('network', 'Unknown')
                else:
                    network_id = 'Unknown'
                network_name = get_network_name(client, network_id)
                mac_address = safe_get_attr(nic, 'mac_address', 'Unknown')
                output.append(f"  • {network_name} (MAC: {mac_address})")
        
        return "\n".join(output)
        
    except Exception as e:
        logger.error(f"Error getting VM info: {str(e)}")
        return f"❌ Error retrieving VM information: {str(e)}"

