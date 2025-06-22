#!/usr/bin/env python3
"""
STANDALONE vCenter Environment Analysis Script
==============================================

This script can be run on any machine with access to your vCenter environment.
It will provide comprehensive analysis of your vCenter to help debug template detection issues.

SETUP INSTRUCTIONS:
1. Install Python 3.8+ on the target machine
2. Install required packages: pip install vmware-vcenter requests urllib3
3. Update the credentials below with your actual vCenter details
4. Run: python debug_vcenter_standalone.py

CREDENTIALS - UPDATE THESE WITH YOUR ACTUAL VALUES:
"""

import os
import sys
import requests
import urllib3

# ===== UPDATE THESE CREDENTIALS WITH YOUR ACTUAL VALUES =====
VCENTER_HOST = "your_vcenter_hostname_or_ip"  # e.g., "192.168.1.100" or "vcenter.company.com"
VCENTER_USER = "your_username"                 # e.g., "administrator@vsphere.local"
VCENTER_PASSWORD = "your_password"             # Your actual password
VCENTER_INSECURE = True                        # Set to True if using self-signed certificates
# =============================================================

def check_dependencies():
    """Check if required packages are installed."""
    try:
        from vmware.vapi.vsphere.client import create_vsphere_client
        print("✅ vmware-vcenter package is available")
    except ImportError:
        print("❌ vmware-vcenter package not found!")
        print("   Install it with: pip install vmware-vcenter")
        sys.exit(1)
    
    try:
        import requests
        print("✅ requests package is available")
    except ImportError:
        print("❌ requests package not found!")
        print("   Install it with: pip install requests")
        sys.exit(1)

def get_vsphere_client():
    """Get vSphere client with proper authentication."""
    from vmware.vapi.vsphere.client import create_vsphere_client
    
    if VCENTER_HOST == "your_vcenter_hostname_or_ip":
        print("❌ Error: Please update the credentials in this script!")
        print("   Edit the VCENTER_HOST, VCENTER_USER, and VCENTER_PASSWORD variables")
        print("   at the top of this script with your actual vCenter details.")
        sys.exit(1)
    
    print(f"🔍 Connecting to vCenter: {VCENTER_HOST}")
    print(f"🔍 Username: {VCENTER_USER}")
    print(f"🔍 Insecure SSL: {VCENTER_INSECURE}")
    
    # Create session with SSL handling
    session = requests.Session()
    session.verify = not VCENTER_INSECURE
    
    # Disable SSL warnings for demo (not recommended in production)
    if VCENTER_INSECURE:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    # Create vSphere client
    return create_vsphere_client(
        server=VCENTER_HOST, 
        username=VCENTER_USER, 
        password=VCENTER_PASSWORD, 
        session=session
    )

