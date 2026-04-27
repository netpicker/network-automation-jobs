from comfy.automate import job


@job(platform=['cisco_ios', 'cisco_xe'])
def assign_vlan_to_access_port(device, interface, vlan_id):
    """Assign a VLAN to an access interface. Rollback: remove_vlan_from_access_port."""
    interface = str(interface).strip()
    vlan_id = str(vlan_id).strip()

    if not interface:
        raise ValueError("interface cannot be empty.")
    if not vlan_id.isdigit() or not (1 <= int(vlan_id) <= 4094):
        raise ValueError("vlan_id must be a number between 1 and 4094.")

    vlan_check = device.cli(f"show vlan id {vlan_id}")
    if "not found" in vlan_check.lower() or "active" not in vlan_check.lower():
        print(f"[SKIP] VLAN {vlan_id} does not exist.")
        return

    interface_config = device.cli(f"show running-config interface {interface}")
    if "switchport mode access" not in interface_config.lower():
        print(f"[SKIP] Interface {interface} is not in access mode.")
        return

    print(f"[PRE-CHECK] VLAN {vlan_id} exists and {interface} is an access port. Proceeding...")
    device.cli.send_config_set([
        f"interface {interface}",
        f"switchport access vlan {vlan_id}"
    ])
    device.cli("write memory")
    print(f"[EXEC] Configuration saved on {device.name}.")

    verification = device.cli(f"show running-config interface {interface}")
    if f"switchport access vlan {vlan_id}" not in verification:
        raise RuntimeError(f"VLAN {vlan_id} assignment could not be verified on {device.name}.")

    print(f"[SUCCESS] VLAN {vlan_id} assigned to {interface} on {device.name}.")
