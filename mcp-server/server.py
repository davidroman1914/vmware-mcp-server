#!/usr/bin/env python3
"""
VMware vSphere MCP Server
Provides VM management capabilities through Model Context Protocol
"""

import os
import sys
from typing import Any

from mcp.server import Server, NotificationOptions
from mcp import types
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolResult,
    ListResourcesResult,
    ListToolsResult,
    ReadResourceResult,
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
)

# Add the scripts directory to the path so we can import our VMware utilities
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from list_vms import ListVM, get_unverified_session


class VMwareMCPServer:
    def __init__(self):
        self.server = Server("vmware-vsphere")
        self.vsphere_client = None
        self.setup_handlers()

    def setup_handlers(self):
        """Setup MCP server handlers"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> ListToolsResult:
            return ListToolsResult(
                tools=[
                    Tool(
                        name="list_vms",
                        description="List all VMs in vCenter server",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "server": {
                                    "type": "string",
                                    "description": "vCenter server address"
                                },
                                "username": {
                                    "type": "string", 
                                    "description": "Username for authentication"
                                },
                                "password": {
                                    "type": "string",
                                    "description": "Password for authentication"
                                },
                                "skip_verification": {
                                    "type": "boolean",
                                    "description": "Skip SSL certificate verification",
                                    "default": False
                                }
                            },
                            "required": ["server", "username", "password"]
                        }
                    ),
                    Tool(
                        name="get_vm_details",
                        description="Get detailed information about a specific VM",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "vm_id": {
                                    "type": "string",
                                    "description": "VM ID (e.g., vm-123)"
                                },
                                "server": {
                                    "type": "string",
                                    "description": "vCenter server address"
                                },
                                "username": {
                                    "type": "string",
                                    "description": "Username for authentication"
                                },
                                "password": {
                                    "type": "string",
                                    "description": "Password for authentication"
                                },
                                "skip_verification": {
                                    "type": "boolean",
                                    "description": "Skip SSL certificate verification",
                                    "default": False
                                }
                            },
                            "required": ["vm_id", "server", "username", "password"]
                        }
                    )
                ]
            )

        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict[str, Any]) -> CallToolResult:
            if name == "list_vms":
                return await self._handle_list_vms(arguments)
            elif name == "get_vm_details":
                return await self._handle_get_vm_details(arguments)
            else:
                raise ValueError(f"Unknown tool: {name}")

        @self.server.list_resources()
        async def handle_list_resources() -> ListResourcesResult:
            return ListResourcesResult(
                resources=[
                    Resource(
                        uri="vmware://vms",
                        name="VMware VMs",
                        description="List of all VMs in vCenter",
                        mimeType="application/json"
                    )
                ]
            )

        @self.server.read_resource()
        async def handle_read_resource(uri: str) -> ReadResourceResult:
            if uri == "vmware://vms":
                # This would require authentication, so we'll return a placeholder
                return ReadResourceResult(
                    contents=[
                        TextContent(
                            type="text",
                            text="VM list resource - use list_vms tool to get actual data"
                        )
                    ]
                )
            else:
                raise ValueError(f"Unknown resource: {uri}")

    async def _handle_list_vms(self, arguments: dict[str, Any]) -> CallToolResult:
        """Handle list_vms tool call"""
        try:
            # Get credentials from arguments or environment variables
            server = arguments.get("server") or os.getenv("VCENTER_SERVER")
            username = arguments.get("username") or os.getenv("VCENTER_USERNAME")
            password = arguments.get("password") or os.getenv("VCENTER_PASSWORD")
            skip_verification = arguments.get("skip_verification", 
                os.getenv("VCENTER_SKIP_VERIFICATION", "false").lower() == "true")

            if not server or not username or not password:
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text="Error: Missing vCenter credentials. Please provide server, username, and password as arguments or set VCENTER_SERVER, VCENTER_USERNAME, and VCENTER_PASSWORD environment variables."
                        )
                    ]
                )

            # Create ListVM instance
            list_vm = ListVM(
                server=server,
                username=username,
                password=password,
                skip_verification=skip_verification
            )

            # Get VM list
            vms = list_vm.run()
            
            if vms is None:
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text="Error: Failed to retrieve VM list"
                        )
                    ]
                )

            # Format the output
            vm_list = []
            for vm in vms:
                vm_info = {
                    "id": vm.vm,
                    "name": vm.name,
                    "power_state": vm.power_state.string,
                    "cpu_count": vm.cpu_count,
                    "memory_size_mib": vm.memory_size_MiB
                }
                vm_list.append(vm_info)

            # Create formatted output
            output_lines = [
                "VMware vCenter VM List",
                "=" * 50,
                f"Total VMs found: {len(vm_list)}",
                ""
            ]

            for vm in vm_list:
                output_lines.append(
                    f"• {vm['name']} (ID: {vm['id']})"
                )
                output_lines.append(
                    f"  Power State: {vm['power_state']}, "
                    f"CPU: {vm['cpu_count']}, "
                    f"Memory: {vm['memory_size_mib']} MiB"
                )
                output_lines.append("")

            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text="\n".join(output_lines)
                    )
                ]
            )

        except Exception as e:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"Error listing VMs: {str(e)}"
                    )
                ]
            )

    async def _handle_get_vm_details(self, arguments: dict[str, Any]) -> CallToolResult:
        """Handle get_vm_details tool call"""
        try:
            vm_id = arguments["vm_id"]
            # Get credentials from arguments or environment variables
            server = arguments.get("server") or os.getenv("VCENTER_SERVER")
            username = arguments.get("username") or os.getenv("VCENTER_USERNAME")
            password = arguments.get("password") or os.getenv("VCENTER_PASSWORD")
            skip_verification = arguments.get("skip_verification", 
                os.getenv("VCENTER_SKIP_VERIFICATION", "false").lower() == "true")

            if not server or not username or not password:
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text="Error: Missing vCenter credentials. Please provide server, username, and password as arguments or set VCENTER_SERVER, VCENTER_USERNAME, and VCENTER_PASSWORD environment variables."
                        )
                    ]
                )

            # Create ListVM instance
            list_vm = ListVM(
                server=server,
                username=username,
                password=password,
                skip_verification=skip_verification
            )

            # Get VM list and find the specific VM
            vms = list_vm.run()
            
            if vms is None:
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text="Error: Failed to retrieve VM list"
                        )
                    ]
                )

            # Find the specific VM
            target_vm = None
            for vm in vms:
                if vm.vm == vm_id:
                    target_vm = vm
                    break

            if target_vm is None:
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=f"Error: VM with ID '{vm_id}' not found"
                        )
                    ]
                )

            # Format the VM details
            output_lines = [
                f"VM Details for {target_vm.name}",
                "=" * 50,
                f"VM ID: {target_vm.vm}",
                f"Name: {target_vm.name}",
                f"Power State: {target_vm.power_state.string}",
                f"CPU Count: {target_vm.cpu_count}",
                f"Memory Size: {target_vm.memory_size_MiB} MiB"
            ]

            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text="\n".join(output_lines)
                    )
                ]
            )

        except Exception as e:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"Error getting VM details: {str(e)}"
                    )
                ]
            )


async def main():
    """Main entry point for the MCP server"""
    server_instance = VMwareMCPServer()
    
    async with stdio_server() as (read_stream, write_stream):
        await server_instance.server.run(
            read_stream,
            write_stream,
            server_instance.server.get_capabilities(
                notification_options=NotificationOptions(),
                experimental_capabilities={}
            )
        )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main()) 