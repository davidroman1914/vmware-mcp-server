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
        
        # ===== SECTION 2.5: Datastore-based Template Detection =====
        result += "## 💾 Datastore-based Template Detection\n"
        result += "Looking for templates stored in specific datastores.\n\n"
        
        try:
            # Get all datastores
            datastores = client.vcenter.Datastore.list()
            datastore_templates = []
            
            for datastore in datastores:
                try:
                    datastore_info = client.vcenter.Datastore.get(datastore.datastore)
                    result += f"💾 **Checking Datastore: {datastore_info.name}**\n"
                    
                    # Look for VMs in this datastore
                    try:
                        # Try to get VMs associated with this datastore
                        # This might require a different approach since VMs are typically listed by folder, not datastore
                        
                        # Alternative: Check if there are any VMs that have this datastore as their primary storage
                        # We'll need to check each VM's datastore property
                        for vm in vms:
                            try:
                                vm_info = client.vcenter.VM.get(vm.vm)
                                
                                # Check if this VM is stored on this datastore
                                # This might require checking the VM's storage configuration
                                if hasattr(vm_info, 'datastore') and vm_info.datastore == datastore.datastore:
                                    # Check if this VM is a template
                                    if hasattr(vm_info, 'template') and vm_info.template:
                                        datastore_templates.append({
                                            'name': vm_info.name,
                                            'id': vm.vm,
                                            'datastore': datastore_info.name,
                                            'vm_info': vm_info
                                        })
                                        result += f"   ✅ **TEMPLATE FOUND**: {vm_info.name} (ID: {vm.vm})\n"
                                        result += f"      • Template Property: {vm_info.template}\n"
                                        result += f"      • Power State: {getattr(vm_info, 'power_state', 'Unknown')}\n"
                                        
                                        # Safely get guest OS info
                                        guest_os = getattr(vm_info, 'guest_OS', None) or getattr(vm_info, 'guest_os', None) or 'Unknown'
                                        result += f"      • Guest OS: {guest_os}\n"
                                        
                                        # Safely get CPU count from nested cpu object
                                        cpu_count = 'Unknown'
                                        if hasattr(vm_info, 'cpu') and vm_info.cpu:
                                            cpu_count = getattr(vm_info.cpu, 'count', 'Unknown')
                                        result += f"      • CPU Count: {cpu_count}\n"
                                        
                                        # Safely get memory size from nested memory object
                                        memory_mb = 'Unknown'
                                        if hasattr(vm_info, 'memory') and vm_info.memory:
                                            memory_mb = getattr(vm_info.memory, 'size_MiB', 'Unknown')
                                        result += f"      • Memory: {memory_mb} MB\n"
                                        
                                        result += "\n"
                                        
                            except Exception as e:
                                continue
                                
                    except Exception as e:
                        result += f"   ❌ Error checking VMs in datastore: {str(e)}\n"
                    
                    # Also check if this datastore name matches the one you mentioned
                    if 'ova-inf-vh03-ds-1' in datastore_info.name.lower():
                        result += f"   🎯 **TARGET DATASTORE DETECTED**: {datastore_info.name}\n"
                        result += f"      • This matches the datastore where you found your template!\n"
                        result += f"      • Checking for templates in this specific datastore...\n\n"
                        
                        # Try to get VMs specifically from this datastore
                        try:
                            # This might require a different API call to get VMs by datastore
                            # For now, let's check all VMs and see which ones are on this datastore
                            for vm in vms:
                                try:
                                    vm_info = client.vcenter.VM.get(vm.vm)
                                    
                                    # Check if this VM is on the target datastore
                                    # We might need to check the VM's storage configuration differently
                                    if hasattr(vm_info, 'datastore') and vm_info.datastore == datastore.datastore:
                                        result += f"      📄 VM on target datastore: {vm_info.name}\n"
                                        result += f"         • Template Property: {getattr(vm_info, 'template', 'Not found')}\n"
                                        result += f"         • VM Type: {getattr(vm_info, 'type', 'Not found')}\n"
                                        result += f"         • Power State: {getattr(vm_info, 'power_state', 'Unknown')}\n"
                                        
                                        # If this VM is a template, add it to our list
                                        if hasattr(vm_info, 'template') and vm_info.template:
                                            datastore_templates.append({
                                                'name': vm_info.name,
                                                'id': vm.vm,
                                                'datastore': datastore_info.name,
                                                'vm_info': vm_info
                                            })
                                            
                                except Exception as e:
                                    continue
                                    
                        except Exception as e:
                            result += f"      ❌ Error checking VMs in target datastore: {str(e)}\n"
                        
                        result += "\n"
                        
                except Exception as e:
                    result += f"   ❌ Error analyzing datastore: {str(e)}\n"
            
            if datastore_templates:
                result += f"✅ Found {len(datastore_templates)} template(s) in datastores:\n\n"
                for template in datastore_templates:
                    result += f"💾 **{template['name']}** (Datastore: {template['datastore']})\n"
                    result += f"   • VM ID: {template['id']}\n"
                    result += f"   • Template Property: {template['vm_info'].template}\n"
                    result += f"   • Power State: {getattr(template['vm_info'], 'power_state', 'Unknown')}\n"
                    result += "\n"
            else:
                result += "ℹ️ No templates found in datastores.\n\n"
                
        except Exception as e:
            result += f"⚠️ Could not check datastores: {str(e)}\n\n"
        
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

