# ESXi MCP Server

> **⚠️ All development, testing, and running of this project must be done inside Docker containers. Do not run any code or install dependencies on your host machine. Use Docker Compose for all workflows.**

A Model Context Protocol (MCP) server for managing VMware ESXi/vSphere environments. This server provides tools and resources for virtual machine management through the MCP protocol.

## Features

- **Virtual Machine Management**: Create, clone, delete, power on/off VMs
- **Resource Monitoring**: Get performance metrics for VMs (CPU, memory, storage, network)
- **MCP Protocol Support**: Full compliance with MCP standards
- **Docker Support**: Easy deployment with Docker containers
- **Comprehensive Testing**: Extensive test suite with mocking
- **Configuration Management**: Support for YAML config files and environment variables

## Quick Start (Docker Only)

### 1. Clone the repository
```bash
git clone <repository-url>
cd vmware-mcp-server
```

### 2. Create configuration file
```bash
cp config.yaml.sample config.yaml
# Edit config.yaml with your VMware settings
```

### 3. Build the Docker images
```bash
docker-compose build --no-cache
```

### 4. Run the server (in a container)
```bash
docker-compose up -d
```

### 5. Run the test suite (in a container)
```bash
docker-compose --profile test run test
```

> **Note:** Never run `pip install`, `pytest`, or any Python commands on your host. All commands must be run via Docker Compose as shown above.

## Configuration

### Configuration File (config.yaml)

```yaml
# VMware Configuration
vcenter_host: "192.168.1.100"
vcenter_user: "administrator@vsphere.local"
vcenter_password: "your-password"
datacenter: "Datacenter1"
cluster: "Cluster1"  # Optional
datastore: "Datastore1"
network: "VM Network"
insecure: true  # Skip SSL verification

# Server Configuration
api_key: "your-api-key-here"
log_file: "./logs/vmware_mcp.log"
log_level: "INFO"
host: "0.0.0.0"
port: 8000
```

### Environment Variables

You can also configure the server using environment variables in your `docker-compose.yml` or by passing them with `docker-compose run`.

## Available Tools

The MCP server provides the following tools for VMware management:

### Basic VM Operations
- **list_vms**: List all VMs in the vCenter
- **create_vm**: Create a new VM from scratch
- **clone_vm**: Clone an existing VM
- **delete_vm**: Delete a VM
- **power_on_vm**: Power on a VM
- **power_off_vm**: Power off a VM

### Advanced VM Creation (Template-based)
- **create_vm_from_template**: Create a VM from template with customization (similar to Ansible vmware_guest)

This advanced tool supports:
- Template-based VM creation
- Cluster and folder placement
- Disk configuration
- Hardware specification (CPU, memory)
- Network configuration with IP addressing
- Guest customization
- Wait for IP address functionality

#### Example Usage for Advanced VM Creation

```json
{
  "name": "web-server-01",
  "template_name": "ubuntu-template",
  "cluster": "production-cluster",
  "folder": "/vm/",
  "disk_spec": [
    {
      "size_gb": 50,
      "name": "disk1.vmdk",
      "type": "SATA"
    }
  ],
  "hardware_spec": {
    "cpu_count": 4,
    "memory_mb": 8192
  },
  "network_spec": [
    {
      "device_type": "VMXNET3",
      "network_id": "VM Network",
      "ip": "192.168.1.100",
      "netmask": "255.255.255.0",
      "gateway": "192.168.1.1"
    }
  ],
  "customization_spec": {
    "hostname": "web-server-01",
    "domain": "example.com"
  },
  "wait_for_ip": true,
  "wait_timeout": 300
}
```

This functionality mirrors the capabilities of the Ansible `community.vmware.vmware_guest` module, providing the same level of control and customization for VM deployment.

## Available Resources

The server provides VM resources with performance metrics:

- **VM Information**: Name, power state, CPU count, memory, guest OS, tools status
- **Performance Metrics**: CPU usage, memory usage, storage usage, network I/O

