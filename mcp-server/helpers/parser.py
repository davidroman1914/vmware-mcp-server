#!/usr/bin/env python3
"""
Parser Helpers for Maintenance Instructions
Provides smart parsing functions for natural language maintenance instructions
"""

import re
from typing import Dict, Any, List, Optional
from collections import defaultdict

def parse_maintenance_instructions_smart(instructions_text: str) -> Dict[str, Any]:
    """
    Parse maintenance instructions using smart pattern matching.
    
    Args:
        instructions_text: Raw maintenance instructions in any natural language format
        
    Returns:
        Structured data with power sequences and categories
    """
    try:
        # Normalize text
        text = instructions_text.lower()
        
        # Extract sections
        sections = _extract_sections(text)
        
        # Parse sequences
        power_down_sequence = _parse_sequence(sections.get("shutdown", ""), "shutdown")
        power_up_sequence = _parse_sequence(sections.get("startup", ""), "startup")
        
        # Extract categories
        categories = _extract_categories(power_down_sequence + power_up_sequence)
        
        return {
            "power_down_sequence": power_down_sequence,
            "power_up_sequence": power_up_sequence,
            "categories": categories,
            "instructions": instructions_text
        }
        
    except Exception as e:
        return {"error": f"Smart parsing failed: {str(e)}"}

def parse_maintenance_instructions_spacy(instructions_text: str) -> Dict[str, Any]:
    """
    Parse maintenance instructions using spaCy NLP (if available).
    
    Args:
        instructions_text: Raw maintenance instructions
        
    Returns:
        Structured data with power sequences and categories
    """
    try:
        import spacy
        
        # Load English language model
        try:
            nlp = spacy.load("en_core_web_sm")
        except OSError:
            return {"error": "spaCy English model not found. Install with: python -m spacy download en_core_web_sm"}
        
        # Parse the text with spaCy
        doc = nlp(instructions_text.lower())
        
        # Extract sections
        sections = _extract_sections_spacy(doc)
        
        # Parse power sequences
        power_down_sequence = _parse_power_sequence_spacy(sections.get("shutdown", ""), "shutdown")
        power_up_sequence = _parse_power_sequence_spacy(sections.get("startup", ""), "startup")
        
        # Extract categories
        categories = _extract_categories(power_down_sequence + power_up_sequence)
        
        return {
            "power_down_sequence": power_down_sequence,
            "power_up_sequence": power_up_sequence,
            "categories": categories,
            "instructions": instructions_text
        }
        
    except ImportError:
        return {"error": "spaCy not available. Install with: pip install spacy"}
    except Exception as e:
        return {"error": f"spaCy parsing failed: {str(e)}"}

def parse_maintenance_instructions_with_fallback(instructions_text: str) -> Dict[str, Any]:
    """
    Parse maintenance instructions with fallback strategy.
    Tries smart parsing first, then spaCy if available, then manual parsing.
    
    Args:
        instructions_text: Raw maintenance instructions
        
    Returns:
        Structured data with power sequences and categories
    """
    # Try smart parsing first
    result = parse_maintenance_instructions_smart(instructions_text)
    if "error" not in result:
        return result
    
    # Try spaCy parsing if smart parsing failed
    result = parse_maintenance_instructions_spacy(instructions_text)
    if "error" not in result:
        return result
    
    # Fall back to manual parsing (your current approach)
    return parse_maintenance_instructions_manual(instructions_text)

def parse_maintenance_instructions_manual(instructions_text: str) -> Dict[str, Any]:
    """
    Manual parsing fallback - your current parsing approach.
    
    Args:
        instructions_text: Raw maintenance instructions
        
    Returns:
        Structured data with power sequences and categories
    """
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
            'instructions': instructions_text
        }
    except Exception as e:
        return {'error': f"Manual parsing failed: {str(e)}"}

