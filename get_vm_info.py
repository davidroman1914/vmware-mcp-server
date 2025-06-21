import os
import requests
import urllib3
import logging
import json
from vmware.vapi.vsphere.client import create_vsphere_client
from com.vmware.vcenter.vm.hardware_client import Memory, Disk
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

def safe_get_attr(obj, attr_name, default="Not available"):
    """Safely get attribute from object with fallback."""
    try:
        if hasattr(obj, attr_name):
            value = getattr(obj, attr_name)
            # Handle enum-like objects that have a name attribute
            if hasattr(value, 'name'):
                return value.name
            # Handle enum-like objects that can be converted to string
            elif hasattr(value, '__str__'):
                return str(value)
            else:
                return value if value is not None else default
        else:
            # Debug: show what attributes are actually available
            available_attrs = [attr for attr in dir(obj) if not attr.startswith('_')]
            logger.debug(f"Object {type(obj).__name__} missing '{attr_name}'. Available: {available_attrs}")
            return default
    except Exception as e:
        logger.debug(f"Error accessing '{attr_name}' on {type(obj).__name__}: {str(e)}")
        return default

def inspect_object(obj, name):
    """Inspect object structure and log details."""
    logger.info(f"=== {name} Object Inspection ===")
    logger.info(f"Type: {type(obj).__name__}")
    
    # Get all public attributes
    attrs = [attr for attr in dir(obj) if not attr.startswith('_')]
    logger.info(f"Available attributes: {attrs}")
    
    # Try to get values for key attributes
    for attr in attrs:
        try:
            value = getattr(obj, attr)
            logger.info(f"  {attr}: {value} (type: {type(value).__name__})")
        except Exception as e:
            logger.info(f"  {attr}: Error accessing - {str(e)}")
    
    logger.info(f"=== End {name} ===")

def obj_to_dict(obj):
    """Convert object to dictionary for JSON logging."""
    try:
        if hasattr(obj, '__dict__'):
            return {k: v for k, v in obj.__dict__.items() if not k.startswith('_')}
        elif hasattr(obj, 'name'):  # Handle enum-like objects
            return {'name': obj.name}
        else:
            return str(obj)
    except:
        return str(obj)

def get_vm_info_text(vm_id: str) -> str:
    """Get VM information as formatted text string for MCP server."""
    try:
        client = get_vsphere_client()
        
        # First, verify the VM exists and get basic info
        vm_info = get_vm_by_id(client, vm_id)
        if not vm_info:
            return f"❌ VM with ID '{vm_id}' not found"
        
        sections = []
        
        # Define API calls and their formatting with enhanced helpers
        api_calls = [
            {
                'name': 'Basic Information',
                'call': lambda: vm_info,
                'format': lambda data: [
                    f"Name: {safe_get_attr(data, 'name')}",
                    f"ID: {safe_get_attr(data, 'vm')}"
                ]
            },
            {
                'name': 'Power State',
                'call': lambda: client.vcenter.vm.Power.get(vm_id),
                'format': lambda data: [f"Power State: {safe_get_attr(data, 'state')}"]
            },
            {
                'name': 'Memory',
                'call': lambda: get_memory_info(client, vm_id),
                'format': lambda data: [f"Memory: {data['size']}"] if data['size'] != "Not available" else []
            },
            {
                'name': 'CPU',
                'call': lambda: client.vcenter.vm.hardware.Cpu.get(vm_id),
                'format': lambda data: [f"CPU: {safe_get_attr(data, 'count')} cores"]
            },
            {
                'name': 'Network Adapters',
                'call': lambda: client.vcenter.vm.hardware.Ethernet.list(vm_id),
                'format': lambda data: [
                    f"Network Adapters: {len(data) if data else 0}",
                    *[f"  {get_network_details_clean(client, vm_id, safe_get_attr(adapter, 'nic'))}" 
                      for adapter in (data or [])]
                ] if data else []
            },
            {
                'name': 'Disks',
                'call': lambda: client.vcenter.vm.hardware.Disk.list(vm_id),
                'format': lambda disk_list: [
                    f"Disks: {len(disk_list) if disk_list else 0}",
                    *[f"  {get_disk_details_clean(client, vm_id, safe_get_attr(disk, 'disk'))}" 
                      for disk in (disk_list or [])]
                ] if disk_list else []
            }
        ]
        
        # Process each API call
        for api_call in api_calls:
            try:
                data = api_call['call']()
                
                # Inspect the object structure
                inspect_object(data, api_call['name'])
                
                section_lines = api_call['format'](data)
                if section_lines:  # Only add section if there's content
                    sections.append(f"### {api_call['name']}\n" + "\n".join([f"- **{line}**" for line in section_lines]))
            except Exception as e:
                logger.error(f"Failed to get {api_call['name'].lower()}: {str(e)}")
                # Don't add failed sections to keep output clean
        
        result = "\n\n".join(sections)
        # Ensure we always return a string
        return str(result) if result else "No VM information available"
        
    except Exception as e:
        logger.error(f"Failed to connect to vCenter: {str(e)}")
        return f"❌ Failed to connect to vCenter: {str(e)}"