## Development & Testing (Docker Only)

### Build the images
```bash
docker-compose build --no-cache
```

### Run the server
```bash
docker-compose up -d
```

### Run the test suite
```bash
docker-compose --profile test run test
```

### Stopping and cleaning up
```bash
docker-compose down --remove-orphans
```

## Project Structure

```
vmware-mcp-server/
├── src/                    # Source code
│   ├── __init__.py
│   ├── __main__.py        # Main entry point
│   ├── config.py          # Configuration management
│   ├── vmware.py          # VMware operations
│   └── mcp_server.py      # MCP server implementation
├── tests/                 # Test suite
│   ├── __init__.py
│   ├── conftest.py        # Pytest configuration
│   ├── test_config.py     # Configuration tests
│   ├── test_vmware.py     # VMware tests
│   └── test_mcp_server.py # MCP server tests
├── config.yaml.sample     # Sample configuration
├── requirements.txt       # Python dependencies (for Docker only)
├── pyproject.toml         # Project metadata and tool config
├── Dockerfile             # Docker image definition
├── docker-compose.yml     # Docker Compose configuration
├── Makefile               # Development tasks (calls Docker Compose)
└── README.md              # This file
```

## Makefile (Docker Only)

All Makefile commands are wrappers for Docker Compose. Example:

```bash
make build         # docker-compose build --no-cache
make test          # docker-compose --profile test run test
make up            # docker-compose up -d
make down          # docker-compose down --remove-orphans
```

> **Do not use `pip`, `pytest`, or any Python tools on your host. Always use Docker Compose or the Makefile.**

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Troubleshooting

### Common Issues

1. **Connection Errors**: Verify VMware credentials and network connectivity
2. **SSL Certificate Issues**: Set `insecure: true` for self-signed certificates
3. **Permission Errors**: Ensure the user has appropriate VMware permissions
4. **Resource Not Found**: Check datacenter, cluster, datastore, and network names

### Logs

Check the logs for detailed error information:

```bash
# View Docker logs
docker logs vmware-mcp-server

# View application logs
tail -f logs/vmware_mcp.log
```

## Support

For issues and questions:

1. Check the troubleshooting section
2. Review the test examples
3. Open an issue on GitHub
4. Check the MCP documentation

## Changelog

### Version 1.0.0
- Initial release
- Basic VM management operations
- MCP protocol support
- Docker containerization
- Comprehensive test suite

## Author

Bright8192

## Acknowledgments

- VMware pyvmomi team
- MCP Protocol development team

## Using with Goose and Other LLMs

This MCP server is designed to work with AI assistants like Goose through the Model Context Protocol (MCP). Here's how to interact with it effectively.

### Setup with Goose

1. **Install Goose** (if not already installed):
   ```bash
   # Follow Goose installation instructions
   ```

2. **Configure Goose to use this MCP server**:
   ```yaml
   # In your Goose configuration
   mcpServers:
     vmware-mcp-server:
       command: docker
       args: ["run", "--rm", "-i", "vmware-mcp-server:latest"]
       env:
         VCENTER_HOST: "your-vcenter-host"
         VCENTER_USER: "your-username"
         VCENTER_PASSWORD: "your-password"
         API_KEY: "your-api-key"
   ```

### Example Prompts and Responses

#### Basic VM Management

**Prompt:** "List all virtual machines in my vCenter"

**Expected Response:**
```
I'll list all the virtual machines in your vCenter for you.

[Using list_vms tool]
Found 5 virtual machines:
- web-server-01 (Powered On, IP: 192.168.1.100)
- db-server-01 (Powered Off)
- test-vm-01 (Powered On, IP: 192.168.1.101)
- template-ubuntu (Powered Off)
- template-windows (Powered Off)
```

**Prompt:** "Power on the web-server-01 VM"

**Expected Response:**
```
I'll power on the web-server-01 virtual machine for you.

[Using power_on tool]
Successfully powered on VM 'web-server-01'
```

