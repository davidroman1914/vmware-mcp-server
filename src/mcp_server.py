"""
MCP Server implementation for ESXi management.
"""
import logging
from typing import Any, Dict, List, Optional
import os

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListResourcesRequest,
    ListResourcesResult,
    ListToolsRequest,
    ListToolsResult,
    Resource,
    TextContent,
    Tool,
)

from .config import Config
from .vmware import VMwareManager, VMInfo, VMPerformance


class ESXiMCPServer:
    """ESXi MCP Server implementation."""
    
    def __init__(self, config: Config):
        self.config = config
        self.vmware_manager: Optional[VMwareManager] = None
        self.authenticated = False
        
        # Initialize VMware manager
        try:
            self.vmware_manager = VMwareManager(config.vmware)
            logging.info("VMware manager initialized successfully")
        except Exception as e:
            logging.error(f"Failed to initialize VMware manager: {e}")
            raise
    
    def _check_auth(self, request: CallToolRequest) -> bool:
        """Check API key authentication."""
        if not self.config.server.api_key:
            return True  # No API key configured, allow all requests
        
        auth_header = request.arguments.get("api_key")
        if not auth_header:
            return False
        
        return auth_header == self.config.server.api_key
    
    async def list_tools(self, request: ListToolsRequest) -> ListToolsResult:
        """List available tools."""
        tools = [
            Tool(
                name="authenticate",
                description="Authenticate with API key",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "api_key": {
                            "type": "string",
                            "description": "API key for authentication"
                        }
                    },
                    "required": ["api_key"]
                }
            ),
            Tool(
                name="list_vms",
                description="List all virtual machines",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "api_key": {
                            "type": "string",
                            "description": "API key for authentication"
                        }
                    },
                    "required": ["api_key"]
                }
            ),
            Tool(
                name="create_vm",
                description="Create a new virtual machine",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "api_key": {
                            "type": "string",
                            "description": "API key for authentication"
                        },
                        "name": {
                            "type": "string",
                            "description": "Name of the virtual machine"
                        },
                        "cpu": {
                            "type": "integer",
                            "description": "Number of CPUs"
                        },
                        "memory": {
                            "type": "integer",
                            "description": "Memory in MB"
                        },
                        "datastore": {
                            "type": "string",
                            "description": "Datastore name (optional)"
                        },
                        "network": {
                            "type": "string",
                            "description": "Network name (optional)"
                        }
                    },
                    "required": ["api_key", "name", "cpu", "memory"]
                }
            ),
            Tool(
                name="clone_vm",
                description="Clone a virtual machine from template",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "api_key": {
                            "type": "string",
                            "description": "API key for authentication"
                        },
                        "template_name": {
                            "type": "string",
                            "description": "Name of the template VM"
                        },
                        "new_name": {
                            "type": "string",
                            "description": "Name for the new VM"
                        }
                    },
                    "required": ["api_key", "template_name", "new_name"]
                }
            ),
            Tool(
                name="delete_vm",
                description="Delete a virtual machine",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "api_key": {
                            "type": "string",
                            "description": "API key for authentication"
                        },
                        "name": {
                            "type": "string",
                            "description": "Name of the virtual machine"
                        }
                    },
                    "required": ["api_key", "name"]
                }
            ),
            Tool(
                name="power_on",
                description="Power on a virtual machine",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "api_key": {
                            "type": "string",
                            "description": "API key for authentication"
                        },
                        "name": {
                            "type": "string",
                            "description": "Name of the virtual machine"
                        }
                    },
                    "required": ["api_key", "name"]
                }
            ),
            Tool(
                name="power_off",
                description="Power off a virtual machine",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "api_key": {
                            "type": "string",
                            "description": "API key for authentication"
                        },
                        "name": {
                            "type": "string",
                            "description": "Name of the virtual machine"
                        }
                    },
                    "required": ["api_key", "name"]
                }
            ),
            Tool(
                name="get_vm_guest_info",
                description="Get detailed guest information for a virtual machine",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "api_key": {
                            "type": "string",
                            "description": "API key for authentication"
                        },
                        "name": {
                            "type": "string",
                            "description": "Name of the virtual machine"
                        }
                    },
                    "required": ["api_key", "name"]
                }
            ),
            Tool(
                name="test_guest_info",
                description="Test guest info functionality and connection",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "api_key": {
                            "type": "string",
                            "description": "API key for authentication"
                        }
                    },
                    "required": ["api_key"]
                }
            ),
            Tool(
                name="create_vm_from_template",
                description="Create a VM from template with customization (similar to Ansible vmware_guest)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Name of the new VM"
                        },
                        "template_name": {
                            "type": "string", 
                            "description": "Name of the template to clone from"
                        },
                        "cluster": {
                            "type": "string",
                            "description": "Target cluster name (optional)"
                        },
                        "folder": {
                            "type": "string",
                            "description": "Target folder path, e.g., '/vm/' (optional)"
                        },
                        "disk_spec": {
                            "type": "array",
                            "description": "Disk configuration array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "type": {"type": "string", "default": "SATA"},
                                    "name": {"type": "string"},
                                    "size_gb": {"type": "integer", "default": 10}
                                }
                            }
                        },
                        "hardware_spec": {
                            "type": "object",
                            "description": "Hardware configuration",
                            "properties": {
                                "cpu_count": {"type": "integer", "default": 1},
                                "memory_mb": {"type": "integer", "default": 1024}
                            }
                        },
                        "network_spec": {
                            "type": "array",
                            "description": "Network configuration array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "device_type": {"type": "string", "default": "VMXNET3"},
                                    "network_id": {"type": "string"},
                                    "ip": {"type": "string"},
                                    "netmask": {"type": "string"},
                                    "gateway": {"type": "string"}
                                }
                            }
                        },
                        "customization_spec": {
                            "type": "object",
                            "description": "Guest customization settings (hostname, domain, etc.)"
                        },
                        "wait_for_ip": {
                            "type": "boolean",
                            "description": "Whether to wait for IP address",
                            "default": False
                        },
                        "wait_timeout": {
                            "type": "integer",
                            "description": "Timeout for IP address wait in seconds",
                            "default": 300
                        }
                    },
                    "required": ["name", "template_name"]
                }
            ),
        ]
        
        return ListToolsResult(tools=tools)
    
    async def call_tool(self, request: CallToolRequest) -> CallToolResult:
        """Handle tool calls."""
        if not self._check_auth(request):
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text="Authentication failed. Please provide a valid API key."
                    )
                ]
            )
        
        try:
            if request.name == "authenticate":
                return await self._handle_authenticate(request)
            elif request.name == "list_vms":
                return await self._handle_list_vms(request)
            elif request.name == "create_vm":
                return await self._handle_create_vm(request)
            elif request.name == "clone_vm":
                return await self._handle_clone_vm(request)
            elif request.name == "delete_vm":
                return await self._handle_delete_vm(request)
            elif request.name == "power_on":
                return await self._handle_power_on(request)
            elif request.name == "power_off":
                return await self._handle_power_off(request)
            elif request.name == "get_vm_guest_info":
                return await self._handle_get_vm_guest_info(request)
            elif request.name == "test_guest_info":
                return await self._handle_test_guest_info(request)
            elif request.name == "create_vm_from_template":
                try:
                    vm_id = self.vmware_manager.create_vm_from_template(
                        name=request.arguments["name"],
                        template_name=request.arguments["template_name"],
                        cluster=request.arguments.get("cluster"),
                        folder=request.arguments.get("folder"),
                        disk_spec=request.arguments.get("disk_spec"),
                        hardware_spec=request.arguments.get("hardware_spec"),
                        network_spec=request.arguments.get("network_spec"),
                        customization_spec=request.arguments.get("customization_spec"),
                        wait_for_ip=request.arguments.get("wait_for_ip", False),
                        wait_timeout=request.arguments.get("wait_timeout", 300)
                    )
                    return CallToolResult(
                        content=[
                            TextContent(
                                type="text",
                                text=f"Successfully created VM '{request.arguments['name']}' from template '{request.arguments['template_name']}' with ID: {vm_id}"
                            )
                        ]
                    )
                except Exception as e:
                    return CallToolResult(
                        content=[
                            TextContent(
                                type="text",
                                text=f"Failed to create VM from template: {str(e)}"
                            )
                        ]
                    )
            else:
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=f"Unknown tool: {request.name}"
                        )
                    ]
                )
        except Exception as e:
            logging.error(f"Error in tool call {request.name}: {e}")
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"Error: {str(e)}"
                    )
                ]
            )
    
    async def _handle_authenticate(self, request: CallToolRequest) -> CallToolResult:
        """Handle authentication."""
        self.authenticated = True
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text="Authentication successful"
                )
            ]
        )
    
    async def _handle_list_vms(self, request: CallToolRequest) -> CallToolResult:
        """Handle list VMs tool."""
        vms = self.vmware_manager.list_vms()
        
        if not vms:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text="No virtual machines found"
                    )
                ]
            )
        
        vm_list = []
        for vm in vms:
            vm_info = f"Name: {vm.name}, Power: {vm.power_state}, CPUs: {vm.cpu_count}, Memory: {vm.memory_mb}MB, Tools: {vm.tools_status}"
            vm_list.append(vm_info)
        
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=f"Found {len(vms)} virtual machines:\n" + "\n".join(vm_list)
                )
            ]
        )
    
    async def _handle_create_vm(self, request: CallToolRequest) -> CallToolResult:
        """Handle create VM tool."""
        name = request.arguments["name"]
        cpu = request.arguments["cpu"]
        memory = request.arguments["memory"]
        datastore = request.arguments.get("datastore")
        network = request.arguments.get("network")
        
        result = self.vmware_manager.create_vm(name, cpu, memory, datastore, network)
        
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=result
                )
            ]
        )
    
    async def _handle_clone_vm(self, request: CallToolRequest) -> CallToolResult:
        """Handle clone VM tool."""
        template_name = request.arguments["template_name"]
        new_name = request.arguments["new_name"]
        
        result = self.vmware_manager.clone_vm(template_name, new_name)
        
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=result
                )
            ]
        )
    
    async def _handle_delete_vm(self, request: CallToolRequest) -> CallToolResult:
        """Handle delete VM tool."""
        name = request.arguments["name"]
        
        result = self.vmware_manager.delete_vm(name)
        
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=result
                )
            ]
        )
    
    async def _handle_power_on(self, request: CallToolRequest) -> CallToolResult:
        """Handle power on VM tool."""
        name = request.arguments["name"]
        
        result = self.vmware_manager.power_on_vm(name)
        
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=result
                )
            ]
        )
    
    async def _handle_power_off(self, request: CallToolRequest) -> CallToolResult:
        """Handle power off VM tool."""
        name = request.arguments["name"]
        
        result = self.vmware_manager.power_off_vm(name)
        
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=result
                )
            ]
        )
    
    async def _handle_get_vm_guest_info(self, request: CallToolRequest) -> CallToolResult:
        """Handle get VM guest info tool."""
        name = request.arguments["name"]
        
        guest_info = self.vmware_manager.get_vm_guest_info(name)
        
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=guest_info
                )
            ]
        )
    
    async def _handle_test_guest_info(self, request: CallToolRequest) -> CallToolResult:
        """Handle test guest info tool."""
        try:
            # Test the guest info functionality
            test_results = self.vmware_manager.test_guest_info_connection()
            
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"Guest Info Test Results: {test_results}"
                    )
                ]
            )
        except Exception as e:
            logging.error(f"Error in test_guest_info: {e}")
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"Error testing guest info: {str(e)}"
                    )
                ]
            )
    
    async def list_resources(self, request: ListResourcesRequest) -> ListResourcesResult:
        """List available resources."""
        if not self.vmware_manager:
            return ListResourcesResult(resources=[])
        
        try:
            vms = self.vmware_manager.list_vms()
            resources = []
            
            for vm in vms:
                # Get performance data for the VM
                try:
                    performance = self.vmware_manager.get_vm_performance(vm.name)
                    performance_text = (
                        f"CPU: {performance.cpu_usage_mhz} MHz, "
                        f"Memory: {performance.memory_usage_mb} MB, "
                        f"Storage: {performance.storage_usage_gb} GB"
                    )
                    if performance.network_transmit_kbps is not None:
                        performance_text += f", Network TX: {performance.network_transmit_kbps} KB/s"
                    if performance.network_receive_kbps is not None:
                        performance_text += f", Network RX: {performance.network_receive_kbps} KB/s"
                except Exception as e:
                    performance_text = f"Performance data unavailable: {e}"
                
                resource = Resource(
                    uri=f"vm://{vm.name}",
                    name=vm.name,
                    description=f"Virtual Machine: {vm.name}",
                    mimeType="application/json",
                    content=[
                        TextContent(
                            type="text",
                            text=(
                                f"Name: {vm.name}\n"
                                f"Power State: {vm.power_state}\n"
                                f"CPUs: {vm.cpu_count}\n"
                                f"Memory: {vm.memory_mb} MB\n"
                                f"Guest OS: {vm.guest_id}\n"
                                f"Tools Status: {vm.tools_status}\n"
                                f"Performance: {performance_text}"
                            )
                        )
                    ]
                )
                resources.append(resource)
            
            return ListResourcesResult(resources=resources)
        except Exception as e:
            logging.error(f"Error listing resources: {e}")
            return ListResourcesResult(resources=[])
    
    def cleanup(self):
        """Cleanup resources."""
        if self.vmware_manager:
            self.vmware_manager.disconnect()


