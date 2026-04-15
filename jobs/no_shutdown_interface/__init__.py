from comfy.automate import job

# =============================================================================
# Job:        no_shutdown_interface
# Platform:   Cisco IOS / IOS-XE
# Version:    1.0
# Description:
#   Enables an interface on Cisco IOS and IOS-XE devices by issuing the no shutdown command.
#   Performs a pre-check to confirm the interface is administratively down before enabling.
#   Verifies the interface is up after configuration.
#
# Variables:
#   interface_name (str)  : Name of the interface to enable  e.g. "GigabitEthernet0/1"
#
# Rollback:
#   To undo a successful run, use the shutdown_interface job.
# =============================================================================


@job(platform=['cisco_ios', 'cisco_xe'])
def no_shutdown_interface(device, interface_name):

    interface_name = str(interface_name).strip()

    # INPUT VALIDATION
    if not interface_name:
        print("[ERROR] interface_name is required. Please provide an interface name.")
        raise ValueError("interface_name cannot be empty.")

    # PRE-CHECK
    existing = device.cli(f"show ip interface {interface_name}")

    if "administratively down" not in existing.lower():
        print(f"[SKIP] Interface {interface_name} is already up on {device.name}. No changes made.")
        return

    print(f"[PRE-CHECK] Interface {interface_name} is down. Proceeding to enable...")

    # EXECUTION
    try:
        device.cli.send_config_set([
            f"interface {interface_name}",
            "no shutdown",
            "exit"
        ])
        print(f"[EXEC] Configuration sent to {device.name} to enable {interface_name}.")

    except Exception as e:
        print(f"[ERROR] Failed to configure {device.name}: {e}")
        raise

    # POST-CHECK
    verification = device.cli(f"show ip interface {interface_name}")

    if "up" in verification.lower():
        print(f"[SUCCESS] Interface {interface_name} enabled successfully on {device.name}.")
    else:
        print("[FAILED] Interface still down after configuration. Check device manually.")
        raise RuntimeError(f"Interface {interface_name} enabling could not be verified on {device.name}.")