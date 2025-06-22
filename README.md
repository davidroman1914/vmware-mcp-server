# VMware MCP Server

A Model Context Protocol (MCP) server for VMware vCenter management, providing comprehensive VM operations including listing, detailed information retrieval, power management, and advanced VM creation/cloning capabilities.

## Features

### VM Management
- **List VMs**: Get all VMs in vCenter with basic information
- **Get VM Info**: Retrieve detailed information about a specific VM including hardware, disks, networks, and power state
- **Power Management**: Power on, off, and restart VMs with intelligent state checking
- **VM Deployment**: Deploy VMs from templates with comprehensive customization
- **Template Creation**: Create templates from existing VMs
- **VM Cloning**: Clone VMs with full customization options

### Advanced Customization
- **Hardware Customization**: CPU, memory, and disk specifications
- **Network Configuration**: Multiple network adapters with custom settings
- **Guest Customization**: Hostname, IP address, DNS, and gateway configuration
- **Placement Control**: Datacenter, cluster, and folder placement
- **Wait for IP**: Automatic IP address detection with timeout

## Installation

### Prerequisites
- Python 3.8+
- VMware vCenter access
- VMware vSphere Automation SDK for Python

### Setup
1. Clone the repository:
```bash
git clone <repository-url>
cd vmware-mcp-server
```

2. Install dependencies using `uv`:
```bash
uv sync
```

3. Configure environment variables:
```bash
cp env.example .env
# Edit .env with your vCenter credentials
```

## Configuration

Set the following environment variables in your `.env` file:

```bash
VCENTER_HOST=your-vcenter-host
VCENTER_USERNAME=your-username
VCENTER_PASSWORD=your-password
VCENTER_PORT=443
VCENTER_SSL_VERIFY=false
```

## Usage

### Running the Server

#### Local Development
```bash
uv run python main.py
```

#### Docker
```bash
docker-compose up
```

### Available Tools

#### Basic VM Operations
- `list-vms` - List all VMs in vCenter
- `get-vm-info` - Get detailed VM information
- `get-power-state` - Check VM power state

#### Power Management
- `power-on-vm` - Power on a VM
- `power-off-vm` - Power off a VM  
- `restart-vm` - Restart a VM

#### Advanced VM Management
- `deploy-vm-from-template` - Deploy VM from template with customization
- `create-template-from-vm` - Create template from existing VM
- `clone-vm` - Clone VM with full customization

## Using Prompts

The VMware MCP Server understands natural language prompts and automatically selects the appropriate tools. Here are examples of what you can ask:

### **VM Information & Discovery**

**List all VMs:**
```
Show me all the VMs in vCenter
List all virtual machines
What VMs do I have?
```

**Get VM details:**
```
Tell me about VM vm-123
What are the specs of my web server VM?
Get detailed information for vm-456
Show me the hardware configuration of vm-789
```

**Check power state:**
```
Is VM vm-123 powered on?
What's the power state of my database server?
Check if vm-456 is running
```

### **Power Management**

**Power on VMs:**
```
Power on VM vm-123
Start my web server VM
Turn on vm-456
Boot up the database server
```

**Power off VMs:**
```
Power off VM vm-123
Shut down my test VM
Turn off vm-456
Stop the development server
```

**Restart VMs:**
```
Restart VM vm-123
Reboot my web server
Restart vm-456
```

### **VM Creation & Deployment**

**Deploy from template (basic):**
```
Deploy a new VM from template template-123 named "my-new-vm"
Create a VM called "web-server" from template "ubuntu-template"
Deploy vm-456 from template "windows-template" and name it "test-server"
```

**Deploy with customization:**
```
Deploy a VM from template "template-123" named "production-web". Put it in datacenter "dc-001" and cluster "cluster-001". Give it 4 CPU cores, 8GB RAM, and connect it to "VM Network". Set hostname to "prod-web-01" and IP to "192.168.1.100".
```

**Deploy with network configuration:**
```
Create a VM named "app-server" from template "centos-template" with 2 CPU cores and 4GB RAM. Set the IP address to 192.168.1.50, netmask 255.255.255.0, gateway 192.168.1.1, and DNS servers 8.8.8.8 and 8.8.4.4. Wait for it to get an IP address.
```

### **Template Management**

**Create templates:**
```
Create a template from VM vm-123 named "golden-template"
Convert my web server VM to a template called "web-template"
Make a template from vm-456 named "base-template" with description "Base Ubuntu 22.04 template"
```

### **VM Cloning**

**Simple cloning:**
```
Clone VM vm-123 and name the new VM "backup-vm"
Create a copy of vm-456 named "test-copy"
Clone my web server to create "web-server-backup"
```

**Clone with modifications:**
```
Clone VM vm-123 to create "scaled-vm" with 8GB RAM instead of 4GB and 4 CPU cores instead of 2
Create a copy of vm-456 named "dev-server" with 2 CPU cores, 4GB RAM, and hostname "dev-server-01"
Clone my database server to "db-backup" and change the IP to 192.168.1.200
```

