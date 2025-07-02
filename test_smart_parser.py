#!/usr/bin/env python3
"""
Test script for Smart Local Maintenance Instruction Parser
Demonstrates parsing different natural language formats without external dependencies
"""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'mcp-server'))

from parser_helpers import parse_maintenance_instructions_smart, parse_maintenance_instructions_with_fallback

def test_smart_parser():
    """Test the smart parser with different instruction formats."""
    
    # Example 1: Simple natural language
    simple_instructions = """
    # VMware Maintenance
    
    ## Shutdown Process
    When we need to shut down the VMware environment for maintenance:
    
    1. First, power off all the worker nodes - these are the VMs that have "worker" or "node" in their names
    2. Then shut down the control plane - look for VMs with "master" or "control-plane" 
    3. Finally, turn off any remaining VMs that haven't been powered off yet
    
    ## Startup Process  
    When bringing the environment back up after maintenance:
    
    1. Start the control plane first (masters and control-plane VMs)
    2. Then power on the worker nodes (worker and node VMs)
    3. Finally, bring up all the application VMs and anything else
    """
    
    # Example 2: Free-form notes
    freeform_instructions = """
    # Maintenance Notes
    
    For shutdown: workers first, then masters, then everything else.
    For startup: masters first, then workers, then apps.
    """
    
    # Example 3: Technical format (your current format)
    technical_instructions = """
    # VMware Maintenance Procedures
    
    ## VM Power-Down Sequence
    
    When shutting down VMs for maintenance:
    
    1. **Wave 1 - Worker Nodes**
       We will power off all the VMs with the following names or selectors in our list below. 
       - workers or node 
    
    2. **Wave 2 - Control Plane**
       We will power off all the VMs with the following names or selectors in our list below. 
       - master or control-plane
    
    3. **Wave 3 - Remaining VMs**
       We will power off all remaining VMs not already powered off.
    
    ## VM Power-Up Sequence
    
    When starting up VMs after maintenance:
    
    1. **Wave 1 - Control Plane**
       We will power on all the VMs with the following names or selectors in our list below. 
       - master or control-plane
    
    2. **Wave 2 - Worker Nodes**
       We will power on all the VMs with the following names or selectors in our list below. 
       - workers or node 
    
    3. **Wave 3 - Applications**
       We will power on all remaining VMs not already powered on.
    """
    
    # Example 4: Very simple format
    simple_format = """
    # Maintenance Plan
    
    Shutdown: worker nodes, then control plane, then remaining VMs.
    Startup: control plane, then worker nodes, then applications.
    """
    
    print("Testing Smart Local Parser")
    print("=" * 60)
    
    try:
        # Test with simple instructions
        print(f"\n1. Testing Simple Natural Language Format:")
        print("-" * 40)
        result = parse_maintenance_instructions_smart(simple_instructions)
        print_json_result(result)
        
        # Test with freeform instructions
        print(f"\n2. Testing Free-form Notes Format:")
        print("-" * 40)
        result = parse_maintenance_instructions_smart(freeform_instructions)
        print_json_result(result)
        
        # Test with technical instructions
        print(f"\n3. Testing Technical Format:")
        print("-" * 40)
        result = parse_maintenance_instructions_smart(technical_instructions)
        print_json_result(result)
        
        # Test with very simple format
        print(f"\n4. Testing Very Simple Format:")
        print("-" * 40)
        result = parse_maintenance_instructions_smart(simple_format)
        print_json_result(result)
        
        # Test VM categorization
        if "error" not in result:
            test_vms = [
                "k8s-worker-01", "k8s-worker-02", "k8s-master-01", 
                "k8s-master-02", "app-server-01", "db-server-01"
            ]
            from parser_helpers import categorize_vms_smart
            categorized = categorize_vms_smart(test_vms, result)
            print(f"\n5. VM Categorization Test:")
            print("-" * 40)
            print(f"Test VMs: {test_vms}")
            print(f"Categorized: {categorized}")
        
    except Exception as e:
        print(f"Error: {e}")

def print_json_result(result):
    """Pretty print the JSON result."""
    if "error" in result:
        print(f"❌ Error: {result['error']}")
    else:
        print("✅ Successfully parsed!")
        print(f"Power-down sequence: {len(result.get('power_down_sequence', []))} waves")
        print(f"Power-up sequence: {len(result.get('power_up_sequence', []))} waves")
        print(f"Categories: {list(result.get('categories', {}).keys())}")
        
        # Show first wave details as example
        if result.get('power_down_sequence'):
            first_wave = result['power_down_sequence'][0]
            print(f"Example - First wave: {first_wave.get('description')} with selectors: {first_wave.get('selectors')}")

def test_performance():
    """Test parsing performance."""
    print(f"\n{'='*60}")
    print("Performance Test")
    print(f"{'='*60}")
    
    import time
    
    test_instructions = """
    # Quick Test
    
    Shutdown: workers, then masters, then remaining.
    Startup: masters, then workers, then apps.
    """
    
    # Test parsing speed
    start_time = time.time()
    for i in range(100):
        result = parse_maintenance_instructions_smart(test_instructions)
    end_time = time.time()
    
    avg_time = (end_time - start_time) / 100
    print(f"Average parsing time: {avg_time*1000:.2f} ms per parse")
    print(f"Throughput: {1000/avg_time:.0f} parses per second")

if __name__ == "__main__":
    test_smart_parser()
    test_performance() 