def categorize_vms_smart(vm_names: List[str], parsed_instructions: Dict[str, Any]) -> Dict[str, List[str]]:
    """
    Categorize VMs based on parsed instructions.
    
    Args:
        vm_names: List of VM names to categorize
        parsed_instructions: Output from parse functions
        
    Returns:
        Dictionary mapping categories to lists of VM names
    """
    if "error" in parsed_instructions:
        return {"error": parsed_instructions["error"]}
    
    categories = parsed_instructions.get("categories", {})
    categorized_vms = {}
    used_vms = set()
    
    # Process each category in order
    for category, selectors in categories.items():
        categorized_vms[category] = []
        
        if "remaining" in selectors:
            # Add all unused VMs to this category
            for vm_name in vm_names:
                if vm_name not in used_vms:
                    categorized_vms[category].append(vm_name)
                    used_vms.add(vm_name)
        else:
            # Match VMs based on selectors
            for vm_name in vm_names:
                if vm_name in used_vms:
                    continue
                
                vm_lower = vm_name.lower()
                for selector in selectors:
                    selector_lower = selector.lower()
                    # Handle plural/singular variations
                    selector_singular = selector_lower[:-1] if selector_lower.endswith('s') else selector_lower
                    
                    if (selector_lower in vm_lower or 
                        selector_singular in vm_lower or
                        vm_lower in selector_lower or 
                        vm_lower in selector_singular):
                        categorized_vms[category].append(vm_name)
                        used_vms.add(vm_name)
                        break
    
    return categorized_vms

# Helper functions for smart parsing
def _extract_sections(text: str) -> Dict[str, str]:
    """Extract shutdown and startup sections."""
    power_patterns = {
        "shutdown": [
            r"shut\s*down", r"power\s*off", r"turn\s*off", r"stop",
            r"power\s*down", r"shutdown", r"poweroff"
        ],
        "startup": [
            r"start\s*up", r"power\s*on", r"turn\s*on", r"start",
            r"bring\s*up", r"startup", r"poweron", r"boot"
        ]
    }
    
    sections = {"shutdown": "", "startup": ""}
    current_section = None
    
    lines = text.split('\n')
    for line in lines:
        line_lower = line.lower()
        
        if any(re.search(pattern, line_lower) for pattern in power_patterns["shutdown"]):
            current_section = "shutdown"
        elif any(re.search(pattern, line_lower) for pattern in power_patterns["startup"]):
            current_section = "startup"
        elif line_lower.startswith('##') and current_section:
            current_section = None
        
        if current_section:
            sections[current_section] += line + "\n"
    
    return sections

def _parse_sequence(section_text: str, sequence_type: str) -> List[Dict[str, Any]]:
    """Parse a sequence section into structured waves."""
    if not section_text.strip():
        return []
    
    sequence_patterns = [
        r"(\d+)\.?\s*\*\*([^*]+)\*\*",  # 1. **Wave 1 - Worker Nodes**
        r"wave\s*(\d+)[:\-]?\s*([^,\n]+)",  # Wave 1: Worker Nodes
        r"(\d+)\.?\s*([^,\n]+?)(?:nodes?|plane|vms?|applications?)",  # 1. Worker Nodes
        r"first[:\-]?\s*([^,\n]+)",  # First: Worker Nodes
        r"second[:\-]?\s*([^,\n]+)",  # Second: Control Plane
        r"third[:\-]?\s*([^,\n]+)",  # Third: Applications
    ]
    
    waves = []
    wave_order = 1
    
    for pattern in sequence_patterns:
        matches = re.finditer(pattern, section_text, re.IGNORECASE)
        for match in matches:
            if len(match.groups()) >= 2:
                description = match.group(2).strip()
            else:
                description = match.group(1).strip()
            
            category = _categorize_description(description)
            selectors = _extract_selectors_from_context(section_text, match.start())
            
            wave = {
                "wave": f"wave_{wave_order}",
                "category": category,
                "description": description.title(),
                "selectors": selectors,
                "order": wave_order
            }
            waves.append(wave)
            wave_order += 1
    
    # If no explicit waves found, try to infer from natural language
    if not waves:
        waves = _infer_waves_from_natural_language(section_text, sequence_type)
    
    return waves

