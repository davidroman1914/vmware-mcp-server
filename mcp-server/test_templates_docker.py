#!/usr/bin/env python3
"""
Enhanced test script for template detection in Docker environment.
Uses multiple aggressive methods to find templates that might be hidden.
"""

import os
import sys
from vmware.vapi.vsphere.client import create_vsphere_client

def get_vsphere_client():
    """Get vSphere client with proper authentication."""
    # Get credentials from environment
    vcenter_host = os.getenv('VCENTER_HOST')
    vcenter_user = os.getenv('VCENTER_USER')
    vcenter_password = os.getenv('VCENTER_PASSWORD')
    vcenter_insecure = os.getenv('VCENTER_INSECURE', 'false').lower() == 'true'
    
    if not all([vcenter_host, vcenter_user, vcenter_password]):
        print("❌ Missing environment variables: VCENTER_HOST, VCENTER_USER, VCENTER_PASSWORD")
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

def test_aggressive_template_detection():
    """Test aggressive template detection with multiple methods."""
    print("🧪 AGGRESSIVE TEMPLATE DETECTION TEST")
    print("=" * 50)
    
    try:
        client = get_vsphere_client()
        print("✅ Connected to vCenter successfully\n")
        
        # ===== METHOD 1: BASIC TEMPLATE PROPERTY =====
        print("🔍 METHOD 1: Basic Template Property Check")
        print("-" * 40)
        
        vms = client.vcenter.VM.list()
        print(f"📊 Found {len(vms)} total VMs in vCenter")
        
        template_property_vms = []
        for vm in vms:
            try:
                vm_info = client.vcenter.VM.get(vm.vm)
                if hasattr(vm_info, 'template') and vm_info.template:
                    template_property_vms.append(vm_info)
                    print(f"   ✅ Template (property): {vm_info.name}")
            except Exception as e:
                continue
        
        print(f"   📊 Found {len(template_property_vms)} VMs with template=True\n")
        
        # ===== METHOD 2: NAME-BASED DETECTION =====
        print("🔍 METHOD 2: Name-Based Template Detection")
        print("-" * 40)
        
        name_patterns = ['template', 'tpl', 'gold', 'master', 'base', 'golden', 'master-image']
        name_based_templates = []
        
        for vm in vms:
            try:
                vm_info = client.vcenter.VM.get(vm.vm)
                vm_name_lower = vm_info.name.lower()
                
                for pattern in name_patterns:
                    if pattern in vm_name_lower:
                        name_based_templates.append((vm_info, pattern))
                        print(f"   ✅ Template (name '{pattern}'): {vm_info.name}")
                        break
            except Exception as e:
                continue
        
        print(f"   📊 Found {len(name_based_templates)} VMs with template-like names\n")
        
        # ===== METHOD 3: POWER STATE + NAME ANALYSIS =====
        print("🔍 METHOD 3: Powered-Off + Template Name Analysis")
        print("-" * 40)
        
        powered_off_templates = []
        for vm in vms:
            try:
                vm_info = client.vcenter.VM.get(vm.vm)
                
                # Check if powered off and has template-like name
                if (getattr(vm_info, 'power_state', '') == 'POWERED_OFF' and 
                    any(pattern in vm_info.name.lower() for pattern in name_patterns)):
                    powered_off_templates.append(vm_info)
                    print(f"   ✅ Template (powered off + name): {vm_info.name}")
            except Exception as e:
                continue
        
        print(f"   📊 Found {len(powered_off_templates)} powered-off VMs with template names\n")
        
        # ===== METHOD 4: DATACENTER-SPECIFIC SEARCH =====
        print("🔍 METHOD 4: Datacenter-Specific Template Search")
        print("-" * 40)
        
        try:
            datacenters = client.vcenter.Datacenter.list()
            print(f"📊 Found {len(datacenters)} datacenter(s)")
            
            for dc in datacenters:
                try:
                    dc_info = client.vcenter.Datacenter.get(dc.datacenter)
                    print(f"\n🏢 Checking Datacenter: {dc_info.name}")
                    
                    # Get VMs in this datacenter
                    dc_vms = client.vcenter.VM.list()
                    dc_templates = []
                    
                    for vm in dc_vms:
                        try:
                            vm_info = client.vcenter.VM.get(vm.vm)
                            
                            # Check if VM is in this datacenter
                            if hasattr(vm_info, 'datacenter') and vm_info.datacenter == dc.datacenter:
                                # Check for template indicators
                                is_template = getattr(vm_info, 'template', False)
                                has_template_name = any(pattern in vm_info.name.lower() for pattern in name_patterns)
                                
                                if is_template or has_template_name:
                                    dc_templates.append(vm_info)
                                    indicator = "template property" if is_template else "template name"
                                    print(f"   ✅ Template ({indicator}): {vm_info.name}")
                        except:
                            continue
                    
                    if dc_templates:
                        print(f"   📊 Found {len(dc_templates)} templates in {dc_info.name}")
                    else:
                        print(f"   ℹ️ No templates found in {dc_info.name}")
                        
                except Exception as e:
                    print(f"   ❌ Error checking datacenter: {str(e)}")
                    
        except Exception as e:
            print(f"❌ Error in datacenter analysis: {str(e)}\n")
        
        # ===== METHOD 5: FOLDER-BASED SEARCH =====
        print("\n🔍 METHOD 5: Folder-Based Template Search")
        print("-" * 40)
        
        try:
            folders = client.vcenter.Folder.list()
            print(f"📊 Found {len(folders)} folders")
            
            template_folders = []
            for folder in folders:
                try:
                    folder_info = client.vcenter.Folder.get(folder.folder)
                    folder_name_lower = folder_info.name.lower()
                    
                    # Check if folder name suggests templates
                    if any(pattern in folder_name_lower for pattern in ['template', 'tpl', 'gold', 'master', 'base']):
                        template_folders.append(folder_info)
                        print(f"   📁 Template folder: {folder_info.name}")
                        
                        # List VMs in this folder
                        try:
                            folder_vms = client.vcenter.VM.list(folder=folder.folder)
                            if folder_vms:
                                print(f"      📊 Contains {len(folder_vms)} VMs")
                                for vm in folder_vms[:3]:  # Show first 3
                                    try:
                                        vm_info = client.vcenter.VM.get(vm.vm)
                                        print(f"      • {vm_info.name}")
                                    except:
                                        print(f"      • {vm.vm} (error getting name)")
                                if len(folder_vms) > 3:
                                    print(f"      ... and {len(folder_vms) - 3} more")
                        except Exception as e:
                            print(f"      ❌ Error listing VMs: {str(e)}")
                            
                except Exception as e:
                    continue
            
            if not template_folders:
                print("   ℹ️ No template-related folders found")
                
        except Exception as e:
            print(f"❌ Error in folder analysis: {str(e)}\n")
        
        # ===== METHOD 6: CONTENT LIBRARY SEARCH =====
        print("\n🔍 METHOD 6: Content Library Template Search")
        print("-" * 40)
        
        try:
            libraries = client.content.Library.list()
            print(f"📊 Found {len(libraries)} Content Library(ies)")
            
            for library in libraries:
                try:
                    library_info = client.content.Library.get(library.library)
                    print(f"\n📚 Library: {library_info.name}")
                    
                    # List items in this library
                    try:
                        items = client.content.library.Item.list(library.library)
                        print(f"   📊 Contains {len(items)} items")
                        
                        for item in items:
                            try:
                                item_info = client.content.library.Item.get(library.library, item.item)
                                item_type = getattr(item_info, 'type', 'Unknown')
                                print(f"   • {item_info.name} (Type: {item_type})")
                                
                                # Check if this is a VM template
                                if item_type == 'vm-template':
                                    print(f"      ✅ **VM TEMPLATE FOUND**: {item_info.name}")
                                    print(f"         • Item ID: {item.item}")
                                    print(f"         • Type: {item_type}")
                                    
                            except Exception as e:
                                print(f"   • Error getting item info: {str(e)}")
                                
                    except Exception as e:
                        print(f"   ❌ Error listing items: {str(e)}")
                        
                except Exception as e:
                    print(f"   ❌ Error getting library info: {str(e)}")
                    
        except Exception as e:
            print(f"❌ Error in Content Library analysis: {str(e)}\n")
        
        # ===== METHOD 7: AGGRESSIVE UBUNTU SEARCH =====
        print("\n🔍 METHOD 7: Aggressive Ubuntu Template Search")
        print("-" * 40)
        
        ubuntu_vms = []
        for vm in vms:
            try:
                vm_info = client.vcenter.VM.get(vm.vm)
                vm_name_lower = vm_info.name.lower()
                
                # Look for Ubuntu VMs specifically
                if 'ubuntu' in vm_name_lower:
                    ubuntu_vms.append(vm_info)
                    print(f"   🎯 Ubuntu VM found: {vm_info.name}")
                    
                    # Check if it might be a template
                    is_template = getattr(vm_info, 'template', False)
                    power_state = getattr(vm_info, 'power_state', 'Unknown')
                    
                    if is_template:
                        print(f"      ✅ **CONFIRMED TEMPLATE** (template=True)")
                    elif power_state == 'POWERED_OFF':
                        print(f"      ⚠️ **POTENTIAL TEMPLATE** (powered off)")
                    else:
                        print(f"      ℹ️ Regular VM (power state: {power_state})")
                        
            except Exception as e:
                continue
        
        print(f"   📊 Found {len(ubuntu_vms)} Ubuntu VMs\n")
        
        # ===== COMPREHENSIVE SUMMARY =====
        print("📊 COMPREHENSIVE TEMPLATE DETECTION SUMMARY")
        print("=" * 50)
        
        all_templates = set()
        
        # Collect all unique templates found
        for vm in template_property_vms:
            all_templates.add(vm.name)
        
        for vm, pattern in name_based_templates:
            all_templates.add(vm.name)
        
        for vm in powered_off_templates:
            all_templates.add(vm.name)
        
        for vm in ubuntu_vms:
            if getattr(vm, 'template', False) or getattr(vm, 'power_state', '') == 'POWERED_OFF':
                all_templates.add(vm.name)
        
        if all_templates:
            print(f"🎉 **TEMPLATES FOUND**: {len(all_templates)} unique template(s)")
            print("\n📄 **Template List:**")
            for template_name in sorted(all_templates):
                print(f"   • {template_name}")
            
            print(f"\n💡 **Detection Methods Used:**")
            print(f"   • Template property check: {len(template_property_vms)} found")
            print(f"   • Name pattern matching: {len(name_based_templates)} found")
            print(f"   • Powered-off + name analysis: {len(powered_off_templates)} found")
            print(f"   • Ubuntu-specific search: {len(ubuntu_vms)} found")
            
        else:
            print("❌ **NO TEMPLATES FOUND**")
            print("\n💡 **Possible Reasons:**")
            print("   1. No VMs have been converted to templates yet")
            print("   2. Templates are in Content Libraries (not regular VMs)")
            print("   3. Templates are in a different datacenter")
            print("   4. Your user doesn't have permission to see templates")
            print("   5. Templates are in a different inventory view")
            print("   6. Templates have different naming conventions")
            
            print(f"\n🔍 **What We Found:**")
            print(f"   • Total VMs in vCenter: {len(vms)}")
            print(f"   • Ubuntu VMs: {len(ubuntu_vms)}")
            print(f"   • VMs with template names: {len(name_based_templates)}")
            
            if ubuntu_vms:
                print(f"\n🎯 **Ubuntu VMs Found (potential templates):**")
                for vm in ubuntu_vms:
                    print(f"   • {vm.name}")
        
        print("\n✅ Template detection test completed!")
        
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
        sys.exit(1)

def test_strict_ansible_template_detection():
    """Strict Ansible-style template detection: only template=True."""
    print("\n🧪 STRICT ANSIBLE TEMPLATE DETECTION (template=True only)")
    print("=" * 50)
    try:
        client = get_vsphere_client()
        vms = client.vcenter.VM.list()
        strict_templates = []
        for vm in vms:
            try:
                vm_info = client.vcenter.VM.get(vm.vm)
                if hasattr(vm_info, 'template') and vm_info.template:
                    strict_templates.append(vm_info)
            except Exception:
                continue
        if strict_templates:
            print(f"✅ Found {len(strict_templates)} template(s) with template=True:")
            for t in strict_templates:
                print(f"   • {t.name} (ID: {t.vm if hasattr(t, 'vm') else 'Unknown'})")
        else:
            print("❌ No templates found with template=True (strict Ansible mode)")
    except Exception as e:
        print(f"❌ Error in strict Ansible template detection: {str(e)}")

if __name__ == "__main__":
    test_aggressive_template_detection()
    test_strict_ansible_template_detection() 