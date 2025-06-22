"""
VMware MCP Server Helpers

Shared utility functions and helpers for the VMware MCP server.
"""

import os
import logging
import requests
import urllib3
from vmware.vapi.vsphere.client import create_vsphere_client
from com.vmware.vcenter_client import VM, Network
from typing import Optional

logger = logging.getLogger(__name__)

def get_vsphere_client():
    """Get vSphere client with proper configuration."""
    host = os.getenv("VCENTER_HOST")
    user = os.getenv("VCENTER_USER")
    pwd = os.getenv("VCENTER_PASSWORD")
    insecure = os.getenv("VCENTER_INSECURE", "false").lower() == "true"

    if not all([host, user, pwd]):
        missing = [k for k, v in [("VCENTER_HOST", host), ("VCENTER_USER", user), ("VCENTER_PASSWORD", pwd)] if not v]
        raise EnvironmentError(f"Missing: {', '.join(missing)}")

    session = requests.Session()
    session.verify = not insecure
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    return create_vsphere_client(server=host, username=user, password=pwd, session=session)

def safe_get_attr(obj, attr_name, default="Not available"):
    """Safely get attribute from object with fallback."""
    try:
        if hasattr(obj, attr_name):
            value = getattr(obj, attr_name)
            if hasattr(value, 'name'):
                return value.name
            elif hasattr(value, '__str__'):
                return str(value)
            else:
                return value if value is not None else default
        else:
            return default
    except Exception as e:
        logger.debug(f"Error accessing '{attr_name}': {str(e)}")
        return default

def format_bytes(bytes_value):
    """Format bytes in human-readable format."""
    if bytes_value is None:
        return "Unknown"
    try:
        bytes_value = int(bytes_value)
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.1f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.1f} PB"
    except:
        return str(bytes_value)

def get_vm_by_id(client, vm_id):
    """Get VM details by ID using VMware helper pattern."""
    try:
        # Ensure VM ID has the proper format (vm-xxx)
        if not vm_id.startswith('vm-'):
            vm_id = f"vm-{vm_id}"
        
        filter_spec = VM.FilterSpec(vms=set([vm_id]))
        vms = client.vcenter.VM.list(filter=filter_spec)
        
        if len(vms) == 0:
            logger.warning(f"VM with ID ({vm_id}) not found")
            return None
            
        vm = vms[0]
        logger.info(f"Found VM '{vm.name}' ({vm.vm})")
        return vm
    except Exception as e:
        logger.error(f"Error getting VM by ID {vm_id}: {str(e)}")
        return None

def get_network_name(client, network_id):
    """Get network name from network ID using VMware helper pattern."""
    try:
        filter_spec = Network.FilterSpec(networks=set([network_id]))
        networks = client.vcenter.Network.list(filter=filter_spec)
        
        if networks:
            return networks[0].name
        else:
            return "Unknown"
    except Exception as e:
        logger.error(f"Failed to get network name for {network_id}: {str(e)}")
        return "Unknown"

def safe_api_call(func, error_msg):
    """Safely execute API call and return formatted result or error."""
    try:
        logger.info(f"Executing API call: {func.__name__ if hasattr(func, '__name__') else 'lambda'}")
        result = func()
        logger.info(f"API call successful: {type(result).__name__}")
        return result, None
    except Exception as e:
        logger.error(f"API call failed: {error_msg}")
        logger.error(f"Exception type: {type(e).__name__}")
        logger.error(f"Exception message: {str(e)}")
        
        # Log additional details for common VMware errors
        if "401" in str(e):
            logger.error("Authentication failed (401 error) - check credentials")
        elif "403" in str(e):
            logger.error("Permission denied (403 error) - check user permissions")
        elif "500" in str(e):
            logger.error("vCenter server error (500 error) - check vCenter status")
        
        return None, f"❌ {error_msg}: {str(e)}"

def resolve_template_id(client, template_identifier: str) -> tuple[Optional[str], Optional[str]]:
    """
    Resolve template identifier (name or ID) to template ID using Content Library API.
    
    Args:
        client: vSphere client
        template_identifier: Template name or ID
        
    Returns:
        tuple: (template_id, error_message) - template_id is None if error
    """
    try:
        from com.vmware.content.library_client import Item
        
        # First, try to use the identifier directly as a template ID
        try:
            # Try to get template info using the identifier as ID
            template_info = client.content.library.Item.get(template_identifier)
            if hasattr(template_info, 'type') and template_info.type == 'com.vmware.content.library.item.VMTemplate':
                return template_identifier, None  # Success - it was already an ID
        except Exception as e:
            # If that fails, the identifier might be a name
            logger.debug(f"Identifier '{template_identifier}' is not a valid template ID: {str(e)}")
        
        # Try to find by name using FindSpec (the correct VMware approach)
        try:
            find_spec = Item.FindSpec(name=template_identifier)
            item_ids = client.content.library.Item.find(find_spec)
            
            if item_ids:
                # Check if the found item is a VM template
                for item_id in item_ids:
                    try:
                        item_info = client.content.library.Item.get(item_id)
                        if hasattr(item_info, 'type') and item_info.type == 'com.vmware.content.library.item.VMTemplate':
                            return item_id, None  # Found by name
                    except Exception as e:
                        logger.debug(f"Error checking item {item_id}: {str(e)}")
                        continue
        except Exception as e:
            logger.debug(f"Error searching for template by name: {str(e)}")
        
        # Since we can't find the template, provide a helpful error
        error_msg = f"❌ Template '{template_identifier}' not found. "
        error_msg += "Please provide the exact template ID or name. "
        error_msg += "Use 'list-templates' to see available templates."
        
        return None, error_msg
        
    except Exception as e:
        logger.error(f"Error resolving template '{template_identifier}': {str(e)}")
        return None, f"❌ Error resolving template '{template_identifier}': {str(e)}"

def list_templates(client) -> tuple[list, Optional[str]]:
    """
    List available templates using the Content Library API.
    
    Args:
        client: vSphere client
        
    Returns:
        tuple: (templates_list, error_message) - templates_list is empty if error
    """
    try:
        from com.vmware.content.library_client import Item, Library
        templates = []
        # Get all content libraries
        libraries = client.content.library.Library.list()
        for library_id in libraries:
            try:
                # List items in this library
                items = client.content.library.Item.list(library_id=library_id)
                for item_id in items:
                    try:
                        item_info = client.content.library.Item.get(item_id)
                        if hasattr(item_info, 'type') and item_info.type == 'com.vmware.content.library.item.VMTemplate':
                            templates.append({
                                'id': item_id,
                                'name': item_info.name,
                                'description': getattr(item_info, 'description', 'No description'),
                                'library_id': library_id
                            })
                    except Exception as e:
                        logger.debug(f"Error getting item info for {item_id}: {str(e)}")
                        continue
            except Exception as e:
                logger.debug(f"Error listing items in library {library_id}: {str(e)}")
                continue
        return templates, None
    except Exception as e:
        logger.error(f"Error listing templates: {str(e)}")
        return [], f"❌ Error listing templates: {str(e)}" 