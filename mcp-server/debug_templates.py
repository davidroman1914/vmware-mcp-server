#!/usr/bin/env python3
"""
Debug script to find VMware templates using datastore-based detection.
This script focuses on finding templates that are stored in specific datastores.
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
        print("❌ Error: Missing vCenter credentials in environment variables")
        print("   Please set: VCENTER_HOST, VCENTER_USER, VCENTER_PASSWORD")
        print("   You can copy env.example to .env and update it with your credentials")
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

def main():
    # Get credentials from environment
    server = os.getenv('VCENTER_HOST')
    username = os.getenv('VCENTER_USER')
    password = os.getenv('VCENTER_PASSWORD')
    
    if not all([server, username, password]):
        print("❌ Missing environment variables: VCENTER_HOST, VCENTER_USER, VCENTER_PASSWORD")
        sys.exit(1)
    
    print(f"🔍 Connecting to vCenter: {server}")
    
    try:
        # Create API client
        client = get_vsphere_client()
        print("✅ Connected to vCenter successfully\n")
        
        # ===== DATABASE-BASED TEMPLATE DETECTION =====
        print("## 💾 DATABASE-BASED TEMPLATE DETECTION")
        print("Looking for templates stored in specific datastores...\n")
        
        # Get all datastores
        datastores = client.vcenter.Datastore.list()
        print(f"📊 Found {len(datastores)} datastores")
        
        datastore_templates = []
        target_datastore_found = False
        
        for datastore in datastores:
            try:
                datastore_info = client.vcenter.Datastore.get(datastore.datastore)
                print(f"\n💾 **Checking Datastore: {datastore_info.name}**")
                
                # Check if this is the target datastore you mentioned
                if 'ova-inf-vh03-ds-1' in datastore_info.name.lower():
                    target_datastore_found = True
                    print(f"   🎯 **TARGET DATASTORE DETECTED**: {datastore_info.name}")
                    print(f"      • This matches the datastore where you found your template!")
                
                # Get all VMs to check which ones are on this datastore
                vms = client.vcenter.VM.list()
                datastore_vms = []
                
                for vm in vms:
                    try:
                        vm_info = client.vcenter.VM.get(vm.vm)
                        
                        # Check if this VM is stored on this datastore
                        # We need to check the VM's storage configuration
                        vm_datastore = None
                        
                        # Try different ways to get the datastore
                        if hasattr(vm_info, 'datastore'):
                            vm_datastore = vm_info.datastore
                        elif hasattr(vm_info, 'storage'):
                            # Check storage configuration
                            pass
                        
                        if vm_datastore == datastore.datastore:
                            datastore_vms.append(vm_info)
                            
                            # Check if this VM is a template
                            is_template = getattr(vm_info, 'template', False)
                            
                            if is_template:
                                print(f"   ✅ **TEMPLATE FOUND**: {vm_info.name}")
                                print(f"      • VM ID: {vm.vm}")
                                print(f"      • Template Property: {is_template}")
                                print(f"      • Power State: {getattr(vm_info, 'power_state', 'Unknown')}")
                                
                                # Get additional details
                                guest_os = getattr(vm_info, 'guest_OS', None) or getattr(vm_info, 'guest_os', None) or 'Unknown'
                                print(f"      • Guest OS: {guest_os}")
                                
                                cpu_count = 'Unknown'
                                if hasattr(vm_info, 'cpu') and vm_info.cpu:
                                    cpu_count = getattr(vm_info.cpu, 'count', 'Unknown')
                                print(f"      • CPU Count: {cpu_count}")
                                
                                memory_mb = 'Unknown'
                                if hasattr(vm_info, 'memory') and vm_info.memory:
                                    memory_mb = getattr(vm_info.memory, 'size_MiB', 'Unknown')
                                print(f"      • Memory: {memory_mb} MB")
                                
                                datastore_templates.append({
                                    'name': vm_info.name,
                                    'id': vm.vm,
                                    'datastore': datastore_info.name,
                                    'vm_info': vm_info
                                })
                            else:
                                print(f"   📄 VM on datastore: {vm_info.name} (not a template)")
                                
                    except Exception as e:
                        print(f"   ❌ Error checking VM {vm.vm}: {str(e)}")
                        continue
                
                if not datastore_vms:
                    print(f"   ℹ️ No VMs found on this datastore")
                    
            except Exception as e:
                print(f"   ❌ Error analyzing datastore: {str(e)}")
        
        print(f"\n## 📊 SUMMARY")
        if datastore_templates:
            print(f"✅ Found {len(datastore_templates)} template(s) in datastores:")
            for template in datastore_templates:
                print(f"   💾 {template['name']} (Datastore: {template['datastore']})")
        else:
            print("❌ No templates found in datastores")
            
        if target_datastore_found:
            print(f"\n🎯 Target datastore 'ova-inf-vh03-ds-1' was found and analyzed")
        else:
            print(f"\n⚠️ Target datastore 'ova-inf-vh03-ds-1' was NOT found")
            print(f"   Available datastores:")
            for datastore in datastores:
                try:
                    datastore_info = client.vcenter.Datastore.get(datastore.datastore)
                    print(f"   • {datastore_info.name}")
                except:
                    print(f"   • {datastore.datastore} (could not get details)")
        
        # ===== ALTERNATIVE: CHECK ALL VMs FOR TEMPLATE PROPERTY =====
        print(f"\n## 🔍 ALTERNATIVE: CHECK ALL VMs FOR TEMPLATE PROPERTY")
        print("Checking all VMs to see which ones have the template property set...\n")
        
        all_vms = client.vcenter.VM.list()
        all_templates = []
        
        for vm in all_vms:
            try:
                vm_info = client.vcenter.VM.get(vm.vm)
                is_template = getattr(vm_info, 'template', False)
                
                if is_template:
                    print(f"✅ **TEMPLATE FOUND**: {vm_info.name}")
                    print(f"   • VM ID: {vm.vm}")
                    print(f"   • Template Property: {is_template}")
                    print(f"   • Power State: {getattr(vm_info, 'power_state', 'Unknown')}")
                    
                    # Try to get datastore info
                    vm_datastore = getattr(vm_info, 'datastore', None)
                    if vm_datastore:
                        try:
                            datastore_info = client.vcenter.Datastore.get(vm_datastore)
                            print(f"   • Datastore: {datastore_info.name}")
                        except:
                            print(f"   • Datastore ID: {vm_datastore}")
                    else:
                        print(f"   • Datastore: Unknown")
                    
                    all_templates.append(vm_info)
                    print()
                    
            except Exception as e:
                print(f"❌ Error checking VM {vm.vm}: {str(e)}")
                continue
        
        print(f"📊 Found {len(all_templates)} template(s) total across all VMs")
        
        # ===== CHECK FOLDERS FOR TEMPLATES =====
        print(f"\n## 📁 CHECKING FOLDERS FOR TEMPLATES")
        print("Looking for template-related folders...\n")
        
        try:
            folders = client.vcenter.Folder.list()
            template_folders = []
            
            for folder in folders:
                try:
                    folder_info = client.vcenter.Folder.get(folder.folder)
                    folder_name = folder_info.name.lower()
                    
                    # Check if folder name suggests it contains templates
                    if any(pattern in folder_name for pattern in ['template', 'tpl', 'gold', 'master', 'base']):
                        template_folders.append(folder_info)
                        print(f"📁 **Template Folder Found**: {folder_info.name}")
                        
                        # List VMs in this folder
                        try:
                            folder_vms = client.vcenter.VM.list(folder=folder.folder)
                            print(f"   • VMs in folder: {len(folder_vms)}")
                            for vm in folder_vms:
                                try:
                                    vm_info = client.vcenter.VM.get(vm.vm)
                                    is_template = getattr(vm_info, 'template', False)
                                    template_marker = " (TEMPLATE)" if is_template else ""
                                    print(f"   • {vm_info.name}{template_marker}")
                                except:
                                    print(f"   • {vm.vm} (could not get details)")
                            print()
                        except Exception as e:
                            print(f"   • Error listing VMs: {str(e)}\n")
                            
                except Exception as e:
                    continue
            
            if not template_folders:
                print("ℹ️ No template-related folders found")
                
        except Exception as e:
            print(f"❌ Error checking folders: {str(e)}")
        
        print(f"\n## 🎯 RECOMMENDATIONS")
        if datastore_templates or all_templates:
            print("✅ Templates found! You can now use them with the MCP server.")
        else:
            print("❌ No templates found. Possible reasons:")
            print("   1. Templates might be stored in Content Libraries (not regular VMs)")
            print("   2. Templates might require different permissions to access")
            print("   3. Templates might be in a different inventory view")
            print("   4. The template property might not be set correctly")
            print("\n💡 Next steps:")
            print("   • Check Content Libraries in vCenter UI")
            print("   • Verify your user has permissions to view templates")
            print("   • Try creating a new template from a VM")
            print("   • Check if templates are in a different datacenter or folder")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 