async def create_server(config: Config) -> Server:
    """Create and configure the MCP server."""
    logging.info("=== CREATE SERVER DEBUG ===")
    logging.info("Creating ESXi MCP server instance...")
    esxi_server = ESXiMCPServer(config)
    logging.info("ESXi MCP server instance created successfully")
    
    logging.info("Creating MCP Server object...")
    server = Server("vmware-mcp-server")
    logging.info("MCP Server object created successfully")
    logging.info(f"Server object type: {type(server)}")
    logging.info(f"Server object dir: {dir(server)}")
    
    logging.info("Registering list_tools handler...")
    try:
        @server.list_tools()
        async def handle_list_tools(request: ListToolsRequest) -> ListToolsResult:
            logging.debug("list_tools handler called")
            logging.debug(f"list_tools request: {request}")
            result = await esxi_server.list_tools(request)
            logging.debug(f"list_tools result: {result}")
            return result
        logging.info("list_tools handler registered successfully")
    except Exception as e:
        logging.error(f"Failed to register list_tools handler: {e}")
        logging.error(f"list_tools error traceback: {traceback.format_exc()}")
        raise
    
    logging.info("Registering call_tool handler...")
    try:
        @server.call_tool()
        async def handle_call_tool(request: CallToolRequest) -> CallToolResult:
            logging.debug("call_tool handler called")
            logging.debug(f"call_tool request: {request}")
            result = await esxi_server.call_tool(request)
            logging.debug(f"call_tool result: {result}")
            return result
        logging.info("call_tool handler registered successfully")
    except Exception as e:
        logging.error(f"Failed to register call_tool handler: {e}")
        logging.error(f"call_tool error traceback: {traceback.format_exc()}")
        raise
    
    logging.info("Registering list_resources handler...")
    try:
        @server.list_resources()
        async def handle_list_resources(request: ListResourcesRequest) -> ListResourcesResult:
            logging.debug("list_resources handler called")
            logging.debug(f"list_resources request: {request}")
            logging.debug(f"list_resources request type: {type(request)}")
            logging.debug(f"list_resources request args: {request.__dict__ if hasattr(request, '__dict__') else 'No __dict__'}")
            result = await esxi_server.list_resources(request)
            logging.debug(f"list_resources result: {result}")
            return result
        logging.info("list_resources handler registered successfully")
        logging.info(f"handle_list_resources function signature: {handle_list_resources.__code__.co_varnames}")
    except Exception as e:
        logging.error(f"Failed to register list_resources handler: {e}")
        logging.error(f"list_resources error traceback: {traceback.format_exc()}")
        raise
    
    logging.info("All MCP server handlers registered successfully")
    logging.info(f"Final server object: {server}")
    return server


