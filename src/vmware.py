"""
VMware management module using official VMware vSphere Automation SDK.
Based on: https://vmware.github.io/vsphere-automation-sdk-python/vsphere/8.0.3.0/com.vmware.vcenter.vm.html
"""
import logging
import requests
import urllib3
from typing import Optional, List, Dict, Any

from vmware.vapi.vsphere.client import create_vsphere_client
from com.vmware.vcenter.vm_client import Power
from com.vmware.vcenter.vm.hardware_client import Cpu, Memory

from .config import VMwareConfig


class VMwareConnectionError(Exception):
    """Exception raised when VMware connection fails."""
    pass


class VMwareManager:
    """VMware vSphere/ESXi manager using official VMware SDK."""
    
    def __init__(self, config: VMwareConfig, connect: bool = True):
        self.config = config
        self.client = None
        if connect:
            self._connect()
    
    def _connect(self) -> None:
        """Connect to vCenter/ESXi using the official VMware SDK."""
        try:
            # Validate connection parameters
            if not self.config.host:
                raise VMwareConnectionError("VCENTER_HOST is required")
            if not self.config.user:
                raise VMwareConnectionError("VCENTER_USER is required")
            if not self.config.password:
                raise VMwareConnectionError("VCENTER_PASSWORD is required")
            
            # Create session with SSL verification settings
            session = requests.session()
            if self.config.insecure:
                session.verify = False
                urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            
            # Create vSphere client
            self.client = create_vsphere_client(
                server=self.config.host,
                username=self.config.user,
                password=self.config.password,
                session=session
            )
            
            logging.info(f"Successfully connected to VMware vCenter/ESXi API at {self.config.host}")
            
        except Exception as e:
            logging.error(f"Failed to connect to vCenter/ESXi: {e}")
            raise VMwareConnectionError(f"Connection failed: {e}")
    
    def list_vms(self) -> List[Dict[str, Any]]:
        """List all virtual machines using official SDK patterns."""
        try:
            if not self.client:
                raise VMwareConnectionError("Not connected to VMware")
            
            # Get list of VMs - following SDK documentation
            vms = self.client.vcenter.VM.list()
            
            vm_list = []
            for vm in vms:
                vm_info = {
                    'name': vm.name,
                    'vm_id': vm.vm,
                    'power_state': 'UNKNOWN',
                    'cpu_count': 0,
                    'memory_mb': 0,
                    'guest_id': 'UNKNOWN'
                }
                
                # Get power state using official SDK
                try:
                    power_info = self.client.vcenter.vm.Power.get(vm.vm)
                    vm_info['power_state'] = power_info.state.value
                except Exception as e:
                    logging.debug(f"Could not get power info for VM {vm.name}: {e}")
                
                # Get hardware info using official SDK
                try:
                    hardware_info = self.client.vcenter.vm.Hardware.get(vm.vm)
                    vm_info['cpu_count'] = hardware_info.cpu.count
                    vm_info['memory_mb'] = hardware_info.memory.size_MiB
                    vm_info['guest_id'] = hardware_info.guest_ID
                except Exception as e:
                    logging.debug(f"Could not get hardware info for VM {vm.name}: {e}")
                
                vm_list.append(vm_info)
            
            return vm_list
            
        except Exception as e:
            logging.error(f"Failed to list VMs: {e}")
            raise
    
    def get_vm_power_state(self, vm_id: str) -> str:
        """Get power state of a specific VM using official SDK."""
        try:
            power_info = self.client.vcenter.vm.Power.get(vm_id)
            return power_info.state.value
        except Exception as e:
            logging.error(f"Failed to get power state for VM {vm_id}: {e}")
            raise
    
    def power_on_vm(self, vm_id: str) -> None:
        """Power on a VM using official SDK."""
        try:
            self.client.vcenter.vm.Power.start(vm_id)
            logging.info(f"Successfully powered on VM {vm_id}")
        except Exception as e:
            logging.error(f"Failed to power on VM {vm_id}: {e}")
            raise
    
    def power_off_vm(self, vm_id: str) -> None:
        """Power off a VM using official SDK."""
        try:
            self.client.vcenter.vm.Power.stop(vm_id)
            logging.info(f"Successfully powered off VM {vm_id}")
        except Exception as e:
            logging.error(f"Failed to power off VM {vm_id}: {e}")
            raise
    
    def get_info(self) -> Dict[str, Any]:
        """Get basic VMware environment information."""
        try:
            if not self.client:
                return {
                    'status': 'disconnected',
                    'message': 'Not connected to VMware environment'
                }
            
            # Try to get basic info
            try:
                vms = self.client.vcenter.VM.list()
                return {
                    'status': 'connected',
                    'host': self.config.host,
                    'total_vms': len(vms),
                    'message': f'Connected to VMware environment at {self.config.host}'
                }
            except Exception as e:
                return {
                    'status': 'error',
                    'host': self.config.host,
                    'message': f'Connected but error getting VM list: {str(e)}'
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Error getting info: {str(e)}'
            }
    
    def disconnect(self) -> None:
        """Disconnect from VMware."""
        self.client = None
        logging.info("Disconnected from VMware") 