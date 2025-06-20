"""
Tests for main entry point functionality.
"""
import pytest
import asyncio
from unittest.mock import patch, AsyncMock
import sys
from pathlib import Path

from src.__main__ import main, setup_logging
from src.config import Config, VMwareConfig, ServerConfig


class TestMainEntryPoint:
    """Test main entry point functionality."""
    
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
    
    def test_setup_logging_with_file(self, mock_config, tmp_path):
        """Test logging setup with log file."""
        log_file = tmp_path / "test.log"
        mock_config.server.log_file = str(log_file)
        
        setup_logging(mock_config)
        
        # Verify log file was created
        assert log_file.exists()
    
    def test_setup_logging_without_file(self, mock_config):
        """Test logging setup without log file."""
        mock_config.server.log_file = None
        
        # Should not raise any exceptions
        setup_logging(mock_config)
    
    @pytest.mark.asyncio
    @patch('src.__main__.Config.from_file')
    @patch('src.__main__.create_server')
    @patch('mcp.server.stdio.stdio_server', new_callable=AsyncMock)
    async def test_main_with_config_file(self, mock_stdio_server, mock_create_server, mock_config_from_file, mock_config):
        """Test main function with config file argument."""
        mock_config_from_file.return_value = mock_config
        mock_server = AsyncMock()
        mock_create_server.return_value = mock_server
        mock_stdio_server.return_value = None
        
        # Mock sys.argv
        with patch.object(sys, 'argv', ['main.py', 'config.yaml']):
            await main()
        
        mock_config_from_file.assert_called_once_with('config.yaml')
        mock_create_server.assert_called_once_with(mock_config)
        mock_stdio_server.assert_called_once_with(mock_server)
    
    @pytest.mark.asyncio
    @patch('src.__main__.Config.from_env')
    @patch('src.__main__.create_server')
    @patch('mcp.server.stdio.stdio_server', new_callable=AsyncMock)
    async def test_main_with_env_config(self, mock_stdio_server, mock_create_server, mock_config_from_env, mock_config):
        """Test main function with environment configuration."""
        mock_config_from_env.return_value = mock_config
        mock_server = AsyncMock()
        mock_create_server.return_value = mock_server
        mock_stdio_server.return_value = None
        
        # Mock sys.argv with no additional arguments
        with patch.object(sys, 'argv', ['main.py']):
            await main()
        
        mock_config_from_env.assert_called_once()
        mock_create_server.assert_called_once_with(mock_config)
        mock_stdio_server.assert_called_once_with(mock_server)
    
    @pytest.mark.asyncio
    @patch('src.__main__.Config.from_env')
    async def test_main_config_error(self, mock_config_from_env):
        """Test main function with configuration error."""
        mock_config_from_env.side_effect = Exception("Config error")
        
        with patch.object(sys, 'argv', ['main.py']):
            with pytest.raises(SystemExit) as exc_info:
                await main()
        
        assert exc_info.value.code == 1
    
    @pytest.mark.asyncio
    @patch('src.__main__.Config.from_env')
    @patch('src.__main__.create_server')
    async def test_main_server_error(self, mock_create_server, mock_config_from_env, mock_config):
        """Test main function with server creation error."""
        mock_config_from_env.return_value = mock_config
        mock_create_server.side_effect = Exception("Server error")
        
        with patch.object(sys, 'argv', ['main.py']):
            with pytest.raises(SystemExit) as exc_info:
                await main()
        
        assert exc_info.value.code == 1


class TestMainModule:
    """Test main module execution."""
    
    @patch('src.__main__.main')
    def test_main_module_execution(self, mock_main):
        """Test that main module can be executed."""
        mock_main.return_value = None
        
        # Import and execute the main module
        with patch.object(sys, 'argv', ['main.py']):
            import src.__main__
        
        # The main module should have been imported successfully
        assert 'src.__main__' in sys.modules 