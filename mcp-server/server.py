#!/usr/bin/env python3
"""
VMware MCP Server - Main Entry Point
Clean, modular FastMCP server for VMware vCenter management
"""

from fastmcp import FastMCP
import vm_info
import power
import vm_creation
import monitoring
import host_info

# Create the MCP server instance
mcp = FastMCP(name="VMware MCP Server")

# VM Information Tools
@mcp.tool()
def list_vms() -> str:
    """List all VMs using fast REST API."""
    return vm_info.list_vms()

@mcp.tool()
def get_vm_details(vm_name: str) -> str:
    """Get detailed VM information including IP addresses and network info."""
    return vm_info.get_vm_details(vm_name)

@mcp.tool()
def list_templates() -> str:
    """List all available templates."""
    return vm_info.list_templates()

@mcp.tool()
def list_datastores() -> str:
    """List all available datastores."""
    return vm_info.list_datastores()

@mcp.tool()
def list_networks() -> str:
    """List all available networks."""
    return vm_info.list_networks()

# Power Management Tools
@mcp.tool()
def power_on_vm(vm_name: str) -> str:
    """Power on a VM by name."""
    return power.power_on_vm(vm_name)

@mcp.tool()
def power_off_vm(vm_name: str) -> str:
    """Power off a VM by name."""
    return power.power_off_vm(vm_name)

# VM Creation Tools
@mcp.tool()
def create_vm_custom(template_name: str, new_vm_name: str, ip_address: str = "192.168.1.100", 
                    netmask: str = "255.255.255.0", gateway: str = "192.168.1.1", 
                    memory_gb: int = 4, cpu_count: int = 2, disk_gb: int = 50, 
                    network_name: str = "VM Network", datastore_name: str = "datastore1") -> str:
    """Create a new VM from template with comprehensive customization (memory, CPU, disk, IP) - powered off by default."""
    return vm_creation.create_vm_custom(
        template_name=template_name,
        new_vm_name=new_vm_name,
        ip_address=ip_address,
        netmask=netmask,
        gateway=gateway,
        memory_gb=memory_gb,
        cpu_count=cpu_count,
        disk_gb=disk_gb,
        network_name=network_name,
        datastore_name=datastore_name
    )

# Host Information Tools
@mcp.tool()
def list_hosts() -> str:
    """List all physical hosts with basic information."""
    return host_info.list_hosts()

@mcp.tool()
def get_host_details(host_name: str) -> str:
    """Get detailed information about a specific physical host (hardware, network, storage, VMs)."""
    return host_info.get_host_details(host_name)

@mcp.tool()
def get_host_performance_metrics(host_name: str) -> str:
    """Get detailed performance metrics for a specific host (CPU, memory, disk, network)."""
    return host_info.get_host_performance_metrics(host_name)

@mcp.tool()
def get_host_hardware_health(host_name: str) -> str:
    """Get hardware health information for a specific host (sensors, system health)."""
    return host_info.get_host_hardware_health(host_name)

# Monitoring Tools
@mcp.tool()
def get_vm_performance(vm_name: str) -> str:
    """Get detailed performance metrics for a specific VM (CPU, memory, disk, network)."""
    return monitoring.get_vm_performance(vm_name)

@mcp.tool()
def get_host_performance(host_name: str = None) -> str:
    """Get performance metrics for hosts (hardware info, health status)."""
    return monitoring.get_host_performance(host_name)

@mcp.tool()
def list_performance_counters() -> str:
    """List all available performance counters in vCenter."""
    return monitoring.list_performance_counters()

@mcp.tool()
def get_vm_summary_stats() -> str:
    """Get summary statistics for all VMs (counts, resource totals)."""
    return monitoring.get_vm_summary_stats()

if __name__ == "__main__":
    mcp.run()