#!/usr/bin/env python3
"""
VM Operations module for VMware vCenter
Handles power management, VM info, and other VM-related operations
"""

import requests
import urllib3
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

def get_all_vms_text():
    """Get all VMs and return formatted text."""
    try:
        client = get_vsphere_client()
        vms = client.vcenter.VM.list()
        
        output = [f"📋 **Found {len(vms)} VMs in vCenter:**"]
        
        for vm in vms:
            output.append(f"\n- **{vm.name}** (ID: {vm.vm})")
            output.append(f"  • Power State: {vm.power_state}")
            output.append(f"  • CPU Count: {vm.cpu_count}")
            output.append(f"  • Memory: {vm.memory_size_mib} MB")
        
        return "\n".join(output)
        
    except Exception as e:
        return f"❌ Error getting VMs: {str(e)}"

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

def get_vm_info_text(vm_id: str):
    """Get detailed VM info and return formatted text."""
    try:
        client = get_vsphere_client()
        vm_info = client.vcenter.VM.get(vm_id)
        
        output = [f"📋 **VM Details for '{vm_info.name}':**"]
        output.append(f"\n- **ID:** {vm_info.vm}")
        output.append(f"- **Power State:** {vm_info.power_state}")
        output.append(f"- **CPU Count:** {vm_info.cpu_count}")
        output.append(f"- **Memory:** {vm_info.memory_size_mib} MB")
        output.append(f"- **Guest OS:** {vm_info.guest_OS}")
        output.append(f"- **Version:** {vm_info.version}")
        output.append(f"- **Hardware Version:** {vm_info.hardware_version}")
        
        return "\n".join(output)
        
    except Exception as e:
        return f"❌ Error getting VM info for {vm_id}: {str(e)}" 