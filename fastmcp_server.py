#!/usr/bin/env python3
"""
FastMCP VMware Server
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
    """Get vCenter REST API session."""
    try:
        host = os.getenv('VCENTER_HOST')
        user = os.getenv('VCENTER_USER')
        password = os.getenv('VCENTER_PASSWORD')
        
        if not all([host, user, password]):
            return None
        
        # Create session
        session = requests.Session()
        session.verify = False  # Disable SSL verification for speed
        
        # Login
        login_url = f"https://{host}/rest/com/vmware/cis/session"
        response = session.post(login_url, auth=(user, password), timeout=5)
        
        if response.status_code == 200:
            return session
        else:
            return None
            
    except Exception as e:
        print(f"REST session error: {e}", file=sys.stderr)
        return None

@mcp.tool()
def list_vms() -> str:
    """List all VMs using REST API - FAST."""
    session = get_vcenter_session()
    if not session:
        return "Error: Failed to connect to vCenter REST API."
    
    try:
        host = os.getenv('VCENTER_HOST')
        url = f"https://{host}/rest/vcenter/vm"
        
        response = session.get(url, timeout=5)
        
        if response.status_code == 200:
            vms = response.json().get('value', [])
            
            if not vms:
                return "No VMs found."
            
            result = f"Found {len(vms)} VMs:\n"
            for vm in vms:
                name = vm.get('name', 'Unknown')
                power_state = vm.get('power_state', 'Unknown')
                result += f"- {name} ({power_state})\n"
            
            return result
        else:
            return f"Error: HTTP {response.status_code}"
            
    except Exception as e:
        return f"Error listing VMs: {str(e)}"

@mcp.tool()
def list_vms_detailed() -> str:
    """List VMs with details using REST API - FAST."""
    session = get_vcenter_session()
    if not session:
        return "Error: Failed to connect to vCenter REST API."
    
    try:
        host = os.getenv('VCENTER_HOST')
        url = f"https://{host}/rest/vcenter/vm"
        
        response = session.get(url, timeout=5)
        
        if response.status_code == 200:
            vms = response.json().get('value', [])
            
            if not vms:
                return "No VMs found."
            
            result = f"Found {len(vms)} VMs:\n"
            for vm in vms:
                name = vm.get('name', 'Unknown')
                power_state = vm.get('power_state', 'Unknown')
                cpu_count = vm.get('cpu_count', 0)
                memory_size_mib = vm.get('memory_size_mib', 0)
                
                # Proper memory conversion
                if memory_size_mib and memory_size_mib > 0:
                    memory_gb = round(memory_size_mib / 1024, 1)
                    memory_str = f"{memory_gb} GB"
                else:
                    memory_str = "Unknown"
                
                result += f"- {name} ({power_state}) - {cpu_count} CPU, {memory_str} RAM\n"
            
            return result
        else:
            return f"Error: HTTP {response.status_code}"
            
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
def debug_vm_data() -> str:
    """Debug tool to show raw VM data from REST API."""
    session = get_vcenter_session()
    if not session:
        return "Error: Failed to connect to vCenter REST API."
    
    try:
        host = os.getenv('VCENTER_HOST')
        url = f"https://{host}/rest/vcenter/vm"
        
        response = session.get(url, timeout=5)
        
        if response.status_code == 200:
            vms = response.json().get('value', [])
            
            if not vms:
                return "No VMs found."
            
            result = "Raw VM data from REST API:\n"
            for vm in vms:
                result += f"\nVM: {vm.get('name', 'Unknown')}\n"
                result += f"  Power State: {vm.get('power_state', 'Unknown')}\n"
                result += f"  CPU Count: {vm.get('cpu_count', 'Unknown')}\n"
                result += f"  Memory Size MiB: {vm.get('memory_size_mib', 'Unknown')}\n"
                result += f"  Raw memory data: {vm.get('memory_size_mib')} (type: {type(vm.get('memory_size_mib'))})\n"
            
            return result
        else:
            return f"Error: HTTP {response.status_code}"
            
    except Exception as e:
        return f"Error getting VM data: {str(e)}"

@mcp.tool()
def fast_test() -> str:
    """A fast test that doesn't require vCenter connection."""
    return "Fast test completed! This should be instant."

@mcp.tool()
def hello(name: str = "World") -> str:
    """A simple test tool."""
    return f"Hello, {name}! VMware MCP Server is working!"

if __name__ == "__main__":
    # Run with stdio transport (default)
    mcp.run() 