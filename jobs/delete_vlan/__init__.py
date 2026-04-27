from comfy.automate import job


@job(platform=['cisco_ios', 'cisco_xe'])
def delete_vlan(device, vlan_id):
    """Delete a VLAN and verify it is removed. Rollback: create_vlan."""
    vlan_id = str(vlan_id).strip()

    if not vlan_id.isdigit() or not (1 <= int(vlan_id) <= 4094):
        raise ValueError("vlan_id must be a number between 1 and 4094.")

    existing = device.cli(f"show vlan id {vlan_id}")
    if "not found" in existing.lower() or "active" not in existing.lower():
        print(f"[SKIP] VLAN {vlan_id} does not exist on {device.name}.")
        return

    print(f"[PRE-CHECK] VLAN {vlan_id} exists. Proceeding with deletion...")
    device.cli.send_config_set([f"no vlan {vlan_id}"])
    device.cli("write memory")
    print(f"[EXEC] Configuration saved on {device.name}.")

    verification = device.cli(f"show vlan id {vlan_id}")
    if "not found" not in verification.lower() and "active" in verification.lower():
        raise RuntimeError(f"VLAN {vlan_id} deletion could not be verified on {device.name}.")

    print(f"[SUCCESS] VLAN {vlan_id} deleted from {device.name}.")
