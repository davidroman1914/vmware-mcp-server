#!/usr/bin/env python3
"""
Simple vCenter connection test
Tests only the connection to vCenter with detailed debug output.
"""

import os
import sys
import ssl
from pyVim.connect import SmartConnect, Disconnect

def test_vcenter_connection():
    """Test vCenter connection with detailed debug output."""
    print("=== vCenter Connection Test ===")
    
    # Read environment variables
    print("[DEBUG] Reading environment variables...")
    host = os.getenv('VCENTER_HOST')
    user = os.getenv('VCENTER_USER')
    password = os.getenv('VCENTER_PASSWORD')
    insecure = os.getenv('VCENTER_INSECURE', 'false').lower() == 'true'
    
    print(f"[DEBUG] VCENTER_HOST: {host}")
    print(f"[DEBUG] VCENTER_USER: {user}")
    print(f"[DEBUG] VCENTER_INSECURE: {insecure}")
    print(f"[DEBUG] VCENTER_PASSWORD: {'***' if password else 'NOT SET'}")
    
    # Check if all required variables are set
    if not all([host, user, password]):
        print("[ERROR] Missing required environment variables:")
        if not host:
            print("  - VCENTER_HOST is not set")
        if not user:
            print("  - VCENTER_USER is not set")
        if not password:
            print("  - VCENTER_PASSWORD is not set")
        return False
    
    try:
        # Create SSL context
        print("[DEBUG] Creating SSL context...")
        if insecure:
            print("[DEBUG] Using insecure SSL context (CERT_NONE)")
            context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
            context.verify_mode = ssl.CERT_NONE
        else:
            print("[DEBUG] Using default SSL context")
            context = ssl.create_default_context()
        
        # Attempt connection
        print(f"[DEBUG] Attempting to connect to vCenter at {host}...")
        service_instance = SmartConnect(
            host=host,
            user=user,
            pwd=password,
            sslContext=context
        )
        
        print("[SUCCESS] Connected to vCenter successfully!")
        
        # Get basic info
        print("[DEBUG] Getting vCenter information...")
        content = service_instance.RetrieveContent()
        about = content.about
        
        print(f"[INFO] vCenter version: {about.version}")
        print(f"[INFO] vCenter build: {about.build}")
        print(f"[INFO] vCenter name: {about.name}")
        print(f"[INFO] vCenter full name: {about.fullName}")
        
        # Disconnect
        print("[DEBUG] Disconnecting from vCenter...")
        Disconnect(service_instance)
        print("[SUCCESS] Disconnected from vCenter")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to connect to vCenter: {e}")
        print(f"[ERROR] Exception type: {type(e).__name__}")
        return False

def main():
    """Main function."""
    print("vCenter Connection Test")
    print("======================")
    
    success = test_vcenter_connection()
    
    if success:
        print("\n[SUCCESS] Connection test passed!")
        sys.exit(0)
    else:
        print("\n[FAILURE] Connection test failed!")
        sys.exit(1)

if __name__ == "__main__":
    main() 