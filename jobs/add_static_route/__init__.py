from comfy.automate import job

# =============================================================================
# Job:        add_static_route
# Platform:   Cisco IOS / IOS-XE
# Version:    1.1
# Description:
#   Adds a static route on Cisco IOS and IOS-XE devices.
#   Performs a pre-check to avoid duplicate routes.
#   Verifies the route exists after configuration.
#
# Variables:
#   destination_network (str)  : Destination network address       e.g. "192.168.1.0"
#   subnet_mask         (str)  : Subnet mask in dotted notation    e.g. "255.255.255.0"
#   next_hop            (str)  : Next hop IP address               e.g. "10.0.0.1"
#
# Rollback:
#   To undo a successful run, use the remove_static_route job.
# =============================================================================


@job(platform=['cisco_ios', 'cisco_xe'])
def add_static_route(device, destination_network, subnet_mask, next_hop):

    destination_network = str(destination_network).strip()
    subnet_mask = str(subnet_mask).strip()
    next_hop = str(next_hop).strip()

    # INPUT VALIDATION
    if not destination_network:
        print("[ERROR] destination_network is required. Please provide a destination network.")
        raise ValueError("destination_network cannot be empty.")

    if not subnet_mask:
        print("[ERROR] subnet_mask is required. Please provide a subnet mask.")
        raise ValueError("subnet_mask cannot be empty.")

    if not next_hop:
        print("[ERROR] next_hop is required. Please provide a next hop IP address.")
        raise ValueError("next_hop cannot be empty.")

    # PRE-CHECK
    existing = device.cli(f"show ip route {destination_network}")

    if destination_network in existing and "directly connected" not in existing.lower():
        print(f"[SKIP] Static route to {destination_network} already exists on {device.name}. No changes made.")
        return

    print(f"[PRE-CHECK] Static route to {destination_network} does not exist. Proceeding...")

    # EXECUTION
    try:
        device.cli.send_config_set([
            f"ip route {destination_network} {subnet_mask} {next_hop}"
        ])
        device.cli.send_command("write memory")
        print(f"[EXEC] Configuration sent to {device.name}.")

    except Exception as e:
        print(f"[ERROR] Failed to configure {device.name}: {e}")
        raise

    # POST-CHECK
    verification = device.cli(f"show ip route {destination_network}")

    if destination_network in verification:
        print(f"[SUCCESS] Static route to {destination_network} {subnet_mask} via {next_hop} created successfully on {device.name}.")
    else:
        print("[FAILED] Static route not found after configuration. Check device manually.")
        raise RuntimeError(f"Static route to {destination_network} creation could not be verified on {device.name}.")