def get_disk_details(client, vm_id, disk_id):
    """Get detailed information for a specific disk."""
    try:
        disk_info = client.vcenter.vm.hardware.Disk.get(vm=vm_id, disk=disk_id)
        vmdk_file = safe_get_attr(safe_get_attr(disk_info, 'backing'), 'vmdk_file', 'Unknown')
        capacity = format_bytes(safe_get_attr(disk_info, 'capacity'))
        return f"{vmdk_file} (Capacity: {capacity})"
    except Exception as e:
        logger.error(f"Failed to get disk details for disk {disk_id}: {str(e)}")
        return "Unknown"

def get_network_details(client, vm_id, nic_id):
    """Get detailed information for a specific network adapter."""
    try:
        nic_info = client.vcenter.vm.hardware.Ethernet.get(vm=vm_id, nic=nic_id)
        
        # Inspect the network adapter object structure
        inspect_object(nic_info, f"Network Adapter {nic_id}")
        
        # Safely get network name from backing
        backing = safe_get_attr(nic_info, 'backing', "No backing")
        network_name = "Unknown"
        if backing and backing != "No backing":
            inspect_object(backing, f"Network Adapter {nic_id} Backing")
            
            # Try to get network name using helper
            network_id = safe_get_attr(backing, 'network', "No network ID")
            if network_id and network_id != "No network ID":
                network_name = get_network_name(client, network_id)
            else:
                network_name = safe_get_attr(backing, 'network_name', 'Unknown')
        
        # Safely get other attributes
        mac_address = safe_get_attr(nic_info, 'mac_address', 'Unknown')
        mac_type = safe_get_attr(nic_info, 'mac_type', 'Unknown')
        start_connected = safe_get_attr(nic_info, 'start_connected', 'Unknown')
        
        return f"{network_name} (MAC: {mac_address}, Type: {mac_type}, Connected: {start_connected})"
    except Exception as e:
        logger.error(f"Failed to get network details for nic {nic_id}: {str(e)}")
        return "Unknown"

def get_vm_by_id(client, vm_id):
    """Get VM details by ID using VMware helper pattern."""
    try:
        # Use FilterSpec to get specific VM
        filter_spec = VM.FilterSpec(vms=set([vm_id]))
        vms = client.vcenter.VM.list(filter=filter_spec)
        
        if len(vms) == 0:
            logger.warning(f"VM with ID ({vm_id}) not found")
            return None
            
        vm = vms[0]
        logger.info(f"Found VM '{vm.name}' ({vm.vm})")
        return vm
    except Exception as e:
        logger.error(f"Error getting VM by ID {vm_id}: {str(e)}")
        return None

def get_guest_os_info(client, vm_id):
    """Get detailed guest OS information with proper error handling."""
    try:
        # Try to get guest identity info
        guest_info = client.vcenter.vm.guest.Identity.get(vm_id)
        
        # Get VM info for additional OS details
        vm_info = client.vcenter.VM.get(vm_id)
        
        guest_os = safe_get_attr(guest_info, 'guest_os', 'Unknown')
        vm_guest_os = safe_get_attr(vm_info, 'guest_OS', 'Unknown')
        
        # Prefer guest identity OS if available, fallback to VM guest OS
        if guest_os and guest_os != 'Unknown':
            return guest_os
        elif vm_guest_os and vm_guest_os != 'Unknown':
            return vm_guest_os
        else:
            return "Not available (VMware Tools may not be running)"
            
    except Exception as e:
        logger.error(f"Failed to get guest OS info: {str(e)}")
        return "Not available"

