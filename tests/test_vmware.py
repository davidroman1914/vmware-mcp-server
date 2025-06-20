"""
Tests for VMware management module.
"""
import pytest
from unittest.mock import Mock, patch
from typing import List

from src.vmware import VMwareManager, VMInfo, VMPerformance, VMwareConnectionError
from src.config import VMwareConfig


class TestVMInfo:
    """Test VMInfo class."""
    
    def test_vm_info_creation(self):
        """Test VMInfo object creation."""
        vm_info = VMInfo(
            name="test-vm",
            power_state="poweredOn",
            cpu_count=2,
            memory_mb=4096,
            guest_id="ubuntu64Guest",
            tools_status="toolsOk"
        )
        
        assert vm_info.name == "test-vm"
        assert vm_info.power_state == "poweredOn"
        assert vm_info.cpu_count == 2
        assert vm_info.memory_mb == 4096
        assert vm_info.guest_id == "ubuntu64Guest"
        assert vm_info.tools_status == "toolsOk"


class TestVMPerformance:
    """Test VMPerformance class."""
    
    def test_vm_performance_creation(self):
        """Test VMPerformance object creation."""
        vm_perf = VMPerformance(
            cpu_usage_mhz=1000,
            memory_usage_mb=2048,
            storage_usage_gb=50.5,
            network_transmit_kbps=100.0,
            network_receive_kbps=200.0
        )
        
        assert vm_perf.cpu_usage_mhz == 1000
        assert vm_perf.memory_usage_mb == 2048
        assert vm_perf.storage_usage_gb == 50.5
        assert vm_perf.network_transmit_kbps == 100.0
        assert vm_perf.network_receive_kbps == 200.0
    
    def test_vm_performance_minimal(self):
        """Test VMPerformance object creation with minimal data."""
        vm_perf = VMPerformance(
            cpu_usage_mhz=500,
            memory_usage_mb=1024,
            storage_usage_gb=25.0
        )
        
        assert vm_perf.cpu_usage_mhz == 500
        assert vm_perf.memory_usage_mb == 1024
        assert vm_perf.storage_usage_gb == 25.0
        assert vm_perf.network_transmit_kbps is None
        assert vm_perf.network_receive_kbps is None


