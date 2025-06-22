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
        
        # Get all VMs
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
            print("   • Check if templates are stored in a specific folder")
            print("   • Look for VMs with specific naming conventions")
            print("   • Check if templates have specific tags or annotations")
            print("   • Verify that templates are actually marked as templates in vCenter")
        
    except Exception as e:
        print(f"❌ Error during debug: {e}")

if __name__ == "__main__":
    debug_vm_properties() 