#!/usr/bin/env python3
"""
Host Information Module for VMware MCP Server
Handles detailed information about physical hosts/rack servers
"""

from pyVmomi import vim
import connection


def list_hosts() -> str:
    """List all physical hosts with basic information."""
    service_instance = connection.get_service_instance()
    if not service_instance:
        return "Error: Could not connect to vCenter"
    
    try:
        content = service_instance.RetrieveContent()
        container = content.viewManager.CreateContainerView(
            content.rootFolder, [vim.HostSystem], True
        )
        
        hosts = []
        for host in container.view:
            hosts.append({
                'name': host.name,
                'connection_state': host.runtime.connectionState,
                'power_state': host.runtime.powerState,
                'maintenance_mode': host.runtime.inMaintenanceMode
            })
        
        if hosts:
            result = f"Found {len(hosts)} physical hosts:\n\n"
            for host in hosts:
                result += f"Host: {host['name']}\n"
                result += f"- Connection: {host['connection_state']}\n"
                result += f"- Power State: {host['power_state']}\n"
                result += f"- Maintenance Mode: {host['maintenance_mode']}\n\n"
            return result
        else:
            return "No hosts found"
            
    except Exception as e:
        return f"Error: {e}"


def get_host_details(host_name: str) -> str:
    """Get detailed information about a specific physical host."""
    service_instance = connection.get_service_instance()
    if not service_instance:
        return "Error: Could not connect to vCenter"
    
    try:
        content = service_instance.RetrieveContent()
        container = content.viewManager.CreateContainerView(
            content.rootFolder, [vim.HostSystem], True
        )
        
        host = None
        for h in container.view:
            if h.name == host_name:
                host = h
                break
        
        if not host:
            return f"Host '{host_name}' not found"
        
        result = f"Detailed Host Information for '{host_name}':\n\n"
        
        # Basic Information
        result += "=== BASIC INFORMATION ===\n"
        result += f"- Name: {host.name}\n"
        result += f"- Connection State: {host.runtime.connectionState}\n"
        result += f"- Power State: {host.runtime.powerState}\n"
        result += f"- Maintenance Mode: {host.runtime.inMaintenanceMode}\n"
        result += f"- Boot Time: {host.runtime.bootTime}\n"
        result += f"- Uptime: {host.runtime.uptime} seconds\n\n"
        
        # Hardware Information
        if host.hardware:
            result += "=== HARDWARE INFORMATION ===\n"
            result += f"- CPU Model: {host.hardware.cpuPkg[0].description if host.hardware.cpuPkg else 'Unknown'}\n"
            result += f"- CPU Cores: {host.hardware.cpuInfo.numCpuCores}\n"
            result += f"- CPU Threads: {host.hardware.cpuInfo.numCpuThreads}\n"
            result += f"- CPU Packages: {len(host.hardware.cpuPkg)}\n"
            result += f"- Total Memory: {host.hardware.memorySize // (1024**3)} GB\n"
            result += f"- Memory Slots: {len(host.hardware.memoryDevice)}\n"
            
            # CPU Details
            if host.hardware.cpuPkg:
                for i, cpu in enumerate(host.hardware.cpuPkg):
                    result += f"- CPU {i+1}: {cpu.description}\n"
                    result += f"  Cores: {cpu.hz / (1024**3):.1f} GHz\n"
            
            # Memory Details
            if host.hardware.memoryDevice:
                result += f"- Memory Devices:\n"
                for i, mem in enumerate(host.hardware.memoryDevice):
                    result += f"  Slot {i+1}: {mem.capacity // (1024**3)} GB\n"
            
            result += "\n"
        
        # Network Information
        if host.config and host.config.network:
            result += "=== NETWORK INFORMATION ===\n"
            result += f"- Virtual Switches: {len(host.config.network.vswitch)}\n"
            result += f"- Port Groups: {len(host.config.network.portgroup)}\n"
            result += f"- Physical NICs: {len(host.config.network.pnic)}\n"
            result += f"- VMkernel NICs: {len(host.config.network.vnic)}\n"
            
            # Physical NICs
            if host.config.network.pnic:
                result += f"- Physical Network Adapters:\n"
                for pnic in host.config.network.pnic:
                    result += f"  {pnic.device}: {pnic.spec.linkSpeed.speedMb} Mbps\n"
            
            result += "\n"
        
        # Storage Information
        if host.config and host.config.storageDevice:
            result += "=== STORAGE INFORMATION ===\n"
            result += f"- HBAs: {len(host.config.storageDevice.hostBusAdapter)}\n"
            result += f"- Storage Arrays: {len(host.config.storageDevice.scsiLun)}\n"
            
            # Storage Arrays
            if host.config.storageDevice.scsiLun:
                result += f"- Storage Arrays:\n"
                for lun in host.config.storageDevice.scsiLun:
                    if hasattr(lun, 'displayName'):
                        result += f"  {lun.displayName}\n"
                        if hasattr(lun, 'capacityBlock') and hasattr(lun, 'blockSize'):
                            capacity_gb = (lun.capacityBlock * lun.blockSize) // (1024**3)
                            result += f"    Capacity: {capacity_gb} GB\n"
            
            result += "\n"
        
        # VM Information
        if host.vm:
            result += "=== VIRTUAL MACHINES ===\n"
            result += f"- Total VMs: {len(host.vm)}\n"
            
            powered_on = sum(1 for vm in host.vm if vm.runtime.powerState == vim.VirtualMachinePowerState.poweredOn)
            powered_off = sum(1 for vm in host.vm if vm.runtime.powerState == vim.VirtualMachinePowerState.poweredOff)
            
            result += f"- Powered On: {powered_on}\n"
            result += f"- Powered Off: {powered_off}\n"
            
            # List VMs
            result += f"- VM List:\n"
            for vm in host.vm:
                result += f"  {vm.name} ({vm.runtime.powerState})\n"
            
            result += "\n"
        
        # Datastore Information
        if host.datastore:
            result += "=== DATASTORES ===\n"
            result += f"- Total Datastores: {len(host.datastore)}\n"
            
            for ds in host.datastore:
                result += f"- {ds.name}\n"
                if ds.summary:
                    capacity_gb = ds.summary.capacity // (1024**3)
                    free_gb = ds.summary.freeSpace // (1024**3)
                    result += f"  Capacity: {capacity_gb} GB, Free: {free_gb} GB\n"
            
            result += "\n"
        
        # Health Information
        if host.runtime.healthSystemRuntime:
            result += "=== HEALTH STATUS ===\n"
            health = host.runtime.healthSystemRuntime
            
            if hasattr(health, 'systemHealth'):
                result += f"- System Health: {health.systemHealth}\n"
            
            if hasattr(health, 'hardwareStatus'):
                result += f"- Hardware Status: {health.hardwareStatus}\n"
            
            if hasattr(health, 'cpuPowerInfo'):
                result += f"- CPU Power Info: {health.cpuPowerInfo}\n"
            
            result += "\n"
        
        return result
        
    except Exception as e:
        return f"Error: {e}"


