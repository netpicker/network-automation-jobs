from comfy.automate import job

# =============================================================================
# Job:        add_vlan_to_trunk
# Platform:   Cisco IOS / IOS-XE
# Version:    1.0
# Description:
#   Adds a VLAN to a trunk port on Cisco IOS and IOS-XE devices.
#   Performs a pre-check to confirm the VLAN is not already allowed on the trunk.
#   Verifies the VLAN is added after configuration.
#
# Variables:
#   interface   (str)  : Interface to configure as trunk  e.g. "GigabitEthernet0/1"
#   vlan_id     (int)  : VLAN ID to add to the trunk       e.g. 100
#
# Rollback:
#   To undo a successful run, use the remove_vlan_from_trunk job.
# =============================================================================


@job(platform=['cisco_ios', 'cisco_xe'])
def add_vlan_to_trunk(device, interface, vlan_id):

    interface = str(interface).strip()
    vlan_id = str(vlan_id).strip()

    # INPUT VALIDATION
    if not interface:
        print("[ERROR] interface is required. Please provide an interface.")
        raise ValueError("interface cannot be empty.")

    if not vlan_id.isdigit() or not (1 <= int(vlan_id) <= 4094):
        print(f"[ERROR] vlan_id '{vlan_id}' is invalid. Must be a number between 1 and 4094.")
        raise ValueError(f"Invalid vlan_id: {vlan_id}")

    # PRE-CHECK
    trunk_config = device.cli(f"show running-config interface {interface}")

    if f"allowed vlan {vlan_id}" in trunk_config:
        print(f"[SKIP] VLAN {vlan_id} is already allowed on {interface}. No changes made.")
        return

    print(f"[PRE-CHECK] VLAN {vlan_id} is not allowed on {interface}. Proceeding...")

    # EXECUTION
    try:
        device.cli.send_config_set([
            f"interface {interface}",
            f"switchport trunk allowed vlan add {vlan_id}",
            "exit"
        ])
        print(f"[EXEC] Configuration sent to {device.name}.")

    except Exception as e:
        print(f"[ERROR] Failed to configure {device.name}: {e}")
        raise

    # POST-CHECK
    verification = device.cli(f"show running-config interface {interface}")

    if f"allowed vlan {vlan_id}" in verification:
        print(f"[SUCCESS] VLAN {vlan_id} added to trunk on {interface} successfully.")
    else:
        print("[FAILED] VLAN not found in trunk configuration after addition. Check device manually.")
        raise RuntimeError(f"VLAN {vlan_id} addition could not be verified on {device.name}.")
