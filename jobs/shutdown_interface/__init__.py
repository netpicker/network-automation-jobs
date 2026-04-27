from comfy.automate import job

# =============================================================================
# Job:        shutdown_interface
# Platform:   Cisco IOS / IOS-XE
# Version:    1.0
# Description:
#   Shuts down a specified interface on Cisco IOS and IOS-XE devices.
#   Performs a pre-check to confirm the interface is up before shutdown.
#   Verifies the interface is down after configuration.
#
# Variables:
#   interface_name (str)  : Name of the interface to shut down  e.g. "GigabitEthernet0/1"
#
# Rollback:
#   To undo a successful run, use the no_shutdown_interface job.
# =============================================================================


@job(platform=['cisco_ios', 'cisco_xe'])
def shutdown_interface(device, interface_name):

    interface_name = str(interface_name).strip()

    # INPUT VALIDATION
    if not interface_name:
        print("[ERROR] interface_name is required. Please provide an interface name.")
        raise ValueError("interface_name cannot be empty.")

    # PRE-CHECK
    existing = device.cli(f"show ip interface brief | include {interface_name}")

    if "up" not in existing.lower():
        print(f"[SKIP] Interface {interface_name} is not up on {device.name}. No changes made.")
        return

    print(f"[PRE-CHECK] Interface {interface_name} is up. Proceeding to shut down...")

    # EXECUTION
    try:
        device.cli.send_config_set([
            f"interface {interface_name}",
            "shutdown"
        ])
        device.cli.send_command("write memory")
        print(f"[EXEC] Shutdown command sent to {device.name} for interface {interface_name}.")

    except Exception as e:
        print(f"[ERROR] Failed to configure {device.name}: {e}")
        raise

    # POST-CHECK
    verification = device.cli(f"show ip interface brief | include {interface_name}")

    if "administratively down" in verification.lower():
        print(f"[SUCCESS] Interface {interface_name} shut down successfully on {device.name}.")
    else:
        print("[FAILED] Interface still up after shutdown command. Check device manually.")
        raise RuntimeError(f"Interface {interface_name} shutdown could not be verified on {device.name}.")
