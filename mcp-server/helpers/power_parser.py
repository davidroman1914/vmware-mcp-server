#!/usr/bin/env python3
"""
Power Parser for Maintenance Instructions
Handles parsing of VM power sequences from maintenance instructions
"""

import re
from typing import Dict, Any, List, Optional
from collections import defaultdict

import spacy

# Constants for power sequence parsing
POWER_ACTIONS = {
    "shutdown": [
        r"shut\s*down", r"power\s*off", r"turn\s*off", r"stop",
        r"power\s*down", r"shutdown", r"poweroff"
    ],
    "startup": [
        r"start\s*up", r"power\s*on", r"turn\s*on", r"start",
        r"bring\s*up", r"startup", r"poweron", r"boot"
    ]
}

SEQUENCE_PATTERNS = [
    r"(\d+)\.?\s*\*\*([^*]+)\*\*",  # 1. **Wave 1 - Worker Nodes**
    r"wave\s*(\d+)[:\-]?\s*([^,\n]+)",  # Wave 1: Worker Nodes
    r"(\d+)\.?\s*([^,\n]+?)(?:nodes?|plane|vms?|applications?)",  # 1. Worker Nodes
    r"first[:\-]?\s*([^,\n]+)",  # First: Worker Nodes
    r"second[:\-]?\s*([^,\n]+)",  # Second: Control Plane
    r"third[:\-]?\s*([^,\n]+)",  # Third: Applications
]

CATEGORY_PATTERNS = {
    "worker_nodes": [
        r"worker\s*nodes?", r"worker", r"node", r"nodes",
        r"worker\s*servers?", r"compute\s*nodes?"
    ],
    "control_plane": [
        r"control\s*plane", r"control-plane", r"controlplane",
        r"master", r"masters", r"api\s*server", r"apiserver"
    ],
    "applications": [
        r"applications?", r"app", r"apps", r"services?",
        r"application\s*servers?", r"app\s*servers?"
    ],
    "database": [
        r"databases?", r"db", r"sql", r"mysql", r"postgres",
        r"database\s*servers?", r"db\s*servers?"
    ],
    "remaining": [
        r"remaining", r"everything\s*else", r"rest", r"others",
        r"remaining\s*vms?", r"everything\s*else"
    ]
}

SELECTOR_PATTERNS = [
    r'"([^"]+)"',  # Quoted strings
    r'(\w+(?:\s+\w+)*)\s+or\s+(\w+(?:\s+\w+)*)',  # "worker or node"
    r'[-•]\s*(\w+(?:\s+\w+)*)',  # Bullet points
    r'selectors?:\s*(\w+(?:\s*,\s*\w+)*)',  # "selectors: worker, node"
    r'(\w+(?:\s+\w+)*)\s+in\s+their\s+names?',  # "worker in their names"
]

def parse_power_instructions(instructions_text: str) -> Dict[str, Any]:
    """
    Parse maintenance instructions for power sequences.
    
    Args:
        instructions_text: Raw maintenance instructions
        
    Returns:
        Structured data with power sequences and categories
    """
    if not instructions_text or not instructions_text.strip():
        return {"error": "Empty or invalid instructions text"}
    
    # Try smart parsing first (most reliable)
    result = parse_power_instructions_smart(instructions_text)
    if "error" not in result:
        return result
    
    # Try spaCy parsing if smart parsing failed
    result = parse_power_instructions_spacy(instructions_text)
    if "error" not in result:
        return result
    
    # Fall back to manual parsing
    return parse_power_instructions_manual(instructions_text)

def parse_power_instructions_smart(instructions_text: str) -> Dict[str, Any]:
    """Parse power instructions using smart pattern matching."""
    try:
        text = instructions_text.lower().strip()
        sections = _extract_power_sections(text)
        
        power_down_sequence = _parse_power_sequence(sections.get("shutdown", ""), "shutdown")
        power_up_sequence = _parse_power_sequence(sections.get("startup", ""), "startup")
        
        if not power_down_sequence and not power_up_sequence:
            return {"error": "No power sequences found in instructions"}
        
        categories = _extract_power_categories(power_down_sequence + power_up_sequence)
        
        return {
            "power_down_sequence": power_down_sequence,
            "power_up_sequence": power_up_sequence,
            "categories": categories,
            "instructions": instructions_text,
            "parser_type": "smart"
        }
        
    except Exception as e:
        return {"error": f"Smart power parsing failed: {str(e)}"}

def parse_power_instructions_spacy(instructions_text: str) -> Dict[str, Any]:
    """Parse power instructions using spaCy NLP."""
    try:
        nlp = spacy.load("en_core_web_sm")
        doc = nlp(instructions_text.lower().strip())
        
        sections = _extract_power_sections_spacy(doc)
        power_down_sequence = _parse_power_sequence_spacy(sections.get("shutdown", ""), "shutdown")
        power_up_sequence = _parse_power_sequence_spacy(sections.get("startup", ""), "startup")
        
        if not power_down_sequence and not power_up_sequence:
            return {"error": "No power sequences found in instructions"}
        
        categories = _extract_power_categories(power_down_sequence + power_up_sequence)
        
        return {
            "power_down_sequence": power_down_sequence,
            "power_up_sequence": power_up_sequence,
            "categories": categories,
            "instructions": instructions_text,
            "parser_type": "spacy"
        }
        
    except OSError:
        return {"error": "spaCy English model not found. Install with: python -m spacy download en_core_web_sm"}
    except Exception as e:
        return {"error": f"spaCy power parsing failed: {str(e)}"}

