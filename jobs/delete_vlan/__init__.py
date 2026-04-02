from comfy.automate import job

# =============================================================================
# Job:        delete_vlan
# Platform:   Cisco IOS / IOS-XE
# Version:    1.1
# Description:
#   Deletes a VLAN on Cisco IOS and IOS-XE devices.
#   Performs a pre-check to confirm VLAN exists before attempting deletion.
#   Warns if any access ports are assigned to the VLAN — those ports will
#   lose connectivity immediately upon deletion.
#   Verifies the VLAN is removed after configuration.
#
# Variables:
#   vlan_id    (int)  : VLAN ID to delete          e.g. 100
# =============================================================================

@job(platform=['cisco_ios', 'cisco_xe'])
def delete_vlan(device, vlan_id):

    vlan_id = str(vlan_id).strip()

    # INPUT VALIDATION
    if not vlan_id:
        print(f"[ERROR] vlan_id is required. Please provide a VLAN ID.")
        raise ValueError("vlan_id cannot be empty.")

    if not vlan_id.isdigit() or not (1 <= int(vlan_id) <= 4094):
        print(f"[ERROR] vlan_id '{vlan_id}' is invalid. Must be a number between 1 and 4094.")
        raise ValueError(f"Invalid vlan_id: {vlan_id}")

    # PRE-CHECK
    existing = device.cli(f"show vlan id {vlan_id}")

    if "active" not in existing.lower() and "suspended" not in existing.lower():
        print(f"[SKIP] VLAN {vlan_id} does not exist on {device.name}. No changes made.")
        return

    print(f"[PRE-CHECK] VLAN {vlan_id} exists on {device.name}. Checking port assignments...")

    # PORT WARNING
    # The 'show vlan id' output contains a table where the VLAN row lists
    # assigned access ports after the VLAN name and state columns.
    # Example line:
    #   82   USERS_VLAN      active    Et0/1, Et0/2, Et0/3
    # We extract anything from the 4th column onward on the matching VLAN line.
    assigned_ports = []
    for line in existing.splitlines():
        parts = line.split()
        if parts and parts[0] == vlan_id:
            # Ports start after: <id> <name> <state>
            assigned_ports = parts[3:]
            break

    # Strip trailing commas left over from column splitting
    assigned_ports = [p.rstrip(',') for p in assigned_ports if p.rstrip(',')]

    if assigned_ports:
        port_list = ', '.join(assigned_ports)
        print(f"[WARNING] VLAN {vlan_id} is assigned to the following ports: {port_list}")
        print(f"[WARNING] These ports will lose connectivity on VLAN {vlan_id} immediately upon deletion.")
    else:
        print(f"[PRE-CHECK] No access ports assigned to VLAN {vlan_id}.")

    print(f"[PRE-CHECK] Proceeding with deletion...")

    # EXECUTION
    try:
        device.cli.send_config_set([
            f"no vlan {vlan_id}"
        ])
        print(f"[EXEC] Deletion command sent to {device.name}.")

    except Exception as e:
        print(f"[ERROR] Failed to configure {device.name}: {e}")
        raise

    # POST-CHECK
    verification = device.cli(f"show vlan id {vlan_id}")

    if "active" not in verification.lower() and "suspended" not in verification.lower():
        print(f"[SUCCESS] VLAN {vlan_id} deleted successfully on {device.name}.")
    else:
        print(f"[FAILED] VLAN {vlan_id} still present after deletion. Check device manually.")
        raise RuntimeError(f"VLAN {vlan_id} deletion could not be verified on {device.name}.")