from comfy.automate import job

# =============================================================================
# Job:        assign_vlan_to_access_port
# Platform:   Cisco IOS / IOS-XE
# Version:    1.0
# Description:
#   Assigns a VLAN to an access port on Cisco IOS and IOS-XE devices.
#   Performs a pre-check to confirm the VLAN exists and the interface is in access mode.
#   Verifies the VLAN assignment after configuration.
#
# Variables:
#   interface   (str)  : Interface to assign the VLAN to  e.g. "GigabitEthernet0/1"
#   vlan_id     (int)  : VLAN ID to assign to the access port  e.g. 100
#
# Rollback:
#   To undo a successful run, use the remove_vlan_from_access_port job.
# =============================================================================


@job(platform=['cisco_ios', 'cisco_xe'])
def assign_vlan_to_access_port(device, interface, vlan_id):

    interface = str(interface).strip()
    vlan_id = str(vlan_id).strip()

    # INPUT VALIDATION
    if not interface:
        print("[ERROR] interface is required. Please provide an interface.")
        raise ValueError("interface cannot be empty.")

    if not vlan_id:
        print("[ERROR] vlan_id is required. Please provide a VLAN ID.")
        raise ValueError("vlan_id cannot be empty.")

    if not vlan_id.isdigit() or not (1 <= int(vlan_id) <= 4094):
        print(f"[ERROR] vlan_id '{vlan_id}' is invalid. Must be a number between 1 and 4094.")
        raise ValueError(f"Invalid vlan_id: {vlan_id}")

    # PRE-CHECK
    vlan_check = device.cli(f"show vlan id {vlan_id}")
    interface_check = device.cli(f"show running-config interface {interface}")

    if "not found" in vlan_check.lower() or "active" not in vlan_check.lower():
        print(f"[SKIP] VLAN {vlan_id} does not exist. No changes made.")
        return

    if "switchport mode access" not in interface_check.lower():
        print(f"[SKIP] Interface {interface} is not in access mode. No changes made.")
        return

    print(f"[PRE-CHECK] VLAN {vlan_id} exists and interface {interface} is in access mode. Proceeding...")

    # EXECUTION
    try:
        device.cli.send_config_set([
            f"interface {interface}",
            f"switchport access vlan {vlan_id}"
        ])
        device.cli.send_command("write memory")
        print(f"[EXEC] Configuration sent to {device.name}.")

    except Exception as e:
        print(f"[ERROR] Failed to configure {device.name}: {e}")
        raise

    # POST-CHECK
    verification = device.cli(f"show running-config interface {interface}")

    if f"switchport access vlan {vlan_id}" in verification:
        print(f"[SUCCESS] VLAN {vlan_id} assigned to {interface} successfully on {device.name}.")
    else:
        print("[FAILED] VLAN assignment not found after configuration. Check device manually.")
        raise RuntimeError(f"VLAN {vlan_id} assignment could not be verified on {device.name}.")
