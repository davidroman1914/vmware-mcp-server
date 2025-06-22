#!/usr/bin/env python3
"""
Debug script to analyze VM templates in vCenter.
Based on pyvmomi community samples approach - templates are VMs with specific properties.
"""

import os
import sys
from vmware.vapi.vsphere.client import create_vsphere_client

def get_vsphere_client():
    """Get vSphere client with proper authentication."""
    # Get credentials from environment
    vcenter_host = os.getenv('VCENTER_SERVER') or os.getenv('VCENTER_HOST')
    vcenter_user = os.getenv('VCENTER_USERNAME') or os.getenv('VCENTER_USER')
    vcenter_password = os.getenv('VCENTER_PASSWORD')
    vcenter_insecure = os.getenv('VCENTER_INSECURE', 'false').lower() == 'true'
    
    if not all([vcenter_host, vcenter_user, vcenter_password]):
        print("❌ Error: Missing vCenter credentials in environment variables")
        print("   Please set: VCENTER_SERVER, VCENTER_USERNAME, VCENTER_PASSWORD")
        print("   Or use: VCENTER_HOST, VCENTER_USER, VCENTER_PASSWORD")
        sys.exit(1)
    
    # Create session with SSL handling
    import requests
    import urllib3
    
    session = requests.Session()
    session.verify = not vcenter_insecure
    
    # Disable SSL warnings for demo (not recommended in production)
    if vcenter_insecure:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    # Create vSphere client
    return create_vsphere_client(
        server=vcenter_host, 
        username=vcenter_user, 
        password=vcenter_password, 
        session=session
    )

def analyze_vm_properties():
    """Analyze VM properties to understand template detection."""
    print("🔍 Analyzing VM properties for template detection...")
    print("=" * 60)
    
    try:
        client = get_vsphere_client()
        vms = client.vcenter.VM.list()
        
        if not vms:
            print("❌ No VMs found in vCenter")
            return
        
        print(f"📊 Found {len(vms)} VMs in vCenter")
        print()
        
        # Analyze first few VMs to understand properties
        for i, vm in enumerate(vms[:5]):  # Analyze first 5 VMs
            print(f"🔍 Analyzing VM {i+1}: {vm.name}")
            print("-" * 40)
            
            try:
                vm_info = client.vcenter.VM.get(vm.vm)
                
                # List all available properties
                print("📋 Available properties:")
                for attr in dir(vm_info):
                    if not attr.startswith('_') and not callable(getattr(vm_info, attr)):
                        try:
                            value = getattr(vm_info, attr)
                            value_type = type(value).__name__
                            
                            # Show the value if it's not too long
                            if isinstance(value, str) and len(str(value)) < 50:
                                print(f"   • {attr}: {value} ({value_type})")
                            else:
                                print(f"   • {attr}: {value_type}")
                                
                        except Exception as e:
                            print(f"   • {attr}: Error accessing ({str(e)})")
                
                # Check for template-specific properties
                print("\n🎯 Template detection checks:")
                
                # Check template property
                if hasattr(vm_info, 'template'):
                    template_value = getattr(vm_info, 'template', None)
                    print(f"   • template property: {template_value}")
                else:
                    print("   • template property: Not found")
                
                # Check VM type
                if hasattr(vm_info, 'type'):
                    vm_type = getattr(vm_info, 'type', None)
                    print(f"   • type property: {vm_type}")
                else:
                    print("   • type property: Not found")
                
                # Check if name contains template patterns
                template_patterns = ['template', 'tpl', 'gold', 'master', 'base']
                name_matches = [pattern for pattern in template_patterns if pattern in vm_info.name.lower()]
                if name_matches:
                    print(f"   • Name patterns: {name_matches}")
                else:
                    print("   • Name patterns: None")
                
                # Check folder location
                if hasattr(vm_info, 'folder'):
                    folder = getattr(vm_info, 'folder', None)
                    print(f"   • folder: {folder}")
                    if folder:
                        folder_matches = [pattern for pattern in template_patterns if pattern in folder.lower()]
                        if folder_matches:
                            print(f"   • Folder patterns: {folder_matches}")
                else:
                    print("   • folder: Not found")
                
                print()
                
            except Exception as e:
                print(f"❌ Error analyzing VM {vm.name}: {str(e)}")
                print()
        
        # Now check for actual templates
        print("🎯 Checking for actual templates...")
        print("-" * 40)
        
        templates_found = []
        for vm in vms:
            try:
                vm_info = client.vcenter.VM.get(vm.vm)
                is_template = False
                detection_method = None
                
                # Check template property (primary method)
                if hasattr(vm_info, 'template') and vm_info.template:
                    is_template = True
                    detection_method = "template property"
                
                # Check VM type
                elif hasattr(vm_info, 'type') and vm_info.type == 'template':
                    is_template = True
                    detection_method = "VM type"
                
                # Check name patterns
                elif any(pattern in vm_info.name.lower() for pattern in ['template', 'tpl', 'gold', 'master', 'base']):
                    is_template = True
                    detection_method = "name pattern"
                
                # Check folder patterns
                elif hasattr(vm_info, 'folder') and vm_info.folder:
                    if any(pattern in vm_info.folder.lower() for pattern in ['template', 'tpl', 'gold', 'master', 'base']):
                        is_template = True
                        detection_method = "folder pattern"
                
                if is_template:
                    templates_found.append((vm_info, detection_method))
                    
            except Exception as e:
                print(f"❌ Error checking VM {vm.name}: {str(e)}")
        
        if templates_found:
            print(f"✅ Found {len(templates_found)} template(s):")
            for template, method in templates_found:
                print(f"   📄 {template.name} (detected via: {method})")
        else:
            print("ℹ️ No templates found using current detection methods")
            print("\n💡 To create templates:")
            print("   1. Right-click on a VM in vCenter")
            print("   2. Select 'Template' > 'Convert to Template'")
            print("   3. The VM will then appear as a template")
        
        print("\n" + "=" * 60)
        print("🔍 Analysis complete!")
        
    except Exception as e:
        print(f"❌ Error during analysis: {str(e)}")

if __name__ == "__main__":
    analyze_vm_properties() 