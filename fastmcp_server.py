#!/usr/bin/env python3
"""
FastMCP VMware Server - Pure pyvmomi approach
"""

import sys
from fastmcp import FastMCP
from fastmcp import Context
import os
import ssl
from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim

# Create the MCP server instance
mcp = FastMCP(name="VMware MCP Server")

# Global service instance
service_instance = None

def connect_to_vcenter():
    """Connect to vCenter using pyvmomi."""
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

@mcp.tool()
def list_vms() -> str:
    """List all VMs using pyvmomi - optimized for speed."""
    if not connect_to_vcenter():
        return "Error: Could not connect to vCenter"
    
    try:
        content = service_instance.RetrieveContent()
        
        # Use a more targeted container view - only get VMs, not templates
        container = content.viewManager.CreateContainerView(
            content.rootFolder, [vim.VirtualMachine], False  # False = don't recurse into subfolders
        )
        
        vms = []
        for vm in container.view:
            # Skip templates quickly
            if hasattr(vm, 'config') and vm.config and vm.config.template:
                continue
                
            # Get only essential properties
            try:
                memory_mb = vm.config.hardware.memoryMB if vm.config and vm.config.hardware else 0
                memory_gb = round(memory_mb / 1024, 1) if memory_mb else 0
                
                vm_info = {
                    'name': vm.name,
                    'power_state': vm.runtime.powerState,
                    'cpu_count': vm.config.hardware.numCPU if vm.config and vm.config.hardware else 0,
                    'memory_gb': memory_gb
                }
                vms.append(vm_info)
            except:
                # Skip VMs with missing config
                continue
        
        # Clean up the container view
        container.Destroy()
        
        if vms:
            result = f"Found {len(vms)} VMs:\n"
            for vm in vms:
                result += f"- {vm['name']} ({vm['power_state']}, {vm['cpu_count']} CPU, {vm['memory_gb']} GB RAM)\n"
            return result
        else:
            return "No VMs found"
            
    except Exception as e:
        return f"Error: {e}"

@mcp.tool()
def list_vms_fast() -> str:
    """List all VMs using pyvmomi - ultra fast (no memory calculation)."""
    if not connect_to_vcenter():
        return "Error: Could not connect to vCenter"
    
    try:
        content = service_instance.RetrieveContent()
        
        # Use a minimal container view for maximum speed
        container = content.viewManager.CreateContainerView(
            content.rootFolder, [vim.VirtualMachine], False
        )
        
        vms = []
        for vm in container.view:
            # Skip templates quickly
            if hasattr(vm, 'config') and vm.config and vm.config.template:
                continue
                
            # Get only name and power state for maximum speed
            try:
                vm_info = {
                    'name': vm.name,
                    'power_state': vm.runtime.powerState
                }
                vms.append(vm_info)
            except:
                continue
        
        # Clean up the container view
        container.Destroy()
        
        if vms:
            result = f"Found {len(vms)} VMs (fast mode):\n"
            for vm in vms:
                result += f"- {vm['name']} ({vm['power_state']})\n"
            return result
        else:
            return "No VMs found"
            
    except Exception as e:
        return f"Error: {e}"

@mcp.tool()
def get_vm_details(vm_name: str) -> str:
    """Get detailed VM information using pyvmomi."""
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
        
        return f"VM Details:\n" + "\n".join([
            f"- {key}: {value}" for key, value in details.items()
        ])
        
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
def debug_connection() -> str:
    """Debug connection status."""
    if connect_to_vcenter():
        return "✓ pyvmomi: Connected successfully"
    else:
        return "✗ pyvmomi: Connection failed"

if __name__ == "__main__":
    mcp.run() 