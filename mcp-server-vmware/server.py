#!/usr/bin/env python3
"""
MCP Server for VMware vCenter using only vmware-vcenter package
Follows the same pattern as the main mcp-server folder
"""

import asyncio
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from vm_operations import (
    get_all_vms_text,
    power_on_vm_text,
    power_off_vm_text,
    restart_vm_text,
    get_vm_info_text
)

server = Server("vmware-vm-server")

@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="get-all-vms",
            description="Get all VMs from vCenter using vmware-vcenter package",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        Tool(
            name="power-on-vm",
            description="Power on a VM by its ID",
            inputSchema={
                "type": "object", 
                "properties": {
                    "vm_id": {"type": "string", "description": "The VM ID to power on"}
                }, 
                "required": ["vm_id"]
            },
        ),
        Tool(
            name="power-off-vm",
            description="Power off a VM by its ID",
            inputSchema={
                "type": "object", 
                "properties": {
                    "vm_id": {"type": "string", "description": "The VM ID to power off"}
                }, 
                "required": ["vm_id"]
            },
        ),
        Tool(
            name="restart-vm",
            description="Restart a VM by its ID",
            inputSchema={
                "type": "object", 
                "properties": {
                    "vm_id": {"type": "string", "description": "The VM ID to restart"}
                }, 
                "required": ["vm_id"]
            },
        ),
        Tool(
            name="get-vm-info",
            description="Get detailed information about a specific VM",
            inputSchema={
                "type": "object", 
                "properties": {
                    "vm_id": {"type": "string", "description": "The VM ID to get info for"}
                }, 
                "required": ["vm_id"]
            },
        ),
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "get-all-vms":
        return [TextContent(type="text", text=get_all_vms_text())]
    elif name == "power-on-vm":
        vm_id = arguments.get("vm_id")
        if not vm_id:
            return [TextContent(type="text", text="❌ Error: vm_id parameter is required")]
        return [TextContent(type="text", text=power_on_vm_text(str(vm_id)))]
    elif name == "power-off-vm":
        vm_id = arguments.get("vm_id")
        if not vm_id:
            return [TextContent(type="text", text="❌ Error: vm_id parameter is required")]
        return [TextContent(type="text", text=power_off_vm_text(str(vm_id)))]
    elif name == "restart-vm":
        vm_id = arguments.get("vm_id")
        if not vm_id:
            return [TextContent(type="text", text="❌ Error: vm_id parameter is required")]
        return [TextContent(type="text", text=restart_vm_text(str(vm_id)))]
    elif name == "get-vm-info":
        vm_id = arguments.get("vm_id")
        if not vm_id:
            return [TextContent(type="text", text="❌ Error: vm_id parameter is required")]
        return [TextContent(type="text", text=get_vm_info_text(str(vm_id)))]
    else:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]

async def serve():
    """Start the MCP server."""
    options = server.create_initialization_options()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, options, raise_exceptions=True)

if __name__ == "__main__":
    asyncio.run(serve()) 