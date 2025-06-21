import logging
import os
import traceback
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListResourcesRequest,
    ListResourcesResult,
    ListToolsRequest,
    ListToolsResult,
    TextContent,
    Tool,
)

from .config import Config
from .vmware import VMwareManager, VMInfo


class Resource(BaseModel):
    id: str
    name: str
    status: str


class ListResourcesResult(BaseModel):
    resources: List[Resource]
    nextCursor: Optional[str] = None


class ESXiMCPServer:
    def __init__(self, config: Config):
        self.config = config
        self.vmware_manager: Optional[VMwareManager] = None
        self.authenticated = False
        try:
            self.vmware_manager = VMwareManager(config.vmware)
            logging.info("VMware manager initialized successfully")
        except Exception as e:
            logging.error(f"Failed to initialize VMware manager: {e}")
            # Don't raise - continue without VMware connection

    def _check_auth(self, request: CallToolRequest) -> bool:
        if not self.config.server.api_key:
            return True
        auth_header = request.arguments.get("api_key")
        return auth_header == self.config.server.api_key if auth_header else False

    async def list_tools(self, request: ListToolsRequest) -> ListToolsResult:
        tools = [
            Tool(
                name="get_info",
                description="Get basic VMware environment information",
                inputSchema={
                    "type": "object",
                    "properties": {"api_key": {"type": "string", "description": "API key for authentication"}},
                    "required": ["api_key"]
                }
            ),
            Tool(
                name="list_vms",
                description="List all virtual machines",
                inputSchema={
                    "type": "object",
                    "properties": {"api_key": {"type": "string", "description": "API key for authentication"}},
                    "required": ["api_key"]
                }
            )
        ]
        return ListToolsResult(tools=tools)

    async def call_tool(self, request: CallToolRequest) -> CallToolResult:
        if not self._check_auth(request):
            return CallToolResult(content=[TextContent(type="text", text="Authentication failed.")])
        
        try:
            if request.name == "get_info":
                return await self._handle_get_info(request)
            elif request.name == "list_vms":
                return await self._handle_list_vms(request)
            else:
                return CallToolResult(content=[TextContent(type="text", text=f"Unknown tool: {request.name}")])
        except Exception as e:
            logging.error(f"Error in tool call {request.name}: {e}")
            return CallToolResult(content=[TextContent(type="text", text=f"Error: {str(e)}")])

    async def _handle_get_info(self, request: CallToolRequest) -> CallToolResult:
        """Get basic VMware environment information."""
        try:
            if not self.vmware_manager:
                return CallToolResult(content=[
                    TextContent(type="text", text="VMware MCP Server is running but not connected to vCenter/ESXi.\n\nAvailable tools:\n- get_info: Get basic information\n- list_vms: List virtual machines\n\nTo connect, provide valid VMware credentials in your configuration.")
                ])
            
            # Try to get basic info
            vms = self.vmware_manager.list_vms()
            vm_count = len(vms) if vms else 0
            
            info = f"""VMware MCP Server Information:
            
✅ Connected to VMware environment
📊 Virtual Machines: {vm_count}
🔧 Available Tools: get_info, list_vms

Server Status: Running
Version: 1.1.0
Environment: VMware vSphere/ESXi

To manage VMs, use the list_vms tool or ask for specific operations."""
            
            return CallToolResult(content=[TextContent(type="text", text=info)])
            
        except Exception as e:
            return CallToolResult(content=[
                TextContent(type="text", text=f"VMware MCP Server is running but encountered an error: {str(e)}\n\nThis is normal if VMware credentials are not configured or the connection failed.")
            ])

    async def _handle_list_vms(self, request: CallToolRequest) -> CallToolResult:
        if not self.vmware_manager:
            return CallToolResult(content=[TextContent(type="text", text="Not connected to VMware environment. Use get_info tool for more details.")])
        
        try:
            vms = self.vmware_manager.list_vms()
            if not vms:
                return CallToolResult(content=[TextContent(type="text", text="No virtual machines found in the VMware environment.")])
            
            vm_details = []
            for vm in vms:
                vm_details.append(f"• {vm.name} (Power: {vm.power_state}, CPUs: {vm.cpu_count}, Memory: {vm.memory_mb}MB)")
            
            result = f"Found {len(vms)} virtual machine(s):\n\n" + "\n".join(vm_details)
            return CallToolResult(content=[TextContent(type="text", text=result)])
        except Exception as e:
            return CallToolResult(content=[TextContent(type="text", text=f"Error listing VMs: {str(e)}")])

    async def list_resources(self, request: Optional[ListResourcesRequest] = None) -> ListResourcesResult:
        try:
            if not self.vmware_manager:
                return ListResourcesResult(
                    resources=[Resource(id="vmware-server", name="VMware MCP Server", status="running")],
                    nextCursor=None
                )

            vms: List[VMInfo] = self.vmware_manager.list_vms()
            resources = [
                Resource(
                    id=vm.name,
                    name=vm.name,
                    status=vm.power_state.lower() if vm.power_state else "unknown"
                ) for vm in vms
            ]
            return ListResourcesResult(resources=resources, nextCursor=None)
        except Exception as e:
            logging.error(f"Error listing resources: {e}")
            return ListResourcesResult(
                resources=[Resource(id="error", name="Error loading VMs", status="error")],
                nextCursor=None
            )

    def cleanup(self):
        if self.vmware_manager:
            self.vmware_manager.disconnect()


async def create_server(config: Config) -> Server:
    esxi_server = ESXiMCPServer(config)
    server = Server("vmware-mcp-server")

    @server.list_tools()
    async def handle_list_tools(request: ListToolsRequest) -> ListToolsResult:
        return await esxi_server.list_tools(request)

    @server.call_tool()
    async def handle_call_tool(request: CallToolRequest) -> CallToolResult:
        return await esxi_server.call_tool(request)

    @server.list_resources()
    async def handle_list_resources() -> ListResourcesResult:
        return await esxi_server.list_resources()

    return server


async def run_server(config: Config) -> None:
    from mcp.server.lowlevel import NotificationOptions
    from mcp.server.models import InitializationOptions

    try:
        server = await create_server(config)
        init_options = InitializationOptions(
            server_name="vmware-mcp-server",
            server_version="1.1.0",
            capabilities=server.get_capabilities(NotificationOptions(), {})
        )
        async with stdio_server() as (read_stream, write_stream):
            await server.run(read_stream, write_stream, init_options)
    except Exception as e:
        logging.error(f"Failed to start server: {e}\n{traceback.format_exc()}")
        raise
