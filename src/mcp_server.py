"""
Minimal MCP Server for VMware ESXi management.
"""
import asyncio
import logging
import sys
from typing import Optional, List, Dict, Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest, CallToolResult, ListToolsRequest, ListToolsResult,
    Tool, TextContent, ListResourcesRequest, ListResourcesResult, Resource
)

from .config import load_config
from .vmware import VMwareManager, VMwareConnectionError


class VMwareMCPServer:
    """Minimal VMware MCP Server with basic functionality."""
    
    def __init__(self):
        self.server = Server("vmware-mcp-server")
        self.vmware_manager: Optional[VMwareManager] = None
        self._setup_server()
    
    def _setup_server(self):
        """Set up the MCP server with basic tools."""
        
        @self.server.list_tools()
        async def handle_list_tools() -> ListToolsResult:
            return ListToolsResult(
                tools=[
                    Tool(
                        name="get_info",
                        description="Get basic information about the VMware environment and connection status"
                    ),
                    Tool(
                        name="list_vms", 
                        description="List all virtual machines in the VMware environment"
                    )
                ]
            )
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
            if name == "get_info":
                return await self._handle_get_info()
            elif name == "list_vms":
                return await self._handle_list_vms()
            else:
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Unknown tool: {name}")]
                )
        
        @self.server.list_resources()
        async def handle_list_resources() -> ListResourcesResult:
            return await self._handle_list_resources()
    
    async def _handle_get_info(self) -> CallToolResult:
        """Handle get_info tool call."""
        try:
            if not self.vmware_manager:
                # Try to connect
                try:
                    config = load_config()
                    self.vmware_manager = VMwareManager(config)
                    info = self.vmware_manager.get_info()
                except Exception as e:
                    info = {
                        'status': 'connection_failed',
                        'message': f'Failed to connect to VMware: {str(e)}'
                    }
            else:
                info = self.vmware_manager.get_info()
            
            # Format the response
            if info['status'] == 'connected':
                result = f"✅ {info['message']}\nTotal VMs: {info.get('total_vms', 0)}"
            elif info['status'] == 'disconnected':
                result = f"❌ {info['message']}"
            else:
                result = f"⚠️ {info['message']}"
            
            return CallToolResult(content=[TextContent(type="text", text=result)])
            
        except Exception as e:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Error getting info: {str(e)}")]
            )
    
    async def _handle_list_vms(self) -> CallToolResult:
        """Handle list_vms tool call."""
        try:
            if not self.vmware_manager:
                return CallToolResult(
                    content=[TextContent(type="text", text="Not connected to VMware. Use get_info tool first.")]
                )
            
            vms = self.vmware_manager.list_vms()
            
            if not vms:
                return CallToolResult(
                    content=[TextContent(type="text", text="No virtual machines found in the VMware environment.")]
                )
            
            # Format VM list
            vm_details = []
            for vm in vms:
                vm_details.append(
                    f"• {vm['name']} (Power: {vm['power_state']}, CPUs: {vm['cpu_count']}, Memory: {vm['memory_mb']}MB)"
                )
            
            result = f"Found {len(vms)} virtual machine(s):\n\n" + "\n".join(vm_details)
            return CallToolResult(content=[TextContent(type="text", text=result)])
            
        except Exception as e:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Error listing VMs: {str(e)}")]
            )
    
    async def _handle_list_resources(self) -> ListResourcesResult:
        """Handle list_resources request."""
        try:
            if not self.vmware_manager:
                return ListResourcesResult(
                    resources=[Resource(id="vmware-server", name="VMware MCP Server", status="disconnected", uri="http://localhost/")],
                    nextCursor=None
                )
            
            vms = self.vmware_manager.list_vms()
            resources = [
                Resource(
                    id=vm['name'],
                    name=vm['name'],
                    status=vm['power_state'].lower() if vm['power_state'] else "unknown",
                    uri=f"http://localhost/vm/{vm['name']}"
                ) for vm in vms
            ]
            return ListResourcesResult(resources=resources, nextCursor=None)
            
        except Exception as e:
            logging.error(f"Error listing resources: {e}")
            return ListResourcesResult(
                resources=[Resource(id="error", name="Error loading VMs", status="error", uri="http://localhost/")],
                nextCursor=None
            )
    
    async def run(self):
        """Run the MCP server with proper initialization."""
        try:
            # Simple approach: just use stdio_server directly
            async with stdio_server() as (read_stream, write_stream):
                # Use the server's built-in method to create initialization options
                init_options = self.server.create_initialization_options()
                
                # Run the server
                await self.server.run(read_stream, write_stream, init_options)
                
        except Exception as e:
            logging.error(f"Server error: {e}")
            import traceback
            logging.error(f"Traceback: {traceback.format_exc()}")
            sys.exit(1)
    
    def cleanup(self):
        """Clean up resources."""
        if self.vmware_manager:
            self.vmware_manager.disconnect()


async def run_server():
    """Simple server runner function."""
    server = VMwareMCPServer()
    try:
        await server.run()
    except KeyboardInterrupt:
        logging.info("Server stopped by user")
    except Exception as e:
        logging.error(f"Server error: {e}")
        sys.exit(1)
    finally:
        server.cleanup()
