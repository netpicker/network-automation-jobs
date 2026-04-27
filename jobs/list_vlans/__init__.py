from comfy.automate import job


@job(platform=['cisco_ios', 'cisco_xe'])
def list_vlans(device):
    """Print all VLANs on the device."""
    print(device.cli("show vlan brief"))