async def run_server(config: Config) -> None:
    """Run the MCP server with proper initialization."""
    from mcp.server.stdio import stdio_server
    from mcp.server.lowlevel import NotificationOptions
    from mcp.server.models import InitializationOptions
    import traceback
    import sys
    
    logging.info("=== MCP SERVER STARTUP DEBUG ===")
    logging.info(f"Python version: {sys.version}")
    logging.info(f"Working directory: {os.getcwd()}")
    
    try:
        logging.info("Creating MCP server instance...")
        server = await create_server(config)
        logging.info("MCP server instance created successfully")
        
        # Set up proper initialization options
        logging.info("Setting up initialization options...")
        init_options = InitializationOptions(
            server_name="vmware-mcp-server",
            server_version="1.1.0",
            capabilities=server.get_capabilities(
                notification_options=NotificationOptions(),
                experimental_capabilities={},
            ),
        )
        logging.info("Initialization options configured successfully")
        logging.info(f"Server capabilities: {server.get_capabilities(NotificationOptions(), {})}")
        
        # Run the server using stdio transport with proper initialization
        try:
            logging.info("Starting stdio server with low-level API...")
            logging.info("About to enter stdio_server context manager...")
            async with stdio_server() as (read_stream, write_stream):
                logging.info("stdio streams acquired successfully")
                logging.info(f"read_stream type: {type(read_stream)}")
                logging.info(f"write_stream type: {type(write_stream)}")
                logging.info("About to call server.run()...")
                await server.run(
                    read_stream,
                    write_stream,
                    init_options,
                )
                logging.info("Server run completed successfully")
        except Exception as e:
            logging.error(f"Failed to run server: {e}")
            logging.error(f"Error type: {type(e).__name__}")
            logging.error(f"Error args: {e.args}")
            logging.error(f"Full error traceback: {traceback.format_exc()}")
            
            # Try to get more details about the error
            if hasattr(e, '__cause__') and e.__cause__:
                logging.error(f"Caused by: {e.__cause__}")
                logging.error(f"Cause traceback: {traceback.format_exc()}")
            
            raise
    except Exception as outer_e:
        logging.error(f"Outer exception during server startup: {outer_e}")
        logging.error(f"Outer error type: {type(outer_e).__name__}")
        logging.error(f"Outer error traceback: {traceback.format_exc()}")
        raise 