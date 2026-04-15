from comfy.automate import job

# =============================================================================
# Job:        list_vlans
# Platform:   Cisco IOS / IOS-XE
# Version:    1.0
# Description:
#   Lists all VLANs on Cisco IOS and IOS-XE devices.
#   No pre-check or post-check is required as this is a read-only operation.
# =============================================================================


@job(platform=['cisco_ios', 'cisco_xe'])
def list_vlans(device):

    # EXECUTION
    try:
        vlans = device.cli("show vlan brief")
        print(vlans)

    except Exception as e:
        print(f"[ERROR] Failed to retrieve VLANs from {device.name}: {e}")
        raise