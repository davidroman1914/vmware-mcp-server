#!/usr/bin/env python3
"""
Debug script to help understand VM template detection
Run this when connected to a real vCenter to see what properties are available
"""

from vmware.vapi.vsphere.client import create_vsphere_client
from config import Config
import json

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

    # Create vSphere client
    return create_vsphere_client(
        server=host, 
        username=user, 
        password=pwd, 
        session=session
    )

def debug_vm_properties():
    """Debug VM properties to understand template detection."""
    try:
        client = get_vsphere_client()
        
        print("🔍 Debugging VM Properties for Template Detection")
        print("=" * 60)
        
        # First, check Content Libraries (the correct way to find templates)
        print("📚 Checking Content Libraries for VM Templates:")
        print("-" * 50)
        
        try:
            libraries = client.content.Library.list()
            print(f"📋 Found {len(libraries)} Content Library(ies)")
            
            for library in libraries:
                print(f"\n📚 Library: {library.name} (ID: {library.library})")
                print(f"   • Type: {library.type}")
                print(f"   • Version: {library.version}")
                
                try:
                    items = client.content.library.Item.list(library.library)
                    print(f"   • Items: {len(items)}")
                    
                    for item in items:
                        print(f"      📄 Item: {item.name} (ID: {item.item})")
                        print(f"         • Type: {item.type}")
                        print(f"         • Description: {item.description}")
                        
                        # Check if this is a VM template
                        if hasattr(item, 'type') and item.type == 'vm-template':
                            print(f"         ✅ This is a VM template!")
                            try:
                                template_info = client.vcenter.vm_template.library_items.get(item.item)
                                print(f"         • Guest OS: {template_info.guest_os}")
                                print(f"         • CPU: {template_info.cpu.count} cores")
                                print(f"         • Memory: {template_info.memory.size_mib} MB")
                                print(f"         • VM Template ID: {template_info.vm_template}")
                            except Exception as e:
                                print(f"         ❌ Error getting template details: {e}")
                        
                except Exception as e:
                    print(f"   ❌ Error listing items: {e}")
                    
        except Exception as e:
            print(f"❌ Error accessing Content Libraries: {e}")
            print("   This might be due to permissions or Content Library not being enabled")
        
        # Get all VMs (fallback method)
        print("\n" + "="*60)
        print("🔍 Checking Regular VMs (Fallback Method)")
        print("="*60)
        
        vms = client.vcenter.VM.list()
        print(f"📋 Found {len(vms)} total VMs\n")
        
        if not vms:
            print("❌ No VMs found in vCenter.")
            return
        
        # Analyze first few VMs in detail
        for i, vm in enumerate(vms[:3]):  # Look at first 3 VMs
            print(f"🔍 Analyzing VM {i+1}: {vm.vm}")
            
            try:
                vm_info = client.vcenter.VM.get(vm.vm)
                print(f"   Name: {vm_info.name}")
                print(f"   Power State: {vm_info.power_state}")
                
                # List all available properties
                print("   Available properties:")
                for attr in dir(vm_info):
                    if not attr.startswith('_') and not callable(getattr(vm_info, attr)):
                        try:
                            value = getattr(vm_info, attr)
                            if value is not None:
                                print(f"     • {attr}: {value} ({type(value).__name__})")
                        except Exception as e:
                            print(f"     • {attr}: Error accessing - {e}")
                
                # Check specific template-related properties
                print("   Template detection checks:")
                print(f"     • has 'template' property: {hasattr(vm_info, 'template')}")
                if hasattr(vm_info, 'template'):
                    print(f"     • template value: {vm_info.template}")
                
                print(f"     • has 'type' property: {hasattr(vm_info, 'type')}")
                if hasattr(vm_info, 'type'):
                    print(f"     • type value: {vm_info.type}")
                
                print(f"     • has 'folder' property: {hasattr(vm_info, 'folder')}")
                if hasattr(vm_info, 'folder'):
                    print(f"     • folder value: {vm_info.folder}")
                
                print(f"     • name contains 'template': {'template' in vm_info.name.lower()}")
                
                print()
                
            except Exception as e:
                print(f"   ❌ Error getting VM info: {e}\n")
        
        # Try to find any VMs that might be templates
        print("🎯 Template Detection Results:")
        print("=" * 40)
        
        potential_templates = []
        
        for vm in vms:
            try:
                vm_info = client.vcenter.VM.get(vm.vm)
                
                # Check various template indicators
                indicators = []
                
                if hasattr(vm_info, 'template') and vm_info.template:
                    indicators.append("template property = True")
                
                if hasattr(vm_info, 'type') and vm_info.type == 'template':
                    indicators.append("type = 'template'")
                
                if 'template' in vm_info.name.lower():
                    indicators.append("name contains 'template'")
                
                if hasattr(vm_info, 'folder') and vm_info.folder and 'template' in vm_info.folder.lower():
                    indicators.append("folder contains 'template'")
                
                if indicators:
                    potential_templates.append((vm_info.name, indicators))
                
            except Exception as e:
                print(f"❌ Error analyzing {vm.vm}: {e}")
        
        if potential_templates:
            print(f"✅ Found {len(potential_templates)} potential templates:")
            for name, indicators in potential_templates:
                print(f"   📄 {name}")
                for indicator in indicators:
                    print(f"      • {indicator}")
                print()
        else:
            print("❌ No potential templates found using current detection methods.")
            print("\n💡 Suggestions:")
            print("   • Check if templates are stored in Content Libraries")
            print("   • Look for VMs with specific naming conventions")
            print("   • Check if templates have specific tags or annotations")
            print("   • Verify that templates are actually marked as templates in vCenter")
        
        # Additional analysis - check for any VMs that might be templates based on other criteria
        print("\n🔍 Additional Template Analysis:")
        print("=" * 40)
        
        # Check for VMs with specific naming patterns
        template_patterns = ['template', 'tpl', 'gold', 'master', 'base']
        for vm in vms:
            try:
                vm_info = client.vcenter.VM.get(vm.vm)
                vm_name_lower = vm_info.name.lower()
                
                for pattern in template_patterns:
                    if pattern in vm_name_lower:
                        print(f"   📄 Potential template by name pattern '{pattern}': {vm_info.name}")
                        break
                        
            except Exception as e:
                continue
        
        # Check for VMs in specific folders
        print("\n📁 Checking for VMs in template-related folders:")
        try:
            folders = client.vcenter.Folder.list()
            for folder in folders:
                folder_name_lower = folder.name.lower()
                if any(pattern in folder_name_lower for pattern in template_patterns):
                    print(f"   📁 Found template-related folder: {folder.name} (ID: {folder.folder})")
                    
                    # List VMs in this folder
                    try:
                        folder_vms = client.vcenter.VM.list(folder=folder.folder)
                        for vm in folder_vms:
                            print(f"      📄 VM in template folder: {vm.vm}")
                    except Exception as e:
                        print(f"      ❌ Error listing VMs in folder: {e}")
        except Exception as e:
            print(f"   ❌ Error listing folders: {e}")
        
    except Exception as e:
        print(f"❌ Error during debug: {e}")

