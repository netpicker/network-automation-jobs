from comfy.automate import job

@job(platform=["cisco_ios","cisco_xe","arista_eos"])
def run_multiple_show_commands(device, cmds: str):
    """
    Executes multiple show commands on the device.
    'cmds' should be a comma-separated string like: "show clock, show version"
    """

    # Validate input
    if not cmds.strip():
        print("[ERROR] No CLI commands provided. Please specify 'cmds' as a comma-separated string.")
        raise RuntimeError("No commands provided to 'cmds' argument.")

    command_list = [cmd.strip() for cmd in cmds.split(",") if cmd.strip()]
    if not command_list:
        print("[ERROR] 'cmds' contains only empty values after splitting.")
        raise RuntimeError("Parsed command list is empty — check formatting.")

    error_indicators = ["^", "Invalid", "Error", "incomplete command", "Ambiguous"]

    for cmd in command_list:
        output = device.cli(cmd)
        print(f"\n--- Output of '{cmd}' on {device.name} ({device.ipaddress}) ---")
        print(output)

        for err in error_indicators:
            if err.lower() in output.lower():
                print(f"[ERROR] Command '{cmd}' failed: found '{err}' in output")
                raise RuntimeError(f"Command '{cmd}' failed on {device.name}: '{err}' detected in output")
