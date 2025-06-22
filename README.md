# VMware MCP Server

A Model Context Protocol (MCP) server for VMware vCenter management. This server provides tools for listing VMs, getting detailed VM information, and managing VM power states through the MCP interface.

## Features

- **List VMs**: Get a list of all VMs in vCenter
- **VM Details**: Get comprehensive information about specific VMs including:
  - Basic information (name, ID)
  - Power state
  - Memory configuration
  - CPU details
  - Network adapters
  - Disk information
- **Power Management**: Control VM power states with intelligent state checking:
  - Power on VMs (only if powered off)
  - Power off VMs (only if powered on)
  - Restart VMs (only if powered on)
  - Check current power state

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
│   ├── get_vm_info.py    # VM details functionality
│   ├── power_vm.py       # Power management functionality
│   └── helpers.py        # Shared utility functions
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

The server provides six main tools:

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
📋 **VM Information: Test-VM-1**
**ID:** vm-123
**Power State:** POWERED_ON
**Guest OS:** Ubuntu Linux (64-bit)
**Guest Family:** LINUX
**CPU Cores:** 2
**CPU Sockets:** 1
**Memory:** 4.0 GB

💾 **Disks:**
  • 100.0 GB (NVME)

🌐 **Network Adapters:**
  • VM Network (MAC: 00:50:56:8a:12:34)
```

### 3. `power-on-vm`
Power on a VM if it's not already powered on.

**Input Schema:**
```json
{
  "vm_id": "vm-123"
}
```

**Example Output:**
```
✅ Successfully powered on Test-VM-1
```

### 4. `power-off-vm`
Power off a VM if it's not already powered off.

**Input Schema:**
```json
{
  "vm_id": "vm-123"
}
```

**Example Output:**
```
✅ Successfully powered off Test-VM-1
```

### 5. `restart-vm`
Restart a VM if it's powered on.

**Input Schema:**
```json
{
  "vm_id": "vm-123"
}
```

**Example Output:**
```
✅ Successfully restarted Test-VM-1
```

### 6. `get-power-state`
Get the current power state of a VM.

**Input Schema:**
```json
{
  "vm_id": "vm-123"
}
```

**Example Output:**
```
🔌 **Power State for Test-VM-1:** POWERED_ON
```

## Power Management Logic

The power management tools include intelligent state checking:

- **Power On**: Only attempts to power on if the VM is currently powered off
- **Power Off**: Only attempts to power off if the VM is currently powered on
- **Restart**: Only attempts to restart if the VM is currently powered on
- **State Checking**: All operations first verify the current power state before taking action

This prevents unnecessary operations and provides clear feedback about the VM's current state.

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
- For power operations, the user needs appropriate permissions to modify VM power states

### Power Operation Issues
- Ensure the VM is not in a transitional state (powering on/off)
- Some VMs may have power protection enabled that prevents power operations
- Check vCenter logs for detailed error messages

## Security Notes

- Never commit your `.env` file with real credentials to version control
- The `VCENTER_INSECURE` flag should only be used in development/testing environments
- Consider using environment variables or secrets for production deployments
- Power management operations can affect running services - use with caution

## Dependencies

This project uses the following key dependencies:
- `mcp`: Model Context Protocol server framework
- `vmware-vapi`: VMware vSphere Automation SDK
- `uv`: Fast Python package manager

## License

This project is provided as-is for educational and development purposes. 