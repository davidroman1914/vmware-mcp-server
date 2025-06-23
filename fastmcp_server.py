#!/usr/bin/env python3
"""
FastMCP VMware Server - Fast REST API approach
"""

import sys
from fastmcp import FastMCP
from fastmcp import Context
import os
import ssl
import requests
from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim

# Create the MCP server instance
mcp = FastMCP(name="VMware MCP Server")

# Global service instance
service_instance = None

def connect_to_vcenter():
    """Connect to vCenter using pyvmomi for power operations."""
    global service_instance
    
    if service_instance:
        try:
            # Test if connection is still alive
            content = service_instance.RetrieveContent()
            return True
        except:
            service_instance = None
    
    try:
        host = os.getenv('VCENTER_HOST')
        user = os.getenv('VCENTER_USER')
        password = os.getenv('VCENTER_PASSWORD')
        
        if not all([host, user, password]):
            return False
        
        # Add timeout to prevent hanging
        import socket
        socket.setdefaulttimeout(3)  # 3 second timeout
        
        # Create SSL context with optimizations
        context = ssl.SSLContext(ssl.PROTOCOL_TLS)
        context.verify_mode = ssl.CERT_NONE
        context.check_hostname = False
        
        service_instance = SmartConnect(
            host=host,
            user=user,
            pwd=password,
            sslContext=context
        )
        return True
        
    except Exception as e:
        print(f"Connection error: {e}", file=sys.stderr)
        return False

def get_vcenter_session():
    """Get vCenter REST API session for fast operations."""
    host = os.getenv('VCENTER_HOST')
    user = os.getenv('VCENTER_USER')
    password = os.getenv('VCENTER_PASSWORD')
    
    if not all([host, user, password]):
        return None
    
    try:
        # Create session
        session_url = f"https://{host}/rest/com/vmware/cis/session"
        response = requests.post(
            session_url,
            auth=(user, password),
            verify=False,
            timeout=5
        )
        
        if response.status_code == 200:
            session_id = response.json()['value']
            return session_id
        else:
            print(f"Failed to create session: {response.status_code}", file=sys.stderr)
            return None
            
    except Exception as e:
        print(f"Session error: {e}", file=sys.stderr)
        return None

@mcp.tool()
def list_vms() -> str:
    """List all VMs using fast REST API."""
    session_id = get_vcenter_session()
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

@mcp.tool()
def get_vm_details(vm_name: str) -> str:
    """Get detailed VM information using pyvmomi including IP addresses and network info."""
    if not connect_to_vcenter():
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
        
        # Get resource pool
        if vm.resourcePool:
            details['resource_pool'] = vm.resourcePool.name
        else:
            details['resource_pool'] = 'N/A'
        
        # Get folder location
        if vm.parent:
            details['folder'] = vm.parent.name
        else:
            details['folder'] = 'Root'
        
        # Get guest OS info
        if vm.guest:
            details['guest_os'] = vm.guest.guestFullName if vm.guest.guestFullName else 'N/A'
            details['tools_status'] = vm.guest.toolsStatus if vm.guest.toolsStatus else 'N/A'
        else:
            details['guest_os'] = 'N/A'
            details['tools_status'] = 'N/A'
        
        result = f"VM Details for '{vm.name}':\n"
        for key, value in details.items():
            # Format the key nicely
            formatted_key = key.replace('_', ' ').title()
            result += f"- {formatted_key}: {value}\n"
        
        return result
        
    except Exception as e:
        return f"Error: {e}"

@mcp.tool()
def power_on_vm(vm_name: str) -> str:
    """Power on a VM using pyvmomi."""
    if not connect_to_vcenter():
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
        
        if vm.runtime.powerState == vim.VirtualMachinePowerState.poweredOn:
            return f"VM '{vm_name}' is already powered on"
        
        task = vm.PowerOn()
        # Wait for task to complete
        while task.info.state not in [vim.TaskInfo.State.success, vim.TaskInfo.State.error]:
            pass
        
        if task.info.state == vim.TaskInfo.State.success:
            return f"Successfully powered on VM '{vm_name}'"
        else:
            return f"Failed to power on VM '{vm_name}': {task.info.error.msg}"
            
    except Exception as e:
        return f"Error: {e}"

