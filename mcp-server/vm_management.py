"""
VM Management Module

Provides functions to create, clone, and manage VMware VMs with comprehensive customization.
Mirrors Ansible vmware_guest functionality.
"""

import logging
import time
from typing import Dict, List, Optional
from helpers import (
    get_vsphere_client,
    get_vm_by_id,
    safe_api_call,
    resolve_template_id
)

logger = logging.getLogger(__name__)

def deploy_vm_from_template(
    template_id: str,
    vm_name: str,
    datacenter: Optional[str] = None,
    cluster: Optional[str] = None,
    folder: Optional[str] = None,
    hardware: Optional[Dict] = None,
    disk: Optional[List[Dict]] = None,
    networks: Optional[List[Dict]] = None,
    customization: Optional[Dict] = None,
    wait_for_ip: bool = False,
    wait_timeout: int = 300
) -> str:
    """
    Deploy a VM from template with comprehensive customization.
    
    Args:
        template_id: Template ID to deploy from
        vm_name: Name for the new VM
        datacenter: Target datacenter
        cluster: Target cluster
        folder: Target folder path
        hardware: Hardware specification (cpu, memory)
        disk: Disk specifications
        networks: Network configurations
        customization: Guest customization settings
        wait_for_ip: Whether to wait for IP address
        wait_timeout: Timeout for IP wait in seconds
    """
    try:
        client = get_vsphere_client()
        
        # Resolve template identifier to template ID
        resolved_template_id, error = resolve_template_id(client, template_id)
        if error:
            return error
        
        if not resolved_template_id:
            return "❌ Failed to resolve template ID"
        
        # Build deployment specification
        deploy_spec = client.vcenter.vm_template.LibraryItems.DeploySpec()
        
        # Set basic deployment info
        deploy_spec.name = vm_name
        
        # Set placement
        if datacenter or cluster or folder:
            placement = client.vcenter.vm_template.LibraryItems.DeployPlacementSpec()
            if datacenter:
                placement.datacenter = datacenter
            if cluster:
                placement.cluster = cluster
            if folder:
                placement.folder = folder
            deploy_spec.placement = placement
        
        # Set hardware customization
        if hardware:
            hw_spec = client.vcenter.vm_template.LibraryItems.HardwareCustomizationSpec()
            
            if 'cpu' in hardware:
                cpu_spec = client.vcenter.vm_template.LibraryItems.CpuUpdateSpec()
                if 'count' in hardware['cpu']:
                    cpu_spec.count = hardware['cpu']['count']
                if 'cores_per_socket' in hardware['cpu']:
                    cpu_spec.cores_per_socket = hardware['cpu']['cores_per_socket']
                hw_spec.cpu = cpu_spec
            
            if 'memory' in hardware:
                memory_spec = client.vcenter.vm_template.LibraryItems.MemoryUpdateSpec()
                if 'size_mib' in hardware['memory']:
                    memory_spec.size_mib = hardware['memory']['size_mib']
                hw_spec.memory = memory_spec
            
            deploy_spec.hardware_customization = hw_spec
        
        # Set disk customization
        if disk:
            # Handle different disk input formats
            if isinstance(disk, list):
                # List format: [{"datastore": "ds1"}, {"datastore": "ds2"}]
                disk_overrides = {}
                for i, disk_config in enumerate(disk):
                    disk_key = f"disk-{i}"
                    disk_storage = client.vcenter.vm_template.LibraryItems.DeploySpecDiskStorage()
                    if 'datastore' in disk_config:
                        disk_storage.datastore = disk_config['datastore']
                    if 'storage_policy' in disk_config:
                        disk_storage.storage_policy = disk_config['storage_policy']
                    disk_overrides[disk_key] = disk_storage
                deploy_spec.disk_storage_overrides = disk_overrides
            elif isinstance(disk, dict):
                # Check if it's a single disk config or a dict of disk configs
                if 'datastore' in disk or 'storage_policy' in disk:
                    # Single disk config: {"datastore": "ds1", "storage_policy": "policy1"}
                    disk_overrides = {}
                    disk_key = "disk-0"
                    disk_storage = client.vcenter.vm_template.LibraryItems.DeploySpecDiskStorage()
                    if 'datastore' in disk:
                        disk_storage.datastore = disk['datastore']
                    if 'storage_policy' in disk:
                        disk_storage.storage_policy = disk['storage_policy']
                    disk_overrides[disk_key] = disk_storage
                    deploy_spec.disk_storage_overrides = disk_overrides
                else:
                    # Dict of disk configs: {"disk-0": {"datastore": "ds1"}, "disk-1": {"datastore": "ds2"}}
                    disk_overrides = {}
                    for disk_key, disk_config in disk.items():
                        disk_storage = client.vcenter.vm_template.LibraryItems.DeploySpecDiskStorage()
                        if 'datastore' in disk_config:
                            disk_storage.datastore = disk_config['datastore']
                        if 'storage_policy' in disk_config:
                            disk_storage.storage_policy = disk_config['storage_policy']
                        disk_overrides[disk_key] = disk_storage
                    deploy_spec.disk_storage_overrides = disk_overrides
        
        # Set network customization
        if networks:
            network_specs = []
            for network_config in networks:
                network_spec = client.vcenter.vm_template.LibraryItems.EthernetUpdateSpec()
                if 'name' in network_config:
                    network_spec.backing = {'network': network_config['name']}
                if 'device_type' in network_config:
                    network_spec.type = network_config['device_type']
                network_specs.append(network_spec)
            deploy_spec.network_interfaces = network_specs
        
        # Set guest customization
        if customization:
            guest_spec = client.vcenter.vm_template.LibraryItems.GuestCustomizationSpec()
            
            if 'hostname' in customization:
                guest_spec.hostname = customization['hostname']
            
            if 'ip_address' in customization:
                guest_spec.ip_address = customization['ip_address']
            
            if 'netmask' in customization:
                guest_spec.netmask = customization['netmask']
            
            if 'gateway' in customization:
                guest_spec.gateway = customization['gateway']
            
            if 'dns_servers' in customization:
                guest_spec.dns_servers = customization['dns_servers']
            
            deploy_spec.guest_customization = guest_spec
        
        # Deploy the VM
        logger.info(f"Deploying VM '{vm_name}' from template '{resolved_template_id}'")
        vm_id, error = safe_api_call(
            lambda: client.vcenter.vm_template.LibraryItems.deploy(resolved_template_id, deploy_spec),
            f"Failed to deploy VM '{vm_name}' from template"
        )
        
        if error:
            return error
        
        # Wait for IP address if requested
        if wait_for_ip:
            logger.info(f"Waiting for IP address for VM '{vm_name}' (timeout: {wait_timeout}s)")
            start_time = time.time()
            
            while time.time() - start_time < wait_timeout:
                try:
                    # Get guest info to check for IP
                    guest_info = client.vcenter.vm.guest.Identity.get(vm_id)
                    if hasattr(guest_info, 'ip_address') and guest_info.ip_address:
                        return f"✅ Successfully deployed VM '{vm_name}' (ID: {vm_id}) with IP: {guest_info.ip_address}"
                    
                    time.sleep(5)  # Wait 5 seconds before checking again
                except Exception as e:
                    logger.debug(f"Waiting for IP: {str(e)}")
                    time.sleep(5)
            
            return f"✅ Successfully deployed VM '{vm_name}' (ID: {vm_id}) - IP address not available within timeout"
        
        return f"✅ Successfully deployed VM '{vm_name}' (ID: {vm_id})"
        
    except Exception as e:
        logger.error(f"Error deploying VM: {str(e)}")
        return f"❌ Error deploying VM: {str(e)}"

