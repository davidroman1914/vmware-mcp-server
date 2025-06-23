#!/usr/bin/env python3
"""
VMware vCenter MCP Server using pyvmomi
Supports VM listing, power management, and VM creation via MCP stdio protocol.
"""

import json
import sys
import os
from typing import Dict, Any, List, Optional
from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim
import ssl

# Import our modules
from vm_info import VMInfoManager
from power import PowerManager
from vm_creation import VMCreationManager

class VMwareMCPServer:
    def __init__(self):
        self.vm_info = VMInfoManager()
        self.power_manager = PowerManager()
        self.vm_creation = VMCreationManager()
        self.service_instance = None
        
    def connect_to_vcenter(self) -> bool:
        """Connect to vCenter using environment variables."""
        try:
            host = os.getenv('VCENTER_HOST')
            user = os.getenv('VCENTER_USER')
            password = os.getenv('VCENTER_PASSWORD')
            insecure = os.getenv('VCENTER_INSECURE', 'false').lower() == 'true'
            
            if not all([host, user, password]):
                return False
            
            # Create SSL context
            if insecure:
                context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
                context.verify_mode = ssl.CERT_NONE
            else:
                context = ssl.create_default_context()
            
            # Connect to vCenter
            self.service_instance = SmartConnect(
                host=host,
                user=user,
                pwd=password,
                sslContext=context
            )
            
            return True
            
        except Exception as e:
            return False
    
    def disconnect_from_vcenter(self):
        """Disconnect from vCenter."""
        if self.service_instance:
            try:
                Disconnect(self.service_instance)
            except:
                pass
            self.service_instance = None
    
    def handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP initialize request."""
        # Define the tools that this server provides
        tools = [
            {
                "name": "list_vms",
                "description": "List all VMs in vCenter with detailed information",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "additionalProperties": False
                }
            },
            {
                "name": "power_on_vm",
                "description": "Power on a VM by name",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "vm_name": {
                            "type": "string",
                            "description": "Name of the VM to power on"
                        }
                    },
                    "required": ["vm_name"],
                    "additionalProperties": False
                }
            },
            {
                "name": "power_off_vm",
                "description": "Power off a VM by name",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "vm_name": {
                            "type": "string",
                            "description": "Name of the VM to power off"
                        }
                    },
                    "required": ["vm_name"],
                    "additionalProperties": False
                }
            },
            {
                "name": "create_vm_from_template",
                "description": "Create a new VM from a template with customization",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "template_name": {
                            "type": "string",
                            "description": "Name of the template VM to clone from"
                        },
                        "vm_name": {
                            "type": "string",
                            "description": "Name for the new VM"
                        },
                        "hostname": {
                            "type": "string",
                            "description": "Hostname for the new VM"
                        },
                        "ip_address": {
                            "type": "string",
                            "description": "Static IP address"
                        },
                        "netmask": {
                            "type": "string",
                            "description": "Subnet mask"
                        },
                        "gateway": {
                            "type": "string",
                            "description": "Gateway IP address"
                        },
                        "network_name": {
                            "type": "string",
                            "description": "Network/port group name"
                        },
                        "cpu_count": {
                            "type": "integer",
                            "description": "Number of CPUs"
                        },
                        "memory_mb": {
                            "type": "integer",
                            "description": "Memory in MB"
                        },
                        "disk_size_gb": {
                            "type": "integer",
                            "description": "Disk size in GB"
                        },
                        "datastore_name": {
                            "type": "string",
                            "description": "Datastore name (optional)"
                        }
                    },
                    "required": ["template_name", "vm_name", "hostname", "ip_address", "netmask", "gateway", "network_name"],
                    "additionalProperties": False
                }
            }
        ]
        
        return {
            "jsonrpc": "2.0",
            "id": params.get("id"),
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": tools
                },
                "serverInfo": {
                    "name": "vmware-vcenter-mcp-server",
                    "version": "1.0.0"
                }
            }
        }
    
    def handle_tools_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP tools/list request."""
        tools = [
            {
                "name": "list_vms",
                "description": "List all VMs in vCenter with detailed information",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "additionalProperties": False
                }
            },
            {
                "name": "power_on_vm",
                "description": "Power on a VM by name",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "vm_name": {
                            "type": "string",
                            "description": "Name of the VM to power on"
                        }
                    },
                    "required": ["vm_name"],
                    "additionalProperties": False
                }
            },
            {
                "name": "power_off_vm",
                "description": "Power off a VM by name",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "vm_name": {
                            "type": "string",
                            "description": "Name of the VM to power off"
                        }
                    },
                    "required": ["vm_name"],
                    "additionalProperties": False
                }
            },
            {
                "name": "create_vm_from_template",
                "description": "Create a new VM from a template with customization",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "template_name": {
                            "type": "string",
                            "description": "Name of the template VM to clone from"
                        },
                        "vm_name": {
                            "type": "string",
                            "description": "Name for the new VM"
                        },
                        "hostname": {
                            "type": "string",
                            "description": "Hostname for the new VM"
                        },
                        "ip_address": {
                            "type": "string",
                            "description": "Static IP address"
                        },
                        "netmask": {
                            "type": "string",
                            "description": "Subnet mask"
                        },
                        "gateway": {
                            "type": "string",
                            "description": "Gateway IP address"
                        },
                        "network_name": {
                            "type": "string",
                            "description": "Network/port group name"
                        },
                        "cpu_count": {
                            "type": "integer",
                            "description": "Number of CPUs"
                        },
                        "memory_mb": {
                            "type": "integer",
                            "description": "Memory in MB"
                        },
                        "disk_size_gb": {
                            "type": "integer",
                            "description": "Disk size in GB"
                        },
                        "datastore_name": {
                            "type": "string",
                            "description": "Datastore name (optional)"
                        }
                    },
                    "required": ["template_name", "vm_name", "hostname", "ip_address", "netmask", "gateway", "network_name"],
                    "additionalProperties": False
                }
            }
        ]
        
        return {
            "jsonrpc": "2.0",
            "id": params.get("id"),
            "result": {
                "tools": tools
            }
        }
    
    def handle_tools_call(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP tools/call request."""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        # Ensure we're connected to vCenter
        if not self.service_instance:
            if not self.connect_to_vcenter():
                return {
                    "jsonrpc": "2.0",
                    "id": params.get("id"),
                    "error": {
                        "code": -1,
                        "message": "Failed to connect to vCenter. Check VCENTER_HOST, VCENTER_USER, VCENTER_PASSWORD environment variables."
                    }
                }
        
        try:
            if tool_name == "list_vms":
                result = self.vm_info.list_all_vms(self.service_instance)
                return {
                    "jsonrpc": "2.0",
                    "id": params.get("id"),
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(result, indent=2)
                            }
                        ]
                    }
                }
            
            elif tool_name == "power_on_vm":
                vm_name = arguments.get("vm_name")
                result = self.power_manager.power_on_vm(self.service_instance, vm_name)
                return {
                    "jsonrpc": "2.0",
                    "id": params.get("id"),
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(result, indent=2)
                            }
                        ]
                    }
                }
            
            elif tool_name == "power_off_vm":
                vm_name = arguments.get("vm_name")
                result = self.power_manager.power_off_vm(self.service_instance, vm_name)
                return {
                    "jsonrpc": "2.0",
                    "id": params.get("id"),
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(result, indent=2)
                            }
                        ]
                    }
                }
            
            elif tool_name == "create_vm_from_template":
                result = self.vm_creation.create_vm_from_template(self.service_instance, arguments)
                return {
                    "jsonrpc": "2.0",
                    "id": params.get("id"),
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(result, indent=2)
                            }
                        ]
                    }
                }
            
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": params.get("id"),
                    "error": {
                        "code": -32601,
                        "message": f"Unknown tool: {tool_name}"
                    }
                }
        
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": params.get("id"),
                "error": {
                    "code": -1,
                    "message": f"Error executing {tool_name}: {str(e)}"
                }
            }
    
    def run(self):
        """Run the MCP server using stdio protocol."""
        while True:
            try:
                # Read request from stdin
                line = sys.stdin.readline()
                if not line:
                    break
                
                request = json.loads(line)
                method = request.get("method")
                params = request.get("params", {})
                
                # Handle different MCP methods
                if method == "initialize":
                    response = self.handle_initialize(params)
                elif method == "tools/list":
                    response = self.handle_tools_list(params)
                elif method == "tools/call":
                    response = self.handle_tools_call(params)
                else:
                    response = {
                        "jsonrpc": "2.0",
                        "id": request.get("id"),
                        "error": {
                            "code": -32601,
                            "message": f"Unknown method: {method}"
                        }
                    }
                
                # Send response to stdout
                print(json.dumps(response))
                sys.stdout.flush()
                
            except json.JSONDecodeError:
                continue
            except KeyboardInterrupt:
                break
            except Exception as e:
                error_response = {
                    "jsonrpc": "2.0",
                    "id": request.get("id") if 'request' in locals() else None,
                    "error": {
                        "code": -1,
                        "message": f"Server error: {str(e)}"
                    }
                }
                print(json.dumps(error_response))
                sys.stdout.flush()
        
        # Cleanup
        self.disconnect_from_vcenter()

if __name__ == "__main__":
    server = VMwareMCPServer()
    server.run() 