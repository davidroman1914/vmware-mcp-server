"""
Pytest configuration and fixtures for ESXi MCP Server tests.
"""
import pytest
from unittest.mock import Mock, MagicMock
from typing import Dict, Any

from src.config import Config, VMwareConfig, ServerConfig
from src.vmware import VMwareManager, VMInfo, VMPerformance


@pytest.fixture
def mock_vmware_config() -> VMwareConfig:
    """Create a mock VMware configuration."""
    return VMwareConfig(
        host="test-vcenter.example.com",
        user="test-user",
        password="test-password",
        datacenter="TestDatacenter",
        cluster="TestCluster",
        datastore="TestDatastore",
        network="TestNetwork",
        insecure=True
    )


@pytest.fixture
def mock_server_config() -> ServerConfig:
    """Create a mock server configuration."""
    return ServerConfig(
        api_key="test-api-key",
        log_file=None,
        log_level="DEBUG",
        host="0.0.0.0",
        port=8000
    )


@pytest.fixture
def mock_config(mock_vmware_config, mock_server_config) -> Config:
    """Create a mock configuration."""
    return Config(
        vmware=mock_vmware_config,
        server=mock_server_config
    )


@pytest.fixture
def mock_vm_info() -> VMInfo:
    """Create a mock VM info object."""
    return VMInfo(
        name="test-vm",
        power_state="poweredOn",
        cpu_count=2,
        memory_mb=4096,
        guest_id="ubuntu64Guest",
        tools_status="toolsOk"
    )


@pytest.fixture
def mock_vm_performance() -> VMPerformance:
    """Create a mock VM performance object."""
    return VMPerformance(
        cpu_usage_mhz=1000,
        memory_usage_mb=2048,
        storage_usage_gb=20.5,
        network_transmit_kbps=1024.0,
        network_receive_kbps=512.0
    )


@pytest.fixture
def mock_vmware_manager(mock_vmware_config) -> Mock:
    """Create a mock VMware manager."""
    manager = Mock(spec=VMwareManager)
    manager.config = mock_vmware_config
    
    # Mock methods
    manager.list_vms.return_value = [
        VMInfo(
            name="test-vm-1",
            power_state="poweredOn",
            cpu_count=2,
            memory_mb=4096,
            guest_id="ubuntu64Guest",
            tools_status="toolsOk"
        ),
        VMInfo(
            name="test-vm-2",
            power_state="poweredOff",
            cpu_count=4,
            memory_mb=8192,
            guest_id="windows9Server64Guest",
            tools_status="toolsNotRunning"
        )
    ]
    
    manager.find_vm.return_value = Mock()
    manager.get_vm_performance.return_value = mock_vm_performance()
    manager.create_vm.return_value = "VM test-vm created successfully"
    manager.clone_vm.return_value = "VM new-vm cloned successfully from template-vm"
    manager.delete_vm.return_value = "VM test-vm deleted successfully"
    manager.power_on_vm.return_value = "VM test-vm powered on successfully"
    manager.power_off_vm.return_value = "VM test-vm powered off successfully"
    manager.disconnect.return_value = None
    
    return manager


@pytest.fixture
def sample_config_dict() -> Dict[str, Any]:
    """Sample configuration dictionary."""
    return {
        "vcenter_host": "192.168.1.100",
        "vcenter_user": "administrator@vsphere.local",
        "vcenter_password": "password123",
        "datacenter": "Datacenter1",
        "cluster": "Cluster1",
        "datastore": "Datastore1",
        "network": "VM Network",
        "insecure": True,
        "api_key": "test-api-key",
        "log_file": "./logs/test.log",
        "log_level": "DEBUG",
        "host": "0.0.0.0",
        "port": 8000
    } 