@mcp.tool()
def power_off_vm(vm_name: str) -> str:
    """Power off a VM using pyvmomi."""
    if not connect_to_vcenter():
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
        
        if vm.runtime.powerState == vim.VirtualMachinePowerState.poweredOff:
            return f"VM '{vm_name}' is already powered off"
        
        task = vm.PowerOff()
        # Wait for task to complete
        while task.info.state not in [vim.TaskInfo.State.success, vim.TaskInfo.State.error]:
            pass
        
        if task.info.state == vim.TaskInfo.State.success:
            return f"Successfully powered off VM '{vm_name}'"
        else:
            return f"Failed to power off VM '{vm_name}': {task.info.error.msg}"
            
    except Exception as e:
        return f"Error: {e}"

@mcp.tool()
def list_templates() -> str:
    """List all VM templates using pyvmomi."""
    if not connect_to_vcenter():
        return "Error: Could not connect to vCenter"
    
    try:
        content = service_instance.RetrieveContent()
        container = content.viewManager.CreateContainerView(
            content.rootFolder, [vim.VirtualMachine], True
        )
        
        templates = []
        for vm in container.view:
            if vm.config.template:
                templates.append({
                    'name': vm.name,
                    'guest_id': vm.config.guestId,
                    'memory_mb': vm.config.hardware.memoryMB,
                    'cpu_count': vm.config.hardware.numCPU
                })
        
        if templates:
            result = f"Found {len(templates)} templates:\n"
            for template in templates:
                memory_gb = round(template['memory_mb'] / 1024, 1) if template['memory_mb'] else 0
                result += f"- {template['name']} ({template['guest_id']}, {template['cpu_count']} CPU, {memory_gb} GB RAM)\n"
            return result
        else:
            return "No templates found"
            
    except Exception as e:
        return f"Error: {e}"

@mcp.tool()
def create_vm_from_template(template_name: str, new_vm_name: str, datastore_name: str = None, cluster_name: str = None) -> str:
    """Create a new VM from a template using pyvmomi."""
    if not connect_to_vcenter():
        return "Error: Could not connect to vCenter"
    
    try:
        content = service_instance.RetrieveContent()
        
        # Find template
        container = content.viewManager.CreateContainerView(
            content.rootFolder, [vim.VirtualMachine], True
        )
        
        template = None
        for vm in container.view:
            if vm.config.template and vm.name == template_name:
                template = vm
                break
        
        if not template:
            return f"Template '{template_name}' not found"
        
        # Find datastore
        datastore = None
        if datastore_name:
            container = content.viewManager.CreateContainerView(
                content.rootFolder, [vim.Datastore], True
            )
            for ds in container.view:
                if ds.name == datastore_name:
                    datastore = ds
                    break
        
        # Find cluster/resource pool
        resource_pool = None
        if cluster_name:
            container = content.viewManager.CreateContainerView(
                content.rootFolder, [vim.ClusterComputeResource], True
            )
            for cluster in container.view:
                if cluster.name == cluster_name:
                    resource_pool = cluster.resourcePool
                    break
        
        # Create VM
        relospec = vim.vm.RelocateSpec()
        if datastore:
            relospec.datastore = datastore
        if resource_pool:
            relospec.pool = resource_pool
        
        configspec = vim.vm.ConfigSpec()
        configspec.location = relospec
        
        task = template.Clone(folder=template.parent, name=new_vm_name, spec=configspec)
        
        # Wait for task to complete
        while task.info.state not in [vim.TaskInfo.State.success, vim.TaskInfo.State.error]:
            pass
        
        if task.info.state == vim.TaskInfo.State.success:
            return f"Successfully created VM '{new_vm_name}' from template '{template_name}'"
        else:
            return f"Failed to create VM: {task.info.error.msg}"
            
    except Exception as e:
        return f"Error: {e}"

