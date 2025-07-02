#!/usr/bin/env python3
"""
VM Information Module for VMware MCP Server
Handles VM listing and detailed information retrieval
"""

import os
import requests
from pyVmomi import vim
import connection


def list_vms() -> str:
    """List all VMs using fast REST API."""
    session_id = connection.get_vcenter_session()
    if not session_id:
        return "Error: Could not connect to vCenter"
    
    try:
        host = os.getenv('VCENTER_HOST')
        headers = {'vmware-api-session-id': session_id}
        
        # Get VMs - this should be very fast
        vm_url = f"https://{host}/rest/vcenter/vm"
        response = requests.get(vm_url, headers=headers, verify=False, timeout=10)
        
        if response.status_code == 200:
            vms = response.json()['value']
            
            if not vms:
                return "No VMs found"
            
            result = f"Found {len(vms)} VMs:\n"
            for vm in vms:
                name = vm.get('name', 'Unknown')
                power_state = vm.get('power_state', 'Unknown')
                result += f"- {name} ({power_state})\n"
            
            return result
        else:
            return f"Error: Failed to get VMs (HTTP {response.status_code})"
            
    except Exception as e:
        return f"Error: {e}"


def get_vm_details(vm_name: str) -> str:
    """Get detailed VM information using pyvmomi including IP addresses and network info."""
    service_instance = connection.get_service_instance()
    if not service_instance:
        return "Error: Could not connect to vCenter"
    
    try:
        content = service_instance.RetrieveContent()
        container = content.viewManager.CreateContainerView(
            content.rootFolder, [vim.VirtualMachine], True
        )
        
        vm = None
        for v in container.view:
            if v.name == vm_name:
                vm = v
                break
        
        if not vm:
            return f"VM '{vm_name}' not found"
        
        # Basic VM info
        memory_mb = vm.config.hardware.memoryMB if vm.config and vm.config.hardware else 0
        memory_gb = round(memory_mb / 1024, 1) if memory_mb else 0
        
        details = {
            'name': vm.name,
            'power_state': vm.runtime.powerState,
            'cpu_count': vm.config.hardware.numCPU if vm.config and vm.config.hardware else 0,
            'memory_mb': memory_mb,
            'memory_gb': memory_gb,
            'guest_id': vm.config.guestId if vm.config else 'N/A',
            'version': vm.config.version if vm.config else 'N/A',
            'template': vm.config.template if vm.config else False
        }
        
        # Get IP addresses and network info
        if vm.guest and vm.guest.net:
            ip_addresses = []
            for nic in vm.guest.net:
                if nic.ipConfig and nic.ipConfig.ipAddress:
                    for ip in nic.ipConfig.ipAddress:
                        ip_info = f"{ip.ipAddress}/{ip.prefixLength}"
                        if ip.state == 'preferred':
                            ip_info += " (primary)"
                        ip_addresses.append(ip_info)
            
            if ip_addresses:
                details['ip_addresses'] = ', '.join(ip_addresses)
            else:
                details['ip_addresses'] = 'No IP addresses found'
        else:
            details['ip_addresses'] = 'Network info not available'
        
        # Get network adapters
        if vm.config and vm.config.hardware and vm.config.hardware.device:
            network_adapters = []
            for device in vm.config.hardware.device:
                if isinstance(device, vim.vm.device.VirtualEthernetCard):
                    adapter_info = f"{device.deviceInfo.label}"
                    if hasattr(device, 'backing') and device.backing:
                        if hasattr(device.backing, 'network'):
                            adapter_info += f" -> {device.backing.network.name}"
                        elif hasattr(device.backing, 'port'):
                            adapter_info += f" -> {device.backing.port.portgroupKey}"
                    network_adapters.append(adapter_info)
            
            if network_adapters:
                details['network_adapters'] = ', '.join(network_adapters)
            else:
                details['network_adapters'] = 'No network adapters found'
        else:
            details['network_adapters'] = 'Network adapters not available'
        
        # Get datastore info
        if vm.datastore:
            datastores = [ds.name for ds in vm.datastore]
            details['datastores'] = ', '.join(datastores)
        else:
            details['datastores'] = 'No datastores found'
        
        # Get resource pool info
        if vm.resourcePool:
            details['resource_pool'] = vm.resourcePool.name
        else:
            details['resource_pool'] = 'No resource pool found'
        
        # Get folder location
        if vm.parent:
            details['folder'] = vm.parent.name
        else:
            details['folder'] = 'No folder found'
        
        # Get VMware Tools status
        if vm.guest:
            details['vmware_tools'] = vm.guest.toolsRunningStatus
        else:
            details['vmware_tools'] = 'Unknown'
        
        # Format the result
        result = f"VM Details for '{vm_name}':\n"
        result += f"- Power State: {details['power_state']}\n"
        result += f"- CPU Count: {details['cpu_count']}\n"
        result += f"- Memory: {details['memory_gb']} GB ({details['memory_mb']} MB)\n"
        result += f"- Guest OS: {details['guest_id']}\n"
        result += f"- VMware Tools: {details['vmware_tools']}\n"
        result += f"- IP Addresses: {details['ip_addresses']}\n"
        result += f"- Network Adapters: {details['network_adapters']}\n"
        result += f"- Datastores: {details['datastores']}\n"
        result += f"- Resource Pool: {details['resource_pool']}\n"
        result += f"- Folder: {details['folder']}\n"
        result += f"- Template: {details['template']}\n"
        
        return result
        
    except Exception as e:
        return f"Error: {e}"


