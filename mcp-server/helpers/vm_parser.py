#!/usr/bin/env python3
"""
VM Parser for VMware Operations
Handles VM-specific parsing tasks like categorization and matching
"""

import re
from typing import Dict, Any, List, Optional
from collections import defaultdict

def categorize_vms_by_type(vm_names: List[str], vm_types: Dict[str, List[str]]) -> Dict[str, Any]:
    """
    Categorize VMs by their type based on naming patterns.
    
    Args:
        vm_names: List of VM names to categorize
        vm_types: Dictionary mapping VM types to selector patterns
        
    Returns:
        Dictionary mapping VM types to lists of VM names
    """
    if not vm_names:
        return {"error": "No VM names provided"}
    
    if not vm_types:
        return {"error": "No VM types provided"}
    
    categorized_vms = {}
    used_vms = set()
    
    for vm_type, selectors in vm_types.items():
        categorized_vms[vm_type] = []
        
        for vm_name in vm_names:
            if vm_name in used_vms:
                continue
            
            if _vm_matches_type_selectors(vm_name, selectors):
                categorized_vms[vm_type].append(vm_name)
                used_vms.add(vm_name)
    
    return categorized_vms

def parse_vm_list(vm_list_text: str) -> List[str]:
    """
    Parse a VM list from various text formats.
    
    Args:
        vm_list_text: Text containing VM names in various formats
        
    Returns:
        List of extracted VM names
    """
    if not vm_list_text or not vm_list_text.strip():
        return []
    
    vm_names = []
    lines = vm_list_text.split('\n')
    
    for line in lines:
        line_stripped = line.strip()
        if not line_stripped:
            continue
        
        # Look for bullet points with VM names: "- ova-inf-k8s-worker-uat-01 (POWERED_ON)"
        if line_stripped.startswith('- ') and '(POWERED_ON)' in line_stripped:
            vm_name = line_stripped[2:].split(' (POWERED_ON)')[0]
            vm_names.append(vm_name)
        # Look for other common formats
        elif line_stripped.startswith('- '):
            vm_name = line_stripped[2:].strip()
            if vm_name:
                vm_names.append(vm_name)
        # Look for plain VM names
        elif re.match(r'^[a-zA-Z0-9\-_\.]+$', line_stripped):
            vm_names.append(line_stripped)
    
    return vm_names

def extract_vm_attributes(vm_name: str) -> Dict[str, str]:
    """
    Extract attributes from a VM name.
    
    Args:
        vm_name: Name of the VM
        
    Returns:
        Dictionary of extracted attributes
    """
    attributes = {
        "name": vm_name,
        "type": "unknown",
        "environment": "unknown",
        "role": "unknown"
    }
    
    vm_lower = vm_name.lower()
    
    # Extract environment
    if any(env in vm_lower for env in ["prod", "production"]):
        attributes["environment"] = "production"
    elif any(env in vm_lower for env in ["staging", "stage"]):
        attributes["environment"] = "staging"
    elif any(env in vm_lower for env in ["dev", "development"]):
        attributes["environment"] = "development"
    elif any(env in vm_lower for env in ["test", "testing"]):
        attributes["environment"] = "testing"
    elif any(env in vm_lower for env in ["uat"]):
        attributes["environment"] = "uat"
    
    # Extract role/type
    if any(role in vm_lower for role in ["worker", "node"]):
        attributes["role"] = "worker"
        attributes["type"] = "worker_node"
    elif any(role in vm_lower for role in ["master", "control"]):
        attributes["role"] = "master"
        attributes["type"] = "control_plane"
    elif any(role in vm_lower for role in ["app", "application"]):
        attributes["role"] = "application"
        attributes["type"] = "application"
    elif any(role in vm_lower for role in ["db", "database"]):
        attributes["role"] = "database"
        attributes["type"] = "database"
    elif any(role in vm_lower for role in ["web", "frontend"]):
        attributes["role"] = "web"
        attributes["type"] = "web_server"
    elif any(role in vm_lower for role in ["api", "backend"]):
        attributes["role"] = "api"
        attributes["type"] = "api_server"
    
    return attributes

def match_vms_by_pattern(vm_names: List[str], pattern: str) -> List[str]:
    """
    Match VMs by a regex pattern.
    
    Args:
        vm_names: List of VM names to search
        pattern: Regex pattern to match against
        
    Returns:
        List of VM names that match the pattern
    """
    if not vm_names or not pattern:
        return []
    
    try:
        regex = re.compile(pattern, re.IGNORECASE)
        return [vm for vm in vm_names if regex.search(vm)]
    except re.error:
        return []

def group_vms_by_attributes(vm_names: List[str]) -> Dict[str, Any]:
    """
    Group VMs by their extracted attributes.
    
    Args:
        vm_names: List of VM names to group
        
    Returns:
        Dictionary grouping VMs by various attributes
    """
    if not vm_names:
        return {}
    
    groups = {
        "by_environment": defaultdict(list),
        "by_role": defaultdict(list),
        "by_type": defaultdict(list)
    }
    
    for vm_name in vm_names:
        attributes = extract_vm_attributes(vm_name)
        
        groups["by_environment"][attributes["environment"]].append(vm_name)
        groups["by_role"][attributes["role"]].append(vm_name)
        groups["by_type"][attributes["type"]].append(vm_name)
    
    # Convert defaultdict to regular dict
    return {
        "by_environment": dict(groups["by_environment"]),
        "by_role": dict(groups["by_role"]),
        "by_type": dict(groups["by_type"])
    }

def _vm_matches_type_selectors(vm_name: str, selectors: List[str]) -> bool:
    """
    Check if a VM name matches type selectors.
    
    Args:
        vm_name: Name of the VM to check
        selectors: List of selector patterns to match against
        
    Returns:
        True if VM matches any selector, False otherwise
    """
    vm_lower = vm_name.lower()
    
    for selector in selectors:
        selector_lower = selector.lower()
        
        # Handle plural/singular variations
        selector_singular = selector_lower[:-1] if selector_lower.endswith('s') else selector_lower
        vm_singular = vm_lower[:-1] if vm_lower.endswith('s') else vm_lower
        
        # Check various matching patterns
        if (selector_lower in vm_lower or 
            selector_singular in vm_lower or
            vm_lower in selector_lower or 
            vm_lower in selector_singular or
            vm_singular in selector_lower or
            vm_singular in selector_singular):
            return True
    
    return False 