def get_host_performance_metrics(host_name: str) -> str:
    """Get detailed performance metrics for a specific host."""
    service_instance = connection.get_service_instance()
    if not service_instance:
        return "Error: Could not connect to vCenter"
    
    try:
        content = service_instance.RetrieveContent()
        container = content.viewManager.CreateContainerView(
            content.rootFolder, [vim.HostSystem], True
        )
        
        host = None
        for h in container.view:
            if h.name == host_name:
                host = h
                break
        
        if not host:
            return f"Host '{host_name}' not found"
        
        # Get performance manager
        perf_manager = content.perfManager
        
        # Define host metrics we want to collect
        metric_ids = [
            vim.PerformanceManager.MetricId(counterId=1, instance="*"),     # CPU usage
            vim.PerformanceManager.MetricId(counterId=4, instance="*"),     # Memory usage
            vim.PerformanceManager.MetricId(counterId=110, instance="*"),   # Disk read rate
            vim.PerformanceManager.MetricId(counterId=111, instance="*"),   # Disk write rate
            vim.PerformanceManager.MetricId(counterId=104, instance="*"),   # Network received
            vim.PerformanceManager.MetricId(counterId=105, instance="*"),   # Network transmitted
        ]
        
        # Create query specification
        query = vim.PerformanceManager.QuerySpec(
            entity=host,
            metricId=metric_ids,
            intervalId=20,  # 20-second intervals
            maxSample=1     # Get latest sample
        )
        
        # Query performance data
        result = perf_manager.QueryPerf([query])
        
        if not result:
            return f"No performance data available for host '{host_name}'"
        
        # Parse the results
        cpu_metrics = {}
        other_metrics = {}
        
        for sample in result[0].value:
            counter_id = sample.id.counterId
            instance = sample.id.instance
            value = sample.value[0] if sample.value else 0
            
            # Map counter IDs to readable names
            counter_names = {
                1: "CPU Usage",
                4: "Memory Usage (MB)",
                110: "Disk Read (KB/s)",
                111: "Disk Write (KB/s)",
                104: "Network Received (KB/s)",
                105: "Network Transmitted (KB/s)"
            }
            
            metric_name = counter_names.get(counter_id, f"Counter {counter_id}")
            
            # Separate CPU metrics for better formatting
            if counter_id == 1:  # CPU
                cpu_metrics[instance] = value
            else:
                other_metrics[f"{metric_name} ({instance})"] = value
        
        # Get host CPU configuration
        cpu_cores = 0
        if host.hardware:
            cpu_cores = host.hardware.cpuInfo.numCpuCores
        
        # Format the results
        result_text = f"Performance Metrics for Host '{host_name}':\n"
        result_text += f"- CPU Cores: {cpu_cores}\n"
        result_text += f"- Connection State: {host.runtime.connectionState}\n"
        result_text += f"- Power State: {host.runtime.powerState}\n\n"
        
        result_text += "=== CPU USAGE (per core) ===\n"
        
        # Format CPU metrics
        total_cpu = 0
        for instance, value in cpu_metrics.items():
            if instance == "":  # Overall CPU
                if cpu_cores > 0:
                    result_text += f"- Overall CPU: {value:.1f}% ({value/cpu_cores:.1f}% per core avg)\n"
                else:
                    result_text += f"- Overall CPU: {value:.1f}%\n"
                total_cpu = value
            else:
                result_text += f"- CPU {instance}: {value:.1f}%\n"
        
        if cpu_metrics:
            result_text += f"- Total CPU Usage: {total_cpu:.1f}% across all cores\n"
        
        result_text += "\n=== OTHER METRICS ===\n"
        for metric_name, value in other_metrics.items():
            result_text += f"- {metric_name}: {value}\n"
        
        return result_text
        
    except Exception as e:
        return f"Error getting host performance: {e}"


