#!/usr/bin/env python3
"""
Power Management module for VMware vCenter
Handles power on, power off, and restart operations
"""

from vmware.vapi.vsphere.client import create_vsphere_client
from config import Config

def get_vsphere_client():
    """Create vSphere client with environment variables."""
    host = Config.get_vcenter_host()
    user = Config.get_vcenter_user()
    pwd = Config.get_vcenter_password()
    insecure = Config.get_vcenter_insecure()

    if not all([host, user, pwd]):
        missing = Config.validate_config()
        raise EnvironmentError(f"Missing environment variables: {', '.join(missing)}")

    # Create session with SSL handling
    import requests
    import urllib3
    
    session = requests.Session()
    session.verify = not insecure
    
    # Disable SSL warnings for demo (not recommended in production)
    if insecure:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    # Create vSphere client (exactly as shown in PyPI docs)
    return create_vsphere_client(
        server=host, 
        username=user, 
        password=pwd, 
        session=session
    )

def power_on_vm_text(vm_id: str):
    """Power on a VM and return formatted text."""
    try:
        client = get_vsphere_client()
        
        # Get VM info first to check current state
        vm_info = client.vcenter.VM.get(vm_id)
        
        if vm_info.power_state == "POWERED_ON":
            return f"ℹ️ VM '{vm_info.name}' is already powered on."
        
        # Power on the VM
        client.vcenter.vm.Power.start(vm_id)
        
        return f"✅ Successfully powered on VM '{vm_info.name}' (ID: {vm_id})"
        
    except Exception as e:
        return f"❌ Error powering on VM {vm_id}: {str(e)}"

def power_off_vm_text(vm_id: str):
    """Power off a VM and return formatted text."""
    try:
        client = get_vsphere_client()
        
        # Get VM info first to check current state
        vm_info = client.vcenter.VM.get(vm_id)
        
        if vm_info.power_state == "POWERED_OFF":
            return f"ℹ️ VM '{vm_info.name}' is already powered off."
        
        # Power off the VM
        client.vcenter.vm.Power.stop(vm_id)
        
        return f"✅ Successfully powered off VM '{vm_info.name}' (ID: {vm_id})"
        
    except Exception as e:
        return f"❌ Error powering off VM {vm_id}: {str(e)}"

def restart_vm_text(vm_id: str):
    """Restart a VM and return formatted text."""
    try:
        client = get_vsphere_client()
        
        # Get VM info first to check current state
        vm_info = client.vcenter.VM.get(vm_id)
        
        if vm_info.power_state == "POWERED_OFF":
            return f"ℹ️ VM '{vm_info.name}' is powered off. Use power-on instead."
        
        # Restart the VM
        client.vcenter.vm.Power.reset(vm_id)
        
        return f"✅ Successfully restarted VM '{vm_info.name}' (ID: {vm_id})"
        
    except Exception as e:
        return f"❌ Error restarting VM {vm_id}: {str(e)}" 