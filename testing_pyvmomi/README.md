# pyvmomi Testing Environment

This directory contains a clean testing environment for VMware vCenter operations using the **pyvmomi** library.

## What This Tests

- **VM Listing**: List all VMs with detailed information (CPU, memory, guest OS, template status)
- **VM Cloning**: Simple VM cloning without customization
- **Resource Discovery**: Finding datastores, resource pools, and folders

## Setup

1. **Update the `.env` file** in the parent directory with your vCenter credentials:
   ```bash
   VCENTER_HOST=your-vcenter-ip-or-hostname
   VCENTER_USER=administrator@vsphere.local
   VCENTER_PASSWORD=your-actual-password
   VCENTER_INSECURE=true  # or false depending on your cert setup
   ```

2. **Build and run the test**:
   ```bash
   make test
   ```

## Available Commands

- `make build` - Build the Docker image
- `make test` - Run the VM operations test
- `make shell` - Start a shell in the container for manual testing
- `make clean` - Clean up Docker resources
- `make help` - Show all available commands

## What the Test Does

1. **Connects to vCenter** using pyvmomi
2. **Lists all VMs** with detailed information:
   - Name and ID
   - Power state
   - CPU count and memory
   - Guest OS
   - Template status
3. **Finds a source VM** (preferably powered off)
4. **Gathers placement resources** (datastore, resource pool, folder)
5. **Attempts to clone the VM** with basic settings
6. **Monitors the clone task** and reports results

## Comparison with vmware-vcenter

This environment lets us compare:
- **pyvmomi** (SOAP API) vs **vmware-vcenter** (REST API)
- **Connection methods** and authentication
- **VM discovery** and property access
- **Cloning approaches** and customization options

## Files

- `test_vm_operations.py` - Main test script
- `requirements.txt` - Python dependencies
- `Dockerfile` - Container setup
- `Makefile` - Build and test commands
- `README.md` - This file 