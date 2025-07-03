#!/usr/bin/env python3
"""
VMware MCP Server - Maintenance Operations
Handles reading maintenance instructions and executing VM power sequences
"""

import os
from typing import Dict, Any
import vm_info
import power

def read_maintenance_instructions() -> str:
    """Read the maintenance-vmware.md file and return its contents."""
    try:
        instructions_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instructions', 'maintenance-vmware.md')
        with open(instructions_path, 'r') as f:
            return f.read()
    except FileNotFoundError:
        return "Error: maintenance-vmware.md file not found in instructions directory"
    except Exception as e:
        return f"Error reading maintenance instructions: {str(e)}"

def parse_maintenance_instructions() -> Dict[str, Any]:
    """Parse the maintenance instructions to extract VM categories and sequences."""
    try:
        instructions = read_maintenance_instructions()
        if instructions.startswith('Error:'):
            return {'error': instructions}
        
        power_down_section, power_up_section = [], []
        in_power_down = in_power_up = False
        
        for line in instructions.split('\n'):
            line_stripped = line.strip()
            if not line_stripped:
                continue
                
            if 'Power-Down' in line:
                in_power_down, in_power_up = True, False
            elif 'Power-Up' in line:
                in_power_down, in_power_up = False, True
            elif line_stripped.startswith('##') and (in_power_down or in_power_up):
                in_power_down = in_power_up = False
            elif in_power_down:
                power_down_section.append(line_stripped)
            elif in_power_up:
                power_up_section.append(line_stripped)
        
        return {
            'power_down_sequence': power_down_section,
            'power_up_sequence': power_up_section,
            'instructions': instructions
        }
    except Exception as e:
        return {'error': f"Error parsing maintenance instructions: {str(e)}"}

def _extract_categories_from_sequence(sequence: list) -> Dict[str, list]:
    """Extract categories and selectors from a power sequence."""
    categories = {}
    current_category = None
    
    for line in sequence:
        line_stripped = line.lstrip()
        if line_stripped.startswith(('1.', '2.', '3.')) and '**' in line_stripped:
            current_category = line_stripped.split('**')[1].split('**')[0].lower().replace(' ', '_')
            categories[current_category] = []
        elif line_stripped.startswith('-') and current_category:
            selector_text = line_stripped[1:].strip()
            if ' or ' in selector_text:
                selectors = [s.strip() for s in selector_text.split(' or ')]
                categories[current_category].extend(selectors)
            else:
                categories[current_category].append(selector_text)
        elif 'remaining' in line_stripped.lower() and current_category:
            categories[current_category].append('remaining')
    
    return categories

def find_vms_by_category() -> Dict[str, Any]:
    """Find VMs and categorize them based on the maintenance instructions."""
    try:
        all_vms = vm_info.list_vms()
        
        # Parse VM names from the actual vCenter response format
        vm_names = []
        lines = all_vms.split('\n')
        for line in lines:
            line_stripped = line.strip()
            # Look for bullet points with VM names: "- ova-inf-k8s-worker-uat-01 (POWERED_ON)"
            if line_stripped.startswith('- ') and '(POWERED_ON)' in line_stripped:
                # Extract VM name: "- ova-inf-k8s-worker-uat-01 (POWERED_ON)" -> "ova-inf-k8s-worker-uat-01"
                vm_name = line_stripped[2:].split(' (POWERED_ON)')[0]  # Remove "- " prefix and " (POWERED_ON)" suffix
                vm_names.append(vm_name)
        
        parsed = parse_maintenance_instructions()
        if 'error' in parsed:
            return parsed
        
        # Extract categories from both sequences
        categories = _extract_categories_from_sequence(parsed['power_down_sequence'])
        categories.update(_extract_categories_from_sequence(parsed['power_up_sequence']))
        
        # Categorize VMs
        categorized_vms = {}
        used_vms = set()
        
        for category, selectors in categories.items():
            categorized_vms[category] = []
            
            if 'remaining' in selectors:
                for vm_name in vm_names:
                    if vm_name not in used_vms:
                        categorized_vms[category].append(vm_name)
                        used_vms.add(vm_name)
            else:
                for vm_name in vm_names:
                    if vm_name in used_vms:
                        continue
                    vm_lower = vm_name.lower()
                    for selector in selectors:
                        selector_lower = selector.lower()
                        selector_singular = selector_lower[:-1] if selector_lower.endswith('s') else selector_lower
                        if (selector_lower in vm_lower or selector_singular in vm_lower or 
                            vm_lower in selector_lower or vm_lower in selector_singular):
                            categorized_vms[category].append(vm_name)
                            used_vms.add(vm_name)
                            break
        
        return {
            'categories': categorized_vms,
            'all_vms': vm_names,
            'parsed_instructions': parsed
        }
    except Exception as e:
        return {'error': f"Error categorizing VMs: {str(e)}"}

def _execute_sequence(sequence_name: str, power_func) -> str:
    """Execute a power sequence (up or down)."""
    try:
        vm_data = find_vms_by_category()
        if 'error' in vm_data:
            return vm_data['error']
        
        results = [f"Starting VM {sequence_name} sequence based on maintenance instructions..."]
        
        for line in vm_data['parsed_instructions'][f'power_{sequence_name}_sequence']:
            if line.startswith(('1.', '2.', '3.')) and '**' in line:
                category = line.split('**')[1].split('**')[0].lower().replace(' ', '_')
                if category in vm_data['categories']:
                    vms = vm_data['categories'][category]
                    if vms:
                        results.append(f"\n{line}:")
                        for vm_name in vms:
                            result = power_func(vm_name)
                            results.append(f"   - {vm_name}: {result}")
                    else:
                        results.append(f"\n{line}: No VMs found in this category")
        
        return '\n'.join(results)
    except Exception as e:
        return f"Error executing {sequence_name} sequence: {str(e)}"

def execute_power_down_sequence() -> str:
    """Execute the power-down sequence based on maintenance instructions."""
    return _execute_sequence('down', power.power_off_vm)

def execute_power_up_sequence() -> str:
    """Execute the power-up sequence based on maintenance instructions."""
    return _execute_sequence('up', power.power_on_vm)

def get_maintenance_plan() -> str:
    """Get the maintenance plan showing what VMs will be affected."""
    try:
        vm_data = find_vms_by_category()
        if 'error' in vm_data:
            return vm_data['error']
        
        plan = ["=== VMware Maintenance Plan ===", "", "Maintenance Instructions:", 
                vm_data['parsed_instructions']['instructions'], "", "VM Categorization:"]
        
        for category, vms in vm_data['categories'].items():
            category_display = category.replace('_', ' ').title()
            plan.append(f"{category_display} ({len(vms)}): {', '.join(vms) if vms else 'None'}")
        
        plan.append(f"\nTotal VMs: {len(vm_data['all_vms'])}")
        
        return '\n'.join(plan)
    except Exception as e:
        return f"Error getting maintenance plan: {str(e)}" 