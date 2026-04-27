# Network Automation Jobs for Netpicker

This repository contains example automation jobs designed for use within [Netpicker](https://netpicker.io/), our all-in-one network automation platform.

> **Note:** Netpicker supports multiple ways to define automation jobs. From the Netpicker GUI you can create a **Simple Job** by specifying configuration commands or show commands to execute — no Python required. The Python-based approach in this repository is for more advanced use cases that need input validation, conditional logic, pre/post checks, or integration with external systems.

## Overview

Netpicker automation jobs are Python functions decorated with `@job` from `comfy.automate`. The examples in this repository show how to use Netpicker's device object and Netmiko-backed CLI access to run operational commands, make configuration changes, validate inputs, and verify the final device state.

Most jobs in this repository target Cisco IOS and IOS-XE devices with:

```python
@job(platform=['cisco_ios', 'cisco_xe'])
```

The `ensure_acl_bound` job uses a wildcard platform selector:

```python
@job(platform='cisco*')
```

The `password_rotation` job supports multiple platforms and branches its command logic by `device.platform`.

## Example Jobs

| Job | Platforms | Purpose |
| --- | --- | --- |
| `create_vlan` | `cisco_ios`, `cisco_xe` | Create a VLAN after checking that it does not already exist. |
| `delete_vlan` | `cisco_ios`, `cisco_xe` | Delete a VLAN after checking that it exists. |
| `list_vlans` | `cisco_ios`, `cisco_xe` | Display `show vlan brief` output. |
| `assign_vlan_to_access_port` | `cisco_ios`, `cisco_xe` | Assign an existing VLAN to an access interface. |
| `add_vlan_to_trunk` | `cisco_ios`, `cisco_xe` | Add a VLAN to a trunk interface. |
| `shutdown_interface` | `cisco_ios`, `cisco_xe` | Shut down an interface after confirming it is up. |
| `no_shutdown_interface` | `cisco_ios`, `cisco_xe` | Enable an administratively down interface. |
| `set_interface_description` | `cisco_ios`, `cisco_xe` | Set an interface description. |
| `set_interface_speed_duplex` | `cisco_ios`, `cisco_xe` | Configure interface speed and duplex. |
| `add_static_route` | `cisco_ios`, `cisco_xe` | Add a static route after checking for an existing route. |
| `ensure_acl_bound` | `cisco*` | Ensure an ACL is applied to an interface in the requested direction. |
| `rotate_password` | `cisco_ios`, `cisco_xe`, `cisco_nxos`, `arista_eos`, `cisco_wlc` | Rotate a local user password and notify a webhook. |

## Creating an Automation Job

Here is a minimal example:

```python
from comfy.automate import job


@job(platform=['cisco_ios', 'cisco_xe'])
def set_interface_description(device, interface_name, description):
    device.cli.send_config_set([f"interface {interface_name}", f"description {description}"])
    device.cli("write memory")
    print(f"Description set on {interface_name}")
```

A more complete example with input validation, pre-checks, and post-checks:

```python
from comfy.automate import job


@job(platform=['cisco_ios', 'cisco_xe'])
def create_vlan(device, vlan_id, vlan_name):
    """Create a VLAN and verify it exists. Rollback: delete_vlan."""
    vlan_id = str(vlan_id).strip()
    vlan_name = str(vlan_name).strip()

    if not vlan_name:
        raise ValueError("vlan_name cannot be empty.")

    if not vlan_id.isdigit() or not (1 <= int(vlan_id) <= 4094):
        raise ValueError("vlan_id must be a number between 1 and 4094.")

    existing = device.cli(f"show vlan id {vlan_id}")
    if "active" in existing.lower() or "suspended" in existing.lower():
        print(f"[SKIP] VLAN {vlan_id} already exists on {device.name}. No changes made.")
        return

    print(f"[PRE-CHECK] VLAN {vlan_id} does not exist. Proceeding...")

    device.cli.send_config_set([
        f"vlan {vlan_id}",
        f"name {vlan_name}",
    ])
    device.cli("write memory")
    print(f"[EXEC] Configuration saved on {device.name}.")

    verification = device.cli(f"show vlan id {vlan_id}")
    if "active" not in verification.lower() and "suspended" not in verification.lower():
        raise RuntimeError(f"VLAN {vlan_id} creation could not be verified on {device.name}.")

    print(f"[SUCCESS] VLAN {vlan_id} ('{vlan_name}') created successfully on {device.name}.")
```

## Common Job Pattern

The configuration examples follow a consistent structure:

1. Normalize and validate inputs.
2. Run a pre-check with a show command.
3. Skip safely if the desired state already exists or prerequisites are missing.
4. Apply configuration with `device.cli.send_config_set([...])`.
5. Save the configuration with `device.cli("write memory")`.
6. Run a post-check to verify the intended state.
7. Raise an exception when validation or verification fails so Netpicker records the job as failed.

This pattern keeps jobs predictable and makes repeated runs safer.

## The `@job` Decorator

The `platform` argument specifies which device platforms can run the job.

- Use a list for exact platform matches, such as `['cisco_ios', 'cisco_xe']`.
- Use a string for a single platform or wildcard selector, such as `'cisco*'`.
- Platform names should match Netmiko platform types used by Netpicker.

## Function Arguments

- `device`: The Netpicker device object. The examples use attributes such as `device.name`, `device.ipaddress`, and `device.platform`.
- Custom arguments: Any parameters after `device`, such as `vlan_id`, `interface_name`, `description`, or `next_hop`, are job inputs.

## Interacting With Devices

Netpicker exposes CLI access through `device.cli`.

### Show Commands

Use `device.cli("...")` for operational commands:

```python
output = device.cli("show vlan brief")
output = device.cli("show running-config interface GigabitEthernet0/1")
```

Use show commands for pre-checks, post-checks, and read-only jobs.

### Configuration Changes

Use `device.cli.send_config_set([...])` to send configuration commands:

```python
device.cli.send_config_set([
    "interface GigabitEthernet0/1",
    "description Uplink to Core Switch",
])
device.cli("write memory")
```

`send_config_set` automatically handles entering and exiting configuration mode. Save persistent changes with `device.cli("write memory")` after `send_config_set` completes.

## Logging and Output

- Use `print()` for execution messages. Netpicker captures this output in job execution details.
- Use clear status prefixes such as `[PRE-CHECK]`, `[EXEC]`, `[SUCCESS]`, `[SKIP]`, `[FAILED]`, and `[ERROR]` to make job output easy to scan.

## Return Values

Jobs may return values that Netpicker can use in workflows. If no return value is needed, rely on `print()` messages and exceptions to signal success or failure.

## Tests

The `tests/` directory contains YAML-based job test data. For example, `tests/ensure_acl_bound.yaml` defines mocked CLI responses and expected outcomes for `ensure_acl_bound`.

---

For more details on Netpicker, visit [netpicker.io](https://netpicker.io/).
For knowledge base articles on network automation jobs, see the [Netpicker Network Automation KB](https://netpicker.io/category/knowledge-base/network-automation/).
For in-depth Netmiko information, refer to the [official Netmiko documentation](https://ktbyers.github.io/netmiko/docs/netmiko/).
