from comfy.automate import job

# =============================================================================
# Job:        create_vlan
# Platform:   Cisco IOS / IOS-XE
# Version:    1.0
# Description:
#   Creates a VLAN on Cisco IOS and IOS-XE devices.
#   Performs a pre-check to avoid duplicate creation.
#   Verifies the VLAN exists after configuration.
#
# Variables:
#   vlan_id    (int)  : VLAN ID to create          e.g. 100
#   vlan_name  (str)  : Name/description for VLAN  e.g. "USERS_VLAN"
#
# Rollback:
#   To undo a successful run, use the delete_vlan job.
# =============================================================================


@job(platform=['cisco_ios', 'cisco_xe'])
def create_vlan(device, vlan_id, vlan_name):

    vlan_id = str(vlan_id).strip()
    vlan_name = str(vlan_name).strip()

    # INPUT VALIDATION
    if not vlan_id:
        print("[ERROR] vlan_id is required. Please provide a VLAN ID.")
        raise ValueError("vlan_id cannot be empty.")

    if not vlan_name:
        print("[ERROR] vlan_name is required. Please provide a VLAN name.")
        raise ValueError("vlan_name cannot be empty.")

    if not vlan_id.isdigit() or not (1 <= int(vlan_id) <= 4094):
        print(f"[ERROR] vlan_id '{vlan_id}' is invalid. Must be a number between 1 and 4094.")
        raise ValueError(f"Invalid vlan_id: {vlan_id}")

    # PRE-CHECK
    existing = device.cli(f"show vlan id {vlan_id}")

    if "active" in existing.lower() or "suspended" in existing.lower():
        print(f"[SKIP] VLAN {vlan_id} already exists on {device.name}. No changes made.")
        return

    print(f"[PRE-CHECK] VLAN {vlan_id} does not exist. Proceeding...")

    # EXECUTION
    try:
        device.cli.send_config_set([
            f"vlan {vlan_id}",
            f"name {vlan_name}"
        ])
        device.cli.send_command("write memory")
        print(f"[EXEC] Configuration sent to {device.name}.")

    except Exception as e:
        print(f"[ERROR] Failed to configure {device.name}: {e}")
        raise

    # POST-CHECK
    verification = device.cli(f"show vlan id {vlan_id}")

    if "active" in verification.lower() or "suspended" in verification.lower():
        print(f"[SUCCESS] VLAN {vlan_id} (\'{vlan_name}\') created successfully on {device.name}.")
    else:
        print("[FAILED] VLAN not found after configuration. Check device manually.")
        raise RuntimeError(f"VLAN {vlan_id} creation could not be verified on {device.name}.")
