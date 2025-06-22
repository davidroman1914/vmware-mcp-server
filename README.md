# VMware MCP Server

A clean, modular Model Context Protocol (MCP) server for VMware vCenter management using the official `vmware-vcenter` Python package.

## 🏗️ Architecture

This project provides a clean, modular implementation of a VMware MCP server:

- **`mcp-server/`** - Clean, modular MCP server implementation
- **Docker support** - Easy deployment and distribution
- **Modern tooling** - Uses `uv` for dependency management

## 🚀 Features

### VM Management
- **List VMs**: Get all VMs in vCenter with basic information
- **Get VM Info**: Retrieve detailed information about a specific VM
- **Power Management**: Power on, off, and restart VMs with intelligent state checking
- **Clone VM**: Clone an existing VM with optional customization
- **Deploy from Template**: Create a new VM from a template with optional customization

### Modular Design
- **Separation of concerns** - Each module has a single responsibility
- **Easy testing** - Individual modules can be tested independently
- **Maintainable** - Changes to one module don't affect others
- **Reusable** - VM operations can be imported and used elsewhere

## 🏛️ Project Structure

```
vmware-mcp-server/
├── mcp-server/                  # Clean, modular MCP server
│   ├── server.py              # Main MCP server
│   ├── vm_creation.py         # VM creation, cloning, template deployment
│   ├── vm_info.py             # VM info and listing
│   ├── power_management.py    # Power management
│   ├── config.py              # Configuration management
│   ├── test_power_management.py  # Test script
│   ├── pyproject.toml         # Project dependencies
│   ├── Dockerfile             # Docker configuration
│   ├── Makefile               # Development tasks
├── docker-compose.yml         # Docker Compose configuration
├── Makefile                   # Main project tasks
└── README.md                  # This file
```

## 🔧 Setup

### Prerequisites
- Python 3.10+
- VMware vCenter access
- Docker (optional)

### Environment Variables

Set these environment variables:

```bash
export VCENTER_HOST="your-vcenter-host"
export VCENTER_USER="your-username"
export VCENTER_PASSWORD="your-password"
export VCENTER_INSECURE="false"  # Set to "true" for self-signed certificates
```

## 🚀 Quick Start

### Using the Clean Server

```bash
# Navigate to the clean server
cd mcp-server

# Install dependencies
uv sync

# Run the server locally
uv run python server.py

# Or build and run with Docker
make build
make docker-run
```

### Using Docker Compose

```bash
# Run both servers (if you have the main server)
docker-compose up

# Or run just the clean server
docker-compose up vmware-mcp-server-clean
```

## 📋 Available Tools (MCP stdio)

All operations are exposed as MCP stdio tools. Use JSON-RPC requests over stdio to interact with the server.

### Basic VM Operations
- `list_vms` - List all VMs in vCenter
- `get_vm_info` - Get detailed VM information
- `list_templates` - List all VM templates

### Power Management
- `power_on_vm` - Power on a VM by ID
- `power_off_vm` - Power off a VM by ID
- `restart_vm` - Restart a VM by ID

### VM Creation & Cloning
- `clone_vm` - Clone a VM with optional customization
- `deploy_from_template` - Deploy a new VM from a template with optional customization

#### Tool Input Schemas

- **clone_vm**
  ```json
  {
    "source_vm_id": "string",         // Required: Source VM ID to clone from
    "new_vm_name": "string",           // Required: Name for the new cloned VM
    "datastore_id": "string",          // Optional: Target datastore ID
    "resource_pool_id": "string",      // Optional: Target resource pool ID
    "folder_id": "string",             // Optional: Target folder ID
    "hostname": "string",              // Optional: Custom hostname for the new VM
    "ip_address": "string",            // Optional: Static IP address
    "netmask": "string",               // Optional: Subnet mask
    "gateway": "string",               // Optional: Default gateway
    "cpu_count": "integer",            // Optional: Number of CPU cores
    "memory_mb": "integer"             // Optional: Memory size in MB
  }
  ```
