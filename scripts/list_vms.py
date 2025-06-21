#!/usr/bin/env python3
"""
VMware vSphere VM List Script
Lists all VMs present in a vCenter server
"""

import argparse
import ssl
from pprint import pprint
from vmware.vapi.vsphere.client import create_vsphere_client
from vmware.vapi.lib.connect import get_requests_connector
from vmware.vapi.security.session import create_session_security_context
from vmware.vapi.stdlib.client.factories import StubConfigurationFactory


def get_unverified_session():
    """
    Create an unverified SSL session for development/testing
    """
    import requests
    session = requests.Session()
    session.verify = False
    # Suppress SSL warnings
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    return session


class ListVM:
    """
    Demonstrates getting list of VMs present in vCenter
    Sample Prerequisites:
    vCenter/ESX
    """
    
    def __init__(self, server, username, password, skip_verification=False):
        self.server = server
        self.username = username
        self.password = password
        self.skip_verification = skip_verification
        
        # Create session if skip verification is enabled
        session = get_unverified_session() if skip_verification else None
        
        # Create vSphere client
        self.client = create_vsphere_client(
            server=server,
            username=username,
            password=password,
            session=session
        )

    def run(self):
        """
        List VMs present in server
        """
        try:
            list_of_vms = self.client.vcenter.VM.list()
            print("=" * 50)
            print("List Of VMs")
            print("=" * 50)
            pprint(list_of_vms)
            print("=" * 50)
            print(f"Total VMs found: {len(list_of_vms)}")
            return list_of_vms
        except Exception as e:
            print(f"Error listing VMs: {e}")
            return None


def main():
    parser = argparse.ArgumentParser(description='List VMs from vCenter server')
    parser.add_argument('--server', required=True, help='vCenter server address')
    parser.add_argument('--username', required=True, help='Username for authentication')
    parser.add_argument('--password', required=True, help='Password for authentication')
    parser.add_argument('--skip-verification', action='store_true', 
                       help='Skip SSL certificate verification')
    
    args = parser.parse_args()
    
    # Create ListVM instance and run
    list_vm = ListVM(
        server=args.server,
        username=args.username,
        password=args.password,
        skip_verification=args.skip_verification
    )
    
    list_vm.run()


if __name__ == '__main__':
    main() 