import re

from comfy.automate import job


def get_boot_statements(output):
    """Return existing 'boot system' statements in their configured order."""
    return [
        line.strip()
        for line in str(output).splitlines()
        if line.strip().startswith("boot system ")
    ]


def schedule_reload(device, reload_minutes):
    """
    Schedule an IOS/IOS-XE reload and handle the interactive confirmation.
    """
    output = str(
        device.cli.send_command_timing(
            f"reload in {reload_minutes}"
        )
    )

    # This should normally not appear because write memory is executed first.
    if "Save?" in output or "[yes/no]" in output:
        response = str(device.cli.send_command_timing("yes"))
        output += "\n" + response

    if "[confirm]" in output or "Proceed with reload" in output:
        response = str(device.cli.send_command_timing(""))
        output += "\n" + response

    return output


@job(platform=[
    "cisco_ios",
    "cisco_xe",
])
def cisco_ios_image_upgrade(
    device,
    file_tag: str,
    reload_minutes: int = 30,
):
    reload_minutes = int(reload_minutes)
    if reload_minutes < 1:
        raise ValueError("reload_minutes must be at least 1")

    uploaded_file = device.file(file_tag)
    file_name = uploaded_file.filename

    print(f"Selected tag: {file_tag}")
    print(f"Resolved filename: {file_name}")
    print(f"Expected MD5: {uploaded_file.md5}")
    print(f"Expected SHA256: {uploaded_file.sha256}")

    # ------------------------------------------------------------
    # 1. Check the file before transfer
    # ------------------------------------------------------------
    print("\nFile status before transfer:")
    before_output = str(device.cli(f"dir {file_name}"))
    print(before_output)

    # ------------------------------------------------------------
    # 2. Transfer and verify the file
    #
    # write_file() performs the transfer and the configured checksum
    # verification. The boot configuration is changed only when it
    # returns successfully.
    # ------------------------------------------------------------
    transfer_result = device.write_file(
        file_tag,
        file_name,
        timeout=3 * 60 * 60 + 10,
    )

    print(f"\nwrite_file result: {transfer_result}")

    if not transfer_result:
        raise RuntimeError(
            "File transfer or checksum verification failed. "
            "Boot configuration will not be changed."
        )

    # ------------------------------------------------------------
    # 3. Confirm the file exists after transfer
    # ------------------------------------------------------------
    print("\nFile status after transfer:")
    after_output = str(device.cli(f"dir {file_name}"))
    print(after_output)

    error_text = after_output.lower()

    if (
        file_name not in after_output
        or "no such file" in error_text
        or "error opening" in error_text
    ):
        raise RuntimeError(
            f"Transferred file {file_name} was not found. "
            "Boot configuration will not be changed."
        )

    # Derive flash0:, flash:, bootflash:, etc. from:
    # Directory of flash0:/filename.bin
    filesystem_match = re.search(
        r"Directory of\s+([^\s/]+:)/",
        after_output,
        flags=re.IGNORECASE,
    )

    if filesystem_match is None:
        raise RuntimeError(
            "Could not determine the destination filesystem from "
            "the post-transfer directory output."
        )

    filesystem = filesystem_match.group(1)
    boot_path = f"{filesystem}/{file_name}"
    new_boot_statement = f"boot system {boot_path}"

    print(f"\nDetected filesystem: {filesystem}")
    print(f"New boot image: {boot_path}")

    # ------------------------------------------------------------
    # 4. Capture the current boot configuration
    # ------------------------------------------------------------
    current_boot_output = str(
        device.cli(
            "show running-config | include ^boot system"
        )
    )

    current_boot_statements = get_boot_statements(
        current_boot_output
    )

    print("\nExisting boot statements:")

    if current_boot_statements:
        for statement in current_boot_statements:
            print(f"  {statement}")
    else:
        print("  No existing boot system statements found")

    # Preserve the existing images as fallback entries, but place the
    # newly transferred image first in the boot order.
    fallback_statements = [
        statement
        for statement in current_boot_statements
        if file_name not in statement
    ]

    config_commands = [
        "no boot system",
        new_boot_statement,
        *fallback_statements,
    ]

    print("\nBoot configuration to apply:")
    for command in config_commands:
        print(f"  {command}")

    # ------------------------------------------------------------
    # 5. Change boot order
    # ------------------------------------------------------------
    config_output = device.cli.send_config_set(
        config_commands
    )

    print("\nConfiguration response:")
    print(config_output)

    # ------------------------------------------------------------
    # 6. Validate running configuration
    # ------------------------------------------------------------
    running_boot_output = str(
        device.cli(
            "show running-config | include ^boot system"
        )
    )

    running_boot_statements = get_boot_statements(
        running_boot_output
    )

    print("\nRunning-config boot order:")
    print(running_boot_output)

    if (
        not running_boot_statements
        or file_name not in running_boot_statements[0]
    ):
        raise RuntimeError(
            "The new image is not the first boot system statement. "
            "The configuration will not be saved and reload will not "
            "be scheduled."
        )

    # ------------------------------------------------------------
    # 7. Save the configuration
    # ------------------------------------------------------------
    print("\nSaving configuration:")
    save_output = str(device.cli("write memory"))
    print(save_output)

    # ------------------------------------------------------------
    # 8. Validate startup configuration
    # ------------------------------------------------------------
    startup_boot_output = str(
        device.cli(
            "show startup-config | include ^boot system"
        )
    )

    startup_boot_statements = get_boot_statements(
        startup_boot_output
    )

    print("\nStartup-config boot order:")
    print(startup_boot_output)

    if (
        not startup_boot_statements
        or file_name not in startup_boot_statements[0]
    ):
        raise RuntimeError(
            "The new boot image was not confirmed in startup-config. "
            "Reload will not be scheduled."
        )

    # ------------------------------------------------------------
    # 9. Schedule the reload
    # ------------------------------------------------------------
    print(
        f"\nScheduling device reload in {reload_minutes} minutes:"
    )

    reload_output = schedule_reload(
        device,
        reload_minutes,
    )

    print(reload_output)

    # ------------------------------------------------------------
    # 10. Display scheduled reload status
    # ------------------------------------------------------------
    reload_status = str(device.cli("show reload"))

    print("\nScheduled reload status:")
    print(reload_status)

    if "no reload is scheduled" in reload_status.lower():
        raise RuntimeError(
            "The reload command was issued, but no reload is scheduled."
        )

    print(
        f"\nUpgrade preparation completed successfully. "
        f"Reload is scheduled in {reload_minutes} minutes."
    )
