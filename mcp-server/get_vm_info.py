import logging
from helpers import (
    get_vsphere_client, 
    safe_get_attr, 
    format_bytes, 
    get_vm_by_id, 
    get_network_name,
    get_resource_pool_name,
    get_datastore_name,
    get_folder_name,
    get_cluster_name
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_memory_info(client, vm_id):
    """Get memory information."""
    try:
        memory_info = client.vcenter.vm.hardware.Memory.get(vm_id)
        size_mib = safe_get_attr(memory_info, 'size_mib', "Not found")
        
        if size_mib and size_mib != "Not found":
            try:
                size_mb = int(size_mib)
                if size_mb >= 1024:
                    size_gb = size_mb / 1024
                    return f"{size_mb} MiB ({size_gb:.1f} GB)"
                else:
                    return f"{size_mb} MiB"
            except (ValueError, TypeError):
                return f"{size_mib} MiB"
        return "Not available"
        
    except Exception as e:
        logger.error(f"Failed to get memory info: {str(e)}")
        return "Not available"

def get_network_details_clean(client, vm_id, nic_id):
    """Get clean network information."""
    try:
        nic_info = client.vcenter.vm.hardware.Ethernet.get(vm=vm_id, nic=nic_id)
        
        # Get network name
        backing = safe_get_attr(nic_info, 'backing', "No backing")
        network_name = "Unknown"
        if backing and backing != "No backing":
            network_id = safe_get_attr(backing, 'network', "No network ID")
            if network_id and network_id != "No network ID":
                network_name = get_network_name(client, network_id)
            else:
                network_name = safe_get_attr(backing, 'network_name', 'Unknown')
        
        # Build clean output
        parts = []
        if network_name != "Unknown":
            parts.append(f"Network: {network_name}")
        if safe_get_attr(nic_info, 'mac_address', 'Unknown') != "Unknown":
            parts.append(f"MAC: {safe_get_attr(nic_info, 'mac_address')}")
        if safe_get_attr(nic_info, 'mac_type', 'Unknown') != "Unknown":
            parts.append(f"Type: {safe_get_attr(nic_info, 'mac_type')}")
        if safe_get_attr(nic_info, 'start_connected', 'Unknown') != "Unknown":
            parts.append(f"Connected: {safe_get_attr(nic_info, 'start_connected')}")
        
        return " | ".join(parts) if parts else "Unknown"
        
    except Exception as e:
        logger.error(f"Failed to get network details: {str(e)}")
        return "Unknown"

def get_disk_details_clean(client, vm_id, disk_id):
    """Get clean disk information."""
    try:
        disk_info = client.vcenter.vm.hardware.Disk.get(vm=vm_id, disk=disk_id)
        vmdk_file = safe_get_attr(safe_get_attr(disk_info, 'backing'), 'vmdk_file', 'Unknown')
        capacity = format_bytes(safe_get_attr(disk_info, 'capacity'))
        
        parts = []
        if vmdk_file != "Unknown":
            parts.append(f"File: {vmdk_file}")
        if capacity != "Unknown":
            parts.append(f"Capacity: {capacity}")
        
        return " | ".join(parts) if parts else "Unknown"
        
    except Exception as e:
        logger.error(f"Failed to get disk details: {str(e)}")
        return "Unknown"

def get_vm_info_text(vm_id: str) -> str:
    """Get VM information as formatted text string for MCP server."""
    try:
        client = get_vsphere_client()
        
        # Verify VM exists
        vm_info = get_vm_by_id(client, vm_id)
        if not vm_info:
            return f"❌ VM with ID '{vm_id}' not found"
        
        sections = []
        
        # Basic Information
        sections.append(f"### Basic Information\n- **Name:** {safe_get_attr(vm_info, 'name')}\n- **ID:** {safe_get_attr(vm_info, 'vm')}")
        
        # Power State
        try:
            power_info = client.vcenter.vm.Power.get(vm_id)
            sections.append(f"### Power State\n- **Power State:** {safe_get_attr(power_info, 'state')}")
        except Exception as e:
            logger.error(f"Failed to get power state: {str(e)}")
        
        # Memory
        memory_size = get_memory_info(client, vm_id)
        if memory_size != "Not available":
            sections.append(f"### Memory\n- **Memory:** {memory_size}")
        
        # CPU
        try:
            cpu_info = client.vcenter.vm.hardware.Cpu.get(vm_id)
            sections.append(f"### CPU\n- **CPU:** {safe_get_attr(cpu_info, 'count')} cores")
        except Exception as e:
            logger.error(f"Failed to get CPU info: {str(e)}")
        
        # Placement Information - Let's see what's actually available
        try:
            # Get the full VM object to inspect
            vm_full = client.vcenter.VM.get(vm_id)
            logger.info(f"=== VM Object Inspection for {vm_id} ===")
            attrs = [attr for attr in dir(vm_full) if not attr.startswith('_')]
            logger.info(f"Available VM attributes: {attrs}")
            
            placement_info = {}
            
            # Check for common placement attributes
            for attr in ['resource_pool', 'datastore', 'folder', 'cluster', 'host', 'parent']:
                if hasattr(vm_full, attr):
                    value = getattr(vm_full, attr)
                    logger.info(f"  {attr}: {value} (type: {type(value).__name__})")
                    if value:
                        placement_info[attr] = value
            
            # If we found any placement info, try to resolve names
            if placement_info:
                placement_lines = ["### Placement Information"]
                
                if 'resource_pool' in placement_info:
                    rp_name = get_resource_pool_name(client, placement_info['resource_pool'])
                    if rp_name != "Unknown":
                        placement_lines.append(f"- **Resource Pool:** {rp_name}")
                
                if 'datastore' in placement_info:
                    ds_name = get_datastore_name(client, placement_info['datastore'])
                    if ds_name != "Unknown":
                        placement_lines.append(f"- **Datastore:** {ds_name}")
                
                if 'folder' in placement_info:
                    folder_name = get_folder_name(client, placement_info['folder'])
                    if folder_name != "Unknown":
                        placement_lines.append(f"- **Folder:** {folder_name}")
                
                if 'cluster' in placement_info:
                    cluster_name = get_cluster_name(client, placement_info['cluster'])
                    if cluster_name != "Unknown":
                        placement_lines.append(f"- **Cluster:** {cluster_name}")
                
                if len(placement_lines) > 1:  # More than just the header
                    sections.append("\n".join(placement_lines))
                    
        except Exception as e:
            logger.error(f"Failed to get placement info: {str(e)}")
        
        # Network Adapters
        try:
            network_adapters = client.vcenter.vm.hardware.Ethernet.list(vm_id)
            if network_adapters:
                network_lines = [f"### Network Adapters\n- **Network Adapters:** {len(network_adapters)}"]
                for adapter in network_adapters:
                    details = get_network_details_clean(client, vm_id, safe_get_attr(adapter, 'nic'))
                    if details != "Unknown":
                        network_lines.append(f"  - **{details}**")
                if len(network_lines) > 1:  # More than just the count
                    sections.append("\n".join(network_lines))
        except Exception as e:
            logger.error(f"Failed to get network adapters: {str(e)}")
        
        # Disks
        try:
            disks = client.vcenter.vm.hardware.Disk.list(vm_id)
            if disks:
                disk_lines = [f"### Disks\n- **Disks:** {len(disks)}"]
                for disk in disks:
                    details = get_disk_details_clean(client, vm_id, safe_get_attr(disk, 'disk'))
                    if details != "Unknown":
                        disk_lines.append(f"  - **{details}**")
                if len(disk_lines) > 1:  # More than just the count
                    sections.append("\n".join(disk_lines))
        except Exception as e:
            logger.error(f"Failed to get disks: {str(e)}")
        
        result = "\n\n".join(sections)
        return str(result) if result else "No VM information available"
        
    except Exception as e:
        logger.error(f"Failed to connect to vCenter: {str(e)}")
        return f"❌ Failed to connect to vCenter: {str(e)}"

