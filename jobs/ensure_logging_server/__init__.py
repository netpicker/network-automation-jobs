import re
from comfy.automate import job


@job(platform='cisco*')
def ensure_logging_server(device, logger, logging_host: str, severity: str = "informational"):
    """
    Verifies and configures a remote syslog server on Cisco devices if not already configured.

    Args:
        device: The Netpicker device object.
        logger: The logging.Logger object.
        logging_host (str): The IP or hostname of the syslog server.
        severity (str): Logging severity (default: informational).
    """
    log_prefix = f"Device {device.ipaddress}:"
    logger.info(f"{log_prefix} Ensuring logging server {logging_host} is configured...")

    try:
        # Step 1: Check existing config
        config = device.cli.send_command("show running-config | include logging")
        logger.debug(f"{log_prefix} Existing logging config:\n{config}")

        # Look for exact match (with space or end of line after the IP)
        already_configured = any(
            re.search(rf'logging (host|server) {re.escape(logging_host)}(\s|$)', line)
            for line in config.splitlines()
        )

        if already_configured:
            logger.info(f"{log_prefix} Logging server {logging_host} already configured. No action needed.")
            return {"status": "exists", "logging_host": logging_host}

        # Step 2: If not configured, add it
        if device.platform == "cisco_nxos":
            commit = "copy running-config startup-config"
        else:
            commit = "write memory"

        config_commands = [
            f"logging host {logging_host} {severity}",
            commit
        ]

        result = device.cli.send_config_set(config_commands)
        logger.info(f"{log_prefix} Logging server {logging_host} configured successfully.")
        return {"status": "configured", "logging_host": logging_host, "output": result}

    except Exception as e:
        logger.error(f"{log_prefix} Failed to verify/configure logging server: {e}")
        raise
