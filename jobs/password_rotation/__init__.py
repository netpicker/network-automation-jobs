import requests
from comfy.automate import job


@job(platform=['cisco_ios', 'cisco_xe', 'cisco_nxos', 'arista_eos', "cisco_wlc"])
def rotate_password(device, local_user: str, local_passwd: str):
    """Rotate a local password and notify a webhook."""
    webhook_url = ""

    try:
        if not local_user or not str(local_user).strip():
            raise RuntimeError("Missing required input: local_user")
        if not local_passwd or not str(local_passwd).strip():
            raise RuntimeError("Missing required input: local_passwd")

        if device.platform == "cisco_nxos":
            device.cli.send_config_set([
                f"username {local_user} password {local_passwd} role network-admin",
                f"username {local_user} role priv-15",
            ])
            device.cli("write memory")
        elif device.platform in ["cisco_xe", "cisco_ios"]:
            device.cli.send_config_set([
                f"username {local_user} privilege 15 secret {local_passwd}",
                "no enable secret"
            ])
            device.cli("write memory")
        elif device.platform == "arista_eos":
            device.cli.send_config_set([
                f"username {local_user} privilege 15 role network-admin secret {local_passwd}"
            ])
            device.cli("write memory")
        elif device.platform == "cisco_wlc":
            device.cli(f"config mgmtuser password {local_user} {local_passwd}")
            device.cli("save config", expect_string="y/n")
            device.cli("y", "aved!")
        else:
            raise RuntimeError(f"Unsupported vendor: {device.platform} on {device.name}")

        requests.post(webhook_url, json={
            "attachments": [{
                "color": "#2EB67D",
                "title": "Password Rotation Successful",
                "text": f"Device: *{device.name}*\nUser: *{local_user}*"
            }]
        }, timeout=10)
    except Exception as e:
        requests.post(webhook_url, json={
            "attachments": [{
                "color": "#E01E5A",
                "title": "Password Rotation Failed",
                "text": f"Device: *{device.name}*\nError: `{str(e)}`"
            }]
        }, timeout=10)
        raise
