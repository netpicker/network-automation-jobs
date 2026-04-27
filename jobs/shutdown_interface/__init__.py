from comfy.automate import job


@job(platform=['cisco_ios', 'cisco_xe'])
def shutdown_interface(device, interface_name):
    """Shut down an interface. Rollback: no_shutdown_interface."""
    interface_name = str(interface_name).strip()

    if not interface_name:
        raise ValueError("interface_name cannot be empty.")

    existing = device.cli(f"show ip interface brief | include {interface_name}")
    if "up" not in existing.lower():
        print(f"[SKIP] Interface {interface_name} is not up on {device.name}.")
        return

    print(f"[PRE-CHECK] Interface {interface_name} is up. Proceeding...")
    device.cli.send_config_set([
        f"interface {interface_name}",
        "shutdown"
    ])
    device.cli("write memory")
    print(f"[EXEC] Configuration saved on {device.name}.")

    verification = device.cli(f"show ip interface brief | include {interface_name}")
    if "administratively down" not in verification.lower():
        raise RuntimeError(f"Interface {interface_name} shutdown could not be verified on {device.name}.")

    print(f"[SUCCESS] Interface {interface_name} shut down on {device.name}.")
