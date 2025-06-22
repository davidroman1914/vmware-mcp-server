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
        
        result = "📋 **VMware Template Analysis**\n\n"
        
        # ===== SECTION 1: VM Templates (Regular VMs converted to templates) =====
        result += "## 🔧 VM Templates (Converted VMs)\n"
        result += "These are regular VMs that have been converted to templates.\n\n"
        
        vms = client.vcenter.VM.list()
        vm_templates = []
        
        # Template detection patterns
        template_patterns = ['template', 'tpl', 'gold', 'master', 'base']
        
        for vm in vms:
            vm_info = client.vcenter.VM.get(vm.vm)
            
            # Multiple ways to detect templates:
            is_template = False
            detection_method = None
            
            # Method 1: Check if VM is marked as a template (primary method)
            if hasattr(vm_info, 'template') and vm_info.template:
                is_template = True
                detection_method = "template property"
            
            # Method 2: Check VM type
            elif hasattr(vm_info, 'type') and vm_info.type == 'template':
                is_template = True
                detection_method = "VM type"
            
            # Method 3: Check if VM name contains template patterns
            elif any(pattern in vm_info.name.lower() for pattern in template_patterns):
                is_template = True
                detection_method = "name pattern"
            
            # Method 4: Check if VM is in a template folder
            elif hasattr(vm_info, 'folder') and vm_info.folder and any(pattern in vm_info.folder.lower() for pattern in template_patterns):
                is_template = True
                detection_method = "folder location"
            
            if is_template:
                # Create a template object with the info we need
                class TemplateInfo:
                    def __init__(self, vm_id, vm_info, detection_method):
                        self.vm = vm_id
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
                vm_templates.append(template)
        
        if vm_templates:
            result += f"✅ Found {len(vm_templates)} VM template(s):\n\n"
            for template in vm_templates:
                result += f"📄 **{template.name}** (ID: `{template.vm}`)\n"
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
        else:
            result += "ℹ️ No VM templates found.\n\n"
        
        # ===== SECTION 2: Content Library Templates =====
        result += "## 📚 Content Library Templates\n"
        result += "These are advanced templates stored in Content Libraries.\n\n"
        
        content_templates = []
        try:
            # Get all content libraries
            libraries = client.content.Library.list()
            
            for library in libraries:
                try:
                    # Get items in this library
                    items = client.content.library.Item.list(library.library)
                    
                    for item in items:
                        # Check if this item is a VM template
                        if hasattr(item, 'type') and item.type == 'vm-template':
                            # Get detailed template info
                            try:
                                template_info = client.vcenter.vm_template.library_items.get(item.item)
                                
                                content_templates.append({
                                    'name': item.name,
                                    'id': item.item,
                                    'library': library.name,
                                    'description': getattr(item, 'description', 'No description'),
                                    'template_info': template_info,
                                    'urn': item.item  # This is the URN you saw
                                })
                            except Exception as e:
                                # If detailed info fails, still include basic info
                                content_templates.append({
                                    'name': item.name,
                                    'id': item.item,
                                    'library': library.name,
                                    'description': getattr(item, 'description', 'No description'),
                                    'template_info': None,
                                    'urn': item.item
                                })
                                
                except Exception as e:
                    # Skip libraries that have errors
                    continue
                    
        except Exception as e:
            result += f"⚠️ Could not access Content Libraries: {str(e)}\n"
            result += "   This might be due to permissions or Content Library not being enabled.\n\n"
        
        if content_templates:
            result += f"✅ Found {len(content_templates)} Content Library template(s):\n\n"
            for template in content_templates:
                result += f"📚 **{template['name']}**\n"
                result += f"   • URN: `{template['urn']}`\n"
                result += f"   • Library: {template['library']}\n"
                result += f"   • Description: {template['description']}\n"
                
                # Show detailed template info if available
                if template['template_info']:
                    template_info = template['template_info']
                    
                    # Guest OS
                    if hasattr(template_info, 'guest_os'):
                        result += f"   • Guest OS: {template_info.guest_os}\n"
                    
                    # CPU info
                    if hasattr(template_info, 'cpu') and template_info.cpu:
                        result += f"   • CPU Count: {template_info.cpu.count}\n"
                    
                    # Memory info
                    if hasattr(template_info, 'memory') and template_info.memory:
                        result += f"   • Memory: {template_info.memory.size_mib} MB\n"
                    
                    # VM Template ID
                    if hasattr(template_info, 'vm_template'):
                        result += f"   • VM Template ID: {template_info.vm_template}\n"
                    
                    # Hardware version
                    if hasattr(template_info, 'hardware_version'):
                        result += f"   • Hardware Version: {template_info.hardware_version}\n"
                
                result += "\n"
        else:
            result += "ℹ️ No Content Library templates found.\n\n"
        
        # ===== SECTION 3: vApp Templates =====
        result += "## 🏗️ vApp Templates\n"
        result += "These are multi-VM templates that can contain multiple VMs.\n\n"
        
        vapp_templates = []
        try:
            # Try to get vApp templates (if available)
            vapps = client.vcenter.VApp.list()
            
            for vapp in vapps:
                try:
                    vapp_info = client.vcenter.VApp.get(vapp.vapp)
                    
                    # Check if this is a template
                    if hasattr(vapp_info, 'template') and vapp_info.template:
                        vapp_templates.append({
                            'name': vapp_info.name,
                            'id': vapp.vapp,
                            'power_state': getattr(vapp_info, 'power_state', 'Unknown')
                        })
                except Exception as e:
                    continue
                    
        except Exception as e:
            result += f"⚠️ Could not access vApp templates: {str(e)}\n\n"
        
        if vapp_templates:
            result += f"✅ Found {len(vapp_templates)} vApp template(s):\n\n"
            for template in vapp_templates:
                result += f"🏗️ **{template['name']}** (ID: `{template['id']}`)\n"
                result += f"   • Power State: {template['power_state']}\n\n"
        else:
            result += "ℹ️ No vApp templates found.\n\n"
        
        # ===== SUMMARY =====
        total_templates = len(vm_templates) + len(content_templates) + len(vapp_templates)
        result += f"## 📊 Summary\n"
        result += f"Total templates found: **{total_templates}**\n"
        result += f"- VM Templates: {len(vm_templates)}\n"
        result += f"- Content Library Templates: {len(content_templates)}\n"
        result += f"- vApp Templates: {len(vapp_templates)}\n\n"
        
        if total_templates == 0:
            result += "💡 **To create templates:**\n"
            result += "1. **VM Templates:** Right-click on a VM → Template → Convert to Template\n"
            result += "2. **Content Library Templates:** Use Content Library Manager in vCenter\n"
            result += "3. **vApp Templates:** Create vApps and convert them to templates\n\n"
            result += "🔍 **Debug Info:** Run 'make debug-templates' for detailed analysis.\n"
        
        return result
        
    except Exception as e:
        return f"❌ Error listing templates: {str(e)}" 