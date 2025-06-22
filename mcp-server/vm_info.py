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
            
            # Safely get guest OS info
            guest_os = getattr(vm_info, 'guest_OS', None) or getattr(vm_info, 'guest_os', None) or 'Unknown'
            result += f"   • Guest OS: {guest_os}\n"
            
            # Safely get CPU count from nested cpu object
            cpu_count = 'Unknown'
            if hasattr(vm_info, 'cpu') and vm_info.cpu:
                cpu_count = getattr(vm_info.cpu, 'count', 'Unknown')
            result += f"   • CPU Count: {cpu_count}\n"
            
            # Safely get memory size from nested memory object
            memory_mb = 'Unknown'
            if hasattr(vm_info, 'memory') and vm_info.memory:
                memory_mb = getattr(vm_info.memory, 'size_MiB', 'Unknown')
            result += f"   • Memory: {memory_mb} MB\n"
            
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
        
        # Safely get guest OS info
        guest_os = getattr(vm_info, 'guest_OS', None) or getattr(vm_info, 'guest_os', None) or 'Unknown'
        result += f"• Guest OS: {guest_os}\n"
        
        # Safely get CPU count from nested cpu object
        cpu_count = 'Unknown'
        if hasattr(vm_info, 'cpu') and vm_info.cpu:
            cpu_count = getattr(vm_info.cpu, 'count', 'Unknown')
        result += f"• CPU Count: {cpu_count}\n"
        
        # Safely get memory size from nested memory object
        memory_mb = 'Unknown'
        if hasattr(vm_info, 'memory') and vm_info.memory:
            memory_mb = getattr(vm_info.memory, 'size_MiB', 'Unknown')
        result += f"• Memory: {memory_mb} MB\n"
        
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
        
        # Get all VMs and filter for templates (the correct approach)
        vms = client.vcenter.VM.list()
        templates = []
        
        # Debug: Let's see what properties are available
        debug_info = []
        
        # Template detection patterns
        template_patterns = ['template', 'tpl', 'gold', 'master', 'base']
        
        for vm in vms:
            vm_info = client.vcenter.VM.get(vm.vm)
            
            # Multiple ways to detect templates:
            is_template = False
            detection_method = None
            
            # Method 1: Check if VM is marked as a template (primary method)
            # Based on pyvmomi community samples, templates have a specific property
            if hasattr(vm_info, 'template') and vm_info.template:
                is_template = True
                detection_method = "template property"
                debug_info.append(f"Template detected via 'template' property: {vm_info.name}")
            
            # Method 2: Check VM type
            elif hasattr(vm_info, 'type') and vm_info.type == 'template':
                is_template = True
                detection_method = "VM type"
                debug_info.append(f"Template detected via type: {vm_info.name}")
            
            # Method 3: Check if VM name contains template patterns
            elif any(pattern in vm_info.name.lower() for pattern in template_patterns):
                is_template = True
                detection_method = "name pattern"
                debug_info.append(f"Template detected via name pattern: {vm_info.name}")
            
            # Method 4: Check if VM is in a template folder
            elif hasattr(vm_info, 'folder') and vm_info.folder and any(pattern in vm_info.folder.lower() for pattern in template_patterns):
                is_template = True
                detection_method = "folder location"
                debug_info.append(f"Template detected via folder: {vm_info.name}")
            
            # Method 5: Check for VMs in template-related folders (additional check)
            if not is_template and hasattr(vm_info, 'folder') and vm_info.folder:
                try:
                    # Check if the folder name contains template-related keywords
                    folder_name_lower = vm_info.folder.lower()
                    if any(pattern in folder_name_lower for pattern in template_patterns):
                        is_template = True
                        detection_method = "folder name pattern"
                        debug_info.append(f"Template detected via folder name pattern: {vm_info.name} (folder: {vm_info.folder})")
                except:
                    pass
            
            if is_template:
                # Create a template object with the info we need
                class TemplateInfo:
                    def __init__(self, vm_id, vm_info, detection_method):
                        self.vm = vm_id  # Use the original VM ID
                        self.name = vm_info.name
                        self.detection_method = detection_method
                        # Copy other attributes from vm_info
                        for attr in dir(vm_info):
                            if not attr.startswith('_') and not callable(getattr(vm_info, attr)):
                                try:
                                    setattr(self, attr, getattr(vm_info, attr))
                                except:
                                    pass
                
                template = TemplateInfo(vm.vm, vm_info, detection_method)
                templates.append(template)
        
        # If no templates found, show debug info to help understand what's available
        if not templates:
            debug_result = "ℹ️ No VM templates found in vCenter.\n\n"
            debug_result += "🔍 Note: VM templates are regular VMs with a 'template' property set to True.\n"
            debug_result += "💡 To create templates:\n"
            debug_result += "   1. Right-click on a VM in vCenter and select 'Template' > 'Convert to Template'\n"
            debug_result += "   2. Or use the vCenter UI to create templates from existing VMs\n"
            debug_result += "   3. Templates will then appear in this list\n\n"
            
            if debug_info:
                debug_result += "🔍 Debug information (fallback detection):\n"
                for info in debug_info[:5]:  # Show first 5 debug entries
                    debug_result += f"   • {info}\n"
                debug_result += "\n"
            
            # Show some sample VM properties to help understand the structure
            if vms:
                sample_vm = client.vcenter.VM.get(vms[0].vm)
                debug_result += "🔍 Sample VM properties available:\n"
                for attr in dir(sample_vm):
                    if not attr.startswith('_') and not callable(getattr(sample_vm, attr)):
                        try:
                            value = getattr(sample_vm, attr)
                            debug_result += f"   • {attr}: {type(value).__name__}\n"
                        except:
                            pass
                debug_result += "\n💡 Tip: Templates might be identified by different properties depending on your vCenter setup."
                debug_result += "\n💡 Run 'make debug-templates' for detailed analysis of your vCenter environment."
            
            return debug_result
        
        # Format the output
        result = f"📋 Found {len(templates)} VM template(s):\n\n"
        
        for template in templates:
            result += f"📄 **{template.name}** (ID: `{template.vm}`)\n"
            
            # Show detection method
            if hasattr(template, 'detection_method'):
                result += f"   • Detection: {template.detection_method}\n"
            
            # Safely get guest OS info
            guest_os = getattr(template, 'guest_OS', None) or getattr(template, 'guest_os', None) or 'Unknown'
            result += f"   • Guest OS: {guest_os}\n"
            
            # Safely get CPU count from nested cpu object
            cpu_count = 'Unknown'
            if hasattr(template, 'cpu') and template.cpu:
                cpu_count = getattr(template.cpu, 'count', 'Unknown')
            result += f"   • CPU Count: {cpu_count}\n"
            
            # Safely get memory size from nested memory object
            memory_mb = 'Unknown'
            if hasattr(template, 'memory') and template.memory:
                memory_mb = getattr(template.memory, 'size_MiB', 'Unknown')
            result += f"   • Memory: {memory_mb} MB\n"
            
            # Add hardware info if available
            if hasattr(template, 'hardware'):
                result += f"   • Version: {template.hardware.version}\n"
            
            # Add folder info if available
            if hasattr(template, 'folder'):
                result += f"   • Folder: {template.folder}\n"
            
            result += "\n"
        
        return result
        
    except Exception as e:
        return f"❌ Error listing templates: {str(e)}" 