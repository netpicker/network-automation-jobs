from comfy.automate import job

# =============================================================================
# Job:        set_interface_description
# Platform:   Cisco IOS / IOS-XE
# Version:    1.0
# Description:
#   Sets the description for a specified interface on Cisco IOS and IOS-XE devices.
#   Performs a pre-check to confirm the interface exists before setting the description.
#   Verifies the description is set after configuration.
#
# Variables:
#   interface_name (str)  : Name of the interface to set the description for  e.g. "GigabitEthernet0/1"
#   description      (str)  : Description to set for the interface            e.g. "Uplink to Core Switch"
#
# Rollback:
#   To undo a successful run, use the unset_interface_description job.
# =============================================================================


@job(platform=['cisco_ios', 'cisco_xe'])
def set_interface_description(device, interface_name, description):

    interface_name = str(interface_name).strip()
    description = str(description).strip()

    # INPUT VALIDATION
    if not interface_name:
        print("[ERROR] interface_name is required. Please provide an interface name.")
        raise ValueError("interface_name cannot be empty.")

    if not description:
        print("[ERROR] description is required. Please provide a description.")
        raise ValueError("description cannot be empty.")

    # PRE-CHECK
    existing = device.cli(f"show running-config interface {interface_name}")

    if "% Invalid" in existing:
        print(f"[SKIP] Interface {interface_name} does not exist on {device.name}. No changes made.")
        return

    print(f"[PRE-CHECK] Interface {interface_name} exists. Proceeding...")

    # EXECUTION
    try:
        device.cli.send_config_set([
            f"interface {interface_name}",
            f"description {description}"
        ])
        device.cli.send_command("write memory")
        print(f"[EXEC] Configuration sent to {device.name}.")

    except Exception as e:
        print(f"[ERROR] Failed to configure {device.name}: {e}")
        raise

    # POST-CHECK
    verification = device.cli(f"show running-config interface {interface_name}")

    if description in verification:
        print(f"[SUCCESS] Description for interface {interface_name} set to '{description}' on {device.name}.")
    else:
        print("[FAILED] Description not found after configuration. Check device manually.")
        raise RuntimeError(f"Setting description for interface {interface_name} could not be verified on {device.name}.")
