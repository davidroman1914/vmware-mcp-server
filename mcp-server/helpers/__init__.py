#!/usr/bin/env python3
"""
Helpers package for VMware MCP Server
Contains utility functions and helper modules
"""

from .power_parser import (
    parse_power_instructions,
    parse_power_instructions_smart,
    parse_power_instructions_spacy,
    parse_power_instructions_manual,
    categorize_vms_by_power
)

from .vm_parser import (
    categorize_vms_by_type,
    parse_vm_list,
    extract_vm_attributes,
    match_vms_by_pattern,
    group_vms_by_attributes
)

# Legacy aliases for backward compatibility
parse_maintenance_instructions_smart = parse_power_instructions_smart
parse_maintenance_instructions_spacy = parse_power_instructions_spacy
parse_maintenance_instructions_with_fallback = parse_power_instructions
parse_maintenance_instructions_manual = parse_power_instructions_manual
categorize_vms_smart = categorize_vms_by_power

__all__ = [
    # Power parser functions
    'parse_power_instructions',
    'parse_power_instructions_smart',
    'parse_power_instructions_spacy', 
    'parse_power_instructions_manual',
    'categorize_vms_by_power',
    
    # VM parser functions
    'categorize_vms_by_type',
    'parse_vm_list',
    'extract_vm_attributes',
    'match_vms_by_pattern',
    'group_vms_by_attributes',
    
    # Legacy aliases (deprecated but maintained for compatibility)
    'parse_maintenance_instructions_smart',
    'parse_maintenance_instructions_spacy',
    'parse_maintenance_instructions_with_fallback',
    'parse_maintenance_instructions_manual',
    'categorize_vms_smart'
] 