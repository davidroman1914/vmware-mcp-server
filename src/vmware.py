"""
VMware management module for ESXi MCP Server using official VMware vSphere Automation SDK.
"""
import logging
import requests
import urllib3
from typing import Optional, List
from dataclasses import dataclass

from vmware.vapi.vsphere.client import create_vsphere_client
from com.vmware.vcenter.vm_client import Power, Tools

from .config import VMwareConfig


@dataclass
class VMInfo:
    """Virtual machine information."""
    name: str
    power_state: str
    cpu_count: int
    memory_mb: int
    guest_id: str
    tools_status: str


@dataclass
class VMPerformance:
    """Virtual machine performance metrics."""
    cpu_usage_mhz: int
    memory_usage_mb: int
    storage_usage_gb: float
    network_transmit_kbps: Optional[float] = None
    network_receive_kbps: Optional[float] = None


class VMwareConnectionError(Exception):
    """Exception raised when VMware connection fails."""
    pass


class VMwareManager:
    """Manages VMware vSphere/ESXi operations using official VMware SDK."""
    
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
    
    def list_vms(self) -> List[VMInfo]:
        """List all virtual machines with their information."""
        try:
            vm_list = []
            vms = self.client.vcenter.VM.list()
            
            for vm in vms:
                # Get detailed VM information
                vm_id = vm.vm
                power_info = self.client.vcenter.vm.Power.get(vm_id)
                hardware_info = self.client.vcenter.vm.Hardware.get(vm_id)
                guest_info = self.client.vcenter.vm.Guest.get(vm_id)
                
                vm_info = VMInfo(
                    name=vm.name,
                    power_state=power_info.state.value,
                    cpu_count=hardware_info.cpu.count,
                    memory_mb=hardware_info.memory.size_MiB,
                    guest_id=hardware_info.guest_ID,
                    tools_status=guest_info.tools_running_status.value if guest_info.tools_running_status else "UNKNOWN"
                )
                vm_list.append(vm_info)
            
            return vm_list
            
        except Exception as e:
            logging.error(f"Failed to list VMs: {e}")
            raise
    
    def find_vm(self, name: str) -> Optional[str]:
        """Find virtual machine ID by name."""
        try:
            vms = self.client.vcenter.VM.list()
            for vm in vms:
                if vm.name == name:
                    return vm.vm
            return None
        except Exception as e:
            logging.error(f"Failed to find VM {name}: {e}")
            raise
    
    def get_vm_performance(self, vm_name: str) -> VMPerformance:
        """Get performance metrics for a virtual machine."""
        vm_id = self.find_vm(vm_name)
        if not vm_id:
            raise ValueError(f"VM {vm_name} not found")
        
        try:
            # Get basic VM information
            hardware_info = self.client.vcenter.vm.Hardware.get(vm_id)
            guest_info = self.client.vcenter.vm.Guest.get(vm_id)
            
            # For performance metrics, we'll use basic info since detailed metrics
            # require additional API calls that may not be available in all environments
            cpu_usage = 0  # Would need additional API calls for real metrics
            memory_usage = guest_info.memory_usage_MiB if guest_info.memory_usage_MiB else 0
            storage_usage = 0  # Would need additional API calls for real metrics
            
            return VMPerformance(
                cpu_usage_mhz=cpu_usage,
                memory_usage_mb=memory_usage,
                storage_usage_gb=storage_usage
            )
            
        except Exception as e:
            logging.error(f"Failed to get VM performance for {vm_name}: {e}")
            raise
    
    def create_vm(self, name: str, cpus: int, memory_mb: int, 
                  datastore: Optional[str] = None, network: Optional[str] = None) -> str:
        """Create a new virtual machine."""
        try:
            # Get datastore ID
            datastore_id = None
            if datastore:
                datastores = self.client.vcenter.Datastore.list()
                datastore_id = next((ds.datastore for ds in datastores if ds.name == datastore), None)
                if not datastore_id:
                    raise ValueError(f"Datastore {datastore} not found")
            else:
                # Use first available datastore
                datastores = self.client.vcenter.Datastore.list()
                if not datastores:
                    raise ValueError("No datastores available")
                datastore_id = datastores[0].datastore
            
            # Get network ID
            network_id = None
            if network:
                networks = self.client.vcenter.Network.list()
                network_id = next((net.network for net in networks if net.name == network), None)
                if not network_id:
                    raise ValueError(f"Network {network} not found")
            else:
                # Use first available network
                networks = self.client.vcenter.Network.list()
                if not networks:
                    raise ValueError("No networks available")
                network_id = networks[0].network
            
            # Get resource pool ID
            resource_pools = self.client.vcenter.ResourcePool.list()
            if not resource_pools:
                raise ValueError("No resource pools available")
            resource_pool_id = resource_pools[0].resource_pool
            
            # Create VM specification
            vm_create_spec = {
                'name': name,
                'guest_ID': 'ubuntu64Guest',
                'cpu': {
                    'count': cpus
                },
                'memory': {
                    'size_MiB': memory_mb
                },
                'disks': [{
                    'type': 'SATA',
                    'new_vmdk': {
                        'name': f"{name}.vmdk",
                        'capacity': 10 * 1024 * 1024 * 1024  # 10GB in bytes
                    }
                }],
                'nics': [{
                    'type': 'VMXNET3',
                    'backing': {
                        'type': 'STANDARD_PORTGROUP',
                        'network': network_id
                    }
                }]
            }
            
            # Create VM
            vm_id = self.client.vcenter.VM.create(vm_create_spec)
            
            logging.info(f"Successfully created VM: {name} (ID: {vm_id})")
            return vm_id
            
        except Exception as e:
            logging.error(f"Failed to create VM {name}: {e}")
            raise
    
    def clone_vm(self, template_name: str, new_name: str) -> str:
        """Clone a virtual machine from template."""
        template_id = self.find_vm(template_name)
        if not template_id:
            raise ValueError(f"Template {template_name} not found")
        
        try:
            # Check if template is powered off
            power_info = self.client.vcenter.vm.Power.get(template_id)
            if power_info.state != Power.State.POWERED_OFF:
                raise ValueError(f"Template {template_name} must be powered off to clone")
            
            # Create clone specification
            clone_spec = {
                'name': new_name,
                'power_on': False
            }
            
            # Clone VM
            vm_id = self.client.vcenter.VM.clone(template_id, clone_spec)
            
            logging.info(f"Successfully cloned VM {template_name} to {new_name}")
            return vm_id
            
        except Exception as e:
            logging.error(f"Failed to clone VM {template_name} to {new_name}: {e}")
            raise
    
    def delete_vm(self, name: str) -> str:
        """Delete a virtual machine."""
        vm_id = self.find_vm(name)
        if not vm_id:
            raise ValueError(f"VM {name} not found")
        
        try:
            # Power off if running
            power_info = self.client.vcenter.vm.Power.get(vm_id)
            if power_info.state == Power.State.POWERED_ON:
                self.client.vcenter.vm.Power.stop(vm_id)
            
            # Delete VM
            self.client.vcenter.VM.delete(vm_id)
            
            logging.info(f"Successfully deleted VM: {name}")
            return f"VM {name} deleted successfully"
            
        except Exception as e:
            logging.error(f"Failed to delete VM {name}: {e}")
            raise
    
    def power_on_vm(self, name: str) -> str:
        """Power on a virtual machine."""
        vm_id = self.find_vm(name)
        if not vm_id:
            raise ValueError(f"VM {name} not found")
        
        try:
            power_info = self.client.vcenter.vm.Power.get(vm_id)
            if power_info.state == Power.State.POWERED_ON:
                return vm_id  # Already powered on, return VM ID
            
            self.client.vcenter.vm.Power.start(vm_id)
            
            logging.info(f"Successfully powered on VM: {name}")
            return vm_id
            
        except Exception as e:
            logging.error(f"Failed to power on VM {name}: {e}")
            raise
    
    def power_off_vm(self, name: str) -> str:
        """Power off a virtual machine."""
        vm_id = self.find_vm(name)
        if not vm_id:
            raise ValueError(f"VM {name} not found")
        
        try:
            power_info = self.client.vcenter.vm.Power.get(vm_id)
            if power_info.state == Power.State.POWERED_OFF:
                return vm_id  # Already powered off, return VM ID
            
            # Try graceful shutdown first
            try:
                guest_info = self.client.vcenter.vm.Guest.get(vm_id)
                if guest_info.tools_running_status == Tools.RunState.RUNNING:
                    self.client.vcenter.vm.Guest.shutdown(vm_id)
                    logging.info(f"Gracefully shut down VM: {name}")
                    return vm_id
            except Exception as e:
                logging.warning(f"Graceful shutdown failed for {name}: {e}")
            
            # Force power off
            self.client.vcenter.vm.Power.stop(vm_id)
            
            logging.info(f"Successfully powered off VM: {name}")
            return vm_id
            
        except Exception as e:
            logging.error(f"Failed to power off VM {name}: {e}")
            raise
    
    def disconnect(self) -> None:
        """Disconnect from VMware."""
        # The official SDK handles connection cleanup automatically
        logging.info("Disconnected from VMware")
    
    def create_vm_from_template(self, name: str, template_name: str, 
                               cluster: Optional[str] = None,
                               folder: Optional[str] = None,
                               disk_spec: Optional[dict] = None,
                               hardware_spec: Optional[dict] = None,
                               network_spec: Optional[dict] = None,
                               customization_spec: Optional[dict] = None,
                               wait_for_ip: bool = False,
                               wait_timeout: int = 300) -> str:
        """
        Create a VM from template with customization (similar to Ansible vmware_guest).
        
        Args:
            name: Name of the new VM
            template_name: Name of the template to clone from
            cluster: Target cluster name
            folder: Target folder path (e.g., "/vm/")
            disk_spec: Disk configuration dict
            hardware_spec: Hardware configuration dict
            network_spec: Network configuration dict with IP settings
            customization_spec: Guest customization settings
            wait_for_ip: Whether to wait for IP address
            wait_timeout: Timeout for IP address wait (seconds)
            
        Returns:
            VM ID of the created VM
        """
        template_id = self.find_vm(template_name)
        if not template_id:
            raise ValueError(f"Template {template_name} not found")
        
        try:
            # Check if template is powered off
            power_info = self.client.vcenter.vm.Power.get(template_id)
            if power_info.state != Power.State.POWERED_OFF:
                raise ValueError(f"Template {template_name} must be powered off to clone")
            
            # Get target folder ID
            folder_id = None
            if folder:
                folders = self.client.vcenter.Folder.list()
                folder_id = next((f.folder for f in folders if f.name == folder.strip('/')), None)
                if not folder_id:
                    raise ValueError(f"Folder {folder} not found")
            
            # Get target cluster ID
            cluster_id = None
            if cluster:
                clusters = self.client.vcenter.Cluster.list()
                cluster_id = next((c.cluster for c in clusters if c.name == cluster), None)
                if not cluster_id:
                    raise ValueError(f"Cluster {cluster} not found")
            
            # Get resource pool from cluster
            resource_pool_id = None
            if cluster_id:
                resource_pools = self.client.vcenter.ResourcePool.list()
                cluster_rps = [rp for rp in resource_pools if rp.cluster == cluster_id]
                if cluster_rps:
                    resource_pool_id = cluster_rps[0].resource_pool
            else:
                # Use first available resource pool
                resource_pools = self.client.vcenter.ResourcePool.list()
                if resource_pools:
                    resource_pool_id = resource_pools[0].resource_pool
            
            if not resource_pool_id:
                raise ValueError("No resource pools available")
            
            # Build clone specification
            clone_spec = {
                'name': name,
                'power_on': False,  # Don't power on initially
                'resource_pool': resource_pool_id
            }
            
            # Add folder placement if specified
            if folder_id:
                clone_spec['folder'] = folder_id
            
            # Add disk specification if provided
            if disk_spec:
                clone_spec['disks'] = self._build_disk_spec(disk_spec)
            
            # Add hardware specification if provided
            if hardware_spec:
                clone_spec['hardware'] = self._build_hardware_spec(hardware_spec)
            
            # Add network specification if provided
            if network_spec:
                clone_spec['nics'] = self._build_network_spec(network_spec)
            
            # Clone VM
            vm_id = self.client.vcenter.VM.clone(template_id, clone_spec)
            
            # Apply customization if specified
            if customization_spec:
                self._apply_guest_customization(vm_id, customization_spec)
            
            # Power on VM
            self.client.vcenter.vm.Power.start(vm_id)
            
            # Wait for IP address if requested
            if wait_for_ip:
                ip_address = self._wait_for_ip_address(vm_id, wait_timeout)
                logging.info(f"VM {name} got IP address: {ip_address}")
            
            logging.info(f"Successfully created VM from template: {name} (ID: {vm_id})")
            return vm_id
            
        except Exception as e:
            logging.error(f"Failed to create VM from template {template_name}: {e}")
            raise
    
    def _build_disk_spec(self, disk_spec: dict) -> list:
        """Build disk specification for VM creation."""
        disks = []
        for disk in disk_spec:
            disk_config = {
                'type': disk.get('type', 'SATA'),
                'new_vmdk': {
                    'name': disk.get('name', f"disk_{len(disks)}.vmdk"),
                    'capacity': disk.get('size_gb', 10) * 1024 * 1024 * 1024  # Convert GB to bytes
                }
            }
            disks.append(disk_config)
        return disks
    
    def _build_hardware_spec(self, hardware_spec: dict) -> dict:
        """Build hardware specification for VM creation."""
        return {
            'cpu': {
                'count': hardware_spec.get('cpu_count', 1)
            },
            'memory': {
                'size_MiB': hardware_spec.get('memory_mb', 1024)
            }
        }
    
    def _build_network_spec(self, network_spec: dict) -> list:
        """Build network specification for VM creation."""
        nics = []
        for network in network_spec:
            nic_config = {
                'type': network.get('device_type', 'VMXNET3'),
                'backing': {
                    'type': 'STANDARD_PORTGROUP',
                    'network': network.get('network_id')
                }
            }
            nics.append(nic_config)
        return nics
    
    def _apply_guest_customization(self, vm_id: str, customization_spec: dict) -> None:
        """Apply guest customization to VM."""
        # This would require additional VMware SDK calls for guest customization
        # For now, we'll log the customization spec
        logging.info(f"Applying guest customization to VM {vm_id}: {customization_spec}")
        # TODO: Implement actual guest customization using VMware SDK
    
    def _wait_for_ip_address(self, vm_id: str, timeout: int) -> str:
        """Wait for VM to get an IP address."""
        import time
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                guest_info = self.client.vcenter.vm.Guest.get(vm_id)
                if guest_info.ip_address:
                    return guest_info.ip_address
            except Exception as e:
                logging.debug(f"Error getting guest info: {e}")
            
            time.sleep(5)  # Wait 5 seconds before checking again
        
        raise TimeoutError(f"Timeout waiting for IP address for VM {vm_id}") 