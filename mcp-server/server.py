import os
import asyncio
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from list_vm import list_vms_text
from get_vm_info import get_vm_info_text

server = Server("vmware-mcp-server")

@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="list-vms",
            description="List all VMs in vCenter",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        Tool(
            name="get-vm-info",
            description="Get info about a VM by ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "vm_id": {"type": "string", "description": "The ID of the VM to fetch"}
                },
                "required": ["vm_id"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "list-vms":
        return [TextContent(type="text", text=list_vms_text())]
    elif name == "get-vm-info":
        vm_id = arguments.get("vm_id")
        if not vm_id:
            return [TextContent(type="text", text="Missing required argument: vm_id")]
        return [TextContent(type="text", text=get_vm_info_text(vm_id))]
    else:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]

async def serve():
    options = server.create_initialization_options()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, options, raise_exceptions=True)

if __name__ == "__main__":
    asyncio.run(serve())

