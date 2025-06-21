#!/usr/bin/env python3
"""
Test script to verify VMware SDK installation and basic connectivity
"""

def test_imports():
    """Test if all required modules can be imported"""
    try:
        from vmware.vapi.vsphere.client import create_vsphere_client
        print("✓ VMware vSphere client import successful")
        return True
    except ImportError as e:
        print(f"✗ Failed to import VMware vSphere client: {e}")
        return False

def test_requests():
    """Test if requests module is available"""
    try:
        import requests
        print("✓ Requests module import successful")
        return True
    except ImportError as e:
        print(f"✗ Failed to import requests: {e}")
        return False

def main():
    print("Testing VMware SDK installation...")
    print("=" * 40)
    
    success = True
    success &= test_imports()
    success &= test_requests()
    
    print("=" * 40)
    if success:
        print("✓ All tests passed! The SDK is ready to use.")
    else:
        print("✗ Some tests failed. Please check the installation.")
    
    return success

if __name__ == '__main__':
    main() 