@mcp.tool()
def create_vm_simple(template_name: str, new_vm_name: str) -> str:
    """Create a new VM from a template using default settings (simpler)."""
    if not connect_to_vcenter():
        return "Error: Could not connect to vCenter"
    
    try:
        content = service_instance.RetrieveContent()
        
        # Find template
        container = content.viewManager.CreateContainerView(
            content.rootFolder, [vim.VirtualMachine], True
        )
        
        template = None
        for vm in container.view:
            if vm.config.template and vm.name == template_name:
                template = vm
                break
        
        if not template:
            return f"Template '{template_name}' not found. Use list_templates() to see available templates."
        
        # Create VM with default settings (same folder and datastore as template)
        clone_spec = vim.vm.CloneSpec()
        task = template.Clone(folder=template.parent, name=new_vm_name, spec=clone_spec)
        
        # Wait for task to complete
        while task.info.state not in [vim.TaskInfo.State.success, vim.TaskInfo.State.error]:
            pass
        
        if task.info.state == vim.TaskInfo.State.success:
            return f"✅ Successfully created VM '{new_vm_name}' from template '{template_name}'"
        else:
            return f"❌ Failed to create VM: {task.info.error.msg}"
            
    except Exception as e:
        return f"Error: {e}"

@mcp.tool()
def list_datastores() -> str:
    """List all available datastores."""
    if not connect_to_vcenter():
        return "Error: Could not connect to vCenter"
    
    try:
        content = service_instance.RetrieveContent()
        container = content.viewManager.CreateContainerView(
            content.rootFolder, [vim.Datastore], True
        )
        
        datastores = []
        for ds in container.view:
            free_space_gb = round(ds.summary.freeSpace / (1024**3), 1)
            total_space_gb = round(ds.summary.capacity / (1024**3), 1)
            datastores.append({
                'name': ds.name,
                'free_space_gb': free_space_gb,
                'total_space_gb': total_space_gb,
                'type': ds.summary.type
            })
        
        if datastores:
            result = f"Found {len(datastores)} datastores:\n"
            for ds in datastores:
                result += f"- {ds['name']} ({ds['type']}, {ds['free_space_gb']} GB free of {ds['total_space_gb']} GB)\n"
            return result
        else:
            return "No datastores found"
            
    except Exception as e:
        return f"Error: {e}"

@mcp.tool()
def list_clusters() -> str:
    """List all available clusters."""
    if not connect_to_vcenter():
        return "Error: Could not connect to vCenter"
    
    try:
        content = service_instance.RetrieveContent()
        container = content.viewManager.CreateContainerView(
            content.rootFolder, [vim.ClusterComputeResource], True
        )
        
        clusters = []
        for cluster in container.view:
            clusters.append({
                'name': cluster.name,
                'host_count': len(cluster.host),
                'resource_pool': cluster.resourcePool.name if cluster.resourcePool else 'N/A'
            })
        
        if clusters:
            result = f"Found {len(clusters)} clusters:\n"
            for cluster in clusters:
                result += f"- {cluster['name']} ({cluster['host_count']} hosts, resource pool: {cluster['resource_pool']})\n"
            return result
        else:
            return "No clusters found"
            
    except Exception as e:
        return f"Error: {e}"

@mcp.tool()
def debug_connection() -> str:
    """Debug connection status."""
    # Test REST API
    session_id = get_vcenter_session()
    rest_status = "✓ REST API: Connected" if session_id else "✗ REST API: Failed"
    
    # Test pyvmomi
    pyvmomi_status = "✓ pyvmomi: Connected" if connect_to_vcenter() else "✗ pyvmomi: Failed"
    
    return f"Connection Status:\n{rest_status}\n{pyvmomi_status}"

