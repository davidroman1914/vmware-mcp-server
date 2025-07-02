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
        cpu_metrics = {}
        other_metrics = {}
        
        for sample in result[0].value:
            counter_id = sample.id.counterId
            instance = sample.id.instance
            value = sample.value[0] if sample.value else 0
            
            # Map counter IDs to readable names
            counter_names = {
                6: "CPU Usage",
                24: "Memory Usage (MB)",
                110: "Disk Read (KB/s)",
                111: "Disk Write (KB/s)",
                104: "Network Received (KB/s)",
                105: "Network Transmitted (KB/s)"
            }
            
            metric_name = counter_names.get(counter_id, f"Counter {counter_id}")
            
            # Separate CPU metrics for better formatting
            if counter_id == 6:  # CPU
                cpu_metrics[instance] = value
            else:
                other_metrics[f"{metric_name} ({instance})"] = value
        
        # Get VM CPU configuration
        cpu_count = 0
        max_cpu_mhz = 0
        if vm.config and vm.config.hardware:
            cpu_count = vm.config.hardware.numCPU
            # Try to get max CPU speed from host or use a reasonable default
            if vm.runtime.host and vm.runtime.host.hardware and vm.runtime.host.hardware.cpuPkg:
                max_cpu_mhz = vm.runtime.host.hardware.cpuPkg[0].hz / 1000000  # Convert Hz to MHz
            else:
                max_cpu_mhz = 3000  # Default to 3 GHz if we can't determine
        
        # Format the results
        result_text = f"Performance Metrics for VM '{vm_name}':\n"
        result_text += f"- Power State: {vm.runtime.powerState}\n"
        result_text += f"- Guest OS: {vm.guest.guestFullName if vm.guest else 'Unknown'}\n"
        result_text += f"- VMware Tools: {vm.guest.toolsRunningStatus if vm.guest else 'Unknown'}\n"
        result_text += f"- CPU Cores: {cpu_count}\n"
        result_text += f"- Max CPU Speed: {max_cpu_mhz:.0f} MHz ({max_cpu_mhz/1000:.1f} GHz)\n"
        
        result_text += "\n=== CPU USAGE ===\n"
        
        # Format CPU metrics in a user-friendly way
        total_cpu = 0
        for instance, value in cpu_metrics.items():
            if instance == "":  # Overall CPU
                total_cpu = value
                if cpu_count > 0:
                    avg_per_core = value / cpu_count
                    utilization_percent = (avg_per_core / max_cpu_mhz) * 100 if max_cpu_mhz > 0 else 0
                    result_text += f"- Overall CPU: {value:.1f} MHz (VMware's way)\n"
                    result_text += f"- Average per Core: {avg_per_core:.1f} MHz\n"
                    result_text += f"- CPU Speed: {avg_per_core/1000:.2f} GHz per core\n"
                    result_text += f"- CPU Utilization: {utilization_percent:.1f}% of max speed\n"
                else:
                    result_text += f"- Overall CPU: {value:.1f} MHz\n"
            else:
                # For individual CPU instances, show as MHz/Hz
                if cpu_count > 0:
                    per_core_value = value / cpu_count
                    utilization_percent = (per_core_value / max_cpu_mhz) * 100 if max_cpu_mhz > 0 else 0
                    result_text += f"- CPU {instance}: {value:.1f} MHz (VMware) / {per_core_value:.1f} MHz per core / {per_core_value/1000:.2f} GHz / {utilization_percent:.1f}% utilization\n"
                else:
                    result_text += f"- CPU {instance}: {value:.1f} MHz\n"
        
        if cpu_metrics and cpu_count > 0:
            avg_utilization = (total_cpu / cpu_count / max_cpu_mhz) * 100 if max_cpu_mhz > 0 else 0
            result_text += f"\n💡 **Explanation:** VMware shows CPU usage in MHz (speed), not percentage.\n"
            result_text += f"   Your VM's CPU cores are running at {total_cpu/cpu_count/1000:.2f} GHz each.\n"
            result_text += f"   This represents {avg_utilization:.1f}% of the maximum CPU speed.\n"
        
        result_text += "\n=== OTHER METRICS ===\n"
        for metric_name, value in other_metrics.items():
            result_text += f"- {metric_name}: {value}\n"
        
        return result_text
        
    except Exception as e:
        return f"Error getting performance data: {e}"


