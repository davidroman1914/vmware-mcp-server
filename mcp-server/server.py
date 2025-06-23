#!/usr/bin/env python3
"""
VMware vCenter MCP Server using pyvmomi
Supports VM listing, power management, and VM creation via MCP stdio protocol.
"""

import json
import sys
import os
import ssl
from typing import Dict, Any
from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim

# Import our modules
from vm_info import VMInfoManager
from power import PowerManager
from vm_creation import VMCreationManager

class VMwareMCPServer:
    def __init__(self):
        self.service_instance = None
        self.vm_info = VMInfoManager()
        self.power_manager = PowerManager()
        self.vm_creation = VMCreationManager()
        
    def connect_to_vcenter(self) -> bool:
        """Connect to vCenter using environment variables."""
        # Check if already connected
        if self.service_instance:
            try:
                # Test if connection is still alive
                content = self.service_instance.RetrieveContent()
                return True
            except:
                # Connection is dead, reset it
                self.service_instance = None
        
        max_retries = 2  # Reduced retries for faster failure
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                print(f"[DEBUG] Attempting vCenter connection (attempt {retry_count + 1}/{max_retries})...", file=sys.stderr)
                host = os.getenv('VCENTER_HOST')
                user = os.getenv('VCENTER_USER')
                password = os.getenv('VCENTER_PASSWORD')
                insecure = os.getenv('VCENTER_INSECURE', 'false').lower() == 'true'
                print(f"[DEBUG] host={host}, user={user}, insecure={insecure}", file=sys.stderr)
                
                if not all([host, user, password]):
                    print("[ERROR] Missing vCenter connection environment variables.", file=sys.stderr)
                    return False
                
                print("[DEBUG] Connecting to vCenter...", file=sys.stderr)
                
                # Add timeout to prevent hanging
                import socket
                socket.setdefaulttimeout(3)  # 3 second timeout
                
                # Create a completely disabled SSL context for non-SSL connections
                context = ssl.SSLContext(ssl.PROTOCOL_TLS)
                context.verify_mode = ssl.CERT_NONE
                context.check_hostname = False
                
                self.service_instance = SmartConnect(
                    host=host,
                    user=user,
                    pwd=password,
                    sslContext=context
                )
                print("[DEBUG] Connected to vCenter successfully!", file=sys.stderr)
                return True
                
            except Exception as e:
                retry_count += 1
                print(f"[ERROR] Connection attempt {retry_count} failed: {e}", file=sys.stderr)
                if retry_count < max_retries:
                    print(f"[DEBUG] Retrying in 2 seconds...", file=sys.stderr)
                    import time
                    time.sleep(2)
                else:
                    print(f"[ERROR] All {max_retries} connection attempts failed", file=sys.stderr)
                    return False
        
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
        print("[DEBUG] Starting initialize handler...", file=sys.stderr)
        # Get the tools list
        print("[DEBUG] Getting tools list...", file=sys.stderr)
        tools_response = self.handle_tools_list({"id": params.get("id")})
        print("[DEBUG] Got tools list, building response...", file=sys.stderr)
        tools = tools_response["result"]["tools"]
        
        response = {
            "jsonrpc": "2.0",
            "id": params.get("id"),
            "result": {
                "protocolVersion": "2025-03-26",
                "capabilities": True,  # Goose expects a boolean, not an object
                "tools": tools,  # Move tools to top level
                "serverInfo": {
                    "name": "vmware-vcenter-mcp-server",
                    "version": "1.0.0"
                }
            }
        }
        print("[DEBUG] Initialize handler completed", file=sys.stderr)
        return response
    
    def handle_tools_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP tools/list request."""
        print("[DEBUG] Starting tools/list handler...", file=sys.stderr)
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
        
        response = {
            "jsonrpc": "2.0",
            "id": params.get("id"),
            "result": {
                "tools": tools
            }
        }
        print("[DEBUG] Tools/list handler completed", file=sys.stderr)
        return response
    
    def handle_tools_call(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP tools/call request."""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        try:
            if tool_name == "list_vms":
                # Use pyvmomi for VM listing
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
                result = self.vm_info.fast_list_vms(self.service_instance)
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
                # Use pyvmomi for power operations
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
                # Use pyvmomi for power operations
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
                # Use pyvmomi for VM creation (advanced features)
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
        print("[DEBUG] MCP Server starting, waiting for messages...", file=sys.stderr)
        while True:
            try:
                # Read request from stdin
                print("[DEBUG] Waiting for input from stdin...", file=sys.stderr)
                line = sys.stdin.readline()
                if not line:
                    print("[DEBUG] No input received, exiting...", file=sys.stderr)
                    break
                
                print(f"[DEBUG] Received input: {line.strip()}", file=sys.stderr)
                request = json.loads(line)
                method = request.get("method")
                params = request.get("params", {})
                request_id = request.get("id")
                
                print(f"[DEBUG] Processing method: {method}, id: {request_id}", file=sys.stderr)
                
                # Add the request ID to params for handlers
                params["id"] = request_id
                
                # Handle different MCP methods
                if method == "initialize":
                    print("[DEBUG] Handling initialize request...", file=sys.stderr)
                    response = self.handle_initialize(params)
                elif method == "tools/list":
                    print("[DEBUG] Handling tools/list request...", file=sys.stderr)
                    response = self.handle_tools_list(params)
                elif method == "tools/call":
                    print("[DEBUG] Handling tools/call request...", file=sys.stderr)
                    response = self.handle_tools_call(params)
                else:
                    print(f"[DEBUG] Unknown method: {method}", file=sys.stderr)
                    response = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32601,
                            "message": f"Unknown method: {method}"
                        }
                    }
                
                print(f"[DEBUG] Sending response: {json.dumps(response)}", file=sys.stderr)
                # Send response to stdout
                print(json.dumps(response))
                sys.stdout.flush()
                
            except json.JSONDecodeError as e:
                print(f"[DEBUG] JSON decode error: {e}", file=sys.stderr)
                continue
            except KeyboardInterrupt:
                print("[DEBUG] Keyboard interrupt received", file=sys.stderr)
                break
            except Exception as e:
                print(f"[DEBUG] Exception in main loop: {e}", file=sys.stderr)
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
        print("[DEBUG] Cleaning up and disconnecting...", file=sys.stderr)
        self.disconnect_from_vcenter()

if __name__ == "__main__":
    server = VMwareMCPServer()
    server.run() 