@mcp.tool()
def get_vm_ip(vm_name: str) -> str:
    """Get VM IP addresses using fast REST API."""
    session_id = get_vcenter_session()
    if not session_id:
        return "Error: Could not connect to vCenter"
    
    try:
        host = os.getenv('VCENTER_HOST')
        headers = {'vmware-api-session-id': session_id}
        
        # Get VM by name
        vm_url = f"https://{host}/rest/vcenter/vm"
        response = requests.get(vm_url, headers=headers, verify=False, timeout=10)
        
        if response.status_code == 200:
            vms = response.json()['value']
            vm = next((v for v in vms if v['name'] == vm_name), None)
            
            if not vm:
                return f"VM '{vm_name}' not found"
            
            vm_id = vm['vm']
            
            # Get VM guest info for IP addresses
            guest_url = f"https://{host}/rest/vcenter/vm/{vm_id}/guest"
            guest_response = requests.get(guest_url, headers=headers, verify=False, timeout=10)
            
            if guest_response.status_code == 200:
                guest_info = guest_response.json()['value']
                
                result = f"IP Addresses for VM '{vm_name}':\n"
                
                if guest_info.get('net'):
                    for nic in guest_info['net']:
                        if nic.get('ipConfig') and nic['ipConfig'].get('ipAddress'):
                            for ip in nic['ipConfig']['ipAddress']:
                                ip_addr = ip.get('ipAddress', 'Unknown')
                                prefix = ip.get('prefixLength', 'Unknown')
                                state = ip.get('state', 'Unknown')
                                
                                ip_info = f"- {ip_addr}/{prefix}"
                                if state == 'preferred':
                                    ip_info += " (primary)"
                                result += ip_info + "\n"
                else:
                    result += "- No IP addresses found (VM may be powered off or tools not running)\n"
                
                return result
            else:
                return f"Error: Failed to get guest info (HTTP {guest_response.status_code})"
        else:
            return f"Error: Failed to get VMs (HTTP {response.status_code})"
            
    except Exception as e:
        return f"Error: {e}"

@mcp.tool()
def create_vm_advanced(template_name: str, new_vm_name: str, memory_gb: int = None, cpu_count: int = None, ip_address: str = None, netmask: str = None, gateway: str = None, dns_servers: str = None) -> str:
    """Create a new VM from template with custom settings (memory, CPU, IP, etc.)."""
    if not connect_to_vcenter():
        return "Error: Could not connect to vCenter"
    
    try:
        content = service_instance.RetrieveContent()
        
        # Find template
        container = content.viewManager.CreateContainerView(
            content.rootFolder, [vim.VirtualMachine], True
        )
        
        template = None
        for vm in container.view:
            if vm.config.template and vm.name == template_name:
                template = vm
                break
        
        if not template:
            return f"Template '{template_name}' not found. Use list_templates() to see available templates."
        
        # Create config spec for customization
        config_spec = vim.vm.ConfigSpec()
        
        # Customize memory if specified
        if memory_gb:
            config_spec.memoryMB = memory_gb * 1024  # Convert GB to MB
            config_spec.memoryHotAddEnabled = True
        
        # Customize CPU if specified
        if cpu_count:
            config_spec.numCPUs = cpu_count
            config_spec.numCoresPerSocket = cpu_count
            config_spec.cpuHotAddEnabled = True
        
        # Create guest customization spec if IP is specified
        if ip_address:
            guest_customization = vim.vm.customization.Sysprep()
            guest_customization.userData = vim.vm.customization.UserData()
            guest_customization.userData.computerName = vim.vm.customization.FixedName(name=new_vm_name)
            
            # Set IP configuration
            nic_setting = vim.vm.customization.AdapterMapping()
            nic_setting.adapter = vim.vm.customization.IPSettings()
            nic_setting.adapter.ip = vim.vm.customization.FixedIp(ipAddress=ip_address)
            
            if netmask:
                nic_setting.adapter.subnetMask = netmask
            
            if gateway:
                nic_setting.adapter.gateway = [gateway]
            
            if dns_servers:
                dns_list = [dns.strip() for dns in dns_servers.split(',')]
                nic_setting.adapter.dnsServerList = dns_list
            
            # Use proper identification for Linux
            guest_customization.identification = vim.vm.customization.LinuxPrep()
            guest_customization.globalIPSettings = vim.vm.customization.GlobalIPSettings()
            
            config_spec.customization = guest_customization
            config_spec.nicSettingMap = [nic_setting]
        
        # Clone the VM
        task = template.Clone(folder=template.parent, name=new_vm_name, spec=config_spec)
        
        # Wait for task to complete
        while task.info.state not in [vim.TaskInfo.State.success, vim.TaskInfo.State.error]:
            pass
        
        if task.info.state == vim.TaskInfo.State.success:
            result = f"✅ Successfully created VM '{new_vm_name}' from template '{template_name}'"
            if memory_gb:
                result += f"\n- Memory: {memory_gb} GB"
            if cpu_count:
                result += f"\n- CPU: {cpu_count} cores"
            if ip_address:
                result += f"\n- IP: {ip_address}"
                if netmask:
                    result += f"/{netmask}"
                if gateway:
                    result += f" (Gateway: {gateway})"
            return result
        else:
            return f"❌ Failed to create VM: {task.info.error.msg}"
            
    except Exception as e:
        return f"Error: {e}"

