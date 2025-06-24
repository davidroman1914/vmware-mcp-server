# VMware MCP Server

A clean, focused Model Context Protocol (MCP) server for VMware vCenter management using pyvmomi.

## 🚀 Features

- **VM Management**: List, create, power on/off VMs
- **Host Monitoring**: Physical host information and health
- **Performance Metrics**: CPU, memory, disk, network monitoring
- **Fast REST API**: Quick VM listing and operations
- **Modular Design**: Clean, maintainable code structure

## Installation

## 🚀 Features

- **VM Listing**: List all VMs with detailed information (power state, IP, CPU, memory, network adapters)
- **Power Management**: Power on/off VMs by name
- **VM Creation**: Create new VMs from templates with full customization (IP, hostname, CPU, memory, disk)
- **MCP stdio Protocol**: Fully compatible with MCP clients
- **Docker Support**: Easy deployment and testing

## 🏛️ Project Structure

```
vmware-mcp-server/
├── mcp-server/                  # Python logic only
│   ├── server.py              # MCP server with stdio protocol
│   ├── vm_info.py             # VM listing and information
│   ├── power.py               # Power management (on/off)
│   ├── vm_creation.py         # VM creation from templates
│   └── test_server.py         # Test script
├── requirements.txt            # Python dependencies (pyvmomi)
├── pyproject.toml              # Project configuration
├── Dockerfile                  # Docker configuration
├── docker-compose.yml          # Docker Compose configuration
├── Makefile                    # Build and run targets
├── env.example                 # Environment variables template
└── README.md                   # This file
```

## 🔧 Setup

### Prerequisites
- Python 3.10+
- VMware vCenter access
- Docker (optional)

### Environment Variables

Create a `.env` file based on `env.example`:

```bash
VCENTER_HOST=your-vcenter-host
VCENTER_USER=your-username
VCENTER_PASSWORD=your-password
VCENTER_INSECURE=true  # Set to "true" for self-signed certificates
```

## 🚀 Quick Start

### Using Docker (Recommended)

```bash
# Setup environment
make setup

# Build and run
make build
make run-docker

# Or run detached
make run-detached

# Test the server
make test-docker
```

### Using Local Python

```bash
# Install dependencies
make install

# Run locally
make run

# Test locally
make test
```

## 📋 Available MCP Tools

### 1. List VMs (`list_vms`)
Lists all VMs in vCenter with detailed information.

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

### 2. Power On VM (`power_on_vm`)
Powers on a VM by name.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/call",
  "params": {
    "name": "power_on_vm",
    "arguments": {
      "vm_name": "my-vm"
    }
  }
}
```

### 3. Power Off VM (`power_off_vm`)
Powers off a VM by name.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/call",
  "params": {
    "name": "power_off_vm",
    "arguments": {
      "vm_name": "my-vm"
    }
  }
}
```

### 4. Create VM from Template (`create_vm_from_template`)
Creates a new VM from a template with full customization.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 4,
  "method": "tools/call",
  "params": {
    "name": "create_vm_from_template",
    "arguments": {
      "template_name": "ubuntu-template",
      "vm_name": "new-vm",
      "hostname": "new-vm",
      "ip_address": "192.168.1.100",
      "netmask": "255.255.255.0",
      "gateway": "192.168.1.1",
      "network_name": "VM Network",
      "cpu_count": 2,
      "memory_mb": 2048,
      "disk_size_gb": 20,
      "datastore_name": "datastore1"
    }
  }
}
```

## 🎯 How to Prompt the MCP Server

Here are example prompts you can use with the MCP server:

### List all VMs
```
List all virtual machines in vCenter
```

### Power management
```
Power on the VM named "ubuntu-server"
```

```
Power off the VM named "test-vm"
```

### Create a new VM
```
Create a new VM named "web-server" from the "ubuntu-template" with IP address 192.168.1.50, 4 CPUs, 8GB RAM, and 50GB disk
```

## 🛠️ Development

### Available Make Targets

```bash
make help              # Show all available commands
make setup             # Create .env file from template
make install           # Install Python dependencies
make run               # Run server locally
make test              # Test server locally
make build             # Build Docker image
make run-docker        # Run server in Docker
make test-docker       # Test server in Docker
make stop              # Stop Docker containers
make clean             # Clean up Docker resources
make logs              # View Docker logs
make docker-shell      # Start shell in Docker container
```

### Testing

```bash
# Test locally
make test

# Test in Docker
make test-docker

# Start interactive shell for manual testing
make docker-shell
```

## 🔍 Troubleshooting

### Connection Issues
1. Verify vCenter credentials are correct
2. Check network connectivity to vCenter
3. For self-signed certificates, set `VCENTER_INSECURE=true`

### VM Creation Issues
1. Ensure the template VM exists and is accessible
2. Verify network and datastore names are correct
3. Check that the target IP address is available on the network

### Power Management Issues
1. Verify the VM name exists
2. Check that the VM is not in a locked state
3. Ensure you have sufficient permissions

## 📄 License

This project is licensed under the MIT License. 