#!/usr/bin/env python3
"""
VM Info Management Module using vmware-vcenter REST API
Fast operations for listing VMs and basic management.
"""

from typing import Dict, Any, List, Optional
import os
from vmware.vcenter.vm import VM
from vmware.vcenter.vm_client import VMClient
from vmware.vcenter.vcenter_client import VcenterClient
from vmware.vcenter.vm.power_client import PowerClient
from vmware.vcenter.vm_client import VMClient

class VMInfoManagerREST:
    def __init__(self):
        self.client = None
        self.vm_client = None
        self.power_client = None
    
    def connect_to_vcenter(self) -> bool:
        """Connect to vCenter using REST API."""
        try:
            host = os.getenv('VCENTER_HOST')
            user = os.getenv('VCENTER_USER')
            password = os.getenv('VCENTER_PASSWORD')
            insecure = os.getenv('VCENTER_INSECURE', 'false').lower() == 'true'
            
            if not all([host, user, password]):
                return False
            
            # Create REST client
            self.client = VcenterClient(host, user, password, verify_ssl=not insecure)
            self.vm_client = VMClient(self.client)
            self.power_client = PowerClient(self.client)
            return True
            
        except Exception as e:
            print(f"[ERROR] REST API connection failed: {e}", file=sys.stderr)
            return False
    
    def list_all_vms(self) -> List[Dict[str, Any]]:
        """List all VMs using REST API (fast)."""
        try:
            if not self.vm_client:
                if not self.connect_to_vcenter():
                    return [{"error": "Failed to connect to vCenter"}]
            
            # Get all VMs
            vms = self.vm_client.list()
            
            vm_list = []
            for vm in vms:
                vm_info = {
                    "name": vm.name,
                    "vm_id": vm.vm,
                    "power_state": vm.power_state,
                    "cpu_count": vm.cpu_count if hasattr(vm, 'cpu_count') else 0,
                    "memory_mb": vm.memory_size_mib if hasattr(vm, 'memory_size_mib') else 0,
                    "guest_id": vm.guest_OS if hasattr(vm, 'guest_OS') else 'Unknown',
                }
                
                # Get power state
                try:
                    power_info = self.power_client.get(vm.vm)
                    vm_info["power_state"] = power_info.state
                except:
                    pass
                
                vm_list.append(vm_info)
            
            return vm_list
            
        except Exception as e:
            return [{"error": f"Failed to list VMs: {str(e)}"}]
    
    def power_on_vm(self, vm_name: str) -> Dict[str, Any]:
        """Power on a VM using REST API."""
        try:
            if not self.vm_client:
                if not self.connect_to_vcenter():
                    return {"error": "Failed to connect to vCenter"}
            
            # Find VM by name
            vms = self.vm_client.list()
            target_vm = None
            for vm in vms:
                if vm.name == vm_name:
                    target_vm = vm
                    break
            
            if not target_vm:
                return {"error": f"VM '{vm_name}' not found"}
            
            # Power on
            self.power_client.start(target_vm.vm)
            return {"success": True, "message": f"VM '{vm_name}' powered on"}
            
        except Exception as e:
            return {"error": f"Failed to power on VM: {str(e)}"}
    
    def power_off_vm(self, vm_name: str) -> Dict[str, Any]:
        """Power off a VM using REST API."""
        try:
            if not self.vm_client:
                if not self.connect_to_vcenter():
                    return {"error": "Failed to connect to vCenter"}
            
            # Find VM by name
            vms = self.vm_client.list()
            target_vm = None
            for vm in vms:
                if vm.name == vm_name:
                    target_vm = vm
                    break
            
            if not target_vm:
                return {"error": f"VM '{vm_name}' not found"}
            
            # Power off
            self.power_client.stop(target_vm.vm)
            return {"success": True, "message": f"VM '{vm_name}' powered off"}
            
        except Exception as e:
            return {"error": f"Failed to power off VM: {str(e)}"} 