def get_host_hardware_health(host_name: str) -> str:
    """Get hardware health information for a specific host."""
    service_instance = connection.get_service_instance()
    if not service_instance:
        return "Error: Could not connect to vCenter"
    
    try:
        content = service_instance.RetrieveContent()
        container = content.viewManager.CreateContainerView(
            content.rootFolder, [vim.HostSystem], True
        )
        
        host = None
        for h in container.view:
            if h.name == host_name:
                host = h
                break
        
        if not host:
            return f"Host '{host_name}' not found"
        
        result = f"Hardware Health for Host '{host_name}':\n\n"
        
        # Get hardware health information
        if host.runtime.healthSystemRuntime:
            health = host.runtime.healthSystemRuntime
            
            result += "=== SYSTEM HEALTH ===\n"
            if hasattr(health, 'systemHealth'):
                result += f"- Overall Health: {health.systemHealth}\n"
            
            if hasattr(health, 'hardwareStatus'):
                result += f"- Hardware Status: {health.hardwareStatus}\n"
            
            if hasattr(health, 'cpuPowerInfo'):
                result += f"- CPU Power: {health.cpuPowerInfo}\n"
            
            if hasattr(health, 'memoryHealthInfo'):
                result += f"- Memory Health: {health.memoryHealthInfo}\n"
            
            if hasattr(health, 'storageHealthInfo'):
                result += f"- Storage Health: {health.storageHealthInfo}\n"
            
            if hasattr(health, 'networkHealthInfo'):
                result += f"- Network Health: {health.networkHealthInfo}\n"
            
            result += "\n"
        
        # Get sensor information if available
        if host.hardware and hasattr(host.hardware, 'sensorInfo'):
            result += "=== SENSOR INFORMATION ===\n"
            for sensor in host.hardware.sensorInfo:
                result += f"- {sensor.name}: {sensor.currentReading} {sensor.unit}\n"
                result += f"  Status: {sensor.healthState}\n"
            
            result += "\n"
        
        return result
        
    except Exception as e:
        return f"Error getting hardware health: {e}" 