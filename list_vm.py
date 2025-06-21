# list_vm.py

from vmware.vapi.vsphere.client import create_vsphere_client
import os
import requests
import urllib3

def get_vsphere_client():
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

def list_vms_text():
    try:
        client = get_vsphere_client()
        vms = client.vcenter.VM.list()
        if not vms:
            return "No VMs found."
        return "\n".join(f"{vm.name} ({vm.vm})" for vm in vms)
    except Exception as e:
        return f"Error listing VMs: {str(e)}"

