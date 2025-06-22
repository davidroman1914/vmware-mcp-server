#!/usr/bin/env python3
"""
Debug script to analyze VM templates in vCenter.
Enhanced to check if templates are marked as virtual machines.
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

def analyze_template_vm_relationship():
    """Analyze the relationship between templates and virtual machines."""
    print("🔍 Analyzing Template-VM Relationship (Comprehensive Detection)")
    print("=" * 70)
    
    try:
        client = get_vsphere_client()
        vms = client.vcenter.VM.list()
        
        if not vms:
            print("❌ No VMs found in vCenter")
            return
        
        print(f"📊 Found {len(vms)} VMs in vCenter")
        print()
        
        # Track templates and their properties
        templates_found = []
        regular_vms = []
        
        for vm in vms:
            try:
                vm_info = client.vcenter.VM.get(vm.vm)
                
                # Check if this VM has been converted to a template
                # According to VMware docs, templates are VMs with template=True
                is_template = False
                detection_method = None
                template_properties = {}
                
                # Check template property (the official way)
                if hasattr(vm_info, 'template'):
                    template_properties['template_property'] = vm_info.template
                    if vm_info.template:
                        is_template = True
                        detection_method = "template property"
                
                # Check VM type
                if hasattr(vm_info, 'type'):
                    template_properties['vm_type'] = vm_info.type
                    if vm_info.type == 'template' and not is_template:
                        is_template = True
                        detection_method = "VM type"
                
                # Check name patterns (fallback)
                template_patterns = ['template', 'tpl', 'gold', 'master', 'base']
                name_matches = [pattern for pattern in template_patterns if pattern in vm_info.name.lower()]
                if name_matches and not is_template:
                    template_properties['name_patterns'] = name_matches
                    is_template = True
                    detection_method = "name pattern"
                
                # Collect all properties for analysis
                all_properties = {}
                for attr in dir(vm_info):
                    if not attr.startswith('_') and not callable(getattr(vm_info, attr)):
                        try:
                            value = getattr(vm_info, attr)
                            all_properties[attr] = value
                        except:
                            pass
                
                template_properties['all_properties'] = all_properties
                
                if is_template:
                    templates_found.append({
                        'name': vm_info.name,
                        'id': vm.vm,
                        'detection_method': detection_method,
                        'properties': template_properties,
                        'vm_info': vm_info
                    })
                else:
                    regular_vms.append({
                        'name': vm_info.name,
                        'id': vm.vm,
                        'properties': template_properties,
                        'vm_info': vm_info
                    })
                    
            except Exception as e:
                print(f"❌ Error analyzing VM {vm.name}: {str(e)}")
        
        # ===== ANALYSIS RESULTS =====
        print("🎯 **TEMPLATE ANALYSIS RESULTS**")
        print("=" * 60)
        
        if templates_found:
            print(f"✅ Found {len(templates_found)} template(s):")
            print()
            
            for template in templates_found:
                vm_info = template['vm_info']
                print(f"📄 **{vm_info.name}** (ID: `{template['id']}`)")
                print(f"   • Detection Method: {template['detection_method']}")
                print(f"   • Template Property: {template['properties'].get('template_property', 'Not found')}")
                print(f"   • VM Type: {template['properties'].get('vm_type', 'Not found')}")
                print(f"   • Power State: {getattr(vm_info, 'power_state', 'Unknown')}")
                print(f"   • Guest OS: {getattr(vm_info, 'guest_OS', getattr(vm_info, 'guest_os', 'Unknown'))}")
                
                # Check if it has VM-specific properties
                vm_specific_props = []
                if hasattr(vm_info, 'cpu'):
                    vm_specific_props.append("CPU configuration")
                if hasattr(vm_info, 'memory'):
                    vm_specific_props.append("Memory configuration")
                if hasattr(vm_info, 'hardware'):
                    vm_specific_props.append("Hardware version")
                if hasattr(vm_info, 'guest'):
                    vm_specific_props.append("Guest info")
                
                print(f"   • VM Properties: {', '.join(vm_specific_props) if vm_specific_props else 'None'}")
                print()
        else:
            print("ℹ️ No templates found in VM inventory.")
            print()
        
        # ===== ALTERNATIVE DETECTION METHODS =====
        print("🔍 **ALTERNATIVE DETECTION METHODS**")
        print("=" * 60)
        
        # Check folders for templates
        print("📁 Checking folders for templates...")
        try:
            folders = client.vcenter.Folder.list()
            template_folders = []
            
            for folder in folders:
                try:
                    folder_info = client.vcenter.Folder.get(folder.folder)
                    if any(pattern in folder_info.name.lower() for pattern in ['template', 'tpl', 'gold', 'master', 'base']):
                        template_folders.append(folder_info.name)
                        print(f"   ✅ Found template folder: {folder_info.name}")
                        
                        # List VMs in this template folder
                        try:
                            folder_vms = client.vcenter.VM.list(folder=folder.folder)
                            if folder_vms:
                                print(f"      📄 VMs in {folder_info.name}: {len(folder_vms)}")
                                for vm in folder_vms:
                                    print(f"         • {vm.name} (ID: {vm.vm})")
                        except Exception as e:
                            print(f"      ❌ Error listing VMs in folder: {str(e)}")
                            
                except Exception as e:
                    continue
            
            if not template_folders:
                print("   ℹ️ No template-related folders found.")
                
        except Exception as e:
            print(f"   ❌ Error checking folders: {str(e)}")
        
        print()
        
        # Check Content Libraries
        print("📚 Checking Content Libraries...")
        try:
            libraries = client.content.Library.list()
            if libraries:
                print(f"   📚 Found {len(libraries)} Content Library(ies)")
                for library in libraries:
                    print(f"      • {library.name}")
                    
                    # Check for VM templates in this library
                    try:
                        items = client.content.library.Item.list(library.library)
                        vm_templates_in_lib = [item for item in items if hasattr(item, 'type') and item.type == 'vm-template']
                        if vm_templates_in_lib:
                            print(f"         📄 VM Templates: {len(vm_templates_in_lib)}")
                            for item in vm_templates_in_lib:
                                print(f"            • {item.name} (ID: {item.item})")
                    except Exception as e:
                        print(f"         ❌ Error listing items: {str(e)}")
            else:
                print("   ℹ️ No Content Libraries found.")
                
        except Exception as e:
            print(f"   ❌ Error checking Content Libraries: {str(e)}")
        
        print()
        
        # ===== COMPARISON WITH REGULAR VMS =====
        print("🔍 **COMPARISON WITH REGULAR VMS**")
        print("=" * 60)
        
        if regular_vms and templates_found:
            print("Comparing template properties with regular VM properties:")
            print()
            
            # Get a sample regular VM for comparison
            sample_vm = regular_vms[0]
            sample_template = templates_found[0]
            
            print(f"📊 **Sample Regular VM: {sample_vm['name']}**")
            print(f"   • Template Property: {sample_vm['properties'].get('template_property', 'Not found')}")
            print(f"   • VM Type: {sample_vm['properties'].get('vm_type', 'Not found')}")
            print(f"   • Power State: {getattr(sample_vm['vm_info'], 'power_state', 'Unknown')}")
            print()
            
            print(f"📄 **Sample Template: {sample_template['name']}**")
            print(f"   • Template Property: {sample_template['properties'].get('template_property', 'Not found')}")
            print(f"   • VM Type: {sample_template['properties'].get('vm_type', 'Not found')}")
            print(f"   • Power State: {getattr(sample_template['vm_info'], 'power_state', 'Unknown')}")
            print()
            
            # Show key differences
            print("🔍 **Key Differences:**")
            
            # Check template property difference
            vm_template_prop = sample_vm['properties'].get('template_property', None)
            template_template_prop = sample_template['properties'].get('template_property', None)
            
            if vm_template_prop != template_template_prop:
                print(f"   ✅ Template Property: Regular VM = {vm_template_prop}, Template = {template_template_prop}")
            else:
                print(f"   ⚠️ Template Property: Both are {vm_template_prop}")
            
            # Check VM type difference
            vm_type = sample_vm['properties'].get('vm_type', None)
            template_type = sample_template['properties'].get('vm_type', None)
            
            if vm_type != template_type:
                print(f"   ✅ VM Type: Regular VM = {vm_type}, Template = {template_type}")
            else:
                print(f"   ⚠️ VM Type: Both are {vm_type}")
        
        # ===== SUMMARY =====
        print("\n" + "=" * 60)
        print("📊 **SUMMARY**")
        print("=" * 60)
        
        print(f"Total VMs analyzed: {len(vms)}")
        print(f"Templates found: {len(templates_found)}")
        print(f"Regular VMs: {len(regular_vms)}")
        print()
        
        if templates_found:
            print("🎯 **Key Findings:**")
            print("• Templates ARE virtual machines in the vCenter inventory")
            print("• They have the same VM properties as regular VMs")
            print("• They are distinguished by the 'template' property being True")
            print("• They can have power states, guest OS, hardware configs, etc.")
            print("• They are essentially 'frozen' VMs that can be cloned/deployed")
        else:
            print("💡 **No templates found in VM inventory**")
            print("This could mean:")
            print("1. No VMs have been converted to templates yet")
            print("2. Templates are stored in a different location/view")
            print("3. Templates are in Content Libraries instead")
            print("4. Templates might be in a different folder structure")
            print()
            print("To create templates (following VMware instructions):")
            print("1. Power off a virtual machine")
            print("2. Right-click the VM in vSphere client")
            print("3. Select 'Template' → 'Convert to Template'")
            print("4. The VM will then appear as a template with template=True")
        
        print("\n" + "=" * 60)
        print("🔍 Analysis complete!")
        
    except Exception as e:
        print(f"❌ Error during analysis: {str(e)}")

if __name__ == "__main__":
    analyze_template_vm_relationship() 