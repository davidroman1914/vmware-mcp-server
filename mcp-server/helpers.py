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

def get_resource_pool_name(client, resource_pool_id):
    """Get resource pool name from ID."""
    try:
        from com.vmware.vcenter_client import ResourcePool
        filter_spec = ResourcePool.FilterSpec(resource_pools=set([resource_pool_id]))
        resource_pools = client.vcenter.ResourcePool.list(filter=filter_spec)
        
        if resource_pools:
            return resource_pools[0].name
        else:
            return "Unknown"
    except Exception as e:
        logger.error(f"Failed to get resource pool name for {resource_pool_id}: {str(e)}")
        return "Unknown"

def get_datastore_name(client, datastore_id):
    """Get datastore name from ID."""
    try:
        from com.vmware.vcenter_client import Datastore
        filter_spec = Datastore.FilterSpec(datastores=set([datastore_id]))
        datastores = client.vcenter.Datastore.list(filter=filter_spec)
        
        if datastores:
            return datastores[0].name
        else:
            return "Unknown"
    except Exception as e:
        logger.error(f"Failed to get datastore name for {datastore_id}: {str(e)}")
        return "Unknown"

def get_folder_name(client, folder_id):
    """Get folder name from ID."""
    try:
        from com.vmware.vcenter_client import Folder
        filter_spec = Folder.FilterSpec(folders=set([folder_id]))
        folders = client.vcenter.Folder.list(filter=filter_spec)
        
        if folders:
            return folders[0].name
        else:
            return "Unknown"
    except Exception as e:
        logger.error(f"Failed to get folder name for {folder_id}: {str(e)}")
        return "Unknown"

def get_cluster_name(client, cluster_id):
    """Get cluster name from ID."""
    try:
        from com.vmware.vcenter_client import Cluster
        filter_spec = Cluster.FilterSpec(clusters=set([cluster_id]))
        clusters = client.vcenter.Cluster.list(filter=filter_spec)
        
        if clusters:
            return clusters[0].name
        else:
            return "Unknown"
    except Exception as e:
        logger.error(f"Failed to get cluster name for {cluster_id}: {str(e)}")
        return "Unknown"

def get_vm_runtime_info(client, vm_id):
    """Get VM runtime information which might contain placement details."""
    try:
        # Try to get runtime info
        runtime_info = client.vcenter.vm.Power.get(vm_id)
        logger.info(f"Runtime info type: {type(runtime_info).__name__}")
        logger.info(f"Runtime info attributes: {[attr for attr in dir(runtime_info) if not attr.startswith('_')]}")
        
        # Try to get VM summary which might have more placement info
        vm_summary = client.vcenter.VM.get(vm_id)
        logger.info(f"VM Summary type: {type(vm_summary).__name__}")
        logger.info(f"VM Summary attributes: {[attr for attr in dir(vm_summary) if not attr.startswith('_')]}")
        
        # Try to get host info
        try:
            host_info = client.vcenter.vm.guest.Identity.get(vm_id)
            logger.info(f"Host info type: {type(host_info).__name__}")
            logger.info(f"Host info attributes: {[attr for attr in dir(host_info) if not attr.startswith('_')]}")
        except Exception as e:
            logger.error(f"Failed to get host info: {str(e)}")
        
        return {
            'runtime': runtime_info,
            'summary': vm_summary
        }
        
    except Exception as e:
        logger.error(f"Failed to get VM runtime info: {str(e)}")
        return {}

def get_vm_placement_info(client, vm_id):
    """Get VM placement information including resource pool, datastore, folder, and cluster."""
    try:
        vm_info = client.vcenter.VM.get(vm_id)
        
        # Debug: Log all available attributes
        logger.info(f"=== VM Object Inspection for {vm_id} ===")
        attrs = [attr for attr in dir(vm_info) if not attr.startswith('_')]
        logger.info(f"Available VM attributes: {attrs}")
        
        for attr in attrs:
            try:
                value = getattr(vm_info, attr)
                logger.info(f"  {attr}: {value} (type: {type(value).__name__})")
            except Exception as e:
                logger.info(f"  {attr}: Error accessing - {str(e)}")
        
        placement_info = {}
        
        # Try different possible attribute names for resource pool
        resource_pool_id = None
        for attr_name in ['resource_pool', 'resourcePool', 'resource_pool_id']:
            if hasattr(vm_info, attr_name) and getattr(vm_info, attr_name):
                resource_pool_id = getattr(vm_info, attr_name)
                break
        
        if resource_pool_id:
            placement_info['resource_pool'] = get_resource_pool_name(client, resource_pool_id)
        
        # Try different possible attribute names for datastore
        datastore_id = None
        for attr_name in ['datastore', 'datastore_id', 'storage']:
            if hasattr(vm_info, attr_name) and getattr(vm_info, attr_name):
                datastore_id = getattr(vm_info, attr_name)
                break
        
        if datastore_id:
            placement_info['datastore'] = get_datastore_name(client, datastore_id)
        
        # Try different possible attribute names for folder
        folder_id = None
        for attr_name in ['folder', 'folder_id', 'parent_folder']:
            if hasattr(vm_info, attr_name) and getattr(vm_info, attr_name):
                folder_id = getattr(vm_info, attr_name)
                break
        
        if folder_id:
            placement_info['folder'] = get_folder_name(client, folder_id)
        
        # Try different possible attribute names for cluster
        cluster_id = None
        for attr_name in ['cluster', 'cluster_id', 'compute_resource']:
            if hasattr(vm_info, attr_name) and getattr(vm_info, attr_name):
                cluster_id = getattr(vm_info, attr_name)
                break
        
        if cluster_id:
            placement_info['cluster'] = get_cluster_name(client, cluster_id)
        
        # Also get runtime info for additional placement details
        runtime_info = get_vm_runtime_info(client, vm_id)
        
        logger.info(f"Placement info found: {placement_info}")
        return placement_info
        
    except Exception as e:
        logger.error(f"Failed to get VM placement info for {vm_id}: {str(e)}")
        return {}

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