def main():
    print("🔍 **COMPREHENSIVE VCENTER ENVIRONMENT ANALYSIS**")
    print("=" * 60)
    print("This script will analyze your vCenter environment to help debug")
    print("template detection issues with the VMware MCP server.")
    print()
    
    # Check dependencies
    print("## 📦 CHECKING DEPENDENCIES")
    check_dependencies()
    print()
    
    try:
        client = get_vsphere_client()
        print("✅ Connected to vCenter successfully\n")
        
        # ===== BASIC ENVIRONMENT INFO =====
        print("## 📊 BASIC ENVIRONMENT INFO")
        print("Getting basic vCenter information...\n")
        
        try:
            # Get vCenter version
            print(f"🔧 vCenter Version: {client.content.about.version}")
            print(f"🔧 vCenter Build: {client.content.about.build}")
            print(f"🔧 vCenter Name: {client.content.about.name}")
            print(f"🔧 vCenter Full Name: {client.content.about.fullName}")
            print()
        except Exception as e:
            print(f"⚠️ Could not get vCenter info: {str(e)}\n")
        
        # ===== DATACENTER ANALYSIS =====
        print("## 🏢 DATACENTER ANALYSIS")
        print("Analyzing datacenters and their structure...\n")
        
        try:
            datacenters = client.vcenter.Datacenter.list()
            print(f"📊 Found {len(datacenters)} datacenter(s)")
            
            for dc in datacenters:
                try:
                    dc_info = client.vcenter.Datacenter.get(dc.datacenter)
                    print(f"\n🏢 **Datacenter: {dc_info.name}** (ID: {dc.datacenter})")
                    
                    # Get VMs in this datacenter
                    try:
                        dc_vms = client.vcenter.VM.list()
                        print(f"   • Total VMs in vCenter: {len(dc_vms)}")
                        
                        # Count VMs in this datacenter (if we can determine)
                        dc_vm_count = 0
                        for vm in dc_vms:
                            try:
                                vm_info = client.vcenter.VM.get(vm.vm)
                                # Check if VM is in this datacenter
                                if hasattr(vm_info, 'datacenter') and vm_info.datacenter == dc.datacenter:
                                    dc_vm_count += 1
                            except:
                                pass
                        
                        if dc_vm_count > 0:
                            print(f"   • VMs in this datacenter: {dc_vm_count}")
                        
                    except Exception as e:
                        print(f"   • Error getting VMs: {str(e)}")
                    
                except Exception as e:
                    print(f"   • Error getting datacenter info: {str(e)}")
                    
        except Exception as e:
            print(f"❌ Error analyzing datacenters: {str(e)}\n")
        
        # ===== COMPREHENSIVE VM ANALYSIS =====
        print("\n## 📋 COMPREHENSIVE VM ANALYSIS")
        print("Analyzing ALL VMs in vCenter...\n")
        
        try:
            all_vms = client.vcenter.VM.list()
            print(f"📊 Found {len(all_vms)} VM(s) total in vCenter")
            
            if len(all_vms) == 0:
                print("❌ **CRITICAL ISSUE**: No VMs found in vCenter!")
                print("   This suggests:")
                print("   • Your user doesn't have permissions to view VMs")
                print("   • You're connected to the wrong vCenter")
                print("   • The vCenter is empty")
                print("   • There's a network/permission issue")
                return
            
            # Analyze first 10 VMs in detail
            print(f"\n📄 **Detailed Analysis of First 10 VMs:**\n")
            
            for i, vm in enumerate(all_vms[:10]):
                try:
                    vm_info = client.vcenter.VM.get(vm.vm)
                    print(f"{i+1}. **{vm_info.name}** (ID: {vm.vm})")
                    
                    # Check all possible properties
                    print(f"   • Template Property: {getattr(vm_info, 'template', 'Not found')}")
                    print(f"   • Power State: {getattr(vm_info, 'power_state', 'Unknown')}")
                    
                    # Guest OS
                    guest_os = getattr(vm_info, 'guest_OS', None) or getattr(vm_info, 'guest_os', None) or 'Unknown'
                    print(f"   • Guest OS: {guest_os}")
                    
                    # CPU and Memory
                    cpu_count = 'Unknown'
                    if hasattr(vm_info, 'cpu') and vm_info.cpu:
                        cpu_count = getattr(vm_info.cpu, 'count', 'Unknown')
                    print(f"   • CPU Count: {cpu_count}")
                    
                    memory_mb = 'Unknown'
                    if hasattr(vm_info, 'memory') and vm_info.memory:
                        memory_mb = getattr(vm_info.memory, 'size_MiB', 'Unknown')
                    print(f"   • Memory: {memory_mb} MB")
                    
                    # Datastore
                    vm_datastore = getattr(vm_info, 'datastore', None)
                    if vm_datastore:
                        try:
                            datastore_info = client.vcenter.Datastore.get(vm_datastore)
                            print(f"   • Datastore: {datastore_info.name}")
                        except:
                            print(f"   • Datastore ID: {vm_datastore}")
                    else:
                        print(f"   • Datastore: Unknown")
                    
                    # Check if this VM name contains "ubuntu" or "template"
                    vm_name_lower = vm_info.name.lower()
                    if 'ubuntu' in vm_name_lower:
                        print(f"   • 🎯 **CONTAINS 'UBUNTU'**")
                    if 'template' in vm_name_lower:
                        print(f"   • 🎯 **CONTAINS 'TEMPLATE'**")
                    
                    print()
                    
                except Exception as e:
                    print(f"{i+1}. Error analyzing VM {vm.vm}: {str(e)}\n")
            
            if len(all_vms) > 10:
                print(f"... and {len(all_vms) - 10} more VMs (showing first 10 only)\n")
            
            # ===== TEMPLATE DETECTION =====
            print("## 🔍 TEMPLATE DETECTION ANALYSIS")
            print("Checking for templates among all VMs...\n")
            
            templates_found = []
            ubuntu_vms = []
            template_vms = []
            
            for vm in all_vms:
                try:
                    vm_info = client.vcenter.VM.get(vm.vm)
                    
                    # Check if it's a template
                    is_template = getattr(vm_info, 'template', False)
                    if is_template:
                        templates_found.append(vm_info)
                    
                    # Check for Ubuntu VMs
                    vm_name_lower = vm_info.name.lower()
                    if 'ubuntu' in vm_name_lower:
                        ubuntu_vms.append(vm_info)
                    
                    # Check for template in name
                    if 'template' in vm_name_lower:
                        template_vms.append(vm_info)
                        
                except Exception as e:
                    continue
            
            print(f"📊 Template Analysis Results:")
            print(f"   • VMs with template=True: {len(templates_found)}")
            print(f"   • VMs with 'ubuntu' in name: {len(ubuntu_vms)}")
            print(f"   • VMs with 'template' in name: {len(template_vms)}")
            print()
            
            if templates_found:
                print("✅ **TEMPLATES FOUND:**")
                for template in templates_found:
                    print(f"   • {template.name} (ID: {template.vm if hasattr(template, 'vm') else 'Unknown'})")
                print()
            
            if ubuntu_vms:
                print("🎯 **UBUNTU VMs FOUND:**")
                for vm in ubuntu_vms:
                    print(f"   • {vm.name} (ID: {vm.vm if hasattr(vm, 'vm') else 'Unknown'})")
                print()
            
            if template_vms:
                print("📄 **VMs WITH 'TEMPLATE' IN NAME:**")
                for vm in template_vms:
                    print(f"   • {vm.name} (ID: {vm.vm if hasattr(vm, 'vm') else 'Unknown'})")
                print()
            
        except Exception as e:
            print(f"❌ Error in comprehensive VM analysis: {str(e)}\n")
        
        # ===== FOLDER ANALYSIS =====
        print("## 📁 FOLDER ANALYSIS")
        print("Analyzing folder structure...\n")
        
        try:
            folders = client.vcenter.Folder.list()
            print(f"📊 Found {len(folders)} folders")
            
            for folder in folders:
                try:
                    folder_info = client.vcenter.Folder.get(folder.folder)
                    print(f"📁 **{folder_info.name}** (ID: {folder.folder})")
                    
                    # Check if this folder contains VMs
                    try:
                        folder_vms = client.vcenter.VM.list(folder=folder.folder)
                        if folder_vms:
                            print(f"   • VMs in folder: {len(folder_vms)}")
                            for vm in folder_vms[:3]:  # Show first 3
                                try:
                                    vm_info = client.vcenter.VM.get(vm.vm)
                                    print(f"     - {vm_info.name}")
                                except:
                                    print(f"     - {vm.vm} (error getting name)")
                            if len(folder_vms) > 3:
                                print(f"     ... and {len(folder_vms) - 3} more")
                        else:
                            print(f"   • No VMs in folder")
                    except Exception as e:
                        print(f"   • Error listing VMs: {str(e)}")
                    
                except Exception as e:
                    print(f"   • Error getting folder info: {str(e)}")
                    
        except Exception as e:
            print(f"❌ Error analyzing folders: {str(e)}\n")
        
        # ===== PERMISSION ANALYSIS =====
        print("## 🔐 PERMISSION ANALYSIS")
        print("Checking what your user can access...\n")
        
        try:
            # Try to access different APIs to see what's available
            print("Testing API access:")
            
            # Test VM API
            try:
                vms = client.vcenter.VM.list()
                print(f"   ✅ VM API: Can list {len(vms)} VMs")
            except Exception as e:
                print(f"   ❌ VM API: {str(e)}")
            
            # Test Datastore API
            try:
                datastores = client.vcenter.Datastore.list()
                print(f"   ✅ Datastore API: Can list {len(datastores)} datastores")
            except Exception as e:
                print(f"   ❌ Datastore API: {str(e)}")
            
            # Test Folder API
            try:
                folders = client.vcenter.Folder.list()
                print(f"   ✅ Folder API: Can list {len(folders)} folders")
            except Exception as e:
                print(f"   ❌ Folder API: {str(e)}")
            
            # Test Content Library API
            try:
                libraries = client.content.Library.list()
                print(f"   ✅ Content Library API: Can list {len(libraries)} libraries")
            except Exception as e:
                print(f"   ❌ Content Library API: {str(e)}")
            
        except Exception as e:
            print(f"❌ Error in permission analysis: {str(e)}\n")
        
        # ===== SUMMARY AND RECOMMENDATIONS =====
        print("## 📊 SUMMARY AND RECOMMENDATIONS")
        print("=" * 60)
        
        if len(all_vms) == 0:
            print("❌ **CRITICAL ISSUE**: No VMs found in vCenter!")
            print("\n💡 **Immediate Actions:**")
            print("   1. Check your vCenter credentials")
            print("   2. Verify you're connecting to the correct vCenter")
            print("   3. Check your user permissions in vCenter")
            print("   4. Try logging into vCenter UI with the same credentials")
            print("   5. Check if there are any VMs visible in the vCenter UI")
        else:
            print(f"✅ Found {len(all_vms)} VMs in vCenter")
            
            if len(templates_found) == 0:
                print("❌ No templates found with template=True")
                print("\n💡 **Possible Reasons:**")
                print("   1. No VMs have been converted to templates yet")
                print("   2. Templates are in a different datacenter")
                print("   3. Templates are in Content Libraries")
                print("   4. Your user doesn't have permission to see templates")
                print("   5. Templates are in a different inventory view")
            else:
                print(f"✅ Found {len(templates_found)} templates")
            
            if len(ubuntu_vms) == 0:
                print("❌ No VMs with 'ubuntu' in the name found")
            else:
                print(f"✅ Found {len(ubuntu_vms)} VMs with 'ubuntu' in name")
        
        print("\n💡 **Next Steps:**")
        print("   1. Check vCenter UI to see what's actually there")
        print("   2. Verify the template name exactly as it appears in vCenter")
        print("   3. Check if templates are in Content Libraries")
        print("   4. Try creating a new template from a VM")
        print("   5. Check user permissions in vCenter")
        
        # ===== COPY-PASTE READY COMMANDS =====
        print("\n## 📋 COPY-PASTE READY COMMANDS")
        print("=" * 60)
        print("Use these commands to install dependencies on the target machine:")
        print()
        print("pip install vmware-vcenter requests urllib3")
        print()
        print("Or if you prefer pip3:")
        print("pip3 install vmware-vcenter requests urllib3")
        print()
        print("Then run this script with:")
        print("python debug_vcenter_standalone.py")
        print()
        print("Or:")
        print("python3 debug_vcenter_standalone.py")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print("\n💡 **Troubleshooting:**")
        print("   1. Check your vCenter credentials are correct")
        print("   2. Verify the vCenter hostname/IP is reachable")
        print("   3. Check if you need to set VCENTER_INSECURE=True for self-signed certs")
        print("   4. Try pinging the vCenter hostname/IP")
        print("   5. Check your network connectivity to the vCenter")
        sys.exit(1)

if __name__ == "__main__":
    main() 