**Prompt:** "Create a new VM called 'app-server-01' with 4 CPUs and 8GB RAM"

**Expected Response:**
```
I'll create a new virtual machine with your specifications.

[Using create_vm tool]
Successfully created VM 'app-server-01' with 4 CPUs and 8192MB RAM
```

#### Advanced VM Creation (Template-based)

**Prompt:** "Create a new web server VM from the ubuntu template. Name it 'web-server-02', put it in the production cluster, give it 50GB disk, 4 CPUs, 8GB RAM, and configure it with IP 192.168.1.102. Wait for it to get an IP address."

**Expected Response:**
```
I'll create a new web server VM from the ubuntu template with your specifications.

[Using create_vm_from_template tool]
Successfully created VM 'web-server-02' from template 'ubuntu-template' with ID: vm-789
VM got IP address: 192.168.1.102
```

**Prompt:** "Clone the template-ubuntu VM and name the new one 'test-server-01'"

**Expected Response:**
```
I'll clone the ubuntu template to create a new VM for you.

[Using clone_vm tool]
Successfully cloned VM 'template-ubuntu' to 'test-server-01'
```

#### Complex Infrastructure Requests

**Prompt:** "I need to deploy a 3-tier application. Create three VMs: a web server (web-tier-01) with 2 CPUs and 4GB RAM, an application server (app-tier-01) with 4 CPUs and 8GB RAM, and a database server (db-tier-01) with 8 CPUs and 16GB RAM. Use the ubuntu template for all of them and put them in the production cluster."

**Expected Response:**
```
I'll help you deploy your 3-tier application infrastructure.

[Using create_vm_from_template tool for each VM]
Successfully created VM 'web-tier-01' from template 'ubuntu-template' with ID: vm-101
Successfully created VM 'app-tier-01' from template 'ubuntu-template' with ID: vm-102  
Successfully created VM 'db-tier-01' from template 'ubuntu-template' with ID: vm-103

Your 3-tier application infrastructure is now deployed:
- Web Tier: web-tier-01 (2 CPUs, 4GB RAM)
- Application Tier: app-tier-01 (4 CPUs, 8GB RAM)  
- Database Tier: db-tier-01 (8 CPUs, 16GB RAM)
```

#### Troubleshooting and Monitoring

**Prompt:** "What's the status of all my VMs?"

**Expected Response:**
```
I'll check the status of all your virtual machines.

[Using list_vms tool]
Here's the current status of your VMs:
- web-server-01: Powered On (IP: 192.168.1.100)
- web-server-02: Powered On (IP: 192.168.1.102)
- app-server-01: Powered Off
- db-server-01: Powered On (IP: 192.168.1.103)
- test-server-01: Powered Off
```

**Prompt:** "Delete the test-server-01 VM"

**Expected Response:**
```
I'll delete the test-server-01 virtual machine for you.

[Using delete_vm tool]
Successfully deleted VM 'test-server-01'
```

### Best Practices for Prompts

1. **Be Specific**: Include VM names, resource specifications, and network details
2. **Use Clear Names**: Use descriptive VM names that indicate their purpose
3. **Specify Resources**: Always mention CPU, memory, and disk requirements
4. **Network Configuration**: Include IP addresses, networks, and cluster placement when needed
5. **Template Usage**: Mention which template to use for new VMs

### Available Operations

The LLM can perform these operations through the MCP server:

- **List VMs**: Get inventory of all virtual machines
- **Create VMs**: Create new VMs from scratch or from templates
- **Clone VMs**: Duplicate existing VMs or templates
- **Power Management**: Power on/off virtual machines
- **Delete VMs**: Remove virtual machines
- **Advanced Configuration**: Network setup, disk configuration, hardware specs

### Error Handling

The LLM will inform you if operations fail and provide error details:

```
I tried to create the VM but encountered an error:
"Template ubuntu-template not found"

Please check that the template name is correct and exists in your vCenter.
```

This integration allows you to manage your VMware infrastructure through natural language conversations with AI assistants like Goose.