- **deploy_from_template**
  ```json
  {
    "template_id": "string",           // Required: Template VM ID to deploy from
    "new_vm_name": "string",           // Required: Name for the new deployed VM
    "datastore_id": "string",          // Optional: Target datastore ID
    "resource_pool_id": "string",      // Optional: Target resource pool ID
    "folder_id": "string",             // Optional: Target folder ID
    "hostname": "string",              // Optional: Custom hostname for the new VM
    "ip_address": "string",            // Optional: Static IP address
    "netmask": "string",               // Optional: Subnet mask
    "gateway": "string",               // Optional: Default gateway
    "cpu_count": "integer",            // Optional: Number of CPU cores
    "memory_mb": "integer"             // Optional: Memory size in MB
  }
  ```

## 🎯 How to Prompt the MCP Server

Here's how to interact with the VMware MCP server to perform common operations:

### 1. List All VMs

**Prompt:** "List all VMs in my vCenter environment"

**MCP Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "list_vms",
    "arguments": {}
  }
}
```

**Expected Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "📋 Found 3 VM(s):\n\n🟢 **web-server-01** (ID: `vm-1001`)\n   • Power State: POWERED_ON\n   • Guest OS: Ubuntu Linux (64-bit)\n   • CPU Count: 2\n   • Memory: 4096 MB\n   • IP Address: 192.168.1.10\n\n🔴 **database-server** (ID: `vm-1002`)\n   • Power State: POWERED_OFF\n   • Guest OS: CentOS Linux (64-bit)\n   • CPU Count: 4\n   • Memory: 8192 MB\n\n🟢 **app-server-01** (ID: `vm-1003`)\n   • Power State: POWERED_ON\n   • Guest OS: Ubuntu Linux (64-bit)\n   • CPU Count: 2\n   • Memory: 4096 MB\n   • IP Address: 192.168.1.20"
      }
    ]
  }
}
```

### 2. Create a VM (Clone from Existing VM)

**Prompt:** "Clone the web-server-01 VM and create a new VM called web-server-02 with IP address 192.168.1.11"

**MCP Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/call",
  "params": {
    "name": "clone_vm",
    "arguments": {
      "source_vm_id": "vm-1001",
      "new_vm_name": "web-server-02",
      "hostname": "web-server-02",
      "ip_address": "192.168.1.11",
      "netmask": "255.255.255.0",
      "gateway": "192.168.1.1"
    }
  }
}
```

**Expected Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "✅ Successfully initiated clone of VM 'web-server-01' to 'web-server-02'\n   • Source VM: web-server-01 (ID: vm-1001)\n   • New VM: web-server-02\n   • Task ID: task-12345\n   • Customization: Network"
      }
    ]
  }
}
```

### 2b. Create a VM with Custom Hardware (Clone)

**Prompt:** "Clone the web-server-01 VM and create a new VM called high-performance-server with 8 CPU cores, 16GB memory, on datastore-21, with IP 192.168.1.100"

**MCP Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/call",
  "params": {
    "name": "clone_vm",
    "arguments": {
      "source_vm_id": "vm-1001",
      "new_vm_name": "high-performance-server",
      "datastore_id": "datastore-21",
      "hostname": "high-performance-server",
      "ip_address": "192.168.1.100",
      "netmask": "255.255.255.0",
      "gateway": "192.168.1.1",
      "cpu_count": 8,
      "memory_mb": 16384
    }
  }
}
```

**Expected Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "✅ Successfully initiated clone of VM 'web-server-01' to 'high-performance-server'\n   • Source VM: web-server-01 (ID: vm-1001)\n   • New VM: high-performance-server\n   • Task ID: task-12347\n   • Customization: Network, CPU: 8 cores, Memory: 16384 MB"
      }
    ]
  }
}
```

### 3. Create a VM from Template

**Prompt:** "Deploy a new VM called prod-server-01 from the Ubuntu template with IP 192.168.1.50"

**MCP Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/call",
  "params": {
    "name": "deploy_from_template",
    "arguments": {
      "template_id": "vm-2001",
      "new_vm_name": "prod-server-01",
      "hostname": "prod-server-01",
      "ip_address": "192.168.1.50",
      "netmask": "255.255.255.0",
      "gateway": "192.168.1.1"
    }
  }
}
```

**Expected Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "✅ Successfully initiated clone of VM 'Ubuntu-Template' to 'prod-server-01'\n   • Source VM: Ubuntu-Template (ID: vm-2001)\n   • New VM: prod-server-01\n   • Task ID: task-12346\n   • Customization: Network"
      }
    ]
  }
}
```

### 3b. Create a VM from Template with Custom Hardware

