"""
List VMs Module

Provides a function to list all VMs as formatted text.
"""

import logging
from helpers import get_vsphere_client, safe_api_call

logger = logging.getLogger(__name__)

def list_vms_text() -> str:
    """List all VMs as formatted text string for MCP server."""
    try:
        client = get_vsphere_client()
        vms, error = safe_api_call(lambda: client.vcenter.VM.list(), "Failed to list VMs")
        if error:
            return error
        if not vms:
            return "No VMs found."
        return "\n".join(f"{vm.name} ({vm.vm})" for vm in vms)
    except Exception as e:
        logger.error(f"Error listing VMs: {str(e)}")
        return f"❌ Failed to connect to vCenter: {str(e)}"

