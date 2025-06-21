# list_vm.py

import os
import requests
import urllib3
import logging
from vmware.vapi.vsphere.client import create_vsphere_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_vsphere_client():
    """Get vSphere client with proper configuration."""
    host = os.getenv("VCENTER_HOST")
    user = os.getenv("VCENTER_USER")
    pwd = os.getenv("VCENTER_PASSWORD")
    insecure = os.getenv("VCENTER_INSECURE", "false").lower() == "true"

    logger.info(f"Connecting to vCenter: {host} (insecure: {insecure})")
    logger.info(f"Using user: {user}")

    if not all([host, user, pwd]):
        missing_vars = []
        if not host: missing_vars.append("VCENTER_HOST")
        if not user: missing_vars.append("VCENTER_USER")
        if not pwd: missing_vars.append("VCENTER_PASSWORD")
        logger.error(f"Missing environment variables: {', '.join(missing_vars)}")
        raise EnvironmentError(f"Missing VCENTER_* env vars: {', '.join(missing_vars)}")

    session = requests.Session()
    session.verify = not insecure
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    try:
        client = create_vsphere_client(server=host, username=user, password=pwd, session=session)
        logger.info("Successfully created vSphere client")
        return client
    except Exception as e:
        logger.error(f"Failed to create vSphere client: {str(e)}")
        logger.error(f"Connection details - Host: {host}, User: {user}, Insecure: {insecure}")
        raise

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

