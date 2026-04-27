from comfy.automate import job


@job(platform=['cisco_ios', 'cisco_xe'])
def no_shutdown_interface(device, interface_name):
    """Enable an administratively down interface. Rollback: shutdown_interface."""
    interface_name = str(interface_name).strip()

    if not interface_name:
        raise ValueError("interface_name cannot be empty.")

    existing = device.cli(f"show ip interface {interface_name}")
    if "administratively down" not in existing.lower():
        print(f"[SKIP] Interface {interface_name} is already up on {device.name}.")
        return

    print(f"[PRE-CHECK] Interface {interface_name} is down. Proceeding...")
    device.cli.send_config_set([
        f"interface {interface_name}",
        "no shutdown"
    ])
    device.cli("write memory")
    print(f"[EXEC] Configuration saved on {device.name}.")

    verification = device.cli(f"show ip interface {interface_name}")
    if "up" not in verification.lower():
        raise RuntimeError(f"Interface {interface_name} enabling could not be verified on {device.name}.")

    print(f"[SUCCESS] Interface {interface_name} enabled on {device.name}.")
