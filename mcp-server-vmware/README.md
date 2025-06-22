# VMware MCP Server (Clean Implementation)

A clean, modular MCP server for VMware vCenter using the official `vmware-vcenter` Python package.

## 🏗️ Modular Architecture

The project is organized into clean, focused modules:

- **`server.py`** - Main MCP server entry point and tool definitions
- **`vm_operations.py`** - All VM-related operations (power management, info, etc.)
- **`config.py`** - Configuration management and environment variable handling
- **`test_power_management.py`** - Test script for power management functionality

## 🚀 Features

### Available Tools

1. **`get-all-vms`** - List all VMs in vCenter
2. **`power-on-vm`** - Power on a VM by ID
3. **`power-off-vm`** - Power off a VM by ID
4. **`restart-vm`** - Restart a VM by ID
5. **`get-vm-info`** - Get detailed information about a specific VM

### Power Management Features

- ✅ **State checking** - Won't try to power on already powered-on VMs
- ✅ **Error handling** - Proper error messages for all operations
- ✅ **Detailed feedback** - Shows VM names and operation results
- ✅ **Type safety** - Fixed all type checking issues
- ✅ **MCP compatible** - Works with any MCP client

## 🔧 Setup

### Environment Variables

Set these environment variables:

```bash
export VCENTER_SERVER="your-vcenter-host"
export VCENTER_USERNAME="your-username"
export VCENTER_PASSWORD="your-password"
export VCENTER_INSECURE="false"  # Set to "true" for self-signed certificates
```

### Installation

```bash
# Install dependencies
uv sync

# Or using the Makefile
make install
```

## 🧪 Testing

### Test Power Management

```bash
# Run power management tests
uv run python test_power_management.py

# Or using the Makefile
make test
```

### Test the Server

```bash
# Run the server locally
uv run python server.py

# Or using the Makefile
make run
```

## 🐳 Docker

### Build and Run

```bash
# Build the Docker image
make build

# Run in Docker (set environment variables first)
make docker-run
```

### Docker Compose

The server is also available in the main project's `docker-compose.yml` as `vmware-mcp-server-clean`.

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

1. Add the function to `vm_operations.py`
2. Add the tool definition to `server.py`
3. Add the tool handler to the `call_tool` function
4. Create tests in `test_power_management.py`

### Project Structure
```
mcp-server-vmware/
├── server.py              # Main MCP server
├── vm_operations.py       # VM operations module
├── config.py             # Configuration management
├── test_power_management.py  # Test script
├── pyproject.toml        # Project dependencies
├── Dockerfile           # Docker configuration
├── Makefile            # Development tasks
└── README.md           # This file
```

This clean, modular implementation provides a solid foundation for VMware management through MCP! 🚀 