class TestVMwareManager:
    """Test VMwareManager class."""
    
    @pytest.fixture
    def mock_vmware_config(self):
        """Create a mock VMware configuration."""
        return VMwareConfig(
            host="test-host",
            user="test-user",
            password="test-password"
        )
    
    @patch('vmware.vapi.vsphere.client.create_vsphere_client')
    def test_vmware_manager_initialization(self, mock_create_client, mock_vmware_config):
        """Test VMwareManager initialization."""
        mock_client = Mock()
        mock_create_client.return_value = mock_client
        
        manager = VMwareManager(mock_vmware_config, connect=False)
        manager.client = mock_client  # Set the client manually for testing
        
        assert manager.config == mock_vmware_config
        assert manager.client == mock_client
        # When connect=False, create_vsphere_client should not be called
        mock_create_client.assert_not_called()
    
    @patch('vmware.vapi.vsphere.client.create_vsphere_client')
    def test_vmware_manager_connection_error(self, mock_create_client, mock_vmware_config):
        """Test VMwareManager initialization with connection error."""
        mock_create_client.side_effect = Exception("Connection failed")
        
        manager = VMwareManager(mock_vmware_config, connect=False)
        with pytest.raises(VMwareConnectionError, match="Connection failed"):
            manager._connect()
    
    @patch('vmware.vapi.vsphere.client.create_vsphere_client')
    def test_list_vms(self, mock_create_client, mock_vmware_config):
        """Test list_vms method."""
        # Mock client and its methods
        mock_client = Mock()
        mock_create_client.return_value = mock_client
        
        # Mock VM list
        mock_vm = Mock()
        mock_vm.vm = "vm-123"
        mock_vm.name = "test-vm"
        mock_client.vcenter.VM.list.return_value = [mock_vm]
        
        # Mock power info
        mock_power = Mock()
        mock_power.state.value = "POWERED_ON"
        mock_client.vcenter.vm.Power.get.return_value = mock_power
        
        # Mock hardware info
        mock_hardware = Mock()
        mock_hardware.cpu.count = 2
        mock_hardware.memory.size_MiB = 4096
        mock_hardware.guest_ID = "ubuntu64Guest"
        mock_client.vcenter.vm.Hardware.get.return_value = mock_hardware
        
        # Mock guest info
        mock_guest = Mock()
        mock_guest.tools_running_status.value = "RUNNING"
        mock_client.vcenter.vm.Guest.get.return_value = mock_guest
        
        manager = VMwareManager(mock_vmware_config, connect=False)
        manager.client = mock_client  # Set the client manually for testing
        vms = manager.list_vms()
        
        assert len(vms) == 1
        assert vms[0].name == "test-vm"
        assert vms[0].power_state == "POWERED_ON"
        assert vms[0].cpu_count == 2
        assert vms[0].memory_mb == 4096
        assert vms[0].guest_id == "ubuntu64Guest"
        assert vms[0].tools_status == "RUNNING"
    
    @patch('vmware.vapi.vsphere.client.create_vsphere_client')
    def test_find_vm(self, mock_create_client, mock_vmware_config):
        """Test find_vm method."""
        mock_client = Mock()
        mock_create_client.return_value = mock_client
        
        # Mock VM list
        mock_vm = Mock()
        mock_vm.vm = "vm-123"
        mock_vm.name = "test-vm"
        mock_client.vcenter.VM.list.return_value = [mock_vm]
        
        manager = VMwareManager(mock_vmware_config, connect=False)
        manager.client = mock_client  # Set the client manually for testing
        vm_id = manager.find_vm("test-vm")
        
        assert vm_id == "vm-123"
    
    @patch('vmware.vapi.vsphere.client.create_vsphere_client')
    def test_find_vm_not_found(self, mock_create_client, mock_vmware_config):
        """Test find_vm method when VM is not found."""
        mock_client = Mock()
        mock_create_client.return_value = mock_client
        
        # Mock empty VM list
        mock_client.vcenter.VM.list.return_value = []
        
        manager = VMwareManager(mock_vmware_config, connect=False)
        manager.client = mock_client  # Set the client manually for testing
        vm_id = manager.find_vm("nonexistent-vm")
        
        assert vm_id is None
    
    @patch('vmware.vapi.vsphere.client.create_vsphere_client')
    def test_get_vm_performance(self, mock_create_client, mock_vmware_config):
        """Test get_vm_performance method."""
        mock_client = Mock()
        mock_create_client.return_value = mock_client
        
        # Mock VM list for find_vm
        mock_vm = Mock()
        mock_vm.vm = "vm-123"
        mock_vm.name = "test-vm"
        mock_client.vcenter.VM.list.return_value = [mock_vm]
        
        # Mock hardware info
        mock_hardware = Mock()
        mock_client.vcenter.vm.Hardware.get.return_value = mock_hardware
        
        # Mock guest info
        mock_guest = Mock()
        mock_guest.memory_usage_MiB = 2048
        mock_client.vcenter.vm.Guest.get.return_value = mock_guest
        
        manager = VMwareManager(mock_vmware_config, connect=False)
        manager.client = mock_client  # Set the client manually for testing
        performance = manager.get_vm_performance("test-vm")
        
        assert performance.memory_usage_mb == 2048
        assert performance.cpu_usage_mhz == 0  # Default value
        assert performance.storage_usage_gb == 0  # Default value
    
    @patch('vmware.vapi.vsphere.client.create_vsphere_client')
    def test_get_vm_performance_vm_not_found(self, mock_create_client, mock_vmware_config):
        """Test get_vm_performance method when VM is not found."""
        mock_client = Mock()
        mock_create_client.return_value = mock_client
        
        # Mock empty VM list
        mock_client.vcenter.VM.list.return_value = []
        
        manager = VMwareManager(mock_vmware_config, connect=False)
        manager.client = mock_client  # Set the client manually for testing
        
        with pytest.raises(ValueError, match="VM nonexistent-vm not found"):
            manager.get_vm_performance("nonexistent-vm")
    
    @patch('vmware.vapi.vsphere.client.create_vsphere_client')
    def test_create_vm(self, mock_create_client, mock_vmware_config):
        """Test create_vm method."""
        mock_client = Mock()
        mock_create_client.return_value = mock_client
        
        # Mock datastore list
        mock_datastore = Mock()
        mock_datastore.datastore = "ds-123"
        mock_datastore.name = "datastore1"
        mock_client.vcenter.Datastore.list.return_value = [mock_datastore]
        
        # Mock network list
        mock_network = Mock()
        mock_network.network = "net-123"
        mock_network.name = "VM Network"
        mock_client.vcenter.Network.list.return_value = [mock_network]
        
        # Mock resource pool list
        mock_rp = Mock()
        mock_rp.resource_pool = "rp-123"
        mock_client.vcenter.ResourcePool.list.return_value = [mock_rp]
        
        # Mock VM creation
        mock_client.vcenter.VM.create.return_value = "vm-456"
        
        manager = VMwareManager(mock_vmware_config, connect=False)
        manager.client = mock_client  # Set the client manually for testing
        vm_id = manager.create_vm("new-vm", 2, 4096)
        
        assert vm_id == "vm-456"
        mock_client.vcenter.VM.create.assert_called_once()
    
    @patch('vmware.vapi.vsphere.client.create_vsphere_client')
    def test_create_vm_with_specific_datastore_network(self, mock_create_client, mock_vmware_config):
        """Test create_vm method with specific datastore and network."""
        mock_client = Mock()
        mock_create_client.return_value = mock_client
        
        # Mock datastore list
        mock_datastore = Mock()
        mock_datastore.datastore = "ds-123"
        mock_datastore.name = "specific-datastore"
        mock_client.vcenter.Datastore.list.return_value = [mock_datastore]
        
        # Mock network list
        mock_network = Mock()
        mock_network.network = "net-123"
        mock_network.name = "specific-network"
        mock_client.vcenter.Network.list.return_value = [mock_network]
        
        # Mock resource pool list
        mock_rp = Mock()
        mock_rp.resource_pool = "rp-123"
        mock_client.vcenter.ResourcePool.list.return_value = [mock_rp]
        
        # Mock VM creation
        mock_client.vcenter.VM.create.return_value = "vm-456"
        
        manager = VMwareManager(mock_vmware_config, connect=False)
        manager.client = mock_client  # Set the client manually for testing
        vm_id = manager.create_vm("new-vm", 2, 4096, "specific-datastore", "specific-network")
        
        assert vm_id == "vm-456"
        mock_client.vcenter.VM.create.assert_called_once()
    
    @patch('vmware.vapi.vsphere.client.create_vsphere_client')
    def test_create_vm_datastore_not_found(self, mock_create_client, mock_vmware_config):
        """Test create_vm method when datastore is not found."""
        mock_client = Mock()
        mock_create_client.return_value = mock_client
        
        # Mock datastore list with different name
        mock_datastore = Mock()
        mock_datastore.datastore = "ds-123"
        mock_datastore.name = "other-datastore"
        mock_client.vcenter.Datastore.list.return_value = [mock_datastore]
        
        manager = VMwareManager(mock_vmware_config, connect=False)
        manager.client = mock_client  # Set the client manually for testing
        
        with pytest.raises(ValueError, match="Datastore specific-datastore not found"):
            manager.create_vm("new-vm", 2, 4096, "specific-datastore")
    
    @patch('vmware.vapi.vsphere.client.create_vsphere_client')
    def test_create_vm_network_not_found(self, mock_create_client, mock_vmware_config):
        """Test create_vm method when network is not found."""
        mock_client = Mock()
        mock_create_client.return_value = mock_client
        
        # Mock datastore list
        mock_datastore = Mock()
        mock_datastore.datastore = "ds-123"
        mock_datastore.name = "datastore1"
        mock_client.vcenter.Datastore.list.return_value = [mock_datastore]
        
        # Mock network list with different name
        mock_network = Mock()
        mock_network.network = "net-123"
        mock_network.name = "other-network"
        mock_client.vcenter.Network.list.return_value = [mock_network]
        
        manager = VMwareManager(mock_vmware_config, connect=False)
        manager.client = mock_client  # Set the client manually for testing
        
        with pytest.raises(ValueError, match="Network specific-network not found"):
            manager.create_vm("new-vm", 2, 4096, "datastore1", "specific-network")
    
    @patch('vmware.vapi.vsphere.client.create_vsphere_client')
    def test_clone_vm(self, mock_create_client, mock_vmware_config):
        """Test clone_vm method."""
        mock_client = Mock()
        mock_create_client.return_value = mock_client
        
        # Mock VM list for find_vm
        mock_template = Mock()
        mock_template.vm = "template-123"
        mock_template.name = "template-vm"
        mock_client.vcenter.VM.list.return_value = [mock_template]
        
        # Mock power info (template is powered off)
        mock_power = Mock()
        mock_power.state = "POWERED_OFF"
        mock_client.vcenter.vm.Power.get.return_value = mock_power
        
        # Mock resource pool list
        mock_rp = Mock()
        mock_rp.resource_pool = "rp-123"
        mock_client.vcenter.ResourcePool.list.return_value = [mock_rp]
        
        # Mock VM cloning
        mock_client.vcenter.VM.clone.return_value = "vm-456"
        
        manager = VMwareManager(mock_vmware_config, connect=False)
        manager.client = mock_client  # Set the client manually for testing
        vm_id = manager.clone_vm("template-vm", "new-vm")
        
        assert vm_id == "vm-456"
        mock_client.vcenter.VM.clone.assert_called_once()
    
    @patch('vmware.vapi.vsphere.client.create_vsphere_client')
    def test_clone_vm_template_not_found(self, mock_create_client, mock_vmware_config):
        """Test clone_vm method when template is not found."""
        mock_client = Mock()
        mock_create_client.return_value = mock_client
        
        # Mock empty VM list
        mock_client.vcenter.VM.list.return_value = []
        
        manager = VMwareManager(mock_vmware_config, connect=False)
        manager.client = mock_client  # Set the client manually for testing
        
        with pytest.raises(ValueError, match="Template template-vm not found"):
            manager.clone_vm("template-vm", "new-vm")
    
    @patch('vmware.vapi.vsphere.client.create_vsphere_client')
    def test_delete_vm(self, mock_create_client, mock_vmware_config):
        """Test delete_vm method."""
        mock_client = Mock()
        mock_create_client.return_value = mock_client
        
        # Mock VM list for find_vm
        mock_vm = Mock()
        mock_vm.vm = "vm-123"
        mock_vm.name = "test-vm"
        mock_client.vcenter.VM.list.return_value = [mock_vm]
        
        manager = VMwareManager(mock_vmware_config, connect=False)
        manager.client = mock_client  # Set the client manually for testing
        result = manager.delete_vm("test-vm")
        
        assert result == "VM test-vm deleted successfully"
        mock_client.vcenter.VM.delete.assert_called_once_with("vm-123")
    
    @patch('vmware.vapi.vsphere.client.create_vsphere_client')
    def test_delete_vm_not_found(self, mock_create_client, mock_vmware_config):
        """Test delete_vm method when VM is not found."""
        mock_client = Mock()
        mock_create_client.return_value = mock_client
        
        # Mock empty VM list
        mock_client.vcenter.VM.list.return_value = []
        
        manager = VMwareManager(mock_vmware_config, connect=False)
        manager.client = mock_client  # Set the client manually for testing
        
        with pytest.raises(ValueError, match="VM nonexistent-vm not found"):
            manager.delete_vm("nonexistent-vm")
    
    @patch('vmware.vapi.vsphere.client.create_vsphere_client')
    def test_power_on_vm(self, mock_create_client, mock_vmware_config):
        """Test power_on_vm method."""
        mock_client = Mock()
        mock_create_client.return_value = mock_client
        
        # Mock VM list for find_vm
        mock_vm = Mock()
        mock_vm.vm = "vm-123"
        mock_vm.name = "test-vm"
        mock_client.vcenter.VM.list.return_value = [mock_vm]
        
        manager = VMwareManager(mock_vmware_config, connect=False)
        manager.client = mock_client  # Set the client manually for testing
        result = manager.power_on_vm("test-vm")
        
        assert result == "vm-123"
        mock_client.vcenter.vm.Power.start.assert_called_once_with("vm-123")
    
    @patch('vmware.vapi.vsphere.client.create_vsphere_client')
    def test_power_on_vm_not_found(self, mock_create_client, mock_vmware_config):
        """Test power_on_vm method when VM is not found."""
        mock_client = Mock()
        mock_create_client.return_value = mock_client
        
        # Mock empty VM list
        mock_client.vcenter.VM.list.return_value = []
        
        manager = VMwareManager(mock_vmware_config, connect=False)
        manager.client = mock_client  # Set the client manually for testing
        
        with pytest.raises(ValueError, match="VM nonexistent-vm not found"):
            manager.power_on_vm("nonexistent-vm")
    
    @patch('vmware.vapi.vsphere.client.create_vsphere_client')
    def test_power_off_vm(self, mock_create_client, mock_vmware_config):
        """Test power_off_vm method."""
        mock_client = Mock()
        mock_create_client.return_value = mock_client
        
        # Mock VM list for find_vm
        mock_vm = Mock()
        mock_vm.vm = "vm-123"
        mock_vm.name = "test-vm"
        mock_client.vcenter.VM.list.return_value = [mock_vm]
        
        manager = VMwareManager(mock_vmware_config, connect=False)
        manager.client = mock_client  # Set the client manually for testing
        result = manager.power_off_vm("test-vm")
        
        assert result == "vm-123"
        mock_client.vcenter.vm.Power.stop.assert_called_once_with("vm-123")
    
    @patch('vmware.vapi.vsphere.client.create_vsphere_client')
    def test_power_off_vm_not_found(self, mock_create_client, mock_vmware_config):
        """Test power_off_vm method when VM is not found."""
        mock_client = Mock()
        mock_create_client.return_value = mock_client
        
        # Mock empty VM list
        mock_client.vcenter.VM.list.return_value = []
        
        manager = VMwareManager(mock_vmware_config, connect=False)
        manager.client = mock_client  # Set the client manually for testing
        
        with pytest.raises(ValueError, match="VM nonexistent-vm not found"):
            manager.power_off_vm("nonexistent-vm")
    
    @patch('vmware.vapi.vsphere.client.create_vsphere_client')
    def test_disconnect(self, mock_create_client, mock_vmware_config):
        """Test disconnect method."""
        mock_client = Mock()
        mock_create_client.return_value = mock_client
        
        manager = VMwareManager(mock_vmware_config, connect=False)
        manager.client = mock_client  # Set the client manually for testing
        manager.disconnect()
        
        # The disconnect method should not raise any exceptions
        # and should clean up resources if needed 

    def test_create_vm_from_template_success(self, mock_vmware_manager):
        """Test successful VM creation from template."""
        with patch.object(mock_vmware_manager, 'find_vm', return_value='template-123'), \
             patch.object(mock_vmware_manager.client.vcenter.vm.Power, 'get', return_value=Mock(state='POWERED_OFF')), \
             patch.object(mock_vmware_manager.client.vcenter.Folder, 'list', return_value=[]), \
             patch.object(mock_vmware_manager.client.vcenter.Cluster, 'list', return_value=[]), \
             patch.object(mock_vmware_manager.client.vcenter.ResourcePool, 'list', return_value=[Mock(resource_pool='rp-123')]), \
             patch.object(mock_vmware_manager.client.vcenter.VM, 'clone', return_value='vm-456'), \
             patch.object(mock_vmware_manager.client.vcenter.vm.Power, 'start') as mock_start:
            
            vm_id = mock_vmware_manager.create_vm_from_template(
                name='test-vm',
                template_name='test-template'
            )
            
            assert vm_id == 'vm-456'
            mock_start.assert_called_once_with('vm-456')
    
    def test_create_vm_from_template_template_not_found(self, mock_vmware_manager):
        """Test VM creation when template is not found."""
        with patch.object(mock_vmware_manager, 'find_vm', return_value=None):
            with pytest.raises(ValueError, match="Template test-template not found"):
                mock_vmware_manager.create_vm_from_template(
                    name='test-vm',
                    template_name='test-template'
                )
    
    def test_create_vm_from_template_template_powered_on(self, mock_vmware_manager):
        """Test VM creation when template is powered on."""
        with patch.object(mock_vmware_manager, 'find_vm', return_value='template-123'), \
             patch.object(mock_vmware_manager.client.vcenter.vm.Power, 'get', return_value=Mock(state='POWERED_ON')):
            
            with pytest.raises(ValueError, match="Template test-template must be powered off to clone"):
                mock_vmware_manager.create_vm_from_template(
                    name='test-vm',
                    template_name='test-template'
                )
    
    def test_create_vm_from_template_with_folder_and_cluster(self, mock_vmware_manager):
        """Test VM creation with folder and cluster specification."""
        with patch.object(mock_vmware_manager, 'find_vm', return_value='template-123'), \
             patch.object(mock_vmware_manager.client.vcenter.vm.Power, 'get', return_value=Mock(state='POWERED_OFF')), \
             patch.object(mock_vmware_manager.client.vcenter.Folder, 'list', return_value=[Mock(folder='folder-123', name='vm')]), \
             patch.object(mock_vmware_manager.client.vcenter.Cluster, 'list', return_value=[Mock(cluster='cluster-123', name='test-cluster')]), \
             patch.object(mock_vmware_manager.client.vcenter.ResourcePool, 'list', return_value=[Mock(resource_pool='rp-123', cluster='cluster-123')]), \
             patch.object(mock_vmware_manager.client.vcenter.VM, 'clone', return_value='vm-456'), \
             patch.object(mock_vmware_manager.client.vcenter.vm.Power, 'start'):
            
            vm_id = mock_vmware_manager.create_vm_from_template(
                name='test-vm',
                template_name='test-template',
                folder='/vm/',
                cluster='test-cluster'
            )
            
            assert vm_id == 'vm-456'
    
    def test_create_vm_from_template_with_disk_spec(self, mock_vmware_manager):
        """Test VM creation with disk specification."""
        with patch.object(mock_vmware_manager, 'find_vm', return_value='template-123'), \
             patch.object(mock_vmware_manager.client.vcenter.vm.Power, 'get', return_value=Mock(state='POWERED_OFF')), \
             patch.object(mock_vmware_manager.client.vcenter.Folder, 'list', return_value=[]), \
             patch.object(mock_vmware_manager.client.vcenter.Cluster, 'list', return_value=[]), \
             patch.object(mock_vmware_manager.client.vcenter.ResourcePool, 'list', return_value=[Mock(resource_pool='rp-123')]), \
             patch.object(mock_vmware_manager.client.vcenter.VM, 'clone', return_value='vm-456'), \
             patch.object(mock_vmware_manager.client.vcenter.vm.Power, 'start'):
            
            vm_id = mock_vmware_manager.create_vm_from_template(
                name='test-vm',
                template_name='test-template',
                disk_spec=[{'size_gb': 20, 'name': 'disk1.vmdk'}]
            )
            
            assert vm_id == 'vm-456'
    
    def test_create_vm_from_template_with_hardware_spec(self, mock_vmware_manager):
        """Test VM creation with hardware specification."""
        with patch.object(mock_vmware_manager, 'find_vm', return_value='template-123'), \
             patch.object(mock_vmware_manager.client.vcenter.vm.Power, 'get', return_value=Mock(state='POWERED_OFF')), \
             patch.object(mock_vmware_manager.client.vcenter.Folder, 'list', return_value=[]), \
             patch.object(mock_vmware_manager.client.vcenter.Cluster, 'list', return_value=[]), \
             patch.object(mock_vmware_manager.client.vcenter.ResourcePool, 'list', return_value=[Mock(resource_pool='rp-123')]), \
             patch.object(mock_vmware_manager.client.vcenter.VM, 'clone', return_value='vm-456'), \
             patch.object(mock_vmware_manager.client.vcenter.vm.Power, 'start'):
            
            vm_id = mock_vmware_manager.create_vm_from_template(
                name='test-vm',
                template_name='test-template',
                hardware_spec={'cpu_count': 4, 'memory_mb': 8192}
            )
            
            assert vm_id == 'vm-456'
    
    def test_create_vm_from_template_with_network_spec(self, mock_vmware_manager):
        """Test VM creation with network specification."""
        with patch.object(mock_vmware_manager, 'find_vm', return_value='template-123'), \
             patch.object(mock_vmware_manager.client.vcenter.vm.Power, 'get', return_value=Mock(state='POWERED_OFF')), \
             patch.object(mock_vmware_manager.client.vcenter.Folder, 'list', return_value=[]), \
             patch.object(mock_vmware_manager.client.vcenter.Cluster, 'list', return_value=[]), \
             patch.object(mock_vmware_manager.client.vcenter.ResourcePool, 'list', return_value=[Mock(resource_pool='rp-123')]), \
             patch.object(mock_vmware_manager.client.vcenter.VM, 'clone', return_value='vm-456'), \
             patch.object(mock_vmware_manager.client.vcenter.vm.Power, 'start'):
            
            vm_id = mock_vmware_manager.create_vm_from_template(
                name='test-vm',
                template_name='test-template',
                network_spec=[{
                    'device_type': 'VMXNET3',
                    'network_id': 'network-123',
                    'ip': '192.168.1.100',
                    'netmask': '255.255.255.0',
                    'gateway': '192.168.1.1'
                }]
            )
            
            assert vm_id == 'vm-456'
    
    def test_create_vm_from_template_wait_for_ip(self, mock_vmware_manager):
        """Test VM creation with IP address waiting."""
        with patch.object(mock_vmware_manager, 'find_vm', return_value='template-123'), \
             patch.object(mock_vmware_manager.client.vcenter.vm.Power, 'get', return_value=Mock(state='POWERED_OFF')), \
             patch.object(mock_vmware_manager.client.vcenter.Folder, 'list', return_value=[]), \
             patch.object(mock_vmware_manager.client.vcenter.Cluster, 'list', return_value=[]), \
             patch.object(mock_vmware_manager.client.vcenter.ResourcePool, 'list', return_value=[Mock(resource_pool='rp-123')]), \
             patch.object(mock_vmware_manager.client.vcenter.VM, 'clone', return_value='vm-456'), \
             patch.object(mock_vmware_manager.client.vcenter.vm.Power, 'start'), \
             patch.object(mock_vmware_manager, '_wait_for_ip_address', return_value='192.168.1.100'):
            
            vm_id = mock_vmware_manager.create_vm_from_template(
                name='test-vm',
                template_name='test-template',
                wait_for_ip=True
            )
            
            assert vm_id == 'vm-456'
    
    def test_build_disk_spec(self, mock_vmware_manager):
        """Test disk specification building."""
        disk_spec = [{'size_gb': 20, 'name': 'disk1.vmdk', 'type': 'SATA'}]
        result = mock_vmware_manager._build_disk_spec(disk_spec)
        
        assert len(result) == 1
        assert result[0]['type'] == 'SATA'
        assert result[0]['new_vmdk']['name'] == 'disk1.vmdk'
        assert result[0]['new_vmdk']['capacity'] == 20 * 1024 * 1024 * 1024
    
    def test_build_hardware_spec(self, mock_vmware_manager):
        """Test hardware specification building."""
        hardware_spec = {'cpu_count': 4, 'memory_mb': 8192}
        result = mock_vmware_manager._build_hardware_spec(hardware_spec)
        
        assert result['cpu']['count'] == 4
        assert result['memory']['size_MiB'] == 8192
    
    def test_build_network_spec(self, mock_vmware_manager):
        """Test network specification building."""
        network_spec = [{
            'device_type': 'VMXNET3',
            'network_id': 'network-123'
        }]
        result = mock_vmware_manager._build_network_spec(network_spec)
        
        assert len(result) == 1
        assert result[0]['type'] == 'VMXNET3'
        assert result[0]['backing']['type'] == 'STANDARD_PORTGROUP'
        assert result[0]['backing']['network'] == 'network-123'
    
    def test_wait_for_ip_address_success(self, mock_vmware_manager):
        """Test successful IP address waiting."""
        with patch.object(mock_vmware_manager.client.vcenter.vm.Guest, 'get', return_value=Mock(ip_address='192.168.1.100')):
            ip = mock_vmware_manager._wait_for_ip_address('vm-123', 10)
            assert ip == '192.168.1.100'
    
    def test_wait_for_ip_address_timeout(self, mock_vmware_manager):
        """Test IP address waiting timeout."""
        with patch.object(mock_vmware_manager.client.vcenter.vm.Guest, 'get', return_value=Mock(ip_address=None)):
            with pytest.raises(TimeoutError):
                mock_vmware_manager._wait_for_ip_address('vm-123', 1) 