@mcp.tool()
def create_vm_with_network(template_name: str, new_vm_name: str, network_name: str, memory_gb: int = None, cpu_count: int = None) -> str:
    """Create a new VM from template with specific network configuration."""
    if not connect_to_vcenter():
        return "Error: Could not connect to vCenter"
    
    try:
        content = service_instance.RetrieveContent()
        
        # Find template
        container = content.viewManager.CreateContainerView(
            content.rootFolder, [vim.VirtualMachine], True
        )
        
        template = None
        for vm in container.view:
            if vm.config.template and vm.name == template_name:
                template = vm
                break
        
        if not template:
            return f"Template '{template_name}' not found. Use list_templates() to see available templates."
        
        # Find network
        container = content.viewManager.CreateContainerView(
            content.rootFolder, [vim.dvs.DistributedVirtualPortgroup, vim.Network], True
        )
        
        network = None
        for net in container.view:
            if net.name == network_name:
                network = net
                break
        
        if not network:
            return f"Network '{network_name}' not found. Use list_networks() to see available networks."
        
        # Create config spec
        config_spec = vim.vm.ConfigSpec()
        
        # Customize memory if specified
        if memory_gb:
            config_spec.memoryMB = memory_gb * 1024
        
        # Customize CPU if specified
        if cpu_count:
            config_spec.numCPUs = cpu_count
        
        # Configure network adapter
        nic_spec = vim.vm.device.VirtualDeviceSpec()
        nic_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
        
        # Create network adapter
        nic_spec.device = vim.vm.device.VirtualVmxnet3()
        nic_spec.device.key = -1
        nic_spec.device.deviceInfo = vim.Description()
        nic_spec.device.deviceInfo.label = "Network adapter 1"
        nic_spec.device.deviceInfo.summary = network_name
        
        # Connect to network
        if isinstance(network, vim.dvs.DistributedVirtualPortgroup):
            nic_spec.device.backing = vim.vm.device.VirtualEthernetCard.DistributedVirtualPortBackingInfo()
            nic_spec.device.backing.port = vim.dvs.PortConnection()
            nic_spec.device.backing.port.portgroupKey = network.key
            nic_spec.device.backing.port.switchUuid = network.config.distributedVirtualSwitch.uuid
        else:
            nic_spec.device.backing = vim.vm.device.VirtualEthernetCard.NetworkBackingInfo()
            nic_spec.device.backing.network = network
            nic_spec.device.backing.deviceName = network_name
        
        config_spec.deviceChange = [nic_spec]
        
        # Clone the VM
        task = template.Clone(folder=template.parent, name=new_vm_name, spec=config_spec)
        
        # Wait for task to complete
        while task.info.state not in [vim.TaskInfo.State.success, vim.TaskInfo.State.error]:
            pass
        
        if task.info.state == vim.TaskInfo.State.success:
            result = f"✅ Successfully created VM '{new_vm_name}' from template '{template_name}'"
            result += f"\n- Network: {network_name}"
            if memory_gb:
                result += f"\n- Memory: {memory_gb} GB"
            if cpu_count:
                result += f"\n- CPU: {cpu_count} cores"
            return result
        else:
            return f"❌ Failed to create VM: {task.info.error.msg}"
            
    except Exception as e:
        return f"Error: {e}"

@mcp.tool()
def list_networks() -> str:
    """List all available networks."""
    if not connect_to_vcenter():
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

