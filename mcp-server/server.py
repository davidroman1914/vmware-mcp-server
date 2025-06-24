#!/usr/bin/env python3
"""
FastMCP VMware Server - Clean and Working Version
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

@mcp.tool()
def power_on_vm(vm_name: str) -> str:
    """Power on a VM by name."""
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
        while task.info.state not in [vim.TaskInfo.State.success, vim.TaskInfo.State.error]:
            pass
        
        if task.info.state == vim.TaskInfo.State.success:
            return f"✅ Successfully powered on VM '{vm_name}'"
        else:
            return f"❌ Failed to power on VM '{vm_name}': {task.info.error.msg}"
            
    except Exception as e:
        return f"Error: {e}"

@mcp.tool()
def power_off_vm(vm_name: str) -> str:
    """Power off a VM by name."""
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
        while task.info.state not in [vim.TaskInfo.State.success, vim.TaskInfo.State.error]:
            pass
        
        if task.info.state == vim.TaskInfo.State.success:
            return f"✅ Successfully powered off VM '{vm_name}'"
        else:
            return f"❌ Failed to power off VM '{vm_name}': {task.info.error.msg}"
            
    except Exception as e:
        return f"Error: {e}"

@mcp.tool()
def list_templates() -> str:
    """List all available templates."""
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

# Helper functions for VM creation
def find_template(service_instance, template_name):
    """Find template by name."""
    try:
        content = service_instance.RetrieveContent()
        container = content.viewManager.CreateContainerView(
            content.rootFolder, [vim.VirtualMachine], True
        )
        
        for vm in container.view:
            if vm.config.template and vm.name == template_name:
                return vm
        
        return None
        
    except Exception as e:
        return None

def find_datastore(service_instance, datastore_name):
    """Find datastore by name."""
    try:
        content = service_instance.RetrieveContent()
        container = content.viewManager.CreateContainerView(
            content.rootFolder, [vim.Datastore], True
        )
        
        for ds in container.view:
            if ds.name == datastore_name:
                return ds
        
        return None
        
    except Exception as e:
        return None

def find_network(service_instance, network_name):
    """Find network by name."""
    try:
        content = service_instance.RetrieveContent()
        container = content.viewManager.CreateContainerView(
            content.rootFolder, [vim.dvs.DistributedVirtualPortgroup, vim.Network], True
        )
        
        for net in container.view:
            if net.name == network_name:
                return net
        
        return None
        
    except Exception as e:
        return None

def find_resource_pool(service_instance):
    """Find the default resource pool."""
    try:
        content = service_instance.RetrieveContent()
        container = content.viewManager.CreateContainerView(
            content.rootFolder, [vim.ClusterComputeResource], True
        )
        
        for cluster in container.view:
            if cluster.resourcePool:
                return cluster.resourcePool
        
        return None
        
    except Exception as e:
        return None

@mcp.tool()
def create_vm_custom(template_name: str, new_vm_name: str, ip_address: str = "10.60.132.105", netmask: str = "255.255.255.0", gateway: str = "10.60.132.1", memory_gb: int = 4, cpu_count: int = 2, disk_gb: int = 50, network_name: str = "PROD VMs", datastore_name: str = "ova-inf-vh03-ds-1") -> str:
    """Create a new VM from template with comprehensive customization (memory, CPU, disk, IP) - powered off by default."""
    if not connect_to_vcenter():
        return "Error: Could not connect to vCenter"
    
    try:
        # Find template
        template = find_template(service_instance, template_name)
        if not template:
            return f"Template '{template_name}' not found. Use list_templates() to see available templates."
        
        # Find datastore
        datastore = find_datastore(service_instance, datastore_name)
        if not datastore:
            return f"Datastore '{datastore_name}' not found. Use list_datastores() to see available datastores."
        
        # Find network
        network = find_network(service_instance, network_name)
        if not network:
            return f"Network '{network_name}' not found. Use list_networks() to see available networks."
        
        # Find resource pool
        resource_pool = find_resource_pool(service_instance)
        if not resource_pool:
            return "Resource pool not found."
        
        # Create relocation spec with both datastore and resource pool
        relospec = vim.vm.RelocateSpec()
        relospec.datastore = datastore
        relospec.pool = resource_pool
        
        # Create clone spec
        clone_spec = vim.vm.CloneSpec()
        clone_spec.location = relospec
        clone_spec.powerOn = False  # Keep powered off
        clone_spec.template = False
        
        # Create config spec for hardware customizations
        config_spec = vim.vm.ConfigSpec()
        config_spec.memoryMB = memory_gb * 1024  # Convert GB to MB
        config_spec.numCPUs = cpu_count
        
        # Disk customization - resize the first disk
        for device in template.config.hardware.device:
            if isinstance(device, vim.vm.device.VirtualDisk):
                disk_spec = vim.vm.device.VirtualDeviceSpec()
                disk_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.edit
                disk_spec.device = device
                disk_spec.device.capacityInKB = disk_gb * 1024 * 1024  # Convert GB to KB
                config_spec.deviceChange = [disk_spec]
                break
        
        # Network customization
        if network:
            # Find existing network adapter and update it
            for device in template.config.hardware.device:
                if isinstance(device, vim.vm.device.VirtualEthernetCard):
                    nic_spec = vim.vm.device.VirtualDeviceSpec()
                    nic_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.edit
                    nic_spec.device = device
                    
                    if isinstance(network, vim.dvs.DistributedVirtualPortgroup):
                        nic_spec.device.backing = vim.vm.device.VirtualEthernetCard.DistributedVirtualPortBackingInfo()
                        nic_spec.device.backing.port = vim.dvs.PortConnection()
                        nic_spec.device.backing.port.portgroupKey = network.key
                        nic_spec.device.backing.port.switchUuid = network.config.distributedVirtualSwitch.uuid
                    else:
                        nic_spec.device.backing = vim.vm.device.VirtualEthernetCard.NetworkBackingInfo()
                        nic_spec.device.backing.network = network
                        nic_spec.device.backing.deviceName = network.name
                    
                    # Add to device changes
                    if config_spec.deviceChange:
                        config_spec.deviceChange.append(nic_spec)
                    else:
                        config_spec.deviceChange = [nic_spec]
                    break
        
        # IP customization
        customizationspec = vim.vm.customization.Specification()
        
        # Identity
        identity = vim.vm.customization.LinuxPrep()
        identity.hostName = vim.vm.customization.FixedName(name=new_vm_name)
        identity.domain = "local"
        customizationspec.identity = identity
        
        # Network interface with IP
        adapter_mapping = vim.vm.customization.AdapterMapping()
        adapter_mapping.adapter = vim.vm.customization.IPSettings()
        adapter_mapping.adapter.ip = vim.vm.customization.FixedIp(ipAddress=ip_address)
        adapter_mapping.adapter.subnetMask = netmask
        adapter_mapping.adapter.gateway = [gateway]
        adapter_mapping.adapter.dnsServerList = ["8.8.8.8", "8.8.4.4"]
        
        customizationspec.nicSettingMap = [adapter_mapping]
        customizationspec.globalIPSettings = vim.vm.customization.GlobalIPSettings()
        customizationspec.globalIPSettings.dnsServerList = ["8.8.8.8", "8.8.4.4"]
        
        clone_spec.customization = customizationspec
        
        # Attach config spec to clone spec
        clone_spec.config = config_spec
        
        # Clone the VM
        task = template.Clone(folder=template.parent, name=new_vm_name, spec=clone_spec)
        
        # Wait for task to complete
        while task.info.state not in [vim.TaskInfo.State.success, vim.TaskInfo.State.error]:
            pass
        
        if task.info.state == vim.TaskInfo.State.success:
            new_vm = task.info.result
            result = f"✅ Successfully created VM '{new_vm_name}' (powered off)"
            result += f"\n- Template: {template_name}"
            result += f"\n- Memory: {memory_gb} GB"
            result += f"\n- CPU: {cpu_count} cores"
            result += f"\n- Disk: {disk_gb} GB"
            result += f"\n- Network: {network_name}"
            result += f"\n- Datastore: {datastore.name}"
            result += f"\n- IP Address: {ip_address}"
            result += f"\n- Power State: Powered off"
            return result
        else:
            return f"❌ Failed to create VM: {task.info.error.msg}"
            
    except Exception as e:
        return f"Error: {e}"

if __name__ == "__main__":
    mcp.run() 