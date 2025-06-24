#!/usr/bin/env python3
"""
Monitoring Module for VMware MCP Server
Handles VM and host metrics collection using pyVmomi
"""

from pyVmomi import vim
import connection


def get_vm_performance(vm_name: str) -> str:
    """Get detailed performance metrics for a specific VM."""
    service_instance = connection.get_service_instance()
    if not service_instance:
        return "Error: Could not connect to vCenter"
    
    try:
        content = service_instance.RetrieveContent()
        container = content.viewManager.CreateContainerView(
            content.rootFolder, [vim.VirtualMachine], True
        )
        
        vm = None
        for v in container.view:
            if v.name == vm_name:
                vm = v
                break
        
        if not vm:
            return f"VM '{vm_name}' not found"
        
        # Get performance manager
        perf_manager = content.perfManager
        
        # Define metrics we want to collect
        metric_ids = [
            vim.PerformanceManager.MetricId(counterId=6, instance="*"),    # CPU usage
            vim.PerformanceManager.MetricId(counterId=24, instance="*"),   # Memory usage
            vim.PerformanceManager.MetricId(counterId=110, instance="*"),  # Disk read rate
            vim.PerformanceManager.MetricId(counterId=111, instance="*"),  # Disk write rate
            vim.PerformanceManager.MetricId(counterId=104, instance="*"),  # Network received
            vim.PerformanceManager.MetricId(counterId=105, instance="*"),  # Network transmitted
        ]
        
        # Create query specification
        query = vim.PerformanceManager.QuerySpec(
            entity=vm,
            metricId=metric_ids,
            intervalId=20,  # 20-second intervals
            maxSample=1     # Get latest sample
        )
        
        # Query performance data
        result = perf_manager.QueryPerf([query])
        
        if not result:
            return f"No performance data available for VM '{vm_name}'"
        
        # Parse the results
        metrics = {}
        for sample in result[0].value:
            counter_id = sample.id.counterId
            instance = sample.id.instance
            value = sample.value[0] if sample.value else 0
            
            # Map counter IDs to readable names
            counter_names = {
                6: "CPU Usage (%)",
                24: "Memory Usage (MB)",
                110: "Disk Read (KB/s)",
                111: "Disk Write (KB/s)",
                104: "Network Received (KB/s)",
                105: "Network Transmitted (KB/s)"
            }
            
            metric_name = counter_names.get(counter_id, f"Counter {counter_id}")
            metrics[f"{metric_name} ({instance})"] = value
        
        # Format the results
        result_text = f"Performance Metrics for VM '{vm_name}':\n"
        result_text += f"- Power State: {vm.runtime.powerState}\n"
        result_text += f"- Guest OS: {vm.guest.guestFullName if vm.guest else 'Unknown'}\n"
        result_text += f"- VMware Tools: {vm.guest.toolsRunningStatus if vm.guest else 'Unknown'}\n\n"
        
        for metric_name, value in metrics.items():
            result_text += f"- {metric_name}: {value}\n"
        
        return result_text
        
    except Exception as e:
        return f"Error getting performance data: {e}"


def get_host_performance(host_name: str = None) -> str:
    """Get performance metrics for hosts."""
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
            if host_name is None or host.name == host_name:
                hosts.append(host)
        
        if not hosts:
            return f"Host '{host_name}' not found" if host_name else "No hosts found"
        
        result_text = f"Host Performance Metrics:\n\n"
        
        for host in hosts:
            result_text += f"Host: {host.name}\n"
            result_text += f"- Connection State: {host.runtime.connectionState}\n"
            result_text += f"- Power State: {host.runtime.powerState}\n"
            
            # Get hardware info
            if host.hardware:
                result_text += f"- CPU Model: {host.hardware.cpuPkg[0].description if host.hardware.cpuPkg else 'Unknown'}\n"
                result_text += f"- CPU Cores: {host.hardware.cpuInfo.numCpuCores}\n"
                result_text += f"- Memory: {host.hardware.memorySize // (1024**3)} GB\n"
            
            # Get resource usage
            if host.runtime.healthSystemRuntime:
                health = host.runtime.healthSystemRuntime
                result_text += f"- System Health: {health.systemHealth}\n"
            
            result_text += "\n"
        
        return result_text
        
    except Exception as e:
        return f"Error getting host performance: {e}"


def list_performance_counters() -> str:
    """List available performance counters."""
    service_instance = connection.get_service_instance()
    if not service_instance:
        return "Error: Could not connect to vCenter"
    
    try:
        content = service_instance.RetrieveContent()
        perf_manager = content.perfManager
        
        # Get available counters
        counters = perf_manager.perfCounter
        
        # Group by category
        categories = {}
        for counter in counters:
            category = counter.groupInfo.key
            if category not in categories:
                categories[category] = []
            categories[category].append({
                'name': counter.nameInfo.key,
                'unit': counter.unitInfo.key,
                'id': counter.key
            })
        
        result_text = "Available Performance Counters:\n\n"
        
        for category, counter_list in categories.items():
            result_text += f"Category: {category}\n"
            for counter in counter_list[:5]:  # Show first 5 per category
                result_text += f"  - {counter['name']} ({counter['unit']}) - ID: {counter['id']}\n"
            if len(counter_list) > 5:
                result_text += f"  ... and {len(counter_list) - 5} more\n"
            result_text += "\n"
        
        return result_text
        
    except Exception as e:
        return f"Error listing performance counters: {e}"


def get_vm_summary_stats() -> str:
    """Get summary statistics for all VMs."""
    service_instance = connection.get_service_instance()
    if not service_instance:
        return "Error: Could not connect to vCenter"
    
    try:
        content = service_instance.RetrieveContent()
        container = content.viewManager.CreateContainerView(
            content.rootFolder, [vim.VirtualMachine], True
        )
        
        total_vms = 0
        powered_on = 0
        powered_off = 0
        suspended = 0
        total_cpu = 0
        total_memory = 0
        
        for vm in container.view:
            total_vms += 1
            
            # Count power states
            if vm.runtime.powerState == vim.VirtualMachinePowerState.poweredOn:
                powered_on += 1
            elif vm.runtime.powerState == vim.VirtualMachinePowerState.poweredOff:
                powered_off += 1
            elif vm.runtime.powerState == vim.VirtualMachinePowerState.suspended:
                suspended += 1
            
            # Sum resources
            if vm.config and vm.config.hardware:
                total_cpu += vm.config.hardware.numCPU
                total_memory += vm.config.hardware.memoryMB
        
        result_text = "VM Summary Statistics:\n\n"
        result_text += f"Total VMs: {total_vms}\n"
        result_text += f"Powered On: {powered_on}\n"
        result_text += f"Powered Off: {powered_off}\n"
        result_text += f"Suspended: {suspended}\n"
        result_text += f"Total CPU Cores: {total_cpu}\n"
        result_text += f"Total Memory: {total_memory // 1024} GB\n"
        
        return result_text
        
    except Exception as e:
        return f"Error getting VM summary stats: {e}" 