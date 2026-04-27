from comfy.automate import job


@job(platform=['cisco_ios', 'cisco_xe'])
def set_interface_description(device, interface_name, description):
    """Set an interface description. Rollback: unset_interface_description."""
    interface_name = str(interface_name).strip()
    description = str(description).strip()

    if not interface_name:
        raise ValueError("interface_name cannot be empty.")
    if not description:
        raise ValueError("description cannot be empty.")

    existing = device.cli(f"show running-config interface {interface_name}")
    if "% Invalid" in existing:
        print(f"[SKIP] Interface {interface_name} does not exist on {device.name}.")
        return

    print(f"[PRE-CHECK] Interface {interface_name} exists. Proceeding...")
    device.cli.send_config_set([
        f"interface {interface_name}",
        f"description {description}"
    ])
    device.cli("write memory")
    print(f"[EXEC] Configuration saved on {device.name}.")

    verification = device.cli(f"show running-config interface {interface_name}")
    if description not in verification:
        raise RuntimeError(f"Interface description could not be verified on {device.name}.")

    print(f"[SUCCESS] Description set on {interface_name} on {device.name}.")