def parse_power_instructions_manual(instructions_text: str) -> Dict[str, Any]:
    """Manual parsing fallback for power instructions."""
    try:
        power_down_section, power_up_section = [], []
        in_power_down = in_power_up = False
        
        for line in instructions_text.split('\n'):
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
            'instructions': instructions_text,
            'parser_type': 'manual'
        }
    except Exception as e:
        return {'error': f"Manual power parsing failed: {str(e)}"}

def categorize_vms_by_power(vm_names: List[str], parsed_instructions: Dict[str, Any]) -> Dict[str, Any]:
    """
    Categorize VMs based on power sequence instructions.
    
    Args:
        vm_names: List of VM names to categorize
        parsed_instructions: Output from parse_power_instructions()
        
    Returns:
        Dictionary mapping categories to lists of VM names
    """
    if not vm_names:
        return {"error": "No VM names provided"}
    
    if "error" in parsed_instructions:
        return {"error": parsed_instructions["error"]}
    
    categories = parsed_instructions.get("categories", {})
    if not categories:
        return {"error": "No categories found in parsed instructions"}
    
    categorized_vms = {}
    used_vms = set()
    
    for category, selectors in categories.items():
        categorized_vms[category] = []
        
        if "remaining" in selectors:
            for vm_name in vm_names:
                if vm_name not in used_vms:
                    categorized_vms[category].append(vm_name)
                    used_vms.add(vm_name)
        else:
            for vm_name in vm_names:
                if vm_name in used_vms:
                    continue
                
                if _vm_matches_power_selectors(vm_name, selectors):
                    categorized_vms[category].append(vm_name)
                    used_vms.add(vm_name)
    
    return categorized_vms

def _vm_matches_power_selectors(vm_name: str, selectors: List[str]) -> bool:
    """Check if a VM name matches power sequence selectors."""
    vm_lower = vm_name.lower()
    
    for selector in selectors:
        selector_lower = selector.lower()
        selector_singular = selector_lower[:-1] if selector_lower.endswith('s') else selector_lower
        vm_singular = vm_lower[:-1] if vm_lower.endswith('s') else vm_lower
        
        if (selector_lower in vm_lower or 
            selector_singular in vm_lower or
            vm_lower in selector_lower or 
            vm_lower in selector_singular or
            vm_singular in selector_lower or
            vm_singular in selector_singular):
            return True
    
    return False

def _extract_power_sections(text: str) -> Dict[str, str]:
    """Extract shutdown and startup sections."""
    sections = {"shutdown": "", "startup": ""}
    current_section = None
    
    lines = text.split('\n')
    for line in lines:
        line_lower = line.lower()
        
        if any(re.search(pattern, line_lower) for pattern in POWER_ACTIONS["shutdown"]):
            current_section = "shutdown"
        elif any(re.search(pattern, line_lower) for pattern in POWER_ACTIONS["startup"]):
            current_section = "startup"
        elif line_lower.startswith('##') and current_section:
            current_section = None
        
        if current_section:
            sections[current_section] += line + "\n"
    
    return sections

def _parse_power_sequence(section_text: str, sequence_type: str) -> List[Dict[str, Any]]:
    """Parse a power sequence section into structured waves."""
    if not section_text.strip():
        return []
    
    waves = []
    wave_order = 1
    
    for pattern in SEQUENCE_PATTERNS:
        matches = re.finditer(pattern, section_text, re.IGNORECASE)
        for match in matches:
            if len(match.groups()) >= 2:
                description = match.group(2).strip()
            else:
                description = match.group(1).strip()
            
            category = _categorize_power_description(description)
            selectors = _extract_power_selectors_from_context(section_text, match.start())
            
            wave = {
                "wave": f"wave_{wave_order}",
                "category": category,
                "description": description.title(),
                "selectors": selectors,
                "order": wave_order
            }
            waves.append(wave)
            wave_order += 1
    
    if not waves:
        waves = _infer_power_waves_from_natural_language(section_text, sequence_type)
    
    return waves

def _categorize_power_description(description: str) -> str:
    """Categorize a power sequence description."""
    desc_lower = description.lower()
    
    for category, patterns in CATEGORY_PATTERNS.items():
        if any(re.search(pattern, desc_lower, re.IGNORECASE) for pattern in patterns):
            return category
    
    if any(word in desc_lower for word in ["worker", "node"]):
        return "worker_nodes"
    elif any(word in desc_lower for word in ["master", "control"]):
        return "control_plane"
    elif any(word in desc_lower for word in ["app", "application", "service"]):
        return "applications"
    elif any(word in desc_lower for word in ["db", "database"]):
        return "database"
    elif any(word in desc_lower for word in ["remaining", "rest", "else"]):
        return "remaining"
    
    return "other"

