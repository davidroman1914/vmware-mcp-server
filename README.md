# VMware vSphere VM Management

This project provides both standalone Python scripts and an MCP (Model Context Protocol) server for VMware vSphere VM management.

## Project Structure

```
vmware-mcp-server/
├── scripts/           # Standalone Python scripts for testing
│   ├── list_vms.py    # VM listing script
│   └── test_connection.py  # SDK connection test
├── mcp-server/        # MCP server implementation
│   ├── server.py      # Main MCP server
│   └── pyproject.toml # MCP server dependencies
├── Dockerfile         # Docker configuration
├── docker-compose.yml # Docker Compose services
├── Makefile          # Build and run commands
└── requirements.txt  # VMware SDK dependencies
```

## Prerequisites

- Docker and Docker Compose installed
- Access to a VMware vCenter server
- Valid credentials for the vCenter server

## Quick Start

1. **Set up environment variables**
   ```bash
   make setup
   ```
   Edit the `.env` file with your vCenter details:
   ```bash
   VCENTER_SERVER=your-vcenter-server.com
   VCENTER_USERNAME=administrator@vsphere.local
   VCENTER_PASSWORD=your_password
   ```

2. **Build the Docker image**
   ```bash
   make build
   ```

## Usage

### Standalone Scripts

**Test the connection:**
```bash
make test-script
```

**Run VM listing script:**
```bash
make run
```

**Open shell in container:**
```bash
make shell
```

**Manual script execution:**
```bash
docker-compose run --rm vmware-vm-list python scripts/list_vms.py \
  --server your-vcenter-server.com \
  --username admin \
  --password password \
  --skip-verification
```

### MCP Server

**Run the MCP server:**
```bash
make run-mcp
```

The MCP server provides the following tools:

- `list_vms` - List all VMs in vCenter server
- `get_vm_details` - Get detailed information about a specific VM

## MCP Server Tools

### list_vms
Lists all VMs in the vCenter server with their basic information.

**Parameters:**
- `server` (required): vCenter server address
- `username` (required): Username for authentication
- `password` (required): Password for authentication
- `skip_verification` (optional): Skip SSL certificate verification

### get_vm_details
Gets detailed information about a specific VM.

**Parameters:**
- `vm_id` (required): VM ID (e.g., vm-123)
- `server` (required): vCenter server address
- `username` (required): Username for authentication
- `password` (required): Password for authentication
- `skip_verification` (optional): Skip SSL certificate verification

## Docker Services

The project includes two Docker services:

1. **vmware-vm-list**: Runs standalone scripts for testing and manual execution
2. **vmware-mcp-server**: Runs the MCP server for integration with MCP clients

## Development

**Build and test everything:**
```bash
make all
```

**Clean up:**
```bash
make clean
```

## Example Output

### Standalone Script
```
==================================================
List Of VMs
==================================================
[Summary(vm='vm-2010', name='ova-inf-dns-01.ova.nydig.local', power_state=State(string='POWERED_ON'), cpu_count=2, memory_size_mib=2048)]
==================================================
Total VMs found: 12
```

### MCP Server Response
```
VMware vCenter VM List
==================================================
Total VMs found: 12

• ova-inf-dns-01.ova.nydig.local (ID: vm-2010)
  Power State: POWERED_ON, CPU: 2, Memory: 2048 MiB

• ova-inf-nfs-uat-01 (ID: vm-2011)
  Power State: POWERED_ON, CPU: 2, Memory: 4096 MiB
```

## Troubleshooting

### SSL Certificate Issues
If you encounter SSL certificate errors, use the `--skip-verification` flag:
```bash
python scripts/list_vms.py --server vcenter.example.com --username admin --password pass --skip-verification
```

### Connection Issues
- Ensure your vCenter server is accessible from the Docker host
- Verify the server address and credentials
- Check if any firewall rules are blocking the connection

### Permission Issues
- Make sure the user has sufficient permissions to list VMs in vCenter
- The user should have at least read access to the vCenter inventory

## Security Notes

- The `--skip-verification` flag disables SSL certificate verification and should only be used in development/testing environments
- Never commit your `.env` file with real credentials to version control
- Consider using environment variables or Docker secrets for production deployments

## Dependencies

This project uses:
- VMware vSphere Automation SDK for Python (from GitHub)
- MCP Python SDK for the MCP server implementation
- Docker for containerization

## License

This project is provided as-is for educational and development purposes. 