def get_network_name(client, network_id):
    """Get network name from network ID using VMware helper pattern."""
    try:
        from com.vmware.vcenter_client import Network
        filter_spec = Network.FilterSpec(networks=set([network_id]))
        networks = client.vcenter.Network.list(filter=filter_spec)
        
        if networks:
            return networks[0].name
        else:
            return "Unknown"
    except Exception as e:
        logger.error(f"Failed to get network name for {network_id}: {str(e)}")
        return "Unknown"

def get_memory_info(client, vm_id):
    """Get detailed memory information with proper error handling."""
    try:
        memory_info = client.vcenter.vm.hardware.Memory.get(vm_id)
        
        # Inspect the memory object structure
        inspect_object(memory_info, f"Memory Info for VM {vm_id}")
        
        # Use the correct attribute name from VMware sample: size_mib
        size_mib = safe_get_attr(memory_info, 'size_mib', "Not found")
        
        # Format memory size
        if size_mib and size_mib != "Not available" and size_mib != "Not found":
            try:
                size_mb = int(size_mib)
                if size_mb >= 1024:
                    size_gb = size_mb / 1024
                    memory_size = f"{size_mb} MiB ({size_gb:.1f} GB)"
                else:
                    memory_size = f"{size_mb} MiB"
            except (ValueError, TypeError):
                memory_size = f"{size_mib} MiB"
        else:
            memory_size = "Not available"
        
        hot_add_enabled = safe_get_attr(memory_info, 'hot_add_enabled', "False")
        
        return {
            'size': memory_size,
            'hot_add_enabled': hot_add_enabled
        }
        
    except Exception as e:
        logger.error(f"Failed to get memory info for VM {vm_id}: {str(e)}")
        return {
            'size': "Not available",
            'hot_add_enabled': False
        }

def get_network_details_clean(client, vm_id, nic_id):
    """Get clean network information without Unknown values."""
    try:
        nic_info = client.vcenter.vm.hardware.Ethernet.get(vm=vm_id, nic=nic_id)
        
        # Get network name from backing
        backing = safe_get_attr(nic_info, 'backing', "No backing")
        network_name = "Unknown"
        if backing and backing != "No backing":
            # Try to get network name using helper
            network_id = safe_get_attr(backing, 'network', "No network ID")
            if network_id and network_id != "No network ID":
                network_name = get_network_name(client, network_id)
            else:
                network_name = safe_get_attr(backing, 'network_name', 'Unknown')
        
        # Get other attributes
        mac_address = safe_get_attr(nic_info, 'mac_address', 'Unknown')
        mac_type = safe_get_attr(nic_info, 'mac_type', 'Unknown')
        start_connected = safe_get_attr(nic_info, 'start_connected', 'Unknown')
        
        # Build clean output
        parts = []
        if network_name != "Unknown":
            parts.append(f"Network: {network_name}")
        if mac_address != "Unknown":
            parts.append(f"MAC: {mac_address}")
        if mac_type != "Unknown":
            parts.append(f"Type: {mac_type}")
        if start_connected != "Unknown":
            parts.append(f"Connected: {start_connected}")
        
        return " | ".join(parts) if parts else "Unknown"
        
    except Exception as e:
        logger.error(f"Failed to get network details for nic {nic_id}: {str(e)}")
        return "Unknown"

def get_disk_details_clean(client, vm_id, disk_id):
    """Get clean disk information without Unknown values."""
    try:
        disk_info = client.vcenter.vm.hardware.Disk.get(vm=vm_id, disk=disk_id)
        vmdk_file = safe_get_attr(safe_get_attr(disk_info, 'backing'), 'vmdk_file', 'Unknown')
        capacity = format_bytes(safe_get_attr(disk_info, 'capacity'))
        
        # Build clean output
        parts = []
        if vmdk_file != "Unknown":
            parts.append(f"File: {vmdk_file}")
        if capacity != "Unknown":
            parts.append(f"Capacity: {capacity}")
        
        return " | ".join(parts) if parts else "Unknown"
        
    except Exception as e:
        logger.error(f"Failed to get disk details for disk {disk_id}: {str(e)}")
        return "Unknown"

