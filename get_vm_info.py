import os
import requests
import urllib3
from vmware.vapi.vsphere.client import create_vsphere_client

def get_vm_info_text(vm_id: str) -> str:
    host = os.getenv("VCENTER_HOST")
    user = os.getenv("VCENTER_USER")
    pwd = os.getenv("VCENTER_PASSWORD")
    insecure = os.getenv("VCENTER_INSECURE", "false").lower() == "true"

    session = requests.Session()
    session.verify = not insecure
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    client = create_vsphere_client(server=host, username=user, password=pwd, session=session)
    report = []

    try:
        power = client.vcenter.vm.Power.get(vm_id)
        hardware = client.vcenter.vm.hardware.Memory.get(vm_id)
        cpu = client.vcenter.vm.hardware.Cpu.get(vm_id)
        identity = client.vcenter.vm.guest.Identity.get(vm_id)
        summary = client.vcenter.VM.get(vm_id)

        report.append("---- Guest Identity ----")
        report.append(f"Host Name         : {identity.name}")
        report.append(f"Ip Address        : {identity.ip_address}")
        report.append(f"Name              : {identity.guest_os}\n")

    except Exception as e:
        report.append("❌ Failed to get guest identity: " + str(e))

    try:
        report.append("---- Power State ----")
        report.append(f"Power State     : {power.state.name}\n")
    except:
        report.append("❌ Failed to get power state")

    try:
        report.append("---- VM Info ----")
        report.append(f"Name              : {summary.name}")
        report.append(f"Guest Os          : {summary.guest_OS or '❌ Not available'}\n")
    except:
        report.append("❌ Failed to get VM info")

    try:
        report.append("---- Memory ----")
        report.append(f"Size Mib          : {hardware.size_MiB}")
        report.append(f"Hot Add Enabled   : {hardware.hot_add_enabled}\n")
    except:
        report.append("❌ Failed to get memory info")

    try:
        report.append("---- CPU ----")
        report.append(f"Count             : {cpu.count}")
        report.append(f"Hot Add Enabled   : {cpu.hot_add_enabled}")
    except:
        report.append("❌ Failed to get CPU info")

    return "\n".join(report)