### **Complex Workflows**

**Multi-step operations:**
```
First create a template from VM vm-123 named "base-template", then deploy 3 VMs from that template named "web-01", "web-02", and "web-03" with 2 CPU cores and 4GB RAM each
```

**Environment setup:**
```
Deploy a development environment: Create a VM named "dev-web" from template "ubuntu-template" with 2 CPU cores, 4GB RAM, IP 192.168.1.10, and hostname "dev-web-01". Then create a VM named "dev-db" from template "mysql-template" with 4 CPU cores, 8GB RAM, IP 192.168.1.11, and hostname "dev-db-01"
```

### **What to Expect**

When you use these prompts, the MCP server will:

1. **Parse your request** and identify the appropriate tools to use
2. **Extract parameters** like VM IDs, names, hardware specs, and network settings
3. **Execute the operations** using the VMware vSphere API
4. **Provide detailed feedback** including:
   - Success confirmations with VM IDs
   - IP addresses (if requested and available)
   - Error messages with specific details
   - Progress updates for long-running operations

**Example responses:**
```
✅ Successfully deployed VM 'web-server' (ID: vm-789) with IP: 192.168.1.100
✅ Successfully powered on Test-VM-1
❌ Error: VM with ID vm-999 not found
✅ Successfully created template 'golden-template' (ID: template-456) from VM 'Test-VM-1'
```

### **Tips for Better Results**

- **Be specific**: Include VM IDs, template IDs, and exact names when possible
- **Use natural language**: "Power on my web server" works better than technical commands
- **Include context**: Mention datacenters, clusters, or networks if relevant
- **Specify requirements**: Include CPU, memory, disk, and network needs
- **Ask for confirmation**: The server will tell you what it's doing and provide results

The server handles the complex VMware API interactions behind the scenes, so you can focus on describing what you want rather than how to do it!

### Example Usage

#### List All VMs
```json
{
  "name": "list-vms"
}
```

#### Get VM Information
```json
{
  "name": "get-vm-info",
  "arguments": {
    "vm_id": "vm-123"
  }
}
```

#### Power On VM
```json
{
  "name": "power-on-vm",
  "arguments": {
    "vm_id": "vm-123"
  }
}
```

#### Deploy VM from Template
```json
{
  "name": "deploy-vm-from-template",
  "arguments": {
    "template_id": "template-456",
    "vm_name": "new-vm-001",
    "datacenter": "dc-001",
    "cluster": "cluster-001",
    "hardware": {
      "cpu": {"count": 2, "cores_per_socket": 1},
      "memory": {"size_mib": 4096}
    },
    "disk": [
      {"datastore": "datastore-001"}
    ],
    "networks": [
      {"name": "VM Network", "device_type": "VMXNET3"}
    ],
    "customization": {
      "hostname": "new-vm-001",
      "ip_address": "192.168.1.100",
      "netmask": "255.255.255.0",
      "gateway": "192.168.1.1",
      "dns_servers": ["8.8.8.8", "8.8.4.4"]
    },
    "wait_for_ip": true,
    "wait_timeout": 300
  }
}
```

#### Clone VM
```json
{
  "name": "clone-vm",
  "arguments": {
    "source_vm_id": "vm-123",
    "new_vm_name": "cloned-vm-001",
    "hardware": {
      "cpu": {"count": 4, "cores_per_socket": 2},
      "memory": {"size_mib": 8192}
    },
    "customization": {
      "hostname": "cloned-vm-001",
      "ip_address": "192.168.1.101"
    }
  }
}
```

## Architecture

The server is organized into modular components:

- `main.py` - Entry point and server initialization
- `mcp-server/` - Core MCP server implementation
  - `server.py` - MCP server with tool definitions
  - `list_vm.py` - VM listing functionality
  - `get_vm_info.py` - Detailed VM information retrieval
  - `power_vm.py` - Power management operations
  - `vm_management.py` - Advanced VM creation and cloning
  - `helpers.py` - Shared utilities and client management

## Error Handling

The server includes comprehensive error handling:
- Connection failures
- Authentication errors
- Invalid VM/Template IDs
- API timeouts
- Customization failures

All errors are logged and returned with descriptive messages.

## Troubleshooting

### Common Issues

1. **Connection Failed**: Verify vCenter host and credentials
2. **SSL Certificate Errors**: Set `VCENTER_SSL_VERIFY=false` for self-signed certificates
3. **Authentication Failed**: Check username/password and permissions
4. **VM Not Found**: Verify VM ID exists in vCenter
5. **Template Deployment Fails**: Ensure template exists and has proper permissions

### Logging

Enable debug logging by setting the log level:
```bash
export LOG_LEVEL=DEBUG
```

## Development

### Adding New Tools

1. Create a new module in `mcp-server/`
2. Implement the tool function
3. Add tool definition to `server.py`
4. Update this README with documentation

### Testing

Test individual functions:
```bash
uv run python -c "from mcp_server.list_vm import list_vms_text; print(list_vms_text())"
```

## License

[Add your license information here] 