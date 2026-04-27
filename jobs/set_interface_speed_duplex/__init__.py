from comfy.automate import job


@job(platform=['cisco_ios', 'cisco_xe'])
def set_interface_speed_duplex(device, interface, speed, duplex):
    """Set interface speed and duplex. Rollback: rollback_interface_speed_duplex."""
    interface = str(interface).strip()
    speed = str(speed).strip()
    duplex = str(duplex).strip().lower()

    if not interface:
        raise ValueError("interface cannot be empty.")
    if not speed.isdigit() or int(speed) not in [10, 100, 1000]:
        raise ValueError("speed must be 10, 100, or 1000.")
    if duplex not in ['full', 'half']:
        raise ValueError("duplex must be 'full' or 'half'.")

    current_config = device.cli(f"show running-config interface {interface}")
    if f"speed {speed}" in current_config and f"duplex {duplex}" in current_config:
        print(f"[SKIP] Interface {interface} already has speed {speed} and duplex {duplex}.")
        return

    print(f"[PRE-CHECK] Interface {interface} needs speed/duplex update. Proceeding...")
    device.cli.send_config_set([
        f"interface {interface}",
        f"speed {speed}",
        f"duplex {duplex}"
    ])
    device.cli("write memory")
    print(f"[EXEC] Configuration saved on {device.name}.")

    verification = device.cli(f"show running-config interface {interface}")
    if f"speed {speed}" not in verification or f"duplex {duplex}" not in verification:
        raise RuntimeError(f"Interface {interface} configuration could not be verified on {device.name}.")

    print(f"[SUCCESS] Interface {interface} set to speed {speed} and duplex {duplex} on {device.name}.")
