# list_vm.py

import logging
from helpers import get_vsphere_client, safe_api_call

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def list_vms_text() -> str:
    """List all VMs as formatted text string for MCP server."""
    logger.info("Starting VM list retrieval")
    
    try:
        client = get_vsphere_client()
        
        # Define the API call and formatting
        api_call = {
            'call': lambda: client.vcenter.VM.list(),
            'format': lambda vms: [
                f"{vm.name} ({vm.vm})" for vm in vms
            ] if vms else ["No VMs found."]
        }
        
        # Execute the API call
        logger.info("Retrieving VM list from vCenter")
        data, error = safe_api_call(api_call['call'], "Failed to list VMs")
        
        if data:
            vm_count = len(data) if data else 0
            logger.info(f"Successfully retrieved {vm_count} VMs")
            result = "\n".join(api_call['format'](data))
            logger.info("Completed VM list retrieval")
            return result
        else:
            logger.error(f"Failed to retrieve VM list: {error}")
            return error or "❌ Unknown error occurred"
            
    except Exception as e:
        logger.error(f"Critical error in list_vms_text: {str(e)}")
        logger.error(f"Exception type: {type(e).__name__}")
        return f"❌ Failed to connect to vCenter: {str(e)}"