**Prompt:** "Deploy a new VM called database-server from the CentOS template with 4 CPU cores, 8GB memory, on datastore-22, with IP 192.168.1.200"

**MCP Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/call",
  "params": {
    "name": "deploy_from_template",
    "arguments": {
      "template_id": "vm-2002",
      "new_vm_name": "database-server",
      "datastore_id": "datastore-22",
      "hostname": "database-server",
      "ip_address": "192.168.1.200",
      "netmask": "255.255.255.0",
      "gateway": "192.168.1.1",
      "cpu_count": 4,
      "memory_mb": 8192
    }
  }
}
```

**Expected Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "✅ Successfully initiated clone of VM 'CentOS-Template' to 'database-server'\n   • Source VM: CentOS-Template (ID: vm-2002)\n   • New VM: database-server\n   • Task ID: task-12348\n   • Customization: Network, CPU: 4 cores, Memory: 8192 MB"
      }
    ]
  }
}
```

### 4. Power Off a VM

**Prompt:** "Power off the database-server VM"

**MCP Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 4,
  "method": "tools/call",
  "params": {
    "name": "power_off_vm",
    "arguments": {
      "vm_id": "vm-1002"
    }
  }
}
```

**Expected Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 4,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "✅ Successfully powered off VM 'database-server' (ID: vm-1002)"
      }
    ]
  }
}
```

### 5. Get VM Details

**Prompt:** "Show me detailed information about the web-server-01 VM"

**MCP Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 5,
  "method": "tools/call",
  "params": {
    "name": "get_vm_info",
    "arguments": {
      "vm_id": "vm-1001"
    }
  }
}
```

**Expected Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 5,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "📋 **VM Details for 'web-server-01'**\n\n**Basic Information:**\n• ID: `vm-1001`\n• Name: web-server-01\n• Power State: 🟢 POWERED_ON\n• Guest OS: Ubuntu Linux (64-bit)\n• CPU Count: 2\n• Memory: 4096 MB\n• Version: vmx-19\n\n**Guest Information:**\n• IP Address: 192.168.1.10\n• Hostname: web-server-01\n• VMware Tools: RUNNING\n\n**Network Interfaces:**\n• Network adapter 1: VM Network"
      }
    ]
  }
}
```

### 6. List Available Templates

**Prompt:** "Show me all available VM templates"

**MCP Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 6,
  "method": "tools/call",
  "params": {
    "name": "list_templates",
    "arguments": {}
  }
}
```

**Expected Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 6,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "📋 Found 2 VM template(s):\n\n📄 **Ubuntu-Template** (ID: `vm-2001`)\n   • Detection: template property\n   • Guest OS: Ubuntu Linux (64-bit)\n   • CPU Count: 2\n   • Memory: 4096 MB\n   • Version: vmx-19\n   • Folder: /Templates\n\n📄 **CentOS-Template** (ID: `vm-2002`)\n   • Detection: template property\n   • Guest OS: CentOS Linux (64-bit)\n   • CPU Count: 4\n   • Memory: 8192 MB\n   • Version: vmx-19\n   • Folder: /Templates\n"
      }
    ]
  }
}
```

### 7. List Available Datastores

**Prompt:** "Show me all available datastores and their free space"

**MCP Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 7,
  "method": "tools/call",
  "params": {
    "name": "list_datastores",
    "arguments": {}
  }
}
```

**Expected Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 7,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "📋 Found 3 datastore(s):\n\n🟢 **datastore-21** (ID: `datastore-21`)\n   • Type: VMFS\n   • Capacity: 1000.0 GB\n   • Free Space: 800.0 GB (80.0%)\n   • Accessible: Yes\n\n🟡 **datastore-22** (ID: `datastore-22`)\n   • Type: VMFS\n   • Capacity: 500.0 GB\n   • Free Space: 75.0 GB (15.0%)\n   • Accessible: Yes\n\n🔴 **datastore-23** (ID: `datastore-23`)\n   • Type: VMFS\n   • Capacity: 200.0 GB\n   • Free Space: 10.0 GB (5.0%)\n   • Accessible: Yes"
      }
    ]
  }
}
```

## 📋 Usage Examples (MCP stdio)

All requests are sent as JSON-RPC over stdio. Example requests and expected responses:

