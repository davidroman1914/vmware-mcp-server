"""
Tests for MCP server module.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any

from src.mcp_server import ESXiMCPServer, create_server
from src.config import Config, VMwareConfig, ServerConfig
from src.vmware import VMInfo, VMPerformance


class TestESXiMCPServer:
    """Test ESXiMCPServer class."""
    
    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration."""
        vmware_config = VMwareConfig(
            host="test-host",
            user="test-user",
            password="test-password"
        )
        server_config = ServerConfig(
            api_key="test-api-key",
            log_level="DEBUG"
        )
        return Config(vmware=vmware_config, server=server_config)
    
    @pytest.fixture
    def mock_vmware_manager(self):
        """Create a mock VMware manager."""
        manager = Mock()
        manager.list_vms.return_value = [
            VMInfo(
                name="test-vm-1",
                power_state="poweredOn",
                cpu_count=2,
                memory_mb=4096,
                guest_id="ubuntu64Guest",
                tools_status="toolsOk"
            )
        ]
        manager.get_vm_performance.return_value = VMPerformance(
            cpu_usage_mhz=1000,
            memory_usage_mb=2048,
            storage_usage_gb=20.0
        )
        manager.create_vm.return_value = "VM test-vm created successfully"
        manager.clone_vm.return_value = "VM new-vm cloned successfully"
        manager.delete_vm.return_value = "VM test-vm deleted successfully"
        manager.power_on_vm.return_value = "VM test-vm powered on successfully"
        manager.power_off_vm.return_value = "VM test-vm powered off successfully"
        return manager
    
    @patch('src.mcp_server.VMwareManager')
    def test_esxi_mcp_server_initialization(self, mock_vmware_manager_class, mock_config):
        """Test ESXiMCPServer initialization."""
        mock_manager = Mock()
        mock_vmware_manager_class.return_value = mock_manager
        
        server = ESXiMCPServer(mock_config)
        
        assert server.config == mock_config
        assert server.vmware_manager == mock_manager
        assert server.authenticated is False
        mock_vmware_manager_class.assert_called_once_with(mock_config.vmware)
    
    @patch('src.mcp_server.VMwareManager')
    def test_esxi_mcp_server_initialization_error(self, mock_vmware_manager_class, mock_config):
        """Test ESXiMCPServer initialization with error."""
        mock_vmware_manager_class.side_effect = Exception("Connection failed")
        
        with pytest.raises(Exception, match="Connection failed"):
            ESXiMCPServer(mock_config)
    
    def test_check_auth_with_api_key(self, mock_config):
        """Test authentication check with API key."""
        server = ESXiMCPServer.__new__(ESXiMCPServer)
        server.config = mock_config
        
        # Mock request
        request = Mock()
        request.arguments = {"api_key": "test-api-key"}
        
        assert server._check_auth(request) is True
    
    def test_check_auth_without_api_key(self, mock_config):
        """Test authentication check without API key."""
        server = ESXiMCPServer.__new__(ESXiMCPServer)
        server.config = mock_config
        
        # Mock request
        request = Mock()
        request.arguments = {}
        
        assert server._check_auth(request) is False
    
    def test_check_auth_wrong_api_key(self, mock_config):
        """Test authentication check with wrong API key."""
        server = ESXiMCPServer.__new__(ESXiMCPServer)
        server.config = mock_config
        
        # Mock request
        request = Mock()
        request.arguments = {"api_key": "wrong-key"}
        
        assert server._check_auth(request) is False
    
    def test_check_auth_no_config_api_key(self, mock_config):
        """Test authentication check when no API key is configured."""
        mock_config.server.api_key = None
        server = ESXiMCPServer.__new__(ESXiMCPServer)
        server.config = mock_config
        
        # Mock request
        request = Mock()
        request.arguments = {}
        
        assert server._check_auth(request) is True
    
    @pytest.mark.asyncio
    async def test_list_tools(self, mock_config):
        """Test list_tools method."""
        server = ESXiMCPServer.__new__(ESXiMCPServer)
        server.config = mock_config
        
        request = Mock()
        result = await server.list_tools(request)
        
        assert len(result.tools) == 8
        tool_names = [tool.name for tool in result.tools]
        expected_tools = ["authenticate", "list_vms", "create_vm", "clone_vm", "delete_vm", "power_on", "power_off"]
        assert all(tool in tool_names for tool in expected_tools)
    
    @pytest.mark.asyncio
    async def test_call_tool_authentication_failed(self, mock_config):
        """Test call_tool with failed authentication."""
        server = ESXiMCPServer.__new__(ESXiMCPServer)
        server.config = mock_config
        
        request = Mock()
        request.arguments = {"api_key": "wrong-key"}
        request.name = "list_vms"
        
        result = await server.call_tool(request)
        
        assert "Authentication failed" in result.content[0].text
    
    @pytest.mark.asyncio
    async def test_call_tool_unknown_tool(self, mock_config):
        """Test call_tool with unknown tool."""
        server = ESXiMCPServer.__new__(ESXiMCPServer)
        server.config = mock_config
        
        request = Mock()
        request.arguments = {"api_key": "test-api-key"}
        request.name = "unknown_tool"
        
        result = await server.call_tool(request)
        
        assert "Unknown tool" in result.content[0].text
    
    @pytest.mark.asyncio
    async def test_handle_authenticate(self, mock_config):
        """Test authenticate tool handler."""
        server = ESXiMCPServer.__new__(ESXiMCPServer)
        server.config = mock_config
        server.authenticated = False
        
        request = Mock()
        request.arguments = {"api_key": "test-api-key"}
        
        result = await server._handle_authenticate(request)
        
        assert result.content[0].text == "Authentication successful"
        assert server.authenticated is True
    
    @pytest.mark.asyncio
    async def test_handle_list_vms(self, mock_config, mock_vmware_manager):
        """Test list_vms tool handler."""
        server = ESXiMCPServer.__new__(ESXiMCPServer)
        server.config = mock_config
        server.vmware_manager = mock_vmware_manager
        
        request = Mock()
        request.arguments = {"api_key": "test-api-key"}
        
        result = await server._handle_list_vms(request)
        
        assert "Found 1 virtual machines" in result.content[0].text
        assert "test-vm-1" in result.content[0].text
        mock_vmware_manager.list_vms.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_list_vms_empty(self, mock_config):
        """Test list_vms tool handler with no VMs."""
        server = ESXiMCPServer.__new__(ESXiMCPServer)
        server.config = mock_config
        server.vmware_manager = Mock()
        server.vmware_manager.list_vms.return_value = []
        
        request = Mock()
        request.arguments = {"api_key": "test-api-key"}
        
        result = await server._handle_list_vms(request)
        
        assert result.content[0].text == "No virtual machines found"
    
    @pytest.mark.asyncio
    async def test_handle_create_vm(self, mock_config, mock_vmware_manager):
        """Test create_vm tool handler."""
        server = ESXiMCPServer.__new__(ESXiMCPServer)
        server.config = mock_config
        server.vmware_manager = mock_vmware_manager
        
        request = Mock()
        request.arguments = {
            "api_key": "test-api-key",
            "name": "test-vm",
            "cpu": 2,
            "memory": 4096,
            "datastore": "test-ds",
            "network": "test-network"
        }
        
        result = await server._handle_create_vm(request)
        
        assert result.content[0].text == "VM test-vm created successfully"
        mock_vmware_manager.create_vm.assert_called_once_with(
            "test-vm", 2, 4096, "test-ds", "test-network"
        )
    
    @pytest.mark.asyncio
    async def test_handle_clone_vm(self, mock_config, mock_vmware_manager):
        """Test clone_vm tool handler."""
        server = ESXiMCPServer.__new__(ESXiMCPServer)
        server.config = mock_config
        server.vmware_manager = mock_vmware_manager
        
        request = Mock()
        request.arguments = {
            "api_key": "test-api-key",
            "template_name": "template-vm",
            "new_name": "new-vm"
        }
        
        result = await server._handle_clone_vm(request)
        
        assert result.content[0].text == "VM new-vm cloned successfully"
        mock_vmware_manager.clone_vm.assert_called_once_with("template-vm", "new-vm")
    
    @pytest.mark.asyncio
    async def test_handle_delete_vm(self, mock_config, mock_vmware_manager):
        """Test delete_vm tool handler."""
        server = ESXiMCPServer.__new__(ESXiMCPServer)
        server.config = mock_config
        server.vmware_manager = mock_vmware_manager
        
        request = Mock()
        request.arguments = {
            "api_key": "test-api-key",
            "name": "test-vm"
        }
        
        result = await server._handle_delete_vm(request)
        
        assert result.content[0].text == "VM test-vm deleted successfully"
        mock_vmware_manager.delete_vm.assert_called_once_with("test-vm")
    
    @pytest.mark.asyncio
    async def test_handle_power_on(self, mock_config, mock_vmware_manager):
        """Test power_on tool handler."""
        server = ESXiMCPServer.__new__(ESXiMCPServer)
        server.config = mock_config
        server.vmware_manager = mock_vmware_manager
        
        request = Mock()
        request.arguments = {
            "api_key": "test-api-key",
            "name": "test-vm"
        }
        
        result = await server._handle_power_on(request)
        
        assert result.content[0].text == "VM test-vm powered on successfully"
        mock_vmware_manager.power_on_vm.assert_called_once_with("test-vm")
    
    @pytest.mark.asyncio
    async def test_handle_power_off(self, mock_config, mock_vmware_manager):
        """Test power_off tool handler."""
        server = ESXiMCPServer.__new__(ESXiMCPServer)
        server.config = mock_config
        server.vmware_manager = mock_vmware_manager
        
        request = Mock()
        request.arguments = {
            "api_key": "test-api-key",
            "name": "test-vm"
        }
        
        result = await server._handle_power_off(request)
        
        assert result.content[0].text == "VM test-vm powered off successfully"
        mock_vmware_manager.power_off_vm.assert_called_once_with("test-vm")
    
    @pytest.mark.asyncio
    async def test_list_resources(self, mock_config, mock_vmware_manager):
        """Test list_resources method."""
        server = ESXiMCPServer.__new__(ESXiMCPServer)
        server.config = mock_config
        server.vmware_manager = mock_vmware_manager
        
        request = Mock()
        result = await server.list_resources(request)
        
        assert len(result.resources) == 1
        resource = result.resources[0]
        assert str(resource.uri) == "vm://test-vm-1"
        assert resource.name == "test-vm-1"
        assert "Virtual Machine: test-vm-1" in resource.description
        assert "test-vm-1" in resource.content[0].text
        assert "poweredOn" in resource.content[0].text
    
    @pytest.mark.asyncio
    async def test_list_resources_no_vmware_manager(self, mock_config):
        """Test list_resources without VMware manager."""
        server = ESXiMCPServer.__new__(ESXiMCPServer)
        server.config = mock_config
        server.vmware_manager = None
        
        request = Mock()
        result = await server.list_resources(request)
        
        assert len(result.resources) == 0
    
    @pytest.mark.asyncio
    async def test_list_resources_error(self, mock_config):
        """Test list_resources with error."""
        server = ESXiMCPServer.__new__(ESXiMCPServer)
        server.config = mock_config
        server.vmware_manager = Mock()
        server.vmware_manager.list_vms.side_effect = Exception("VMware error")
        
        request = Mock()
        result = await server.list_resources(request)
        
        assert len(result.resources) == 0
    
    def test_cleanup(self, mock_config):
        """Test cleanup method."""
        server = ESXiMCPServer.__new__(ESXiMCPServer)
        server.config = mock_config
        server.vmware_manager = Mock()
        
        server.cleanup()
        
        server.vmware_manager.disconnect.assert_called_once()


@pytest.mark.asyncio
@patch('src.mcp_server.VMwareManager')
async def test_create_server(mock_vmware_manager_class, mock_config):
    """Test create_server function."""
    # Mock the VMwareManager to avoid real connection attempts
    mock_manager = Mock()
    mock_vmware_manager_class.return_value = mock_manager
    
    server = await create_server(mock_config)
    
    assert server is not None
    # Verify VMwareManager was called with the correct config
    mock_vmware_manager_class.assert_called_once_with(mock_config.vmware) 