def create_template_from_vm(
    vm_id: str,
    template_name: str,
    description: Optional[str] = None
) -> str:
    """Create a template from an existing VM."""
    try:
        client = get_vsphere_client()
        
        # Get VM details
        vm, error = safe_api_call(
            lambda: get_vm_by_id(client, vm_id),
            f"Failed to get VM details for {vm_id}"
        )
        if error:
            return error
        
        if not vm:
            return f"❌ VM with ID {vm_id} not found"
        
        # Build template creation specification
        create_spec = client.vcenter.vm_template.LibraryItems.CreateSpec()
        create_spec.name = template_name
        if description:
            create_spec.description = description
        
        # Create the template
        logger.info(f"Creating template '{template_name}' from VM '{vm.name}'")
        template_id, error = safe_api_call(
            lambda: client.vcenter.vm_template.LibraryItems.create(vm.vm, create_spec),
            f"Failed to create template from VM '{vm.name}'"
        )
        
        if error:
            return error
        
        return f"✅ Successfully created template '{template_name}' (ID: {template_id}) from VM '{vm.name}'"
        
    except Exception as e:
        logger.error(f"Error creating template: {str(e)}")
        return f"❌ Error creating template: {str(e)}"

def clone_vm(
    source_vm_id: str,
    new_vm_name: str,
    datacenter: Optional[str] = None,
    cluster: Optional[str] = None,
    folder: Optional[str] = None,
    hardware: Optional[Dict] = None,
    disk: Optional[List[Dict]] = None,
    networks: Optional[List[Dict]] = None,
    customization: Optional[Dict] = None,
    wait_for_ip: bool = False,
    wait_timeout: int = 300
) -> str:
    """
    Clone a VM by creating a template and deploying from it.
    This provides the same functionality as direct cloning.
    """
    try:
        # Create a temporary template name
        temp_template_name = f"temp_template_{new_vm_name}_{int(time.time())}"
        
        # Create template from source VM
        template_result = create_template_from_vm(source_vm_id, temp_template_name)
        if template_result.startswith("❌"):
            return template_result
        
        # Extract template ID from result
        template_id = template_result.split("ID: ")[-1].split(")")[0]
        
        # Deploy new VM from template
        deploy_result = deploy_vm_from_template(
            template_id=template_id,
            vm_name=new_vm_name,
            datacenter=datacenter,
            cluster=cluster,
            folder=folder,
            hardware=hardware,
            disk=disk,
            networks=networks,
            customization=customization,
            wait_for_ip=wait_for_ip,
            wait_timeout=wait_timeout
        )
        
        # Clean up temporary template (optional - you might want to keep it)
        # For now, we'll leave the template for potential reuse
        
        return deploy_result
        
    except Exception as e:
        logger.error(f"Error cloning VM: {str(e)}")
        return f"❌ Error cloning VM: {str(e)}" 