def find_template_by_name_text(template_name: str):
    """Find a template by name using multiple discovery methods (Ansible-style)."""
    try:
        client = get_vsphere_client()
        
        result = f"🔍 **Searching for template: '{template_name}'**\n\n"
        
        # ===== METHOD 1: Search VM inventory by name =====
        result += "## 📋 Method 1: VM Inventory Search\n"
        result += "Searching all VMs for exact name match...\n\n"
        
        vms = client.vcenter.VM.list()
        vm_template_found = None
        
        for vm in vms:
            try:
                vm_info = client.vcenter.VM.get(vm.vm)
                
                # Check for exact name match
                if vm_info.name.lower() == template_name.lower():
                    vm_template_found = {
                        'name': vm_info.name,
                        'id': vm.vm,
                        'type': 'vm_template',
                        'template_property': getattr(vm_info, 'template', False),
                        'power_state': getattr(vm_info, 'power_state', 'Unknown'),
                        'guest_os': getattr(vm_info, 'guest_OS', None) or getattr(vm_info, 'guest_os', None) or 'Unknown',
                        'vm_info': vm_info
                    }
                    
                    result += f"✅ **VM Template Found**: {vm_info.name}\n"
                    result += f"   • VM ID: `{vm.vm}`\n"
                    result += f"   • Template Property: {vm_template_found['template_property']}\n"
                    result += f"   • Power State: {vm_template_found['power_state']}\n"
                    result += f"   • Guest OS: {vm_template_found['guest_os']}\n"
                    
                    # Get CPU and memory info
                    cpu_count = 'Unknown'
                    if hasattr(vm_info, 'cpu') and vm_info.cpu:
                        cpu_count = getattr(vm_info.cpu, 'count', 'Unknown')
                    result += f"   • CPU Count: {cpu_count}\n"
                    
                    memory_mb = 'Unknown'
                    if hasattr(vm_info, 'memory') and vm_info.memory:
                        memory_mb = getattr(vm_info.memory, 'size_MiB', 'Unknown')
                    result += f"   • Memory: {memory_mb} MB\n"
                    
                    # Get datastore info
                    vm_datastore = getattr(vm_info, 'datastore', None)
                    if vm_datastore:
                        try:
                            datastore_info = client.vcenter.Datastore.get(vm_datastore)
                            result += f"   • Datastore: {datastore_info.name}\n"
                        except:
                            result += f"   • Datastore ID: {vm_datastore}\n"
                    else:
                        result += f"   • Datastore: Unknown\n"
                    
                    result += "\n"
                    break
                    
            except Exception as e:
                continue
        
        if not vm_template_found:
            result += "❌ No VM found with exact name match.\n\n"
        
        # ===== METHOD 2: Search Content Libraries by name =====
        result += "## 📚 Method 2: Content Library Search\n"
        result += "Searching Content Libraries for template name...\n\n"
        
        content_template_found = None
        
        try:
            libraries = client.content.Library.list()
            result += f"📚 Found {len(libraries)} Content Library(ies)\n\n"
            
            for library in libraries:
                try:
                    library_info = client.content.Library.get(library.library)
                    result += f"📚 **Checking Library: {library_info.name}**\n"
                    
                    # List items in this library
                    try:
                        items = client.content.library.Item.list(library.library)
                        result += f"   • Items in library: {len(items)}\n"
                        
                        for item in items:
                            try:
                                item_info = client.content.library.Item.get(library.library, item.item)
                                
                                # Check for exact name match
                                if item_info.name.lower() == template_name.lower():
                                    content_template_found = {
                                        'name': item_info.name,
                                        'id': item.item,
                                        'type': 'content_library_template',
                                        'library': library_info.name,
                                        'urn': item.item,
                                        'description': getattr(item_info, 'description', 'No description'),
                                        'item_info': item_info
                                    }
                                    
                                    result += f"   ✅ **Content Library Template Found**: {item_info.name}\n"
                                    result += f"      • URN: `{item.item}`\n"
                                    result += f"      • Library: {library_info.name}\n"
                                    result += f"      • Type: {getattr(item_info, 'type', 'Unknown')}\n"
                                    result += f"      • Description: {content_template_found['description']}\n"
                                    
                                    # Try to get detailed template info
                                    try:
                                        template_info = client.vcenter.vm_template.library_items.get(item.item)
                                        
                                        # Guest OS
                                        if hasattr(template_info, 'guest_os'):
                                            result += f"      • Guest OS: {template_info.guest_os}\n"
                                        
                                        # CPU info
                                        if hasattr(template_info, 'cpu') and template_info.cpu:
                                            result += f"      • CPU Count: {template_info.cpu.count}\n"
                                        
                                        # Memory info
                                        if hasattr(template_info, 'memory') and template_info.memory:
                                            result += f"      • Memory: {template_info.memory.size_mib} MB\n"
                                        
                                        # Hardware version
                                        if hasattr(template_info, 'hardware_version'):
                                            result += f"      • Hardware Version: {template_info.hardware_version}\n"
                                            
                                    except Exception as e:
                                        result += f"      • Error getting detailed info: {str(e)}\n"
                                    
                                    result += "\n"
                                    break
                                    
                            except Exception as e:
                                continue
                        
                        if content_template_found:
                            break
                            
                    except Exception as e:
                        result += f"   • Error listing items: {str(e)}\n"
                        
                except Exception as e:
                    result += f"   • Error getting library info: {str(e)}\n"
                    
        except Exception as e:
            result += f"❌ Error checking Content Libraries: {str(e)}\n"
        
        if not content_template_found:
            result += "❌ No Content Library template found with exact name match.\n\n"
        
        # ===== METHOD 3: Fuzzy name search =====
        result += "## 🔍 Method 3: Fuzzy Name Search\n"
        result += "Searching for partial name matches...\n\n"
        
        fuzzy_matches = []
        
        # Search VMs for partial matches
        for vm in vms:
            try:
                vm_info = client.vcenter.VM.get(vm.vm)
                vm_name_lower = vm_info.name.lower()
                template_name_lower = template_name.lower()
                
                # Check if template name is contained in VM name or vice versa
                if (template_name_lower in vm_name_lower or 
                    vm_name_lower in template_name_lower or
                    any(word in vm_name_lower for word in template_name_lower.split())):
                    
                    fuzzy_matches.append({
                        'name': vm_info.name,
                        'id': vm.vm,
                        'type': 'vm',
                        'template_property': getattr(vm_info, 'template', False),
                        'power_state': getattr(vm_info, 'power_state', 'Unknown'),
                        'match_type': 'fuzzy'
                    })
                    
            except Exception as e:
                continue
        
        # Search Content Libraries for partial matches
        try:
            for library in libraries:
                try:
                    items = client.content.library.Item.list(library.library)
                    
                    for item in items:
                        try:
                            item_info = client.content.library.Item.get(library.library, item.item)
                            item_name_lower = item_info.name.lower()
                            template_name_lower = template_name.lower()
                            
                            # Check if template name is contained in item name or vice versa
                            if (template_name_lower in item_name_lower or 
                                item_name_lower in template_name_lower or
                                any(word in item_name_lower for word in template_name_lower.split())):
                                
                                fuzzy_matches.append({
                                    'name': item_info.name,
                                    'id': item.item,
                                    'type': 'content_library',
                                    'library': library.name,
                                    'urn': item.item,
                                    'match_type': 'fuzzy'
                                })
                                
                        except Exception as e:
                            continue
                            
                except Exception as e:
                    continue
                    
        except Exception as e:
            pass
        
        if fuzzy_matches:
            result += f"🎯 Found {len(fuzzy_matches)} potential matches:\n\n"
            for match in fuzzy_matches:
                result += f"📄 **{match['name']}**\n"
                result += f"   • Type: {match['type']}\n"
                result += f"   • ID: {match['id']}\n"
                
                if match['type'] == 'vm':
                    result += f"   • Template Property: {match['template_property']}\n"
                    result += f"   • Power State: {match['power_state']}\n"
                elif match['type'] == 'content_library':
                    result += f"   • Library: {match['library']}\n"
                    result += f"   • URN: `{match['urn']}`\n"
                
                result += "\n"
        else:
            result += "❌ No fuzzy matches found.\n\n"
        
        # ===== SUMMARY =====
        result += "## 📊 Summary\n"
        
        if vm_template_found:
            result += f"✅ **Exact VM Template Match**: {vm_template_found['name']}\n"
            result += f"   • Use VM ID: `{vm_template_found['id']}` for deployment\n"
            result += f"   • Template Property: {vm_template_found['template_property']}\n"
            result += "\n"
        elif content_template_found:
            result += f"✅ **Exact Content Library Template Match**: {content_template_found['name']}\n"
            result += f"   • Use URN: `{content_template_found['urn']}` for deployment\n"
            result += f"   • Library: {content_template_found['library']}\n"
            result += "\n"
        else:
            result += "❌ **No exact match found**\n"
            if fuzzy_matches:
                result += f"💡 Found {len(fuzzy_matches)} potential matches above. Check if any match your template.\n"
            result += "\n"
        
        result += "💡 **Next Steps:**\n"
        if vm_template_found:
            result += "   • Use the VM ID with `deploy_from_template` tool\n"
        elif content_template_found:
            result += "   • Use the URN with `deploy_from_content_library` tool\n"
        else:
            result += "   • Check the fuzzy matches above\n"
            result += "   • Verify the template name in vCenter UI\n"
            result += "   • Check if template is in a different datacenter or folder\n"
        
        return result
        
    except Exception as e:
        return f"❌ Error searching for template '{template_name}': {str(e)}"

