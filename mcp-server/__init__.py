"""
VMware MCP Server Package

A Model Context Protocol (MCP) server for VMware vCenter management.
Provides tools for listing VMs and getting detailed VM information.
"""

from .server import server
from .list_vm import list_vms_text
from .get_vm_info import get_vm_info_text
from .helpers import (
    get_vsphere_client,
    safe_get_attr,
    format_bytes,
    get_vm_by_id,
    get_network_name,
    safe_api_call,
    get_resource_pool_name,
    get_datastore_name,
    get_folder_name,
    get_cluster_name,
    get_vm_placement_info
)

__version__ = "1.0.0"
__author__ = "VMware MCP Server Team"

__all__ = [
    "server",
    "list_vms_text", 
    "get_vm_info_text",
    "get_vsphere_client",
    "safe_get_attr",
    "format_bytes",
    "get_vm_by_id",
    "get_network_name",
    "safe_api_call",
    "get_resource_pool_name",
    "get_datastore_name",
    "get_folder_name",
    "get_cluster_name",
    "get_vm_placement_info"
]