@mcp.tool()
def create_vm_custom(template_name: str, new_vm_name: str, memory_gb: int = None, cpu_count: int = None, disk_gb: int = None, network_name: str = None) -> str:
    """Create a new VM from template with custom memory, CPU, disk size, and network."""
    if not connect_to_vcenter():
        return "Error: Could not connect to vCenter"
    
    try:
        content = service_instance.RetrieveContent()
        
        # Find template
        container = content.viewManager.CreateContainerView(
            content.rootFolder, [vim.VirtualMachine], True
        )
        
        template = None
        for vm in container.view:
            if vm.config.template and vm.name == template_name:
                template = vm
                break
        
        if not template:
            return f"Template '{template_name}' not found. Use list_templates() to see available templates."
        
        # Create clone spec for customization
        clone_spec = vim.vm.CloneSpec()
        clone_spec.config = vim.vm.ConfigSpec()
        
        # Customize memory if specified
        if memory_gb:
            clone_spec.config.memoryMB = memory_gb * 1024  # Convert GB to MB
            clone_spec.config.memoryHotAddEnabled = True
        
        # Customize CPU if specified
        if cpu_count:
            clone_spec.config.numCPUs = cpu_count
            clone_spec.config.numCoresPerSocket = cpu_count
            clone_spec.config.cpuHotAddEnabled = True
        
        # Customize disk size if specified
        if disk_gb:
            # Find the first virtual disk in the template
            template_disk = None
            for device in template.config.hardware.device:
                if isinstance(device, vim.vm.device.VirtualDisk):
                    template_disk = device
                    break
            
            if template_disk:
                # Create disk spec
                disk_spec = vim.vm.device.VirtualDeviceSpec()
                disk_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.edit
                disk_spec.device = vim.vm.device.VirtualDisk()
                disk_spec.device.key = template_disk.key
                disk_spec.device.capacityInKB = disk_gb * 1024 * 1024  # Convert GB to KB
                disk_spec.device.backing = template_disk.backing
                
                clone_spec.config.deviceChange = [disk_spec]
        
        # Customize network if specified
        if network_name:
            # Find network
            container = content.viewManager.CreateContainerView(
                content.rootFolder, [vim.dvs.DistributedVirtualPortgroup, vim.Network], True
            )
            
            network = None
            for net in container.view:
                if net.name == network_name:
                    network = net
                    break
            
            if network:
                # Create network adapter spec
                nic_spec = vim.vm.device.VirtualDeviceSpec()
                nic_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
                
                # Create network adapter
                nic_spec.device = vim.vm.device.VirtualVmxnet3()
                nic_spec.device.key = -1
                nic_spec.device.deviceInfo = vim.Description()
                nic_spec.device.deviceInfo.label = "Network adapter 1"
                nic_spec.device.deviceInfo.summary = network_name
                
                # Connect to network
                if isinstance(network, vim.dvs.DistributedVirtualPortgroup):
                    nic_spec.device.backing = vim.vm.device.VirtualEthernetCard.DistributedVirtualPortBackingInfo()
                    nic_spec.device.backing.port = vim.dvs.PortConnection()
                    nic_spec.device.backing.port.portgroupKey = network.key
                    nic_spec.device.backing.port.switchUuid = network.config.distributedVirtualSwitch.uuid
                else:
                    nic_spec.device.backing = vim.vm.device.VirtualEthernetCard.NetworkBackingInfo()
                    nic_spec.device.backing.network = network
                    nic_spec.device.backing.deviceName = network_name
                
                # Add network spec to device changes
                if clone_spec.config.deviceChange:
                    clone_spec.config.deviceChange.append(nic_spec)
                else:
                    clone_spec.config.deviceChange = [nic_spec]
            else:
                return f"Network '{network_name}' not found. Use list_networks() to see available networks."
        
        # Clone the VM
        task = template.Clone(folder=template.parent, name=new_vm_name, spec=clone_spec)
        
        # Wait for task to complete
        while task.info.state not in [vim.TaskInfo.State.success, vim.TaskInfo.State.error]:
            pass
        
        if task.info.state == vim.TaskInfo.State.success:
            result = f"✅ Successfully created VM '{new_vm_name}' from template '{template_name}'"
            if memory_gb:
                result += f"\n- Memory: {memory_gb} GB"
            if cpu_count:
                result += f"\n- CPU: {cpu_count} cores"
            if disk_gb:
                result += f"\n- Disk: {disk_gb} GB"
            if network_name:
                result += f"\n- Network: {network_name}"
            result += f"\n\n💡 Note: IP address will be assigned via DHCP. You can configure static IP after powering on the VM."
            return result
        else:
            return f"❌ Failed to create VM: {task.info.error.msg}"
            
    except Exception as e:
        return f"Error: {e}"

if __name__ == "__main__":
    mcp.run() 