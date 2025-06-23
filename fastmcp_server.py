#!/usr/bin/env python3
"""
FastMCP VMware Server - Hybrid approach
"""

import sys
from fastmcp import FastMCP
from fastmcp import Context
import os
import ssl
import requests
from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim

# Try to import vmware-vcenter for fast operations
try:
    from vmware.vcenter import VCenter
    from vmware.vcenter.vm import VM
    VMWARE_VCENTER_AVAILABLE = True
except ImportError:
    VMWARE_VCENTER_AVAILABLE = False
    print("vmware-vcenter not available, using REST API fallback", file=sys.stderr)

# Create the MCP server instance
mcp = FastMCP(name="VMware MCP Server")

# Global service instance
service_instance = None
vcenter_client = None

def connect_to_vcenter():
    """Connect to vCenter using pyvmomi for complex operations."""
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

def get_vcenter_client():
    """Get vmware-vcenter client for fast operations."""
    global vcenter_client
    
    if vcenter_client:
        return vcenter_client
    
    if not VMWARE_VCENTER_AVAILABLE:
        return None
    
    try:
        host = os.getenv('VCENTER_HOST')
        user = os.getenv('VCENTER_USER')
        password = os.getenv('VCENTER_PASSWORD')
        
        if not all([host, user, password]):
            return None
        
        vcenter_client = VCenter(host, user, password, verify_ssl=False)
        return vcenter_client
        
    except Exception as e:
        print(f"vmware-vcenter connection error: {e}", file=sys.stderr)
        return None

def get_vcenter_session():
    """Get vCenter REST API session."""
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
def list_vms_fast() -> str:
    """List all VMs using vmware-vcenter for maximum speed."""
    client = get_vcenter_client()
    
    if client:
        try:
            # Use vmware-vcenter for fast listing
            vms = client.list_vms()
            result = []
            
            for vm in vms:
                vm_info = {
                    'name': vm.name,
                    'power_state': vm.power_state,
                    'cpu_count': vm.cpu_count,
                    'memory_mb': vm.memory_mb,
                    'memory_gb': round(vm.memory_mb / 1024, 1),
                    'vm_id': vm.vm_id
                }
                result.append(vm_info)
            
            return f"Found {len(result)} VMs using vmware-vcenter:\n" + "\n".join([
                f"- {vm['name']} ({vm['power_state']}, {vm['cpu_count']} CPU, {vm['memory_gb']} GB RAM)"
                for vm in result
            ])
            
        except Exception as e:
            print(f"vmware-vcenter error: {e}", file=sys.stderr)
            # Fall back to REST API
            pass
    
    # Fallback to REST API
    session_id = get_vcenter_session()
    if not session_id:
        return "Error: Could not connect to vCenter"
    
    try:
        host = os.getenv('VCENTER_HOST')
        headers = {'vmware-api-session-id': session_id}
        
        # Get VMs
        vm_url = f"https://{host}/rest/vcenter/vm"
        response = requests.get(vm_url, headers=headers, verify=False, timeout=5)
        
        if response.status_code == 200:
            vms = response.json()['value']
            result = []
            
            for vm in vms:
                vm_info = {
                    'name': vm['name'],
                    'power_state': vm['power_state'],
                    'cpu_count': vm['cpu_count'],
                    'memory_mb': vm['memory_MiB'],
                    'memory_gb': round(vm['memory_MiB'] / 1024, 1),
                    'vm_id': vm['vm']
                }
                result.append(vm_info)
            
            return f"Found {len(result)} VMs using REST API:\n" + "\n".join([
                f"- {vm['name']} ({vm['power_state']}, {vm['cpu_count']} CPU, {vm['memory_gb']} GB RAM)"
                for vm in result
            ])
        else:
            return f"Error: Failed to get VMs (HTTP {response.status_code})"
            
    except Exception as e:
        return f"Error: {e}"

@mcp.tool()
def get_vm_details_fast(vm_name: str) -> str:
    """Get detailed VM information using vmware-vcenter."""
    client = get_vcenter_client()
    
    if client:
        try:
            # Use vmware-vcenter for fast details
            vm = client.get_vm(vm_name)
            if vm:
                details = {
                    'name': vm.name,
                    'power_state': vm.power_state,
                    'cpu_count': vm.cpu_count,
                    'memory_mb': vm.memory_mb,
                    'memory_gb': round(vm.memory_mb / 1024, 1),
                    'vm_id': vm.vm_id,
                    'guest_id': vm.guest_id,
                    'version': vm.version
                }
                
                return f"VM Details (vmware-vcenter):\n" + "\n".join([
                    f"- {key}: {value}" for key, value in details.items()
                ])
            else:
                return f"VM '{vm_name}' not found"
                
        except Exception as e:
            print(f"vmware-vcenter error: {e}", file=sys.stderr)
            # Fall back to REST API
            pass
    
    # Fallback to REST API
    session_id = get_vcenter_session()
    if not session_id:
        return "Error: Could not connect to vCenter"
    
    try:
        host = os.getenv('VCENTER_HOST')
        headers = {'vmware-api-session-id': session_id}
        
        # Get VM by name
        vm_url = f"https://{host}/rest/vcenter/vm"
        response = requests.get(vm_url, headers=headers, verify=False, timeout=5)
        
        if response.status_code == 200:
            vms = response.json()['value']
            vm = next((v for v in vms if v['name'] == vm_name), None)
            
            if vm:
                details = {
                    'name': vm['name'],
                    'power_state': vm['power_state'],
                    'cpu_count': vm['cpu_count'],
                    'memory_mb': vm['memory_MiB'],
                    'memory_gb': round(vm['memory_MiB'] / 1024, 1),
                    'vm_id': vm['vm'],
                    'guest_id': vm.get('guest_ID', 'N/A'),
                    'version': vm.get('version', 'N/A')
                }
                
                return f"VM Details (REST API):\n" + "\n".join([
                    f"- {key}: {value}" for key, value in details.items()
                ])
            else:
                return f"VM '{vm_name}' not found"
        else:
            return f"Error: Failed to get VMs (HTTP {response.status_code})"
            
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
                result += f"- {template['name']} ({template['guest_id']}, {template['cpu_count']} CPU, {template['memory_mb']} MB RAM)\n"
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
def debug_connection() -> str:
    """Debug connection status and available methods."""
    result = []
    
    # Test vmware-vcenter
    if VMWARE_VCENTER_AVAILABLE:
        client = get_vcenter_client()
        if client:
            result.append("✓ vmware-vcenter: Connected")
        else:
            result.append("✗ vmware-vcenter: Connection failed")
    else:
        result.append("✗ vmware-vcenter: Not available")
    
    # Test pyvmomi
    if connect_to_vcenter():
        result.append("✓ pyvmomi: Connected")
    else:
        result.append("✗ pyvmomi: Connection failed")
    
    # Test REST API
    session_id = get_vcenter_session()
    if session_id:
        result.append("✓ REST API: Connected")
    else:
        result.append("✗ REST API: Connection failed")
    
    return "Connection Status:\n" + "\n".join(result)

if __name__ == "__main__":
    mcp.run() 