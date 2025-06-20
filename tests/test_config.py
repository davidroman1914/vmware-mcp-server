"""
Tests for configuration module.
"""
import pytest
import os
import tempfile
from pathlib import Path

from src.config import Config, VMwareConfig, ServerConfig


class TestVMwareConfig:
    """Test VMwareConfig class."""
    
    def test_vmware_config_creation(self):
        """Test creating VMwareConfig with all parameters."""
        config = VMwareConfig(
            host="test-host",
            user="test-user",
            password="test-password",
            datacenter="test-dc",
            cluster="test-cluster",
            datastore="test-ds",
            network="test-network",
            insecure=True
        )
        
        assert config.host == "test-host"
        assert config.user == "test-user"
        assert config.password == "test-password"
        assert config.datacenter == "test-dc"
        assert config.cluster == "test-cluster"
        assert config.datastore == "test-ds"
        assert config.network == "test-network"
        assert config.insecure is True
    
    def test_vmware_config_minimal(self):
        """Test creating VMwareConfig with minimal parameters."""
        config = VMwareConfig(
            host="test-host",
            user="test-user",
            password="test-password"
        )
        
        assert config.host == "test-host"
        assert config.user == "test-user"
        assert config.password == "test-password"
        assert config.datacenter is None
        assert config.cluster is None
        assert config.datastore is None
        assert config.network is None
        assert config.insecure is False


class TestServerConfig:
    """Test ServerConfig class."""
    
    def test_server_config_creation(self):
        """Test creating ServerConfig with all parameters."""
        config = ServerConfig(
            api_key="test-key",
            log_file="/path/to/log",
            log_level="DEBUG",
            host="127.0.0.1",
            port=9000
        )
        
        assert config.api_key == "test-key"
        assert config.log_file == "/path/to/log"
        assert config.log_level == "DEBUG"
        assert config.host == "127.0.0.1"
        assert config.port == 9000
    
    def test_server_config_defaults(self):
        """Test ServerConfig default values."""
        config = ServerConfig()
        
        assert config.api_key is None
        assert config.log_file is None
        assert config.log_level == "INFO"
        assert config.host == "0.0.0.0"
        assert config.port == 8000


class TestConfig:
    """Test Config class."""
    
    def test_config_creation(self, mock_vmware_config, mock_server_config):
        """Test creating Config with all parameters."""
        config = Config(
            vmware=mock_vmware_config,
            server=mock_server_config
        )
        
        assert config.vmware == mock_vmware_config
        assert config.server == mock_server_config
    
    def test_config_from_dict(self, sample_config_dict):
        """Test creating Config from dictionary."""
        config = Config.from_dict(sample_config_dict)
        
        assert config.vmware.host == "192.168.1.100"
        assert config.vmware.user == "administrator@vsphere.local"
        assert config.vmware.password == "password123"
        assert config.vmware.datacenter == "Datacenter1"
        assert config.vmware.cluster == "Cluster1"
        assert config.vmware.datastore == "Datastore1"
        assert config.vmware.network == "VM Network"
        assert config.vmware.insecure is True
        
        assert config.server.api_key == "test-api-key"
        assert config.server.log_file == "./logs/test.log"
        assert config.server.log_level == "DEBUG"
        assert config.server.host == "0.0.0.0"
        assert config.server.port == 8000
    
    def test_config_from_dict_minimal(self):
        """Test creating Config from minimal dictionary."""
        data = {
            "vcenter_host": "test-host",
            "vcenter_user": "test-user",
            "vcenter_password": "test-password"
        }
        
        config = Config.from_dict(data)
        
        assert config.vmware.host == "test-host"
        assert config.vmware.user == "test-user"
        assert config.vmware.password == "test-password"
        assert config.vmware.datacenter is None
        assert config.vmware.insecure is False
        
        assert config.server.api_key is None
        assert config.server.log_level == "INFO"
        assert config.server.host == "0.0.0.0"
        assert config.server.port == 8000
    
    def test_config_from_env(self, monkeypatch):
        """Test creating Config from environment variables."""
        env_vars = {
            "VCENTER_HOST": "env-host",
            "VCENTER_USER": "env-user",
            "VCENTER_PASSWORD": "env-password",
            "VCENTER_DATACENTER": "env-dc",
            "VCENTER_CLUSTER": "env-cluster",
            "VCENTER_DATASTORE": "env-ds",
            "VCENTER_NETWORK": "env-network",
            "VCENTER_INSECURE": "true",
            "API_KEY": "env-key",
            "LOG_FILE": "/env/log",
            "LOG_LEVEL": "WARNING",
            "HOST": "env-host",
            "PORT": "9000"
        }
        
        for key, value in env_vars.items():
            monkeypatch.setenv(key, value)
        
        config = Config.from_env()
        
        assert config.vmware.host == "env-host"
        assert config.vmware.user == "env-user"
        assert config.vmware.password == "env-password"
        assert config.vmware.datacenter == "env-dc"
        assert config.vmware.cluster == "env-cluster"
        assert config.vmware.datastore == "env-ds"
        assert config.vmware.network == "env-network"
        assert config.vmware.insecure is True
        
        assert config.server.api_key == "env-key"
        assert config.server.log_file == "/env/log"
        assert config.server.log_level == "WARNING"
        assert config.server.host == "env-host"
        assert config.server.port == 9000
    
    def test_config_from_env_defaults(self, monkeypatch):
        """Test Config from environment with defaults."""
        # Clear all relevant environment variables
        env_vars = [
            "VCENTER_HOST", "VCENTER_USER", "VCENTER_PASSWORD",
            "VCENTER_DATACENTER", "VCENTER_CLUSTER", "VCENTER_DATASTORE",
            "VCENTER_NETWORK", "VCENTER_INSECURE", "API_KEY", "LOG_FILE",
            "LOG_LEVEL", "HOST", "PORT"
        ]
        
        for var in env_vars:
            monkeypatch.delenv(var, raising=False)
        
        # Set only required variables
        monkeypatch.setenv("VCENTER_HOST", "test-host")
        monkeypatch.setenv("VCENTER_USER", "test-user")
        monkeypatch.setenv("VCENTER_PASSWORD", "test-password")
        
        config = Config.from_env()
        
        assert config.vmware.host == "test-host"
        assert config.vmware.user == "test-user"
        assert config.vmware.password == "test-password"
        assert config.vmware.insecure is False
        
        assert config.server.log_level == "INFO"
        assert config.server.host == "0.0.0.0"
        assert config.server.port == 8000
    
    def test_config_from_file(self, sample_config_dict):
        """Test creating Config from YAML file."""
        import yaml
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(sample_config_dict, f)
            config_path = f.name
        
        try:
            config = Config.from_file(config_path)
            
            assert config.vmware.host == "192.168.1.100"
            assert config.vmware.user == "administrator@vsphere.local"
            assert config.vmware.password == "password123"
            assert config.server.api_key == "test-api-key"
        finally:
            os.unlink(config_path)
    
    def test_config_from_file_not_found(self):
        """Test Config.from_file with non-existent file."""
        with pytest.raises(FileNotFoundError):
            Config.from_file("/non/existent/path/config.yaml")
    
    def test_config_from_file_path_object(self, sample_config_dict):
        """Test creating Config from Path object."""
        import yaml
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(sample_config_dict, f)
            config_path = Path(f.name)
        
        try:
            config = Config.from_file(config_path)
            
            assert config.vmware.host == "192.168.1.100"
            assert config.vmware.user == "administrator@vsphere.local"
        finally:
            os.unlink(config_path) 