#!/usr/bin/env python3
"""
VM Information module for VMware vCenter
Handles listing VMs and getting detailed VM information
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

def list_all_vms_text():
    """List all VMs and return formatted text."""
    try:
        client = get_vsphere_client()
        
        # Get all VMs
        vms = client.vcenter.VM.list()
        
        if not vms:
            return "ℹ️ No VMs found in vCenter."
        
        # Format the output
        result = f"📋 Found {len(vms)} VM(s):\n\n"
        
        for vm in vms:
            # Get detailed info for each VM
            vm_info = client.vcenter.VM.get(vm.vm)
            
            # Format power state with emoji
            power_emoji = {
                "POWERED_ON": "🟢",
                "POWERED_OFF": "🔴", 
                "SUSPENDED": "🟡",
                "RESETTING": "🔄"
            }.get(vm_info.power_state, "❓")
            
            result += f"{power_emoji} **{vm_info.name}** (ID: `{vm.vm}`)\n"
            result += f"   • Power State: {vm_info.power_state}\n"
            result += f"   • Guest OS: {vm_info.guest_OS or 'Unknown'}\n"
            result += f"   • CPU Count: {vm_info.cpu_count}\n"
            result += f"   • Memory: {vm_info.memory_size_MiB} MB\n"
            
            # Add IP address if available
            if hasattr(vm_info, 'guest') and vm_info.guest and vm_info.guest.ip_address:
                result += f"   • IP Address: {vm_info.guest.ip_address}\n"
            
            result += "\n"
        
        return result
        
    except Exception as e:
        return f"❌ Error listing VMs: {str(e)}"

def get_vm_info_text(vm_id: str):
    """Get detailed information about a specific VM and return formatted text."""
    try:
        client = get_vsphere_client()
        
        # Get VM info
        vm_info = client.vcenter.VM.get(vm_id)
        
        # Format power state with emoji
        power_emoji = {
            "POWERED_ON": "🟢",
            "POWERED_OFF": "🔴", 
            "SUSPENDED": "🟡",
            "RESETTING": "🔄"
        }.get(vm_info.power_state, "❓")
        
        result = f"📋 **VM Details for '{vm_info.name}'**\n\n"
        result += f"**Basic Information:**\n"
        result += f"• ID: `{vm_id}`\n"
        result += f"• Name: {vm_info.name}\n"
        result += f"• Power State: {power_emoji} {vm_info.power_state}\n"
        result += f"• Guest OS: {vm_info.guest_OS or 'Unknown'}\n"
        result += f"• CPU Count: {vm_info.cpu_count}\n"
        result += f"• Memory: {vm_info.memory_size_MiB} MB\n"
        
        # Add hardware info if available
        if hasattr(vm_info, 'hardware'):
            result += f"• Version: {vm_info.hardware.version}\n"
        
        # Add guest info if available
        if hasattr(vm_info, 'guest') and vm_info.guest:
            result += f"\n**Guest Information:**\n"
            if vm_info.guest.ip_address:
                result += f"• IP Address: {vm_info.guest.ip_address}\n"
            if vm_info.guest.host_name:
                result += f"• Hostname: {vm_info.guest.host_name}\n"
            if vm_info.guest.tools_running_status:
                result += f"• VMware Tools: {vm_info.guest.tools_running_status}\n"
        
        # Add network info if available
        try:
            nics = client.vcenter.vm.hardware.Ethernet.list(vm_id)
            if nics:
                result += f"\n**Network Interfaces:**\n"
                for nic in nics:
                    nic_info = client.vcenter.vm.hardware.Ethernet.get(vm_id, nic.nic)
                    result += f"• {nic_info.label}: {nic_info.backing.network_name}\n"
        except:
            pass
        
        return result
        
    except Exception as e:
        return f"❌ Error getting VM info for {vm_id}: {str(e)}"

def list_templates_text():
    """List all VM templates and return formatted text."""
    try:
        client = get_vsphere_client()
        
        # Get all VMs and filter for templates
        vms = client.vcenter.VM.list()
        templates = []
        
        for vm in vms:
            vm_info = client.vcenter.VM.get(vm.vm)
            # Check if VM is a template (has template property)
            if hasattr(vm_info, 'template') and vm_info.template:
                templates.append(vm_info)
        
        if not templates:
            return "ℹ️ No VM templates found in vCenter."
        
        # Format the output
        result = f"📋 Found {len(templates)} VM template(s):\n\n"
        
        for template in templates:
            result += f"📄 **{template.name}** (ID: `{template.vm}`)\n"
            result += f"   • Guest OS: {template.guest_OS or 'Unknown'}\n"
            result += f"   • CPU Count: {template.cpu_count}\n"
            result += f"   • Memory: {template.memory_size_MiB} MB\n"
            
            # Add hardware info if available
            if hasattr(template, 'hardware'):
                result += f"   • Version: {template.hardware.version}\n"
            
            result += "\n"
        
        return result
        
    except Exception as e:
        return f"❌ Error listing templates: {str(e)}" 