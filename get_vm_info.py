import os
import logging
import requests
import urllib3
from vmware.vapi.vsphere.client import create_vsphere_client
from com.vmware.vcenter_client import VM

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_vsphere_client():
    """Get vSphere client with proper configuration."""
    host = os.getenv("VCENTER_HOST")
    user = os.getenv("VCENTER_USER")
    pwd = os.getenv("VCENTER_PASSWORD")
    insecure = os.getenv("VCENTER_INSECURE", "false").lower() == "true"

    if not all([host, user, pwd]):
        missing = [k for k, v in [("VCENTER_HOST", host), ("VCENTER_USER", user), ("VCENTER_PASSWORD", pwd)] if not v]
        raise EnvironmentError(f"Missing: {', '.join(missing)}")

    session = requests.Session()
    session.verify = not insecure
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    return create_vsphere_client(server=host, username=user, password=pwd, session=session)

def safe_get_attr(obj, attr_name, default="Not available"):
    """Safely get attribute from object with fallback."""
    try:
        if hasattr(obj, attr_name):
            value = getattr(obj, attr_name)
            if hasattr(value, 'name'):
                return value.name
            elif hasattr(value, '__str__'):
                return str(value)
            else:
                return value if value is not None else default
        else:
            return default
    except Exception as e:
        logger.debug(f"Error accessing '{attr_name}': {str(e)}")
        return default

def format_bytes(bytes_value):
    """Format bytes in human-readable format."""
    if bytes_value is None:
        return "Unknown"
    try:
        bytes_value = int(bytes_value)
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.1f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.1f} PB"
    except:
        return str(bytes_value)

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
                try:
                    from com.vmware.vcenter_client import Network
                    filter_spec = Network.FilterSpec(networks=set([network_id]))
                    networks = client.vcenter.Network.list(filter=filter_spec)
                    if networks:
                        network_name = networks[0].name
                except:
                    pass
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
        try:
            filter_spec = VM.FilterSpec(vms=set([vm_id]))
            vms = client.vcenter.VM.list(filter=filter_spec)
            if not vms:
                return f"❌ VM with ID '{vm_id}' not found"
            vm_info = vms[0]
        except Exception as e:
            return f"❌ Failed to find VM: {str(e)}"
        
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