### List All VMs
**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "list_vms",
    "arguments": {}
  }
}
```

### Clone a VM
**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/call",
  "params": {
    "name": "clone_vm",
    "arguments": {
      "source_vm_id": "vm-1001",
      "new_vm_name": "cloned-vm-01",
      "datastore_id": "datastore-21",
      "resource_pool_id": "resgroup-8",
      "folder_id": "group-v3",
      "hostname": "cloned-vm-01",
      "ip_address": "192.168.1.50",
      "netmask": "255.255.255.0",
      "gateway": "192.168.1.1"
    }
  }
}
```

### Deploy a VM from Template
**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/call",
  "params": {
    "name": "deploy_from_template",
    "arguments": {
      "template_id": "vm-2001",
      "new_vm_name": "webserver-01",
      "datastore_id": "datastore-21",
      "resource_pool_id": "resgroup-8",
      "folder_id": "group-v3",
      "hostname": "webserver-01",
      "ip_address": "192.168.1.60",
      "netmask": "255.255.255.0",
      "gateway": "192.168.1.1"
    }
  }
}
```

### Get Detailed VM Info
**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 4,
  "method": "tools/call",
  "params": {
    "name": "get_vm_info",
    "arguments": {
      "vm_id": "vm-1001"
    }
  }
}
```

### Power Management
**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 5,
  "method": "tools/call",
  "params": {
    "name": "power_on_vm",
    "arguments": {
      "vm_id": "vm-1001"
    }
  }
}
```

### List Templates
**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 6,
  "method": "tools/call",
  "params": {
    "name": "list_templates",
    "arguments": {}
  }
}
```

## 🏛️ Architecture Benefits

### Modular Design
- **Separation of concerns** - Each module has a single responsibility
- **Easy testing** - Individual modules can be tested independently
- **Maintainable** - Changes to one module don't affect others
- **Reusable** - VM operations can be imported and used elsewhere

### Configuration Management
- **Centralized config** - All environment variables handled in one place
- **Validation** - Automatic validation of required settings
- **Flexible** - Supports multiple environment variable naming conventions
- **Secure** - No sensitive data in logs or error messages

### Error Handling
- **Consistent** - All operations use the same error handling patterns
- **Informative** - Clear error messages with actionable information
- **Safe** - Operations check VM state before attempting actions

## 🔄 Development

### Adding New Operations

1. Add the function to `mcp-server/vm_creation.py` (for creation/cloning/template)
2. Add the tool definition to `mcp-server/server.py`
3. Add the tool handler to the server's request handler
4. Create tests in `mcp-server/test_power_management.py`

## 🎯 Key Features

- ✅ **Pure vmware-vcenter** - Uses only the official VMware SDK
- ✅ **MCP Protocol** - Works with stdio and follows MCP standards
- ✅ **Modular Architecture** - Clean separation of concerns
- ✅ **Docker Support** - Easy deployment and distribution
- ✅ **Modern Tooling** - Uses `uv` for dependency management
- ✅ **Comprehensive Testing** - Test scripts for all operations
- ✅ **Production Ready** - Error handling and validation

## 🔧 Troubleshooting

### Template Detection Issues

If you're having trouble with template detection (getting "No VM templates found"), the server includes a debug script to help identify the issue:

```bash
# Run the debug script to analyze VM properties
make debug-templates
```

This will:
- Show all available VM properties
- Check multiple template detection methods
- Provide suggestions for improving detection
- Help understand your vCenter's template organization

**Common Template Detection Methods:**
1. **Template Property** - VMs marked as templates in vCenter
2. **Name Pattern** - VMs with "template" in their name
3. **Folder Location** - VMs in template-specific folders
4. **VM Type** - VMs with type set to "template"

**If No Templates Are Found:**
- Verify templates exist in your vCenter
- Check if templates are in a specific folder
- Look for naming conventions used in your environment
- Ensure templates are properly marked as templates in vCenter

### Connection Issues

If you're getting connection errors:
1. Verify your `.env` file has correct vCenter credentials
2. Check network connectivity to your vCenter server
3. Ensure SSL certificate issues are handled (set `VCENTER_INSECURE=true` if needed)
4. Verify the vCenter user has appropriate permissions

### Permission Issues

Common permission requirements:
- **VM Management** - Power on/off, restart VMs
- **VM Creation** - Clone VMs, deploy from templates
- **Resource Pool Access** - Access to target resource pools
- **Datastore Access** - Read/write access to target datastores

This clean, modular implementation provides a solid foundation for VMware management through MCP! 🚀 

