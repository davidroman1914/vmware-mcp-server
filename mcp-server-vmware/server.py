#!/usr/bin/env python3
"""
MCP Server for VMware vCenter using only vmware-vcenter package
Follows the same pattern as the main mcp-server folder
"""

import os
import asyncio
import requests
import urllib3
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from vmware.vapi.vsphere.client import create_vsphere_client

server = Server("vmware-vm-server")

def get_vsphere_client():
    """Create vSphere client with environment variables."""
    host = os.getenv("VCENTER_HOST")
    user = os.getenv("VCENTER_USER")
    pwd = os.getenv("VCENTER_PASSWORD")
    insecure = os.getenv("VCENTER_INSECURE", "false").lower() == "true"

    if not all([host, user, pwd]):
        missing = [k for k, v in [("VCENTER_HOST", host), ("VCENTER_USER", user), ("VCENTER_PASSWORD", pwd)] if not v]
        raise EnvironmentError(f"Missing environment variables: {', '.join(missing)}")

    # Create session with SSL handling
    session = requests.Session()
    session.verify = not insecure
    
    # Disable SSL warnings for demo (not recommended in production)
    if insecure:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    # Create vSphere client (exactly as shown in PyPI docs)
    return create_vsphere_client(
        server=host, 
        username=user, 
        password=pwd, 
        session=session
    )

def get_all_vms_text():
    """Get all VMs and return formatted text."""
    try:
        client = get_vsphere_client()
        vms = client.vcenter.VM.list()
        
        output = [f"📋 **Found {len(vms)} VMs in vCenter:**"]
        
        for vm in vms:
            output.append(f"\n- **{vm.name}** (ID: {vm.vm})")
            output.append(f"  • Power State: {vm.power_state}")
            output.append(f"  • CPU Count: {vm.cpu_count}")
            output.append(f"  • Memory: {vm.memory_size_mib} MB")
        
        return "\n".join(output)
        
    except Exception as e:
        return f"❌ Error getting VMs: {str(e)}"

@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="get-all-vms",
            description="Get all VMs from vCenter using vmware-vcenter package",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "get-all-vms":
        return [TextContent(type="text", text=get_all_vms_text())]
    else:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]

async def serve():
    """Start the MCP server."""
    options = server.create_initialization_options()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, options, raise_exceptions=True)

if __name__ == "__main__":
    asyncio.run(serve()) 