def _categorize_description(description: str) -> str:
    """Categorize a description into a standard category."""
    category_patterns = {
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
    
    desc_lower = description.lower()
    
    for category, patterns in category_patterns.items():
        if any(re.search(pattern, desc_lower, re.IGNORECASE) for pattern in patterns):
            return category
    
    # Default categorization
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

def _extract_selectors_from_context(text: str, position: int) -> List[str]:
    """Extract selectors from the context around a position."""
    selector_patterns = [
        r'"([^"]+)"',  # Quoted strings
        r'(\w+(?:\s+\w+)*)\s+or\s+(\w+(?:\s+\w+)*)',  # "worker or node"
        r'[-•]\s*(\w+(?:\s+\w+)*)',  # Bullet points
        r'selectors?:\s*(\w+(?:\s*,\s*\w+)*)',  # "selectors: worker, node"
        r'(\w+(?:\s+\w+)*)\s+in\s+their\s+names?',  # "worker in their names"
    ]
    
    selectors = []
    sentences = re.split(r'[.!?]', text)
    current_pos = 0
    
    for sentence in sentences:
        sentence_end = current_pos + len(sentence)
        if current_pos <= position <= sentence_end:
            for pattern in selector_patterns:
                matches = re.findall(pattern, sentence, re.IGNORECASE)
                for match in matches:
                    if isinstance(match, tuple):
                        selectors.extend(match)
                    else:
                        selectors.append(match)
            break
        current_pos = sentence_end + 1
    
    # Clean and deduplicate
    clean_selectors = []
    for selector in selectors:
        clean_selector = re.sub(r'\s+', ' ', selector.strip()).lower()
        if clean_selector and clean_selector not in clean_selectors:
            clean_selectors.append(clean_selector)
    
    return clean_selectors

def _infer_waves_from_natural_language(text: str, sequence_type: str) -> List[Dict[str, Any]]:
    """Infer waves from natural language when explicit patterns aren't found."""
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
            category = _categorize_description(description)
            selectors = _extract_selectors_from_context(text, match.start())
            
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

def _extract_categories(sequences: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    """Extract unique categories from sequences."""
    categories = defaultdict(list)
    
    for wave in sequences:
        category = wave.get("category")
        selectors = wave.get("selectors", [])
        if category and selectors:
            categories[category] = list(set(selectors))
    
    return dict(categories)

# spaCy helper functions (only used if spaCy is available)
def _extract_sections_spacy(doc) -> Dict[str, str]:
    """Extract shutdown and startup sections using spaCy."""
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
    """Parse a power sequence section using spaCy."""
    if not section_text.strip():
        return []
    
    import spacy
    nlp = spacy.load("en_core_web_sm")
    doc = nlp(section_text)
    
    waves = []
    current_wave = None
    wave_order = 1
    
    sentences = list(doc.sents)
    
    for sent in sentences:
        sent_text = sent.text.lower()
        wave_match = _extract_wave_info_spacy(sent_text)
        
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
            additional_selectors = _extract_selectors_from_context(sent_text, 0)
            current_wave["selectors"].extend(additional_selectors)
    
    if current_wave:
        waves.append(current_wave)
    
    return waves

def _extract_wave_info_spacy(text: str) -> Optional[Dict[str, Any]]:
    """Extract wave information using spaCy patterns."""
    patterns = [
        r'(\d+)\.?\s*\*\*([^*]+)\*\*',  # 1. **Wave 1 - Worker Nodes**
        r'wave\s*(\d+)[:\-]?\s*([^,\n]+)',  # Wave 1: Worker Nodes
        r'(\d+)\.?\s*([^,\n]+?)(?:nodes?|plane|vms?|applications?)',  # 1. Worker Nodes
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            description = match.group(2).strip()
            category = _categorize_description(description)
            selectors = _extract_selectors_from_context(text, 0)
            
            return {
                "category": category,
                "description": description.title(),
                "selectors": selectors
            }
    
    return None 