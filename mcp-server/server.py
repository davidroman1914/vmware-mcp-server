import os
import asyncio
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from list_vm import list_vms_text
from get_vm_info import get_vm_info_text
from power_vm import power_on_vm, power_off_vm, restart_vm, get_power_state_text
from vm_management import deploy_vm_from_template, create_template_from_vm, clone_vm

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
            description="Get detailed information about a VM by ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "vm_id": {"type": "string", "description": "The ID of the VM to fetch"}
                },
                "required": ["vm_id"]
            }
        ),
        Tool(
            name="power-on-vm",
            description="Power on a VM if it's not already powered on",
            inputSchema={
                "type": "object",
                "properties": {
                    "vm_id": {"type": "string", "description": "The ID of the VM to power on"}
                },
                "required": ["vm_id"]
            }
        ),
        Tool(
            name="power-off-vm",
            description="Power off a VM if it's not already powered off",
            inputSchema={
                "type": "object",
                "properties": {
                    "vm_id": {"type": "string", "description": "The ID of the VM to power off"}
                },
                "required": ["vm_id"]
            }
        ),
        Tool(
            name="restart-vm",
            description="Restart a VM if it's powered on",
            inputSchema={
                "type": "object",
                "properties": {
                    "vm_id": {"type": "string", "description": "The ID of the VM to restart"}
                },
                "required": ["vm_id"]
            }
        ),
        Tool(
            name="get-power-state",
            description="Get the current power state of a VM",
            inputSchema={
                "type": "object",
                "properties": {
                    "vm_id": {"type": "string", "description": "The ID of the VM to check"}
                },
                "required": ["vm_id"]
            }
        ),
        Tool(
            name="deploy-vm-from-template",
            description="Deploy a VM from template with comprehensive customization",
            inputSchema={
                "type": "object",
                "properties": {
                    "template_id": {"type": "string", "description": "Template ID to deploy from"},
                    "vm_name": {"type": "string", "description": "Name for the new VM"},
                    "datacenter": {"type": "string", "description": "Target datacenter"},
                    "cluster": {"type": "string", "description": "Target cluster"},
                    "folder": {"type": "string", "description": "Target folder path"},
                    "hardware": {
                        "type": "object", 
                        "description": "Hardware specification (cpu, memory)",
                        "properties": {
                            "cpu": {"type": "object", "properties": {"count": {"type": "integer"}, "cores_per_socket": {"type": "integer"}}},
                            "memory": {"type": "object", "properties": {"size_mib": {"type": "integer"}}}
                        }
                    },
                    "disk": {
                        "type": "array",
                        "description": "Disk specifications",
                        "items": {
                            "type": "object",
                            "properties": {
                                "size_gb": {"type": "integer"},
                                "datastore": {"type": "string"}
                            }
                        }
                    },
                    "networks": {
                        "type": "array",
                        "description": "Network configurations",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "device_type": {"type": "string"}
                            }
                        }
                    },
                    "customization": {
                        "type": "object",
                        "description": "Guest customization settings",
                        "properties": {
                            "hostname": {"type": "string"},
                            "ip_address": {"type": "string"},
                            "netmask": {"type": "string"},
                            "gateway": {"type": "string"},
                            "dns_servers": {"type": "array", "items": {"type": "string"}}
                        }
                    },
                    "wait_for_ip": {"type": "boolean", "description": "Whether to wait for IP address"},
                    "wait_timeout": {"type": "integer", "description": "Timeout for IP wait in seconds"}
                },
                "required": ["template_id", "vm_name"]
            }
        ),
        Tool(
            name="create-template-from-vm",
            description="Create a template from an existing VM",
            inputSchema={
                "type": "object",
                "properties": {
                    "vm_id": {"type": "string", "description": "The ID of the VM to convert to template"},
                    "template_name": {"type": "string", "description": "Name for the new template"},
                    "description": {"type": "string", "description": "Description for the template"}
                },
                "required": ["vm_id", "template_name"]
            }
        ),
        Tool(
            name="clone-vm",
            description="Clone a VM with comprehensive customization",
            inputSchema={
                "type": "object",
                "properties": {
                    "source_vm_id": {"type": "string", "description": "The ID of the VM to clone"},
                    "new_vm_name": {"type": "string", "description": "Name for the new VM"},
                    "datacenter": {"type": "string", "description": "Target datacenter"},
                    "cluster": {"type": "string", "description": "Target cluster"},
                    "folder": {"type": "string", "description": "Target folder path"},
                    "hardware": {
                        "type": "object", 
                        "description": "Hardware specification (cpu, memory)",
                        "properties": {
                            "cpu": {"type": "object", "properties": {"count": {"type": "integer"}, "cores_per_socket": {"type": "integer"}}},
                            "memory": {"type": "object", "properties": {"size_mib": {"type": "integer"}}}
                        }
                    },
                    "disk": {
                        "type": "array",
                        "description": "Disk specifications",
                        "items": {
                            "type": "object",
                            "properties": {
                                "size_gb": {"type": "integer"},
                                "datastore": {"type": "string"}
                            }
                        }
                    },
                    "networks": {
                        "type": "array",
                        "description": "Network configurations",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "device_type": {"type": "string"}
                            }
                        }
                    },
                    "customization": {
                        "type": "object",
                        "description": "Guest customization settings",
                        "properties": {
                            "hostname": {"type": "string"},
                            "ip_address": {"type": "string"},
                            "netmask": {"type": "string"},
                            "gateway": {"type": "string"},
                            "dns_servers": {"type": "array", "items": {"type": "string"}}
                        }
                    },
                    "wait_for_ip": {"type": "boolean", "description": "Whether to wait for IP address"},
                    "wait_timeout": {"type": "integer", "description": "Timeout for IP wait in seconds"}
                },
                "required": ["source_vm_id", "new_vm_name"]
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
    elif name == "power-on-vm":
        vm_id = arguments.get("vm_id")
        if not vm_id:
            return [TextContent(type="text", text="Missing required argument: vm_id")]
        return [TextContent(type="text", text=power_on_vm(vm_id))]
    elif name == "power-off-vm":
        vm_id = arguments.get("vm_id")
        if not vm_id:
            return [TextContent(type="text", text="Missing required argument: vm_id")]
        return [TextContent(type="text", text=power_off_vm(vm_id))]
    elif name == "restart-vm":
        vm_id = arguments.get("vm_id")
        if not vm_id:
            return [TextContent(type="text", text="Missing required argument: vm_id")]
        return [TextContent(type="text", text=restart_vm(vm_id))]
    elif name == "get-power-state":
        vm_id = arguments.get("vm_id")
        if not vm_id:
            return [TextContent(type="text", text="Missing required argument: vm_id")]
        return [TextContent(type="text", text=get_power_state_text(vm_id))]
    elif name == "deploy-vm-from-template":
        template_id = arguments.get("template_id")
        vm_name = arguments.get("vm_name")
        if not template_id or not vm_name:
            return [TextContent(type="text", text="Missing required arguments: template_id and vm_name")]
        
        return [TextContent(type="text", text=deploy_vm_from_template(
            template_id=template_id,
            vm_name=vm_name,
            datacenter=arguments.get("datacenter"),
            cluster=arguments.get("cluster"),
            folder=arguments.get("folder"),
            hardware=arguments.get("hardware"),
            disk=arguments.get("disk"),
            networks=arguments.get("networks"),
            customization=arguments.get("customization"),
            wait_for_ip=arguments.get("wait_for_ip", False),
            wait_timeout=arguments.get("wait_timeout", 300)
        ))]
    elif name == "create-template-from-vm":
        vm_id = arguments.get("vm_id")
        template_name = arguments.get("template_name")
        if not vm_id or not template_name:
            return [TextContent(type="text", text="Missing required arguments: vm_id and template_name")]
        
        return [TextContent(type="text", text=create_template_from_vm(
            vm_id=vm_id,
            template_name=template_name,
            description=arguments.get("description")
        ))]
    elif name == "clone-vm":
        source_vm_id = arguments.get("source_vm_id")
        new_vm_name = arguments.get("new_vm_name")
        if not source_vm_id or not new_vm_name:
            return [TextContent(type="text", text="Missing required arguments: source_vm_id and new_vm_name")]
        
        return [TextContent(type="text", text=clone_vm(
            source_vm_id=source_vm_id,
            new_vm_name=new_vm_name,
            datacenter=arguments.get("datacenter"),
            cluster=arguments.get("cluster"),
            folder=arguments.get("folder"),
            hardware=arguments.get("hardware"),
            disk=arguments.get("disk"),
            networks=arguments.get("networks"),
            customization=arguments.get("customization"),
            wait_for_ip=arguments.get("wait_for_ip", False),
            wait_timeout=arguments.get("wait_timeout", 300)
        ))]
    else:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]

async def serve():
    options = server.create_initialization_options()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, options, raise_exceptions=True)

if __name__ == "__main__":
    asyncio.run(serve())

