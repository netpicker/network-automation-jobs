from comfy.automate import job


@job(platform=['cisco_ios', 'cisco_xe'])
def add_vlan_to_trunk(device, interface, vlan_id):
    """Add a VLAN to a trunk interface. Rollback: remove_vlan_from_trunk."""
    interface = str(interface).strip()
    vlan_id = str(vlan_id).strip()

    if not interface:
        raise ValueError("interface cannot be empty.")
    if not vlan_id.isdigit() or not (1 <= int(vlan_id) <= 4094):
        raise ValueError("vlan_id must be a number between 1 and 4094.")

    trunk_config = device.cli(f"show running-config interface {interface}")
    if f"allowed vlan {vlan_id}" in trunk_config:
        print(f"[SKIP] VLAN {vlan_id} is already allowed on {interface}.")
        return

    print(f"[PRE-CHECK] VLAN {vlan_id} is not allowed on {interface}. Proceeding...")
    device.cli.send_config_set([
        f"interface {interface}",
        f"switchport trunk allowed vlan add {vlan_id}"
    ])
    device.cli("write memory")
    print(f"[EXEC] Configuration saved on {device.name}.")

    verification = device.cli(f"show running-config interface {interface}")
    if f"allowed vlan {vlan_id}" not in verification:
        raise RuntimeError(f"VLAN {vlan_id} addition could not be verified on {device.name}.")

    print(f"[SUCCESS] VLAN {vlan_id} added to trunk {interface} on {device.name}.")