def test_template_detection_methods():
    """Test different template detection methods."""
    try:
        client = get_vsphere_client()
        
        print("\n🧪 Testing Template Detection Methods:")
        print("=" * 50)
        
        vms = client.vcenter.VM.list()
        
        # Method 1: Check if VM is marked as template
        print("Method 1: Checking 'template' property")
        template_vms = []
        for vm in vms:
            try:
                vm_info = client.vcenter.VM.get(vm.vm)
                if hasattr(vm_info, 'template') and vm_info.template:
                    template_vms.append(vm_info.name)
            except:
                continue
        
        if template_vms:
            print(f"   ✅ Found {len(template_vms)} VMs with template=True:")
            for name in template_vms:
                print(f"      • {name}")
        else:
            print("   ❌ No VMs found with template=True")
        
        # Method 2: Check VM type
        print("\nMethod 2: Checking VM type")
        type_templates = []
        for vm in vms:
            try:
                vm_info = client.vcenter.VM.get(vm.vm)
                if hasattr(vm_info, 'type') and vm_info.type == 'template':
                    type_templates.append(vm_info.name)
            except:
                continue
        
        if type_templates:
            print(f"   ✅ Found {len(type_templates)} VMs with type='template':")
            for name in type_templates:
                print(f"      • {name}")
        else:
            print("   ❌ No VMs found with type='template'")
        
        # Method 3: Check naming patterns
        print("\nMethod 3: Checking naming patterns")
        name_templates = []
        for vm in vms:
            try:
                vm_info = client.vcenter.VM.get(vm.vm)
                if 'template' in vm_info.name.lower():
                    name_templates.append(vm_info.name)
            except:
                continue
        
        if name_templates:
            print(f"   ✅ Found {len(name_templates)} VMs with 'template' in name:")
            for name in name_templates:
                print(f"      • {name}")
        else:
            print("   ❌ No VMs found with 'template' in name")
        
        # Method 4: Check folder location
        print("\nMethod 4: Checking folder location")
        folder_templates = []
        for vm in vms:
            try:
                vm_info = client.vcenter.VM.get(vm.vm)
                if hasattr(vm_info, 'folder') and vm_info.folder and 'template' in vm_info.folder.lower():
                    folder_templates.append((vm_info.name, vm_info.folder))
            except:
                continue
        
        if folder_templates:
            print(f"   ✅ Found {len(folder_templates)} VMs in template folders:")
            for name, folder in folder_templates:
                print(f"      • {name} (folder: {folder})")
        else:
            print("   ❌ No VMs found in template folders")
        
        # Summary
        all_templates = set(template_vms + type_templates + name_templates + [name for name, _ in folder_templates])
        print(f"\n📊 Summary: Found {len(all_templates)} unique potential templates")
        if all_templates:
            print("   Templates found:")
            for name in sorted(all_templates):
                print(f"      • {name}")
        
    except Exception as e:
        print(f"❌ Error testing template detection: {e}")

if __name__ == "__main__":
    debug_vm_properties()
    test_template_detection_methods() 