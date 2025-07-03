#!/usr/bin/env python3
"""
Test file for VMware MCP Server Maintenance Operations
Tests the parsing, categorization, and execution logic
"""

import sys
import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock

# Add the mcp-server directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'mcp-server'))

import maintenance

class TestMaintenanceLogic(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        self.sample_instructions = """# VMware VM Maintenance Procedures

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
        
        self.sample_vm_list = """VM List:
Name: k8s-worker-01
Status: poweredOn
IP: 192.168.1.10

Name: k8s-worker-02
Status: poweredOn
IP: 192.168.1.11

Name: k8s-master-01
Status: poweredOn
IP: 192.168.1.20

Name: k8s-master-02
Status: poweredOn
IP: 192.168.1.21

Name: app-server-01
Status: poweredOn
IP: 192.168.1.30

Name: db-server-01
Status: poweredOn
IP: 192.168.1.40
"""

    def test_parse_maintenance_instructions(self):
        """Test parsing of maintenance instructions."""
        with patch('maintenance.read_maintenance_instructions', return_value=self.sample_instructions):
            result = maintenance.parse_maintenance_instructions()
            
            self.assertNotIn('error', result)
            self.assertIn('power_down_sequence', result)
            self.assertIn('power_up_sequence', result)
            
            # Check power-down sequence
            power_down = result['power_down_sequence']
            self.assertTrue(any('Wave 1 - Worker Nodes' in line for line in power_down))
            self.assertTrue(any('workers or node' in line for line in power_down))
            self.assertTrue(any('Wave 2 - Control Plane' in line for line in power_down))
            self.assertTrue(any('master or control-plane' in line for line in power_down))
            
            # Check power-up sequence
            power_up = result['power_up_sequence']
            self.assertTrue(any('Wave 1 - Control Plane' in line for line in power_up))
            self.assertTrue(any('Wave 2 - Worker Nodes' in line for line in power_up))

    def test_find_vms_by_category(self):
        """Test VM categorization based on instructions."""
        with patch('maintenance.vm_info.list_vms', return_value=self.sample_vm_list), \
             patch('maintenance.parse_maintenance_instructions') as mock_parse:
            
            # Mock the parsed instructions
            mock_parse.return_value = {
                'power_down_sequence': [
                    '1. **Wave 1 - Worker Nodes**',
                    '   We will power off all the VMs with the following names or selectors in our list below.',
                    '   - workers or node',
                    '2. **Wave 2 - Control Plane**',
                    '   We will power off all the VMs with the following names or selectors in our list below.',
                    '   - master or control-plane',
                    '3. **Wave 3 - Remaining VMs**',
                    '   We will power off all remaining VMs not already powered off.'
                ],
                'power_up_sequence': [],
                'instructions': self.sample_instructions
            }
            
            result = maintenance.find_vms_by_category()
            
            self.assertNotIn('error', result)
            self.assertIn('categories', result)
            self.assertIn('all_vms', result)
            
            categories = result['categories']
            
            # Debug output
            print(f"Categories found: {list(categories.keys())}")
            print(f"All VMs: {result['all_vms']}")
            for cat, vms in categories.items():
                print(f"Category '{cat}': {vms}")
            
            # Check worker nodes
            self.assertIn('wave_1_-_worker_nodes', categories)
            worker_vms = categories['wave_1_-_worker_nodes']
            self.assertEqual(len(worker_vms), 2)
            self.assertIn('k8s-worker-01', worker_vms)
            self.assertIn('k8s-worker-02', worker_vms)
            
            # Check master nodes
            self.assertIn('wave_2_-_control_plane', categories)
            master_vms = categories['wave_2_-_control_plane']
            self.assertEqual(len(master_vms), 2)
            self.assertIn('k8s-master-01', master_vms)
            self.assertIn('k8s-master-02', master_vms)
            
            # Check remaining VMs
            self.assertIn('wave_3_-_remaining_vms', categories)
            remaining_vms = categories['wave_3_-_remaining_vms']
            self.assertEqual(len(remaining_vms), 2)
            self.assertIn('app-server-01', remaining_vms)
            self.assertIn('db-server-01', remaining_vms)

    def test_execute_power_down_sequence(self):
        """Test power-down sequence execution."""
        with patch('maintenance.find_vms_by_category') as mock_find, \
             patch('maintenance.power.power_off_vm') as mock_power_off:
            
            # Mock VM categorization
            mock_find.return_value = {
                'categories': {
                    'wave_1_-_worker_nodes': ['k8s-worker-01', 'k8s-worker-02'],
                    'wave_2_-_control_plane': ['k8s-master-01', 'k8s-master-02'],
                    'wave_3_-_remaining_vms': ['app-server-01', 'db-server-01']
                },
                'all_vms': ['k8s-worker-01', 'k8s-worker-02', 'k8s-master-01', 'k8s-master-02', 'app-server-01', 'db-server-01'],
                'parsed_instructions': {
                    'power_down_sequence': [
                        '1. **Wave 1 - Worker Nodes**',
                        '   - workers or node',
                        '2. **Wave 2 - Control Plane**',
                        '   - master or control-plane',
                        '3. **Wave 3 - Remaining VMs**',
                        '   - remaining'
                    ]
                }
            }
            
            # Mock power operations
            mock_power_off.return_value = "Success"
            
            result = maintenance.execute_power_down_sequence()
            
            # Verify power operations were called
            self.assertEqual(mock_power_off.call_count, 6)
            
            # Check that workers were powered off first
            worker_calls = [call for call in mock_power_off.call_args_list if 'worker' in str(call)]
            self.assertEqual(len(worker_calls), 2)
            
            # Check that masters were powered off second
            master_calls = [call for call in mock_power_off.call_args_list if 'master' in str(call)]
            self.assertEqual(len(master_calls), 2)
            
            # Check that remaining VMs were powered off last
            remaining_calls = [call for call in mock_power_off.call_args_list if 'app-server' in str(call) or 'db-server' in str(call)]
            self.assertEqual(len(remaining_calls), 2)

    def test_execute_power_up_sequence(self):
        """Test power-up sequence execution."""
        with patch('maintenance.find_vms_by_category') as mock_find, \
             patch('maintenance.power.power_on_vm') as mock_power_on:
            
            # Mock VM categorization
            mock_find.return_value = {
                'categories': {
                    'wave_1_-_control_plane': ['k8s-master-01', 'k8s-master-02'],
                    'wave_2_-_worker_nodes': ['k8s-worker-01', 'k8s-worker-02'],
                    'wave_3_-_applications': ['app-server-01', 'db-server-01']
                },
                'all_vms': ['k8s-worker-01', 'k8s-worker-02', 'k8s-master-01', 'k8s-master-02', 'app-server-01', 'db-server-01'],
                'parsed_instructions': {
                    'power_up_sequence': [
                        '1. **Wave 1 - Control Plane**',
                        '   - master or control-plane',
                        '2. **Wave 2 - Worker Nodes**',
                        '   - workers or node',
                        '3. **Wave 3 - Applications**',
                        '   - remaining'
                    ]
                }
            }
            
            # Mock power operations
            mock_power_on.return_value = "Success"
            
            result = maintenance.execute_power_up_sequence()
            
            # Verify power operations were called
            self.assertEqual(mock_power_on.call_count, 6)
            
            # Check that masters were powered on first
            master_calls = [call for call in mock_power_on.call_args_list if 'master' in str(call)]
            self.assertEqual(len(master_calls), 2)
            
            # Check that workers were powered on second
            worker_calls = [call for call in mock_power_on.call_args_list if 'worker' in str(call)]
            self.assertEqual(len(worker_calls), 2)
            
            # Check that applications were powered on last
            app_calls = [call for call in mock_power_on.call_args_list if 'app-server' in str(call) or 'db-server' in str(call)]
            self.assertEqual(len(app_calls), 2)

    def test_get_maintenance_plan(self):
        """Test maintenance plan generation."""
        with patch('maintenance.find_vms_by_category') as mock_find:
            # Mock VM categorization
            mock_find.return_value = {
                'categories': {
                    'wave_1_-_worker_nodes': ['k8s-worker-01', 'k8s-worker-02'],
                    'wave_2_-_control_plane': ['k8s-master-01', 'k8s-master-02'],
                    'wave_3_-_remaining_vms': ['app-server-01', 'db-server-01']
                },
                'all_vms': ['k8s-worker-01', 'k8s-worker-02', 'k8s-master-01', 'k8s-master-02', 'app-server-01', 'db-server-01'],
                'parsed_instructions': {
                    'instructions': self.sample_instructions
                }
            }
            
            result = maintenance.get_maintenance_plan()
            
            self.assertIn('=== VMware Maintenance Plan ===', result)
            self.assertIn('Wave 1 - Worker Nodes (2): k8s-worker-01, k8s-worker-02', result)
            self.assertIn('Wave 2 - Control Plane (2): k8s-master-01, k8s-master-02', result)
            self.assertIn('Wave 3 - Remaining Vms (2): app-server-01, db-server-01', result)
            self.assertIn('Total VMs: 6', result)

    def test_error_handling(self):
        """Test error handling in various scenarios."""
        # Test file not found
        with patch('maintenance.read_maintenance_instructions', return_value="Error: maintenance-vmware.md file not found in instructions directory"):
            result = maintenance.parse_maintenance_instructions()
            self.assertIn('error', result)
            self.assertIn('Error:', result['error'])
        
        # Test VM list parsing error
        with patch('maintenance.vm_info.list_vms', side_effect=Exception("Connection failed")):
            result = maintenance.find_vms_by_category()
            self.assertIn('error', result)
            self.assertIn('Connection failed', result['error'])

    def test_edge_cases(self):
        """Test edge cases and boundary conditions."""
        # Test with no VMs
        with patch('maintenance.vm_info.list_vms', return_value="VM List:\n"), \
             patch('maintenance.parse_maintenance_instructions') as mock_parse:
            
            mock_parse.return_value = {
                'power_down_sequence': [
                    '1. **Wave 1 - Worker Nodes**',
                    '   - workers or node'
                ],
                'power_up_sequence': [],
                'instructions': self.sample_instructions
            }
            
            result = maintenance.find_vms_by_category()
            self.assertNotIn('error', result)
            self.assertEqual(len(result['all_vms']), 0)
            self.assertEqual(len(result['categories']['wave_1_-_worker_nodes']), 0)
        
        # Test with empty instructions
        with patch('maintenance.read_maintenance_instructions', return_value=""):
            result = maintenance.parse_maintenance_instructions()
            self.assertNotIn('error', result)
            self.assertEqual(len(result['power_down_sequence']), 0)
            self.assertEqual(len(result['power_up_sequence']), 0)

if __name__ == '__main__':
    # Create a temporary instructions file for testing
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.md') as f:
        f.write("""# Test Instructions

## VM Power-Down Sequence

1. **Wave 1 - Test Nodes**
   - test or demo

## VM Power-Up Sequence

1. **Wave 1 - Test Nodes**
   - test or demo
""")
        temp_file = f.name
    
    try:
        # Run the tests
        unittest.main(verbosity=2)
    finally:
        # Clean up
        if os.path.exists(temp_file):
            os.unlink(temp_file) 