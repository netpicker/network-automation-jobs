from comfy.automate import job


@job(platform=['cisco_ios', 'cisco_xe'])
def create_vlan(device, vlan_id, vlan_name):
    """Create a VLAN and verify it exists. Rollback: delete_vlan."""
    vlan_id = str(vlan_id).strip()
    vlan_name = str(vlan_name).strip()

    if not vlan_name:
        raise ValueError("vlan_name cannot be empty.")

    if not vlan_id.isdigit() or not (1 <= int(vlan_id) <= 4094):
        raise ValueError("vlan_id must be a number between 1 and 4094.")

    existing = device.cli(f"show vlan id {vlan_id}")
    if "active" in existing.lower() or "suspended" in existing.lower():
        print(f"[SKIP] VLAN {vlan_id} already exists on {device.name}. No changes made.")
        return

    print(f"[PRE-CHECK] VLAN {vlan_id} does not exist. Proceeding...")

    device.cli.send_config_set([
        f"vlan {vlan_id}",
        f"name {vlan_name}"
    ])
    device.cli("write memory")
    print(f"[EXEC] Configuration saved on {device.name}.")

    verification = device.cli(f"show vlan id {vlan_id}")
    if "active" not in verification.lower() and "suspended" not in verification.lower():
        raise RuntimeError(f"VLAN {vlan_id} creation could not be verified on {device.name}.")

    print(f"[SUCCESS] VLAN {vlan_id} ('{vlan_name}') created successfully on {device.name}.")