def get_host_performance(host_name: str) -> str:
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
                6: "CPU Usage",
                24: "Memory Usage (MB)",
                110: "Disk Read (KB/s)",
                111: "Disk Write (KB/s)",
                104: "Network Received (KB/s)",
                105: "Network Transmitted (KB/s)"
            }
            
            metric_name = counter_names.get(counter_id, f"Counter {counter_id}")
            
            # Separate CPU metrics for better formatting
            if counter_id == 6:  # CPU
                cpu_metrics[instance] = value
            else:
                other_metrics[f"{metric_name} ({instance})"] = value
        
        # Get host CPU configuration
        cpu_count = 0
        max_cpu_mhz = 0
        if host.hardware and host.hardware.cpuInfo:
            cpu_count = host.hardware.cpuInfo.numCpuCores
            if host.hardware.cpuPkg:
                max_cpu_mhz = host.hardware.cpuPkg[0].hz / 1000000  # Convert Hz to MHz
            else:
                max_cpu_mhz = 3000  # Default to 3 GHz if we can't determine
        
        # Format the results
        result_text = f"Performance Metrics for Host '{host_name}':\n"
        result_text += f"- Connection State: {host.runtime.connectionState}\n"
        result_text += f"- Power State: {host.runtime.powerState}\n"
        result_text += f"- CPU Cores: {cpu_count}\n"
        result_text += f"- Max CPU Speed: {max_cpu_mhz:.0f} MHz ({max_cpu_mhz/1000:.1f} GHz)\n"
        
        result_text += "\n=== CPU USAGE ===\n"
        
        # Format CPU metrics in a user-friendly way
        total_cpu = 0
        for instance, value in cpu_metrics.items():
            if instance == "":  # Overall CPU
                total_cpu = value
                if cpu_count > 0:
                    avg_per_core = value / cpu_count
                    utilization_percent = (avg_per_core / max_cpu_mhz) * 100 if max_cpu_mhz > 0 else 0
                    result_text += f"- Overall CPU: {value:.1f} MHz (VMware's way)\n"
                    result_text += f"- Average per Core: {avg_per_core:.1f} MHz\n"
                    result_text += f"- CPU Speed: {avg_per_core/1000:.2f} GHz per core\n"
                    result_text += f"- CPU Utilization: {utilization_percent:.1f}% of max speed\n"
                else:
                    result_text += f"- Overall CPU: {value:.1f} MHz\n"
            else:
                # For individual CPU instances, show as MHz/Hz
                if cpu_count > 0:
                    per_core_value = value / cpu_count
                    utilization_percent = (per_core_value / max_cpu_mhz) * 100 if max_cpu_mhz > 0 else 0
                    result_text += f"- CPU {instance}: {value:.1f} MHz (VMware) / {per_core_value:.1f} MHz per core / {per_core_value/1000:.2f} GHz / {utilization_percent:.1f}% utilization\n"
                else:
                    result_text += f"- CPU {instance}: {value:.1f} MHz\n"
        
        if cpu_metrics and cpu_count > 0:
            avg_utilization = (total_cpu / cpu_count / max_cpu_mhz) * 100 if max_cpu_mhz > 0 else 0
            result_text += f"\n💡 **Explanation:** VMware shows CPU usage in MHz (speed), not percentage.\n"
            result_text += f"   Your host's CPU cores are running at {total_cpu/cpu_count/1000:.2f} GHz each.\n"
            result_text += f"   This represents {avg_utilization:.1f}% of the maximum CPU speed.\n"
        
        result_text += "\n=== OTHER METRICS ===\n"
        for metric_name, value in other_metrics.items():
            result_text += f"- {metric_name}: {value}\n"
        
        return result_text
        
    except Exception as e:
        return f"Error getting performance data: {e}"


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


def debug_vm_performance_raw(vm_name: str) -> str:
    """Debug function to show raw VMware performance data."""
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
        
        # Get all available CPU counters
        cpu_counters = []
        for counter in perf_manager.perfCounter:
            if counter.groupInfo.key == 'cpu':
                cpu_counters.append(counter)
        
        # Define metrics we want to collect
        metric_ids = [
            vim.PerformanceManager.MetricId(counterId=6, instance="*"),    # CPU usage
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
        
        # Get VM CPU configuration
        cpu_count = 0
        if vm.config and vm.config.hardware:
            cpu_count = vm.config.hardware.numCPU
        
        result_text = f"Raw Performance Data for VM '{vm_name}':\n"
        result_text += f"- CPU Cores: {cpu_count}\n"
        result_text += f"- Available CPU Counters: {len(cpu_counters)}\n\n"
        
        result_text += "=== RAW CPU METRICS ===\n"
        for sample in result[0].value:
            counter_id = sample.id.counterId
            instance = sample.id.instance
            value = sample.value[0] if sample.value else 0
            
            result_text += f"- Counter ID: {counter_id}\n"
            result_text += f"- Instance: '{instance}' (empty = overall, number = specific core)\n"
            result_text += f"- Raw Value: {value}\n"
            
            if instance == "":
                result_text += f"- Interpretation: Overall CPU usage across all cores\n"
                if cpu_count > 0:
                    result_text += f"- Per-core average: {value/cpu_count:.1f}%\n"
            else:
                result_text += f"- Interpretation: CPU core {instance} usage\n"
            
            result_text += "\n"
        
        return result_text
        
    except Exception as e:
        return f"Error getting raw performance data: {e}" 