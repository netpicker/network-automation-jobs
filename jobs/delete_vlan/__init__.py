from comfy.automate import job

# =============================================================================
# Job:        delete_vlan
# Platform:   Cisco IOS / IOS-XE
# Version:    1.0
# Description:
#   Deletes a VLAN from Cisco IOS and IOS-XE devices.
#   Performs a pre-check to confirm the VLAN exists before deletion.
#   Verifies the VLAN is removed after configuration.
#
# Variables:
#   vlan_id    (int)  : VLAN ID to delete          e.g. 100
#
# Rollback:
#   To undo a successful run, use the create_vlan job.
# =============================================================================


@job(platform=['cisco_ios', 'cisco_xe'])
def delete_vlan(device, vlan_id):

    vlan_id = str(vlan_id).strip()

    # INPUT VALIDATION
    if not vlan_id:
        print("[ERROR] vlan_id is required. Please provide a VLAN ID.")
        raise ValueError("vlan_id cannot be empty.")

    if not vlan_id.isdigit() or not (1 <= int(vlan_id) <= 4094):
        print(f"[ERROR] vlan_id '{vlan_id}' is invalid. Must be a number between 1 and 4094.")
        raise ValueError(f"Invalid vlan_id: {vlan_id}")

    # PRE-CHECK
    existing = device.cli(f"show vlan id {vlan_id}")

    if "not found" in existing.lower() or "active" not in existing.lower():
        print(f"[SKIP] VLAN {vlan_id} does not exist on {device.name}. No changes needed.")
        return

    print(f"[PRE-CHECK] VLAN {vlan_id} exists. Proceeding with deletion...")

    # EXECUTION
    try:
        device.cli.send_config_set([
            f"no vlan {vlan_id}",
            "exit"
        ])
        print(f"[EXEC] Delete configuration sent to {device.name}.")

    except Exception as e:
        print(f"[ERROR] Failed to configure {device.name}: {e}")
        raise

    # POST-CHECK
    verification = device.cli(f"show vlan id {vlan_id}")

    if "not found" in verification.lower() or "active" not in verification.lower():
        print(f"[SUCCESS] VLAN {vlan_id} deleted successfully from {device.name}.")
    else:
        print("[FAILED] VLAN still present after deletion. Check device manually.")
        raise RuntimeError(f"VLAN {vlan_id} deletion could not be verified on {device.name}.")