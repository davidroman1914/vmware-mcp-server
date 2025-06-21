from vmware.vapi.vsphere.client import create_vsphere_client
import urllib3
import requests

def get_unverified_session():
    session = requests.Session()
    session.verify = False
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    return session

class ListVM:
    def __init__(self, server, username, password, skip_verification=False):
        session = get_unverified_session() if skip_verification else None
        self.client = create_vsphere_client(
            server=server,
            username=username,
            password=password,
            session=session
        )

    def run(self):
        return self.client.vcenter.VM.list()