## VM Template Management

The server supports listing and deploying VMs from templates. Based on analysis of the [Ansible vmware_guest module](https://github.com/ansible-collections/community.vmware/blob/main/plugins/modules/vmware_guest.py), VMware has two main types of templates:

### **Template Types:**

1. **VM Templates** - Regular VMs converted to templates
   - These are VMs with `template` property set to `True`
   - They appear in the VM inventory
   - Deployed using `CloneVM_Task` API (same as VM cloning)

2. **Content Library Templates** - Advanced templates stored in Content Libraries
   - These are "pure templates" designed for template management
   - Stored in Content Libraries with URNs like `urn:vapi:com.vmware.content.library.Item:...`
   - Deployed using `DeployTemplate` API (different from cloning)

### **Template Detection:**

Our server intelligently detects both types:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "list_templates",
    "arguments": {}
  }
}
```

**Response shows both types:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "📋 **VMware Template Analysis**\n\n## 🔧 VM Templates (Converted VMs)\n✅ Found 1 VM template(s):\n\n📄 **ova-inf-k8s-master-uat-01** (ID: `vm-123`)\n   • Detection: name pattern\n   • Guest OS: Ubuntu Linux (64-bit)\n   • CPU Count: 2\n   • Memory: 4096 MB\n\n## 📚 Content Library Templates\n✅ Found 1 Content Library template(s):\n\n📚 **Ubuntu-Template-01-Testing**\n   • URN: `urn:vapi:com.vmware.content.library.Item:f677a69d-55b3-4f9b-a19e-5dfda38bb739:5c3e4892-782e-4a2e-b29e-7d06a182b4ce`\n   • Library: VM-Templates\n   • Guest OS: Ubuntu Linux (64-bit)\n   • CPU Count: 2\n   • Memory: 4444 MB\n\n## 📊 Summary\nTotal templates found: **2**\n- VM Templates: 1\n- Content Library Templates: 1"
      }
    ]
  }
}
```

### **Deploy from Template (Ansible-style):**

Following the Ansible approach, our `deploy_from_template` tool handles both types intelligently:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "deploy_from_template",
    "arguments": {
      "template_id": "vm-123",  // VM template ID
      "new_vm_name": "new-vm-from-template",
      "cpu_count": 4,
      "memory_mb": 8192
    }
  }
}
```

**Or for Content Library templates:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "deploy_from_template",
    "arguments": {
      "template_id": "urn:vapi:com.vmware.content.library.Item:f677a69d-55b3-4f9b-a19e-5dfda38bb739:5c3e4892-782e-4a2e-b29e-7d06a182b4ce",
      "new_vm_name": "new-vm-from-content-library",
      "cpu_count": 4,
      "memory_mb": 8192
    }
  }
}
```

### **How It Works (Under the Hood):**

1. **Template Detection**: Server checks if `template_id` starts with `urn:vapi:com.vmware.content.library.Item:`
2. **VM Templates**: Uses `CloneVM_Task` API (same as VM cloning)
3. **Content Library Templates**: Uses `DeployTemplate` API (different process)
4. **Unified Interface**: Same tool handles both types, just like Ansible's `vmware_guest` module

### **Creating Templates:**

**VM Templates:**
1. Right-click on a VM in vCenter
2. Select "Template" > "Convert to Template"
3. The VM becomes a template with `template=True`

**Content Library Templates:**
1. Use Content Library Manager in vCenter
2. Create templates from VMs or import OVAs
3. Templates are stored in Content Libraries with URNs

### **Comparison with Ansible:**

Our implementation follows the same pattern as Ansible's `vmware_guest` module:

```yaml
# Ansible playbook
- name: Create VM from template
  community.vmware.vmware_guest:
    template: "{{ vars.vcenter.template }}"  # Handles both types!
    name: "{{ item.host }}"
    hardware: "{{ item.hardware }}"
```

```json
// Our MCP equivalent
{
  "name": "deploy_from_template",
  "arguments": {
    "template_id": "template-id-or-urn",  // Handles both types!
    "new_vm_name": "new-vm",
    "cpu_count": 4,
    "memory_mb": 8192
  }
}
```

💡 **Key Insight**: Templates are either "converted VMs" (VM templates) or "pure templates" (Content Library templates), but both can be deployed using the same unified interface, just like Ansible does! 