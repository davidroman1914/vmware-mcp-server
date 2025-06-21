# list_vm.py

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

def list_vms_text() -> str:
    """List all VMs as formatted text string for MCP server."""
    try:
        client = get_vsphere_client()
        
        # Define the API call and formatting
        api_call = {
            'call': lambda: client.vcenter.VM.list(),
            'format': lambda vms: [
                f"{vm.name} ({vm.vm})" for vm in vms
            ] if vms else ["No VMs found."]
        }
        
        # Execute the API call
        data, error = safe_api_call(api_call['call'], "Failed to list VMs")
        
        if data:
            return "\n".join(api_call['format'](data))
        else:
            return error or "❌ Unknown error occurred"
            
    except Exception as e:
        return f"❌ Failed to connect to vCenter: {str(e)}"

