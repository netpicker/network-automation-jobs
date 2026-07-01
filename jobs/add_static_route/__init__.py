from comfy.automate import job
from ipaddress import IPv4Network


@job(platform=['cisco_ios', 'cisco_xe'])
def add_static_route(device, destination_network, subnet_mask, next_hop):
    """Add a static route and verify it exists. Rollback: remove_static_route."""
    destination_network = str(destination_network).strip()
    subnet_mask = str(subnet_mask).strip()
    next_hop = str(next_hop).strip()

    try:
        IPv4Network((destination_network, subnet_mask), strict=True)
    except ValueError as exc:
        raise ValueError(
            f"Invalid destination network/subnet mask combination: "
            f"{destination_network} {subnet_mask}"
        ) from exc

    existing = device.cli(f"show ip route {destination_network}")
    if destination_network in existing and "directly connected" not in existing.lower():
        print(f"[SKIP] Static route to {destination_network} already exists on {device.name}.")
        return

    print(f"[PRE-CHECK] Static route to {destination_network} does not exist. Proceeding...")
    device.cli.send_config_set([f"ip route {destination_network} {subnet_mask} {next_hop}"])
    device.cli("write memory")
    print(f"[EXEC] Configuration saved on {device.name}.")

    verification = device.cli(f"show ip route {destination_network}")
    if destination_network not in verification:
        raise RuntimeError(f"Static route to {destination_network} could not be verified on {device.name}.")

    print(f"[SUCCESS] Static route to {destination_network} via {next_hop} created on {device.name}.")
