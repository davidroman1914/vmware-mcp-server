#!/usr/bin/env python3
"""
Configuration module for VMware MCP Server
Handles environment variables and settings
"""

import os
from typing import Optional, List

class Config:
    """Configuration class for VMware vCenter settings."""
    
    @staticmethod
    def get_vcenter_host() -> Optional[str]:
        """Get vCenter host from environment."""
        return os.getenv("VCENTER_HOST")
    
    @staticmethod
    def get_vcenter_user() -> Optional[str]:
        """Get vCenter user from environment."""
        return os.getenv("VCENTER_USER")
    
    @staticmethod
    def get_vcenter_password() -> Optional[str]:
        """Get vCenter password from environment."""
        return os.getenv("VCENTER_PASSWORD")
    
    @staticmethod
    def get_vcenter_insecure() -> bool:
        """Get vCenter insecure flag from environment."""
        return os.getenv("VCENTER_INSECURE", "false").lower() == "true"
    
    @staticmethod
    def validate_config() -> List[str]:
        """Validate configuration and return list of missing variables."""
        missing = []
        
        if not Config.get_vcenter_host():
            missing.append("VCENTER_HOST")
        
        if not Config.get_vcenter_user():
            missing.append("VCENTER_USER")
        
        if not Config.get_vcenter_password():
            missing.append("VCENTER_PASSWORD")
        
        return missing
    
    @staticmethod
    def get_config_summary() -> dict:
        """Get a summary of the current configuration (without sensitive data)."""
        return {
            "host": Config.get_vcenter_host(),
            "user": Config.get_vcenter_user(),
            "password_set": bool(Config.get_vcenter_password()),
            "insecure": Config.get_vcenter_insecure()
        } 