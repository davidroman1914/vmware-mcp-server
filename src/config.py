"""
Configuration management for ESXi MCP Server.
"""
import os
import yaml
from dataclasses import dataclass, field
from typing import Optional, Union
from pathlib import Path


@dataclass
class VMwareConfig:
    """VMware connection configuration."""
    host: str
    user: str
    password: str
    datacenter: Optional[str] = None
    cluster: Optional[str] = None
    datastore: Optional[str] = None
    network: Optional[str] = None
    insecure: bool = False
    
    def __post_init__(self):
        """Validate required fields."""
        if not self.host:
            raise ValueError("VCENTER_HOST is required")
        if not self.user:
            raise ValueError("VCENTER_USER is required")
        if not self.password:
            raise ValueError("VCENTER_PASSWORD is required")


@dataclass
class ServerConfig:
    """MCP server configuration."""
    api_key: Optional[str] = None
    log_file: Optional[str] = None
    log_level: str = "INFO"
    host: str = "0.0.0.0"
    port: int = 8000


@dataclass
class Config:
    """Main configuration class."""
    vmware: VMwareConfig
    server: ServerConfig = field(default_factory=ServerConfig)
    
    @classmethod
    def from_file(cls, config_path: Union[str, Path]) -> "Config":
        """Load configuration from YAML file."""
        config_path = Path(config_path)
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(config_path, 'r') as f:
            data = yaml.safe_load(f)
        
        return cls.from_dict(data)
    
    @classmethod
    def from_dict(cls, data: dict) -> "Config":
        """Create configuration from dictionary."""
        vmware_data = {
            'host': data.get('vcenter_host'),
            'user': data.get('vcenter_user'),
            'password': data.get('vcenter_password'),
            'datacenter': data.get('datacenter'),
            'cluster': data.get('cluster'),
            'datastore': data.get('datastore'),
            'network': data.get('network'),
            'insecure': data.get('insecure', False),
        }
        
        server_data = {
            'api_key': data.get('api_key'),
            'log_file': data.get('log_file'),
            'log_level': data.get('log_level', 'INFO'),
            'host': data.get('host', '0.0.0.0'),
            'port': data.get('port', 8000),
        }
        
        return cls(
            vmware=VMwareConfig(**vmware_data),
            server=ServerConfig(**server_data)
        )
    
    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables."""
        vmware_data = {
            'host': os.getenv('VCENTER_HOST'),
            'user': os.getenv('VCENTER_USER'),
            'password': os.getenv('VCENTER_PASSWORD'),
            'datacenter': os.getenv('VCENTER_DATACENTER'),
            'cluster': os.getenv('VCENTER_CLUSTER'),
            'datastore': os.getenv('VCENTER_DATASTORE'),
            'network': os.getenv('VCENTER_NETWORK'),
            'insecure': os.getenv('VCENTER_INSECURE', 'false').lower() == 'true',
        }
        
        server_data = {
            'api_key': os.getenv('API_KEY'),
            'log_file': os.getenv('LOG_FILE'),
            'log_level': os.getenv('LOG_LEVEL', 'INFO'),
            'host': os.getenv('HOST', '0.0.0.0'),
            'port': int(os.getenv('PORT', '8000')),
        }
        
        return cls(
            vmware=VMwareConfig(**vmware_data),
            server=ServerConfig(**server_data)
        ) 