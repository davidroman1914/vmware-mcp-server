#!/usr/bin/env python3
"""
Simple test script for Docker container to test template detection
Run this inside the Docker container with: python test_templates_docker.py
"""

import os
import sys

# Add current directory to path for imports
sys.path.insert(0, '.')

try:
    from vm_info import list_templates_text, list_all_vms_text
    from debug_templates import debug_vm_properties, test_template_detection_methods
    print("✅ Successfully imported modules")
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Available files:")
    for file in os.listdir('.'):
        if file.endswith('.py'):
            print(f"  - {file}")
    sys.exit(1)

def main():
    """Main test function."""
    print("🔧 VMware Template Detection Test")
    print("=" * 50)
    
    # Check environment variables
    print("\n📋 Environment Variables:")
    vcenter_host = os.getenv('VCENTER_SERVER') or os.getenv('VCENTER_HOST')
    vcenter_user = os.getenv('VCENTER_USERNAME') or os.getenv('VCENTER_USER')
    vcenter_pass = os.getenv('VCENTER_PASSWORD') or os.getenv('VCENTER_PWD')
    vcenter_insecure = os.getenv('VCENTER_INSECURE', 'false').lower() == 'true'
    
    print(f"   • Host: {vcenter_host or 'NOT SET'}")
    print(f"   • User: {vcenter_user or 'NOT SET'}")
    print(f"   • Password: {'SET' if vcenter_pass else 'NOT SET'}")
    print(f"   • Insecure: {vcenter_insecure}")
    
    if not all([vcenter_host, vcenter_user, vcenter_pass]):
        print("\n❌ Missing required environment variables!")
        print("Please set: VCENTER_SERVER, VCENTER_USERNAME, VCENTER_PASSWORD")
        return
    
    print("\n🚀 Starting tests...")
    
    # Test 1: List all VMs
    print("\n" + "="*50)
    print("TEST 1: List All VMs")
    print("="*50)
    try:
        result = list_all_vms_text()
        print(result)
    except Exception as e:
        print(f"❌ Error listing VMs: {e}")
    
    # Test 2: List templates (enhanced detection)
    print("\n" + "="*50)
    print("TEST 2: List Templates (Enhanced Detection)")
    print("="*50)
    try:
        result = list_templates_text()
        print(result)
    except Exception as e:
        print(f"❌ Error listing templates: {e}")
    
    # Test 3: Detailed debug analysis
    print("\n" + "="*50)
    print("TEST 3: Detailed Debug Analysis")
    print("="*50)
    try:
        debug_vm_properties()
    except Exception as e:
        print(f"❌ Error in debug analysis: {e}")
    
    # Test 4: Template detection methods
    print("\n" + "="*50)
    print("TEST 4: Template Detection Methods")
    print("="*50)
    try:
        test_template_detection_methods()
    except Exception as e:
        print(f"❌ Error testing detection methods: {e}")
    
    print("\n" + "="*50)
    print("✅ All tests completed!")
    print("="*50)

if __name__ == "__main__":
    main() 