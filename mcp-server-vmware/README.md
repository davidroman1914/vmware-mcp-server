# VMware vCenter MCP Server

A clean MCP server implementation using only the `vmware-vcenter` package, following the same pattern as the main `mcp-server` folder.

## Structure

```
mcp-server-vmware/
├── server.py          # MCP server using vmware-vcenter package
├── test_server.py     # Test script to verify MCP server
├── requirements.txt   # Dependencies
└── README.md         # This file
```

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set environment variables:**
   ```bash
   export VCENTER_HOST="your-vcenter-ip"
   export VCENTER_USER="your-username"
   export VCENTER_PASSWORD="your-password"
   export VCENTER_INSECURE="true"  # Set to "false" for production
   ```

3. **Run the MCP server:**
   ```bash
   python server.py
   ```

## Available Tools

### `get-all-vms`
- **Description**: Get all VMs from vCenter using vmware-vcenter package
- **Input**: No parameters required
- **Output**: Formatted list of all VMs with details

## Key Features

- ✅ **Pure vmware-vcenter** - Uses only the official VMware SDK
- ✅ **MCP Protocol** - Works with stdio and follows MCP standards
- ✅ **Same Pattern** - Follows the exact structure of main mcp-server folder
- ✅ **Clean Implementation** - No complex abstractions or helper layers
- ✅ **Environment-based config** - No hardcoded credentials

## Testing

Run the test script to verify the MCP server works:

```bash
python test_server.py
```

## Expected Output

When called via MCP, the `get-all-vms` tool returns:

```
📋 **Found 12 VMs in vCenter:**

- **ova-inf-dns-01.ova.nydig.local** (ID: vm-2010)
  • Power State: POWERED_OFF
  • CPU Count: 2
  • Memory: 4096 MB

- **ova-inf-nfs-uat-01** (ID: vm-2011)
  • Power State: POWERED_ON
  • CPU Count: 4
  • Memory: 8192 MB
...
```

## Comparison with Main mcp-server

| Feature | Main mcp-server | mcp-server-vmware |
|---------|----------------|-------------------|
| **Dependencies** | Multiple packages + helpers | Only vmware-vcenter |
| **Complexity** | Full MCP server with many tools | Simple, focused example |
| **Pattern** | Modular with separate files | Single server.py file |
| **Purpose** | Production MCP server | Clean reference implementation |

This demonstrates the minimal approach using only the official VMware SDK while maintaining MCP compatibility. 