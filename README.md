# VMware vSphere VM List Docker Container

This Docker container provides a simple way to list all VMs from a VMware vCenter server using the official VMware vSphere Automation SDK for Python.

## Prerequisites

- Docker and Docker Compose installed
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
   VCENTER_SERVER=your-vcenter-server.com
   VCENTER_USERNAME=administrator@vsphere.local
   VCENTER_PASSWORD=your_password
   ```

3. **Build and run the container**
   ```bash
   docker-compose up --build
   ```

## Manual Docker Commands

If you prefer to use Docker commands directly:

### Build the image
```bash
docker build -t vmware-vm-list .
```

### Run the container
```bash
docker run --rm \
  -e VCENTER_SERVER=your-vcenter-server.com \
  -e VCENTER_USERNAME=administrator@vsphere.local \
  -e VCENTER_PASSWORD=your_password \
  vmware-vm-list \
  python list_vms.py \
  --server your-vcenter-server.com \
  --username administrator@vsphere.local \
  --password your_password \
  --skip-verification
```

## Command Line Options

The script supports the following command line arguments:

- `--server`: vCenter server address (required)
- `--username`: Username for authentication (required)
- `--password`: Password for authentication (required)
- `--skip-verification`: Skip SSL certificate verification (optional, useful for self-signed certificates)

## Example Output

```
==================================================
List Of VMs
==================================================
[{'memory_size_MiB': 4096,
  'name': 'Test-VM-1',
  'power_state': 'POWERED_ON',
  'vm': 'vm-123'},
 {'memory_size_MiB': 2048,
  'name': 'Test-VM-2',
  'power_state': 'POWERED_OFF',
  'vm': 'vm-456'}]
==================================================
Total VMs found: 2
```

## Troubleshooting

### SSL Certificate Issues
If you encounter SSL certificate errors, use the `--skip-verification` flag:
```bash
python list_vms.py --server vcenter.example.com --username admin --password pass --skip-verification
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

This container uses the following VMware SDK packages:
- vsphere-automation-sdk==8.0.2.0
- vsphere-automation-sdk-python==8.0.2.0
- vsphere-automation-sdk-python-lib==8.0.2.0
- vsphere-automation-sdk-python-samples==8.0.2.0

## License

This project is provided as-is for educational and development purposes. 