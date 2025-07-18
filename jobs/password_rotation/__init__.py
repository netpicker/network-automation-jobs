from comfy.automate import job


@job(platform='cisco*')
def rotate_password_cisco(device, logger, username: str, new_password: str):
    """
    Rotates the password for a specified user on a Cisco IOS / NX-OS device.

    Args:
        device: The Netpicker device object.
        logger: The logger.Logger object.
        username (str): The username whose password needs to be rotated.
        new_password (str): The new secret password to set.
    """
    log_prefix = f"Device {device.ipaddress}, User '{username}':"
    logger.info(f"{log_prefix} Starting password rotation job.")

    config_commands = [
        f"username {username} secret {new_password}",
        "write memory"  # Or use "copy running-config startup-config"
    ]

    try:
        result = device.cli.send_config_set(config_commands)
    except Exception as e:
        logger.error(f"{log_prefix} Error during password rotation: {e}")
        raise
    logger.info(f"{log_prefix} Password rotation successful.")
    logger.debug(f"{log_prefix} Output: {result}")
    return result
