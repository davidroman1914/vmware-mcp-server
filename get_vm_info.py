import os
import requests
import urllib3
import logging
import json
from vmware.vapi.vsphere.client import create_vsphere_client
from com.vmware.vcenter.vm.hardware_client import Memory, Disk

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
        sections = []
        
        # Define API calls and their formatting
        api_calls = [
            {
                'name': 'Guest Identity',
                'call': lambda: client.vcenter.vm.guest.Identity.get(vm_id),
                'format': lambda data: [
                    f"Host Name         : {safe_get_attr(data, 'name')}",
                    f"Ip Address        : {safe_get_attr(data, 'ip_address')}",
                    f"Guest OS          : {safe_get_attr(data, 'guest_os')}"
                ]
            },
            {
                'name': 'Power State',
                'call': lambda: client.vcenter.vm.Power.get(vm_id),
                'format': lambda data: [f"Power State       : {safe_get_attr(data, 'state')}"]
            },
            {
                'name': 'VM Info',
                'call': lambda: client.vcenter.VM.get(vm_id),
                'format': lambda data: [
                    f"Name              : {safe_get_attr(data, 'name')}",
                    f"Guest OS          : {safe_get_attr(data, 'guest_OS')}"
                ]
            },
            {
                'name': 'Memory',
                'call': lambda: client.vcenter.vm.hardware.Memory.get(vm_id),
                'format': lambda data: [
                    f"Size MiB          : {safe_get_attr(data, 'size_MiB')}",
                    f"Hot Add Enabled   : {safe_get_attr(data, 'hot_add_enabled')}"
                ]
            },
            {
                'name': 'CPU',
                'call': lambda: client.vcenter.vm.hardware.Cpu.get(vm_id),
                'format': lambda data: [
                    f"Count             : {safe_get_attr(data, 'count')}",
                    f"Hot Add Enabled   : {safe_get_attr(data, 'hot_add_enabled')}"
                ]
            },
            {
                'name': 'Network Adapters',
                'call': lambda: client.vcenter.vm.hardware.Ethernet.list(vm_id),
                'format': lambda data: [
                    f"Count             : {len(data) if data else 0}",
                    *[f"Adapter {i+1}      : {safe_get_attr(adapter, 'nic')} - {get_network_details(client, vm_id, safe_get_attr(adapter, 'nic'))}" 
                      for i, adapter in enumerate(data or [])]
                ]
            },
            {
                'name': 'Disks',
                'call': lambda: client.vcenter.vm.hardware.Disk.list(vm_id),
                'format': lambda disk_list: [
                    f"Count             : {len(disk_list) if disk_list else 0}",
                    *[f"Disk {i+1}        : {safe_get_attr(disk, 'disk')} - {get_disk_details(client, vm_id, safe_get_attr(disk, 'disk'))}" 
                      for i, disk in enumerate(disk_list or [])]
                ]
            }
        ]
        
        # Process each API call
        for api_call in api_calls:
            try:
                data = api_call['call']()
                
                # Inspect the object structure
                inspect_object(data, api_call['name'])
                
                section_lines = [f"---- {api_call['name']} ----"] + api_call['format'](data)
                sections.append("\n".join(section_lines))
            except Exception as e:
                logger.error(f"Failed to get {api_call['name'].lower()}: {str(e)}")
                sections.append(f"❌ Failed to get {api_call['name'].lower()}: {str(e)}")
        
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
            network_name = safe_get_attr(backing, 'network_name', 
                                       safe_get_attr(backing, 'network', 'Unknown'))
        
        # Safely get other attributes
        mac_address = safe_get_attr(nic_info, 'mac_address', 'Unknown')
        mac_type = safe_get_attr(nic_info, 'mac_type', 'Unknown')
        start_connected = safe_get_attr(nic_info, 'start_connected', 'Unknown')
        
        return f"{network_name} (MAC: {mac_address}, Type: {mac_type}, Connected: {start_connected})"
    except Exception as e:
        logger.error(f"Failed to get network details for nic {nic_id}: {str(e)}")
        return "Unknown"