def _extract_power_selectors_from_context(text: str, position: int) -> List[str]:
    """Extract power selectors from context."""
    selectors = []
    sentences = re.split(r'[.!?]', text)
    current_pos = 0
    
    for sentence in sentences:
        sentence_end = current_pos + len(sentence)
        if current_pos <= position <= sentence_end:
            selectors.extend(_extract_power_selectors_from_text(sentence))
            break
        current_pos = sentence_end + 1
    
    return selectors

def _extract_power_selectors_from_text(text: str) -> List[str]:
    """Extract power selectors from text."""
    selectors = []
    
    for pattern in SELECTOR_PATTERNS:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            if isinstance(match, tuple):
                selectors.extend(match)
            else:
                selectors.append(match)
    
    for category, patterns in CATEGORY_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                selectors.append(pattern.replace(r'\s+', ' '))
    
    clean_selectors = []
    for selector in selectors:
        clean_selector = re.sub(r'\s+', ' ', selector.strip()).lower()
        if clean_selector and clean_selector not in clean_selectors:
            clean_selectors.append(clean_selector)
    
    return clean_selectors

def _infer_power_waves_from_natural_language(text: str, sequence_type: str) -> List[Dict[str, Any]]:
    """Infer power waves from natural language."""
    waves = []
    wave_order = 1
    
    natural_patterns = [
        (r"first[,\s]+([^,.]+)", "first"),
        (r"second[,\s]+([^,.]+)", "second"),
        (r"third[,\s]+([^,.]+)", "third"),
        (r"then[,\s]+([^,.]+)", "then"),
        (r"next[,\s]+([^,.]+)", "next"),
        (r"finally[,\s]+([^,.]+)", "finally"),
    ]
    
    for pattern, indicator in natural_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            description = match.group(1).strip()
            category = _categorize_power_description(description)
            selectors = _extract_power_selectors_from_context(text, match.start())
            
            wave = {
                "wave": f"wave_{wave_order}",
                "category": category,
                "description": description.title(),
                "selectors": selectors,
                "order": wave_order
            }
            waves.append(wave)
            wave_order += 1
    
    return waves

def _extract_power_categories(sequences: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    """Extract unique power categories from sequences."""
    categories = defaultdict(list)
    
    for wave in sequences:
        category = wave.get("category")
        selectors = wave.get("selectors", [])
        if category and selectors:
            categories[category] = list(set(selectors))
    
    return dict(categories)

# spaCy helper functions
def _extract_power_sections_spacy(doc) -> Dict[str, str]:
    """Extract power sections using spaCy."""
    power_actions = {
        "shutdown": ["shutdown", "shut down", "power off", "turn off", "stop"],
        "startup": ["startup", "start up", "power on", "turn on", "start", "bring up"]
    }
    
    sections = {"shutdown": "", "startup": ""}
    current_section = None
    
    for sent in doc.sents:
        sent_text = sent.text.lower()
        
        if any(action in sent_text for action in power_actions["shutdown"]):
            current_section = "shutdown"
        elif any(action in sent_text for action in power_actions["startup"]):
            current_section = "startup"
        
        if current_section:
            sections[current_section] += sent.text + " "
    
    return sections

def _parse_power_sequence_spacy(section_text: str, sequence_type: str) -> List[Dict[str, Any]]:
    """Parse power sequence using spaCy."""
    if not section_text.strip():
        return []
    
    nlp = spacy.load("en_core_web_sm")
    doc = nlp(section_text)
    
    waves = []
    current_wave = None
    wave_order = 1
    
    sentences = list(doc.sents)
    
    for sent in sentences:
        sent_text = sent.text.lower()
        wave_match = _extract_power_wave_info_spacy(sent_text)
        
        if wave_match:
            if current_wave:
                waves.append(current_wave)
            
            current_wave = {
                "wave": f"wave_{wave_order}",
                "category": wave_match["category"],
                "description": wave_match["description"],
                "selectors": wave_match["selectors"],
                "order": wave_order
            }
            wave_order += 1
        elif current_wave:
            additional_selectors = _extract_power_selectors_from_context(sent_text, 0)
            current_wave["selectors"].extend(additional_selectors)
    
    if current_wave:
        waves.append(current_wave)
    
    return waves

def _extract_power_wave_info_spacy(text: str) -> Optional[Dict[str, Any]]:
    """Extract power wave information using spaCy patterns."""
    patterns = [
        r'(\d+)\.?\s*\*\*([^*]+)\*\*',  # 1. **Wave 1 - Worker Nodes**
        r'wave\s*(\d+)[:\-]?\s*([^,\n]+)',  # Wave 1: Worker Nodes
        r'(\d+)\.?\s*([^,\n]+?)(?:nodes?|plane|vms?|applications?)',  # 1. Worker Nodes
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            description = match.group(2).strip()
            category = _categorize_power_description(description)
            selectors = _extract_power_selectors_from_context(text, 0)
            
            return {
                "category": category,
                "description": description.title(),
                "selectors": selectors
            }
    
    return None 