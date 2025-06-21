import os
import requests
import urllib3
from vmware.vapi.vsphere.client import create_vsphere_client

def get_vsphere_client():
    """Get vSphere client with proper configuration."""
    host = os.getenv("VCENTER_HOST")
    user = os.getenv("VCENTER_USER")
    pwd = os.getenv("VCENTER_PASSWORD")
    insecure = os.getenv("VCENTER_INSECURE", "false").lower() == "true"

    if not all([host, user, pwd]):
        raise EnvironmentError("Missing VCENTER_* env vars")

    session = requests.Session()
    session.verify = not insecure
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    return create_vsphere_client(server=host, username=user, password=pwd, session=session)

def safe_api_call(func, error_msg):
    """Safely execute API call and return formatted result or error."""
    try:
        return func(), None
    except Exception as e:
        return None, f"❌ {error_msg}: {str(e)}"

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
                    f"Host Name         : {data.name}",
                    f"Ip Address        : {data.ip_address}",
                    f"Guest OS          : {data.guest_os}"
                ]
            },
            {
                'name': 'Power State',
                'call': lambda: client.vcenter.vm.Power.get(vm_id),
                'format': lambda data: [f"Power State       : {data.state.name}"]
            },
            {
                'name': 'VM Info',
                'call': lambda: client.vcenter.VM.get(vm_id),
                'format': lambda data: [
                    f"Name              : {data.name}",
                    f"Guest OS          : {data.guest_OS or 'Not available'}"
                ]
            },
            {
                'name': 'Memory',
                'call': lambda: client.vcenter.vm.hardware.Memory.get(vm_id),
                'format': lambda data: [
                    f"Size MiB          : {data.size_MiB}",
                    f"Hot Add Enabled   : {data.hot_add_enabled}"
                ]
            },
            {
                'name': 'CPU',
                'call': lambda: client.vcenter.vm.hardware.Cpu.get(vm_id),
                'format': lambda data: [
                    f"Count             : {data.count}",
                    f"Hot Add Enabled   : {data.hot_add_enabled}"
                ]
            }
        ]
        
        # Process each API call
        for api_call in api_calls:
            data, error = safe_api_call(api_call['call'], f"Failed to get {api_call['name'].lower()}")
            
            if data:
                section_lines = [f"---- {api_call['name']} ----"] + api_call['format'](data)
                sections.append("\n".join(section_lines))
            else:
                sections.append(error)
        
        return "\n\n".join(sections)
        
    except Exception as e:
        return f"❌ Failed to connect to vCenter: {str(e)}"