def find_template_by_name_ansible_style_text(template_name: str):
    """Find a template by name using Ansible's Container View approach."""
    try:
        client = get_vsphere_client()
        
        result = f"🔍 **Ansible-Style Template Search: '{template_name}'**\n\n"
        
        # ===== METHOD 1: Use VMware vCenter API (Ansible's approach) =====
        result += "## 📋 Method 1: VMware vCenter API (Ansible's Approach)\n"
        result += "Using vCenter's API to search all VMs and templates...\n\n"
        
        # Get all VMs using the VMware vCenter API
        # This is equivalent to Ansible's approach but using our API
        vms = client.vcenter.VM.list()
        
        template_found = None
        all_vms = []
        
        for vm in vms:
            try:
                vm_info = client.vcenter.VM.get(vm.vm)
                all_vms.append(vm_info)
                
                # Check for exact name match
                if vm_info.name.lower() == template_name.lower():
                    template_found = vm_info
                    result += f"✅ **EXACT MATCH FOUND**: {vm_info.name}\n"
                    result += f"   • VM ID: {vm.vm}\n"
                    result += f"   • Template Property: {getattr(vm_info, 'template', 'Not found')}\n"
                    result += f"   • Power State: {getattr(vm_info, 'power_state', 'Unknown')}\n"
                    
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
                    
                    # Get datastore info
                    vm_datastore = getattr(vm_info, 'datastore', None)
                    if vm_datastore:
                        try:
                            datastore_info = client.vcenter.Datastore.get(vm_datastore)
                            result += f"   • Datastore: {datastore_info.name}\n"
                        except:
                            result += f"   • Datastore ID: {vm_datastore}\n"
                    else:
                        result += f"   • Datastore: Unknown\n"
                    
                    result += "\n"
                    break
                    
            except Exception as e:
                continue
        
        if not template_found:
            result += "❌ No exact match found using VMware vCenter API.\n\n"
            
            # ===== METHOD 2: Search for partial matches =====
            result += "## 🔍 Method 2: Partial Name Matches\n"
            result += "Searching for VMs with similar names...\n\n"
            
            partial_matches = []
            for vm_info in all_vms:
                try:
                    vm_name_lower = vm_info.name.lower()
                    template_name_lower = template_name.lower()
                    
                    # Check for partial matches
                    if (template_name_lower in vm_name_lower or 
                        vm_name_lower in template_name_lower or
                        any(word in vm_name_lower for word in template_name_lower.split())):
                        
                        partial_matches.append({
                            'name': vm_info.name,
                            'id': vm_info.vm if hasattr(vm_info, 'vm') else 'Unknown',
                            'template': getattr(vm_info, 'template', False),
                            'power_state': getattr(vm_info, 'power_state', 'Unknown'),
                            'guest_os': getattr(vm_info, 'guest_OS', None) or getattr(vm_info, 'guest_os', None) or 'Unknown'
                        })
                        
                except Exception as e:
                    continue
            
            if partial_matches:
                result += f"🎯 Found {len(partial_matches)} potential matches:\n\n"
                for match in partial_matches:
                    template_marker = " (TEMPLATE)" if match['template'] else ""
                    result += f"📄 **{match['name']}{template_marker}**\n"
                    result += f"   • VM ID: {match['id']}\n"
                    result += f"   • Template Property: {match['template']}\n"
                    result += f"   • Power State: {match['power_state']}\n"
                    result += f"   • Guest OS: {match['guest_os']}\n"
                    result += "\n"
            else:
                result += "❌ No partial matches found.\n\n"
        
        # ===== METHOD 3: List all templates found =====
        result += "## 📋 Method 3: All Templates in vCenter\n"
        result += "Listing all VMs that are marked as templates...\n\n"
        
        all_templates = []
        for vm_info in all_vms:
            try:
                if getattr(vm_info, 'template', False):
                    # Safely get CPU count from nested cpu object
                    cpu_count = 'Unknown'
                    if hasattr(vm_info, 'cpu') and vm_info.cpu:
                        cpu_count = getattr(vm_info.cpu, 'count', 'Unknown')
                    
                    # Safely get memory size from nested memory object
                    memory_mb = 'Unknown'
                    if hasattr(vm_info, 'memory') and vm_info.memory:
                        memory_mb = getattr(vm_info.memory, 'size_MiB', 'Unknown')
                    
                    all_templates.append({
                        'name': vm_info.name,
                        'id': vm_info.vm if hasattr(vm_info, 'vm') else 'Unknown',
                        'power_state': getattr(vm_info, 'power_state', 'Unknown'),
                        'guest_os': getattr(vm_info, 'guest_OS', None) or getattr(vm_info, 'guest_os', None) or 'Unknown',
                        'cpu_count': cpu_count,
                        'memory_mb': memory_mb
                    })
            except Exception as e:
                continue
        
        if all_templates:
            result += f"✅ Found {len(all_templates)} template(s) in vCenter:\n\n"
            for template in all_templates:
                result += f"📄 **{template['name']}**\n"
                result += f"   • VM ID: {template['id']}\n"
                result += f"   • Power State: {template['power_state']}\n"
                result += f"   • Guest OS: {template['guest_os']}\n"
                result += f"   • CPU Count: {template['cpu_count']}\n"
                result += f"   • Memory: {template['memory_mb']} MB\n"
                result += "\n"
        else:
            result += "❌ No templates found in vCenter.\n\n"
        
        # ===== SUMMARY =====
        result += "## 📊 Summary\n"
        
        if template_found:
            result += f"✅ **Template Found**: {template_found.name}\n"
            result += f"   • Use VM ID: `{vm.vm}` for deployment\n"
            result += f"   • Template Property: {getattr(template_found, 'template', 'Not found')}\n"
            result += "\n"
        else:
            result += "❌ **No exact match found**\n"
            if partial_matches:
                result += f"💡 Found {len(partial_matches)} potential matches above.\n"
            if all_templates:
                result += f"💡 Found {len(all_templates)} templates in vCenter.\n"
            result += "\n"
        
        result += "💡 **Next Steps:**\n"
        if template_found:
            result += "   • Use the VM ID with `deploy_from_template` tool\n"
        else:
            result += "   • Check the partial matches above\n"
            result += "   • Verify the template name in vCenter UI\n"
            result += "   • Check if template is in a different datacenter\n"
        
        return result
        
    except Exception as e:
        return f"❌ Error in Ansible-style template search: {str(e)}"

def get_vm_folder_path(vm_obj):
    """Get the folder path for a VM object (helper function)."""
    try:
        paths = []
        current_obj = vm_obj
        
        while hasattr(current_obj, 'parent') and current_obj.parent:
            current_obj = current_obj.parent
            if hasattr(current_obj, 'name'):
                paths.append(current_obj.name)
            # Stop at root folders
            if hasattr(current_obj, '_moId') and current_obj._moId in ['group-d1', 'ha-folder-root']:
                break
        
        paths.reverse()
        return '/' + '/'.join(paths) if paths else None
        
    except Exception:
        return None 