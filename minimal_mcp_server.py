#!/usr/bin/env python3
"""
Minimal MCP server for testing
"""

import json
import sys

def handle_initialize(params):
    """Minimal initialize handler."""
    return {
        "jsonrpc": "2.0",
        "id": params.get("id"),
        "result": {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": [
                    {
                        "name": "hello",
                        "description": "A simple hello world tool",
                        "inputSchema": {
                            "type": "object",
                            "properties": {},
                            "additionalProperties": False
                        }
                    }
                ]
            },
            "serverInfo": {
                "name": "minimal-mcp-server",
                "version": "1.0.0"
            }
        }
    }

def handle_tools_call(params):
    """Handle tools/call requests."""
    tool_name = params.get("name")
    
    if tool_name == "hello":
        return {
            "jsonrpc": "2.0",
            "id": params.get("id"),
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": "Hello from minimal MCP server!"
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

def main():
    """Minimal MCP server."""
    print("[DEBUG] Minimal MCP Server starting...", file=sys.stderr)
    
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            
            print(f"[DEBUG] Received: {line.strip()}", file=sys.stderr)
            request = json.loads(line)
            method = request.get("method")
            params = request.get("params", {})
            request_id = request.get("id")
            
            if method == "initialize":
                response = handle_initialize({"id": request_id})
                print(f"[DEBUG] Sending: {json.dumps(response)}", file=sys.stderr)
                print(json.dumps(response))
                sys.stdout.flush()
            elif method == "tools/call":
                response = handle_tools_call({"id": request_id, **params})
                print(f"[DEBUG] Sending: {json.dumps(response)}", file=sys.stderr)
                print(json.dumps(response))
                sys.stdout.flush()
            else:
                print(f"[DEBUG] Unknown method: {method}", file=sys.stderr)
                
        except Exception as e:
            print(f"[DEBUG] Error: {e}", file=sys.stderr)
            break

if __name__ == "__main__":
    main() 