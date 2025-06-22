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
        
        # ===== SECTION 1: VM Templates (Converted VMs) =====
        result += "## 🔧 VM Templates (Converted VMs)\n"
        result += "These are virtual machines that have been converted to templates using 'Convert to Template'.\n\n"
        
        vms = client.vcenter.VM.list()
        vm_templates = []
        
        # Debug info
        debug_info = []
        
        for vm in vms:
            try:
                vm_info = client.vcenter.VM.get(vm.vm)
                
                # Check if this VM has been converted to a template
                # According to VMware docs, templates are VMs with template=True
                if hasattr(vm_info, 'template') and vm_info.template:
                    vm_templates.append({
                        'name': vm_info.name,
                        'id': vm.vm,
                        'vm_info': vm_info,
                        'detection_method': 'template property'
                    })
                    debug_info.append(f"Found template via template property: {vm_info.name}")
                
                # Also check for other template indicators
                elif hasattr(vm_info, 'type') and vm_info.type == 'template':
                    vm_templates.append({
                        'name': vm_info.name,
                        'id': vm.vm,
                        'vm_info': vm_info,
                        'detection_method': 'VM type'
                    })
                    debug_info.append(f"Found template via VM type: {vm_info.name}")
                
                # Check if name contains template patterns (fallback)
                elif any(pattern in vm_info.name.lower() for pattern in ['template', 'tpl', 'gold', 'master', 'base']):
                    vm_templates.append({
                        'name': vm_info.name,
                        'id': vm.vm,
                        'vm_info': vm_info,
                        'detection_method': 'name pattern'
                    })
                    debug_info.append(f"Found template via name pattern: {vm_info.name}")
                    
            except Exception as e:
                # Skip VMs that have errors
                continue
        
        if vm_templates:
            result += f"✅ Found {len(vm_templates)} VM template(s):\n\n"
            for template in vm_templates:
                vm_info = template['vm_info']
                result += f"📄 **{vm_info.name}** (ID: `{template['id']}`)\n"
                result += f"   • Detection: {template['detection_method']}\n"
                
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
                
                # Add power state
                result += f"   • Power State: {getattr(vm_info, 'power_state', 'Unknown')}\n"
                
                # Add hardware info if available
                if hasattr(vm_info, 'hardware'):
                    result += f"   • Version: {vm_info.hardware.version}\n"
                
                # Add folder info if available
                if hasattr(vm_info, 'folder'):
                    result += f"   • Folder: {vm_info.folder}\n"
                
                result += "\n"
        else:
            result += "ℹ️ No VM templates found.\n\n"
            result += "💡 **To create templates (following VMware instructions):**\n"
            result += "1. Power off a virtual machine\n"
            result += "2. Right-click the VM in vSphere client\n"
            result += "3. Select 'Template' → 'Convert to Template'\n"
            result += "4. The VM will then appear as a template with template=True\n\n"
            
            # Show debug info
            if debug_info:
                result += "🔍 **Debug Info:**\n"
                for info in debug_info:
                    result += f"   • {info}\n"
                result += "\n"
            
            # Show sample VM properties to help understand what's available
            if vms:
                try:
                    sample_vm = client.vcenter.VM.get(vms[0].vm)
                    result += "🔍 **Sample VM Properties:**\n"
                    result += f"   • Name: {sample_vm.name}\n"
                    result += f"   • Template Property: {getattr(sample_vm, 'template', 'Not found')}\n"
                    result += f"   • VM Type: {getattr(sample_vm, 'type', 'Not found')}\n"
                    result += f"   • Power State: {getattr(sample_vm, 'power_state', 'Unknown')}\n"
                    result += f"   • Folder: {getattr(sample_vm, 'folder', 'Not found')}\n"
                    result += "\n"
                except:
                    pass
        
        # ===== SECTION 2: Try Alternative Template Detection =====
        result += "## 🔍 Alternative Template Detection\n"
        result += "Trying additional methods to find templates that might be stored differently.\n\n"
        
        # Try to get templates from different views or folders
        try:
            # Check if there's a specific template folder or view
            folders = client.vcenter.Folder.list()
            template_folders = []
            
            for folder in folders:
                try:
                    folder_info = client.vcenter.Folder.get(folder.folder)
                    if any(pattern in folder_info.name.lower() for pattern in ['template', 'tpl', 'gold', 'master', 'base']):
                        template_folders.append(folder_info.name)
                        
                        # List VMs in this template folder
                        try:
                            folder_vms = client.vcenter.VM.list(folder=folder.folder)
                            if folder_vms:
                                result += f"📁 **Template Folder: {folder_info.name}**\n"
                                result += f"   • VMs in folder: {len(folder_vms)}\n"
                                for vm in folder_vms:
                                    result += f"   • {vm.name} (ID: {vm.vm})\n"
                                result += "\n"
                        except Exception as e:
                            result += f"   • Error listing VMs in folder: {str(e)}\n"
                            
                except Exception as e:
                    continue
            
            if template_folders:
                result += f"✅ Found {len(template_folders)} template-related folder(s): {', '.join(template_folders)}\n\n"
            else:
                result += "ℹ️ No template-related folders found.\n\n"
                
        except Exception as e:
            result += f"⚠️ Could not check folders: {str(e)}\n\n"
        
        # ===== SECTION 3: Content Library Templates =====
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
                                    'urn': item.item
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
        
        # ===== SUMMARY =====
        total_templates = len(vm_templates) + len(content_templates)
        result += f"## 📊 Summary\n"
        result += f"Total templates found: **{total_templates}**\n"
        result += f"- VM Templates (Converted VMs): {len(vm_templates)}\n"
        result += f"- Content Library Templates: {len(content_templates)}\n\n"
        
        if total_templates == 0:
            result += "🔍 **Debug Info:** Run 'make debug-templates' for detailed analysis of your vCenter environment.\n"
            result += "💡 **Note:** If you converted a VM to template but it's not showing up, it might be stored in a different location or view.\n"
        
        return result
        
    except Exception as e:
        return f"❌ Error listing templates: {str(e)}" 