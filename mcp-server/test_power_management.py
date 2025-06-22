#!/usr/bin/env python3
"""
Test script for power management functionality
"""

import sys
import asyncio
import json
from power_management import power_on_vm_text, power_off_vm_text, restart_vm_text
from vm_info import get_vm_info_text
from config import Config

def test_power_management():
    """Test power management functions."""
    print("🔧 Testing Power Management Functions")
    print("=" * 50)
    
    # Test VM ID (using one from your environment)
    test_vm_id = "vm-2027"  # ova-inf-radius-01 (powered off)
    
    try:
        print(f"📋 Testing with VM ID: {test_vm_id}")
        print()
        
        # Test getting VM info
        print("1. Getting VM info...")
        info_result = get_vm_info_text(test_vm_id)
        print(info_result)
        print()
        
        # Test power on (if powered off)
        print("2. Testing power on...")
        power_on_result = power_on_vm_text(test_vm_id)
        print(power_on_result)
        print()
        
        # Wait a moment for power on to complete
        print("⏳ Waiting 10 seconds for power on to complete...")
        import time
        time.sleep(10)
        
        # Test restart
        print("3. Testing restart...")
        restart_result = restart_vm_text(test_vm_id)
        print(restart_result)
        print()
        
        # Wait a moment for restart to complete
        print("⏳ Waiting 15 seconds for restart to complete...")
        time.sleep(15)
        
        # Test power off
        print("4. Testing power off...")
        power_off_result = power_off_vm_text(test_vm_id)
        print(power_off_result)
        print()
        
        print("✅ Power management tests completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    # Check environment variables using config module
    missing_vars = Config.validate_config()
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        print("Please set VCENTER_HOST, VCENTER_USER, and VCENTER_PASSWORD")
        sys.exit(1)
    
    # Show current config (without sensitive data)
    config_summary = Config.get_config_summary()
    print(f"🔧 Using vCenter: {config_summary['host']}")
    print(f"👤 User: {config_summary['user']}")
    print(f"🔒 Password set: {config_summary['password_set']}")
    print(f"⚠️  Insecure: {config_summary['insecure']}")
    print()
    
    success = test_power_management()
    sys.exit(0 if success else 1) 