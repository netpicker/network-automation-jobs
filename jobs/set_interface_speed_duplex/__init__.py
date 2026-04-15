from comfy.automate import job

# =============================================================================
# Job:        set_interface_speed_duplex
# Platform:   Cisco IOS / IOS-XE
# Version:    1.0
# Description:
#   Sets the speed and duplex mode of an interface on Cisco IOS and IOS-XE devices.
#   Performs a pre-check to verify current settings before applying changes.
#   Verifies the settings after configuration.
#
# Variables:
#   interface  (str)  : Interface to configure      e.g. 'GigabitEthernet0/1'
#   speed      (int)  : Speed to set                e.g. 1000
#   duplex     (str)  : Duplex mode to set          e.g. 'full'
#
# Rollback:
#   To undo a successful run, use the rollback_interface_speed_duplex job.
# =============================================================================


@job(platform=['cisco_ios', 'cisco_xe'])
def set_interface_speed_duplex(device, interface, speed, duplex):

    interface = str(interface).strip()
    speed = str(speed).strip()
    duplex = str(duplex).strip()

    # INPUT VALIDATION
    if not interface:
        print("[ERROR] interface is required. Please provide an interface name.")
        raise ValueError("interface cannot be empty.")

    if not speed.isdigit() or int(speed) not in [10, 100, 1000]:
        print(f"[ERROR] speed '{speed}' is invalid. Must be 10, 100, or 1000.")
        raise ValueError(f"Invalid speed: {speed}")

    if duplex not in ['full', 'half']:
        print(f"[ERROR] duplex '{duplex}' is invalid. Must be 'full' or 'half'.")
        raise ValueError(f"Invalid duplex: {duplex}")

    # PRE-CHECK
    current_settings = device.cli(f"show running-config interface {interface}")

    if f"speed {speed}" in current_settings and f"duplex {duplex}" in current_settings:
        print(f"[SKIP] Interface {interface} already set to speed {speed} and duplex {duplex}. No changes made.")
        return

    print(f"[PRE-CHECK] Current settings for {interface} do not match desired configuration. Proceeding...")

    # EXECUTION
    try:
        device.cli.send_config_set([
            f"interface {interface}",
            f"speed {speed}",
            f"duplex {duplex}",
            "exit"
        ])
        print(f"[EXEC] Configuration sent to {device.name} for {interface}.")

    except Exception as e:
        print(f"[ERROR] Failed to configure {device.name}: {e}")
        raise

    # POST-CHECK
    verification = device.cli(f"show running-config interface {interface}")

    if f"speed {speed}" in verification and f"duplex {duplex}" in verification:
        print(f"[SUCCESS] Interface {interface} set to speed {speed} and duplex {duplex} successfully on {device.name}.")
    else:
        print("[FAILED] Interface settings not found after configuration. Check device manually.")
        raise RuntimeError(f"Interface {interface} configuration could not be verified on {device.name}.")