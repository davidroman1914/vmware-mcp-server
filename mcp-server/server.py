#!/usr/bin/env python3
"""
VMware vCenter MCP Server
Provides tools for managing VMware vCenter resources
"""

import asyncio
import json
import sys
from typing import Any, Dict, List, Optional

# Import from modular files
from vm_info import list_all_vms_text, get_vm_info_text, list_templates_text, find_template_by_name_text, find_template_by_name_ansible_style_text
from power_management import power_on_vm_text, power_off_vm_text, restart_vm_text
from vm_creation import (
    clone_vm_text, deploy_from_template_text, deploy_from_content_library_template_text,
    list_datastores_text, list_resource_pools_text, list_folders_text
)

class VMwareMCPServer:
    """MCP Server for VMware vCenter operations"""
    
    def __init__(self):
        self.tools = {
            "list_vms": {
                "name": "list_vms",
                "description": "List all VMs in vCenter with their power states and basic info",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            "get_vm_info": {
                "name": "get_vm_info", 
                "description": "Get detailed information about a specific VM including network, hardware, and guest info",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "vm_id": {
                            "type": "string",
                            "description": "The VM ID to get information for"
                        }
                    },
                    "required": ["vm_id"]
                }
            },
            "list_templates": {
                "name": "list_templates",
                "description": "List all available VM templates (both VM templates and Content Library templates)",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            "find_template_by_name": {
                "name": "find_template_by_name",
                "description": "Find a specific template by name using multiple discovery methods (Ansible-style)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "template_name": {
                            "type": "string",
                            "description": "Name of the template to search for (e.g., 'Ubuntu-Template-01')"
                        }
                    },
                    "required": ["template_name"]
                }
            },
            "find_template_by_name_ansible_style": {
                "name": "find_template_by_name_ansible_style",
                "description": "Find a template by name using Ansible's Container View approach (most comprehensive)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "template_name": {
                            "type": "string",
                            "description": "Name of the template to search for (e.g., 'Ubuntu-Template-01')"
                        }
                    },
                    "required": ["template_name"]
                }
            },
            "power_on_vm": {
                "name": "power_on_vm",
                "description": "Power on a VM",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "vm_id": {
                            "type": "string",
                            "description": "The VM ID to power on"
                        }
                    },
                    "required": ["vm_id"]
                }
            },
            "power_off_vm": {
                "name": "power_off_vm", 
                "description": "Power off a VM",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "vm_id": {
                            "type": "string",
                            "description": "The VM ID to power off"
                        }
                    },
                    "required": ["vm_id"]
                }
            },
            "restart_vm": {
                "name": "restart_vm",
                "description": "Restart a VM",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "vm_id": {
                            "type": "string", 
                            "description": "The VM ID to restart"
                        }
                    },
                    "required": ["vm_id"]
                }
            },
            "clone_vm": {
                "name": "clone_vm",
                "description": "Clone a VM with optional customization",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "source_vm_id": {
                            "type": "string",
                            "description": "Source VM ID to clone from"
                        },
                        "new_vm_name": {
                            "type": "string", 
                            "description": "Name for the new cloned VM"
                        },
                        "datastore_id": {
                            "type": "string",
                            "description": "Target datastore ID (optional)"
                        },
                        "resource_pool_id": {
                            "type": "string",
                            "description": "Target resource pool ID (optional)"
                        },
                        "folder_id": {
                            "type": "string",
                            "description": "Target folder ID (optional)"
                        },
                        "hostname": {
                            "type": "string",
                            "description": "Custom hostname for the new VM (optional)"
                        },
                        "ip_address": {
                            "type": "string",
                            "description": "Static IP address (optional)"
                        },
                        "netmask": {
                            "type": "string",
                            "description": "Subnet mask (optional)"
                        },
                        "gateway": {
                            "type": "string",
                            "description": "Default gateway (optional)"
                        },
                        "cpu_count": {
                            "type": "integer",
                            "description": "Number of CPU cores (optional)"
                        },
                        "memory_mb": {
                            "type": "integer",
                            "description": "Memory size in MB (optional)"
                        }
                    },
                    "required": ["source_vm_id", "new_vm_name"]
                }
            },
            "deploy_from_template": {
                "name": "deploy_from_template",
                "description": "Deploy a new VM from a template with optional customization",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "template_id": {
                            "type": "string",
                            "description": "Template VM ID to deploy from"
                        },
                        "new_vm_name": {
                            "type": "string",
                            "description": "Name for the new deployed VM"
                        },
                        "datastore_id": {
                            "type": "string",
                            "description": "Target datastore ID (optional)"
                        },
                        "resource_pool_id": {
                            "type": "string",
                            "description": "Target resource pool ID (optional)"
                        },
                        "folder_id": {
                            "type": "string",
                            "description": "Target folder ID (optional)"
                        },
                        "hostname": {
                            "type": "string",
                            "description": "Custom hostname for the new VM (optional)"
                        },
                        "ip_address": {
                            "type": "string",
                            "description": "Static IP address (optional)"
                        },
                        "netmask": {
                            "type": "string",
                            "description": "Subnet mask (optional)"
                        },
                        "gateway": {
                            "type": "string",
                            "description": "Default gateway (optional)"
                        },
                        "cpu_count": {
                            "type": "integer",
                            "description": "Number of CPU cores (optional)"
                        },
                        "memory_mb": {
                            "type": "integer",
                            "description": "Memory size in MB (optional)"
                        }
                    },
                    "required": ["template_id", "new_vm_name"]
                }
            },
            "deploy_from_content_library": {
                "name": "deploy_from_content_library",
                "description": "Deploy a new VM from a Content Library template (different from VM templates)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "template_urn": {
                            "type": "string",
                            "description": "Content Library template URN (e.g., urn:vapi:com.vmware.content.library.Item:...)"
                        },
                        "vm_name": {
                            "type": "string",
                            "description": "Name for the new deployed VM"
                        },
                        "datacenter": {
                            "type": "string",
                            "description": "Target datacenter name (optional)"
                        },
                        "datastore": {
                            "type": "string",
                            "description": "Target datastore name (optional)"
                        },
                        "cluster": {
                            "type": "string",
                            "description": "Target cluster name (optional)"
                        },
                        "cpu_count": {
                            "type": "integer",
                            "description": "Number of CPU cores (optional)"
                        },
                        "memory_mb": {
                            "type": "integer",
                            "description": "Memory size in MB (optional)"
                        }
                    },
                    "required": ["template_urn", "vm_name"]
                }
            },
            "list_datastores": {
                "name": "list_datastores",
                "description": "List all datastores with capacity and free space information",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            "list_resource_pools": {
                "name": "list_resource_pools",
                "description": "List all resource pools with CPU and memory allocation",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            "list_folders": {
                "name": "list_folders",
                "description": "List all VM folders for organization",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        }

    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming MCP requests"""
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")

        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {}
                    },
                    "serverInfo": {
                        "name": "vmware-vcenter-mcp-server",
                        "version": "0.1.0"
                    }
                }
            }
        
        elif method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "tools": list(self.tools.values())
                }
            }
        
        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            if tool_name not in self.tools:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Tool '{tool_name}' not found"
                    }
                }
            
            try:
                # Call the appropriate function based on tool name
                if tool_name == "list_vms":
                    result = list_all_vms_text()
                elif tool_name == "get_vm_info":
                    result = get_vm_info_text(arguments["vm_id"])
                elif tool_name == "list_templates":
                    result = list_templates_text()
                elif tool_name == "power_on_vm":
                    result = power_on_vm_text(arguments["vm_id"])
                elif tool_name == "power_off_vm":
                    result = power_off_vm_text(arguments["vm_id"])
                elif tool_name == "restart_vm":
                    result = restart_vm_text(arguments["vm_id"])
                elif tool_name == "clone_vm":
                    result = clone_vm_text(
                        source_vm_id=arguments["source_vm_id"],
                        new_vm_name=arguments["new_vm_name"],
                        datastore_id=arguments.get("datastore_id"),
                        resource_pool_id=arguments.get("resource_pool_id"),
                        folder_id=arguments.get("folder_id"),
                        hostname=arguments.get("hostname"),
                        ip_address=arguments.get("ip_address"),
                        netmask=arguments.get("netmask"),
                        gateway=arguments.get("gateway"),
                        cpu_count=arguments.get("cpu_count"),
                        memory_mb=arguments.get("memory_mb")
                    )
                elif tool_name == "deploy_from_template":
                    result = deploy_from_template_text(
                        template_id=arguments["template_id"],
                        new_vm_name=arguments["new_vm_name"],
                        datastore_id=arguments.get("datastore_id"),
                        resource_pool_id=arguments.get("resource_pool_id"),
                        folder_id=arguments.get("folder_id"),
                        hostname=arguments.get("hostname"),
                        ip_address=arguments.get("ip_address"),
                        netmask=arguments.get("netmask"),
                        gateway=arguments.get("gateway"),
                        cpu_count=arguments.get("cpu_count"),
                        memory_mb=arguments.get("memory_mb")
                    )
                elif tool_name == "deploy_from_content_library":
                    result = deploy_from_content_library_template_text(
                        template_urn=arguments["template_urn"],
                        vm_name=arguments["vm_name"],
                        datacenter=arguments.get("datacenter"),
                        datastore=arguments.get("datastore"),
                        cluster=arguments.get("cluster"),
                        cpu_count=arguments.get("cpu_count"),
                        memory_mb=arguments.get("memory_mb")
                    )
                elif tool_name == "list_datastores":
                    result = list_datastores_text()
                elif tool_name == "list_resource_pools":
                    result = list_resource_pools_text()
                elif tool_name == "list_folders":
                    result = list_folders_text()
                elif tool_name == "find_template_by_name":
                    result = find_template_by_name_text(arguments["template_name"])
                elif tool_name == "find_template_by_name_ansible_style":
                    result = find_template_by_name_ansible_style_text(arguments["template_name"])
                else:
                    raise ValueError(f"Unknown tool: {tool_name}")
                
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": result
                            }
                        ]
                    }
                }
                
            except Exception as e:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32603,
                        "message": f"Internal error: {str(e)}"
                    }
                }
        
        else:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32601,
                    "message": f"Method '{method}' not found"
                }
            }

async def main():
    """Main server loop"""
    server = VMwareMCPServer()
    
    while True:
        try:
            # Read request from stdin
            line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
            if not line:
                break
            
            request = json.loads(line.strip())
            response = await server.handle_request(request)
            
            # Write response to stdout
            print(json.dumps(response), flush=True)
            
        except json.JSONDecodeError as e:
            error_response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32700,
                    "message": f"Parse error: {str(e)}"
                }
            }
            print(json.dumps(error_response), flush=True)
            
        except Exception as e:
            error_response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }
            print(json.dumps(error_response), flush=True)

if __name__ == "__main__":
    asyncio.run(main()) 