#!/usr/bin/env python3
"""
FastMCP VMware Server
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
    """Connect to vCenter using environment variables."""
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
        
        # Create SSL context
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
    """List all VMs in vCenter with detailed information."""
    if not connect_to_vcenter():
        return "Error: Failed to connect to vCenter. Check environment variables."
    
    try:
        content = service_instance.RetrieveContent()
        container = content.viewManager.CreateContainerView(
            content.rootFolder, [vim.VirtualMachine], True
        )
        
        vms = []
        for vm in container.view:
            vm_info = {
                "name": vm.name,
                "power_state": vm.runtime.powerState,
                "guest_id": getattr(vm.config, 'guestId', 'Unknown'),
                "cpu_count": vm.config.hardware.numCPU if hasattr(vm.config, 'hardware') and vm.config.hardware else 0,
                "memory_mb": vm.config.hardware.memoryMB if hasattr(vm.config, 'hardware') and vm.config.hardware else 0,
                "ip_address": vm.guest.ipAddress if vm.guest else None,
            }
            vms.append(vm_info)
        
        container.Destroy()
        return f"Found {len(vms)} VMs:\n" + "\n".join([f"- {vm['name']} ({vm['power_state']})" for vm in vms])
        
    except Exception as e:
        return f"Error listing VMs: {str(e)}"

@mcp.tool()
def power_on_vm(vm_name: str) -> str:
    """Power on a VM by name."""
    if not connect_to_vcenter():
        return "Error: Failed to connect to vCenter. Check environment variables."
    
    try:
        content = service_instance.RetrieveContent()
        container = content.viewManager.CreateContainerView(
            content.rootFolder, [vim.VirtualMachine], True
        )
        
        for vm in container.view:
            if vm.name == vm_name:
                if vm.runtime.powerState == vim.VirtualMachinePowerState.poweredOn:
                    container.Destroy()
                    return f"VM '{vm_name}' is already powered on."
                
                task = vm.PowerOn()
                container.Destroy()
                return f"Powering on VM '{vm_name}'..."
        
        container.Destroy()
        return f"VM '{vm_name}' not found."
        
    except Exception as e:
        return f"Error powering on VM: {str(e)}"

@mcp.tool()
def power_off_vm(vm_name: str) -> str:
    """Power off a VM by name."""
    if not connect_to_vcenter():
        return "Error: Failed to connect to vCenter. Check environment variables."
    
    try:
        content = service_instance.RetrieveContent()
        container = content.viewManager.CreateContainerView(
            content.rootFolder, [vim.VirtualMachine], True
        )
        
        for vm in container.view:
            if vm.name == vm_name:
                if vm.runtime.powerState == vim.VirtualMachinePowerState.poweredOff:
                    container.Destroy()
                    return f"VM '{vm_name}' is already powered off."
                
                task = vm.PowerOff()
                container.Destroy()
                return f"Powering off VM '{vm_name}'..."
        
        container.Destroy()
        return f"VM '{vm_name}' not found."
        
    except Exception as e:
        return f"Error powering off VM: {str(e)}"

@mcp.tool()
def hello(name: str = "World") -> str:
    """A simple test tool."""
    return f"Hello, {name}! VMware MCP Server is working!"

if __name__ == "__main__":
    # Run with stdio transport (default)
    mcp.run() 