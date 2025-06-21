# VMware MCP Server

A Model Context Protocol (MCP) server for VMware vCenter management. This server provides tools for listing VMs and getting detailed VM information through the MCP interface.

## Features

- **List VMs**: Get a list of all VMs in vCenter
- **VM Details**: Get comprehensive information about specific VMs including:
  - Basic information (name, ID)
  - Power state
  - Memory configuration
  - CPU details
  - Network adapters
  - Disk information

## Prerequisites

- Python 3.11+
- Access to a VMware vCenter server
- Valid credentials for the vCenter server

## Quick Start

1. **Clone or download this repository**

2. **Set up environment variables**
   ```bash
   cp env.example .env
   ```
   Edit the `.env` file with your vCenter details:
   ```bash
   VCENTER_HOST=your-vcenter-server.com
   VCENTER_USER=administrator@vsphere.local
   VCENTER_PASSWORD=your_password
   VCENTER_INSECURE=false
   ```

3. **Install dependencies**
   ```bash
   make install
   ```

4. **Run the MCP server**
   ```bash
   make run-local
   ```

## Project Structure

```
vmware-mcp-server/
├── mcp-server/           # MCP server package
│   ├── __init__.py       # Package initialization
│   ├── server.py         # Main MCP server
│   ├── list_vm.py        # VM listing functionality
│   └── get_vm_info.py    # VM details functionality
├── main.py               # Entry point
├── pyproject.toml        # Dependencies and project config
├── Makefile              # Build and run commands
└── README.md             # This file
```

## Available Commands

### Local Development
```bash
make install          # Install dependencies
make run-local        # Run MCP server locally
make run-server       # Run server directly
make shell            # Start Python shell
```

### Docker (Optional)
```bash
make setup            # Create .env file
make build            # Build Docker image
make run              # Run in Docker
make stop             # Stop Docker containers
```

## MCP Tools

The server provides two main tools:

### 1. `list-vms`
Lists all VMs in the vCenter server.

**Input Schema:**
```json
{}
```

**Example Output:**
```
vm-123: Test-VM-1
vm-456: Test-VM-2
vm-789: Production-Server
```

### 2. `get-vm-info`
Get detailed information about a specific VM.

**Input Schema:**
```json
{
  "vm_id": "vm-123"
}
```

**Example Output:**
```
### Basic Information
- **Name:** Test-VM-1
- **ID:** vm-123

### Power State
- **Power State:** POWERED_ON

### Memory
- **Memory:** 4096 MiB (4.0 GB)

### CPU
- **CPU:** 2 cores

### Network Adapters
- **Network Adapters:** 1
  - **Network: VM Network | MAC: 00:50:56:8a:12:34 | Type: ASSIGNED | Connected: True**

### Disks
- **Disks:** 1
  - **Capacity:** 100.0 GB
```

## Troubleshooting

### SSL Certificate Issues
If you encounter SSL certificate errors, set `VCENTER_INSECURE=true` in your `.env` file.

### Connection Issues
- Ensure your vCenter server is accessible
- Verify the server address and credentials
- Check if any firewall rules are blocking the connection

### Permission Issues
- Make sure the user has sufficient permissions to access vCenter
- The user should have at least read access to the vCenter inventory

## Security Notes

- Never commit your `.env` file with real credentials to version control
- The `VCENTER_INSECURE` flag should only be used in development/testing environments
- Consider using environment variables or secrets for production deployments

## Dependencies

This project uses the following key dependencies:
- `mcp`: Model Context Protocol server framework
- `vmware-vapi`: VMware vSphere Automation SDK
- `uv`: Fast Python package manager

## License

This project is provided as-is for educational and development purposes. 