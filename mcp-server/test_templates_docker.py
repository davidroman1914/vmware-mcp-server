#!/usr/bin/env python3
"""
Test script for template detection in Docker environment.
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

def test_template_detection():
    """Test template detection functionality."""
    print("🧪 Testing Template Detection")
    print("=" * 40)
    
    try:
        client = get_vsphere_client()
        
        # Test 1: List all VMs
        print("📋 Test 1: Listing all VMs...")
        vms = client.vcenter.VM.list()
        print(f"   ✅ Found {len(vms)} VMs")
        
        # Test 2: Check for templates
        print("\n📄 Test 2: Checking for templates...")
        templates_found = []
        
        for vm in vms:
            try:
                vm_info = client.vcenter.VM.get(vm.vm)
                
                # Check template property (primary method)
                if hasattr(vm_info, 'template') and vm_info.template:
                    templates_found.append((vm_info.name, "template property"))
                    print(f"   ✅ Found template: {vm_info.name} (via template property)")
                
                # Check VM type
                elif hasattr(vm_info, 'type') and vm_info.type == 'template':
                    templates_found.append((vm_info.name, "VM type"))
                    print(f"   ✅ Found template: {vm_info.name} (via VM type)")
                
                # Check name patterns
                elif any(pattern in vm_info.name.lower() for pattern in ['template', 'tpl', 'gold', 'master', 'base']):
                    templates_found.append((vm_info.name, "name pattern"))
                    print(f"   ✅ Found template: {vm_info.name} (via name pattern)")
                
            except Exception as e:
                print(f"   ⚠️ Error checking VM {vm.name}: {str(e)}")
        
        if templates_found:
            print(f"\n🎉 Success! Found {len(templates_found)} template(s):")
            for name, method in templates_found:
                print(f"   📄 {name} (detected via: {method})")
        else:
            print("\nℹ️ No templates found - this is normal if no templates exist yet")
            print("💡 To create templates:")
            print("   1. Right-click on a VM in vCenter")
            print("   2. Select 'Template' > 'Convert to Template'")
            print("   3. Run this test again")
        
        # Test 3: Test template listing function
        print("\n🔧 Test 3: Testing template listing function...")
        from vm_info import list_templates_text
        template_list = list_templates_text()
        print("   Template listing result:")
        print("   " + "\n   ".join(template_list.split('\n')))
        
        print("\n✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    test_template_detection() 