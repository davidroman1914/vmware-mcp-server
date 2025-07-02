#!/usr/bin/env python3
"""
Connection Management Module for VMware MCP Server
Handles vCenter connections and session management
"""

import os
import ssl
import socket
import requests
import sys
from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim

# Global service instance
_service_instance = None


def connect_to_vcenter():
    """Connect to vCenter using pyvmomi for power operations."""
    global _service_instance
    
    if _service_instance:
        try:
            # Test if connection is still alive
            content = _service_instance.RetrieveContent()
            return True
        except:
            _service_instance = None
    
    try:
        host = os.getenv('VCENTER_HOST')
        user = os.getenv('VCENTER_USER')
        password = os.getenv('VCENTER_PASSWORD')
        
        if not all([host, user, password]):
            return False
        
        # Add timeout to prevent hanging
        socket.setdefaulttimeout(3)  # 3 second timeout
        
        # Create SSL context with optimizations
        context = ssl.SSLContext(ssl.PROTOCOL_TLS)
        context.verify_mode = ssl.CERT_NONE
        context.check_hostname = False
        
        _service_instance = SmartConnect(
            host=host,
            user=user,
            pwd=password,
            sslContext=context
        )
        return True
        
    except Exception as e:
        print(f"Connection error: {e}", file=sys.stderr)
        return False


def get_service_instance():
    """Get the global service instance, connecting if necessary."""
    if connect_to_vcenter():
        return _service_instance
    return None


def get_vcenter_session():
    """Get vCenter REST API session for fast operations."""
    host = os.getenv('VCENTER_HOST')
    user = os.getenv('VCENTER_USER')
    password = os.getenv('VCENTER_PASSWORD')
    
    if not all([host, user, password]):
        return None
    
    try:
        # Create session
        session_url = f"https://{host}/rest/com/vmware/cis/session"
        response = requests.post(
            session_url,
            auth=(user, password),
            verify=False,
            timeout=5
        )
        
        if response.status_code == 200:
            session_id = response.json()['value']
            return session_id
        else:
            print(f"Failed to create session: {response.status_code}", file=sys.stderr)
            return None
            
    except Exception as e:
        print(f"Session error: {e}", file=sys.stderr)
        return None


def disconnect_vcenter():
    """Disconnect from vCenter."""
    global _service_instance
    if _service_instance:
        try:
            Disconnect(_service_instance)
        except:
            pass
        _service_instance = None 