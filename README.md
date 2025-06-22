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
│   ├── vm_operations.py       # VM operations module
│   ├── config.py             # Configuration management
│   ├── test_power_management.py  # Test script
│   ├── pyproject.toml        # Project dependencies
│   ├── Dockerfile           # Docker configuration
│   ├── Makefile            # Development tasks
│   └── README.md           # Detailed documentation
├── docker-compose.yml       # Docker Compose configuration
├── Makefile                # Main project tasks
└── README.md              # This file
```

## 🔧 Setup

### Prerequisites
- Python 3.10+
- VMware vCenter access
- Docker (optional)

### Environment Variables

Set these environment variables:

```bash
export VCENTER_SERVER="your-vcenter-host"
export VCENTER_USERNAME="your-username"
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

## 📋 Available Tools

### Basic VM Operations
- `get-all-vms` - List all VMs in vCenter
- `get-vm-info` - Get detailed VM information

### Power Management
- `power-on-vm` - Power on a VM by ID
- `power-off-vm` - Power off a VM by ID
- `restart-vm` - Restart a VM by ID

## 🧪 Testing

### Test Power Management

```bash
cd mcp-server
uv run python test_power_management.py
```

### Test the Server

```bash
cd mcp-server
uv run python server.py
```

## 🐳 Docker

### Build and Run

```bash
cd mcp-server

# Build the Docker image
make build

# Run in Docker (set environment variables first)
make docker-run
```

### Docker Compose

The server is available in `docker-compose.yml` as `vmware-mcp-server-clean`.

## 📋 Usage Examples

### List All VMs
```bash
# Returns formatted list of all VMs with power states
get-all-vms
```

### Power Management
```bash
# Power on a VM
power-on-vm vm-2027

# Power off a VM
power-off-vm vm-2010

# Restart a VM
restart-vm vm-2011

# Get detailed VM info
get-vm-info vm-2010
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

1. Add the function to `mcp-server/vm_operations.py`
2. Add the tool definition to `mcp-server/server.py`
3. Add the tool handler to the `call_tool` function
4. Create tests in `mcp-server/test_power_management.py`

## 🎯 Key Features

- ✅ **Pure vmware-vcenter** - Uses only the official VMware SDK
- ✅ **MCP Protocol** - Works with stdio and follows MCP standards
- ✅ **Modular Architecture** - Clean separation of concerns
- ✅ **Docker Support** - Easy deployment and distribution
- ✅ **Modern Tooling** - Uses `uv` for dependency management
- ✅ **Comprehensive Testing** - Test scripts for all operations
- ✅ **Production Ready** - Error handling and validation

This clean, modular implementation provides a solid foundation for VMware management through MCP! 🚀 