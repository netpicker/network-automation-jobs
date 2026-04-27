from comfy.automate import job


@job(platform='cisco*')
def ensure_acl_bound(device, interface: str, acl_name: str, direction: str = "in"):
    """Apply an ACL to an interface if it is not already bound."""
    log_prefix = f"Device {device.ipaddress}, Interface {interface}:"
    acl_line = f"ip access-group {acl_name} {direction}"

    config = device.cli(f"show running-config interface {interface}")
    if acl_line in config:
        print(f"{log_prefix} ACL already bound. No changes needed.")
        return {"status": "exists", "interface": interface, "acl": acl_name, "direction": direction}

    print(f"{log_prefix} Binding ACL '{acl_name}' {direction}.")
    result = device.cli.send_config_set([
        f"interface {interface}",
        acl_line
    ])

    device.cli("write memory")
    print(f"{log_prefix} ACL bound successfully.")
    return {
        "status": "bound",
        "interface": interface,
        "acl": acl_name,
        "direction": direction,
        "output": result
    }