def list_templates() -> str:
    """List all available templates."""
    service_instance = connection.get_service_instance()
    if not service_instance:
        return "Error: Could not connect to vCenter"
    
    try:
        content = service_instance.RetrieveContent()
        container = content.viewManager.CreateContainerView(
            content.rootFolder, [vim.VirtualMachine], True
        )
        
        templates = []
        for vm in container.view:
            if vm.config.template:
                templates.append(vm.name)
        
        if templates:
            result = f"Found {len(templates)} templates:\n"
            for template in templates:
                result += f"- {template}\n"
            return result
        else:
            return "No templates found"
            
    except Exception as e:
        return f"Error: {e}"


def list_datastores() -> str:
    """List all available datastores."""
    service_instance = connection.get_service_instance()
    if not service_instance:
        return "Error: Could not connect to vCenter"
    
    try:
        content = service_instance.RetrieveContent()
        container = content.viewManager.CreateContainerView(
            content.rootFolder, [vim.Datastore], True
        )
        
        datastores = []
        for ds in container.view:
            datastores.append({
                'name': ds.name,
                'type': ds.summary.type,
                'capacity_gb': round(ds.summary.capacity / (1024**3), 1),
                'free_gb': round(ds.summary.freeSpace / (1024**3), 1)
            })
        
        if datastores:
            result = f"Found {len(datastores)} datastores:\n"
            for ds in datastores:
                result += f"- {ds['name']} ({ds['type']}, {ds['free_gb']}GB free of {ds['capacity_gb']}GB)\n"
            return result
        else:
            return "No datastores found"
            
    except Exception as e:
        return f"Error: {e}"


def list_networks() -> str:
    """List all available networks."""
    service_instance = connection.get_service_instance()
    if not service_instance:
        return "Error: Could not connect to vCenter"
    
    try:
        content = service_instance.RetrieveContent()
        container = content.viewManager.CreateContainerView(
            content.rootFolder, [vim.dvs.DistributedVirtualPortgroup, vim.Network], True
        )
        
        networks = []
        for net in container.view:
            if isinstance(net, vim.dvs.DistributedVirtualPortgroup):
                networks.append({
                    'name': net.name,
                    'type': 'Distributed Port Group',
                    'vswitch': net.config.distributedVirtualSwitch.name
                })
            else:
                networks.append({
                    'name': net.name,
                    'type': 'Standard Network',
                    'vswitch': 'N/A'
                })
        
        if networks:
            result = f"Found {len(networks)} networks:\n"
            for net in networks:
                result += f"- {net['name']} ({net['type']}, vSwitch: {net['vswitch']})\n"
            return result
        else:
            return "No networks found"
            
    except Exception as e:
        return f"Error: {e}" 