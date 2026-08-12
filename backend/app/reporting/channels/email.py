import smtplib
from email.mime.text import MIMEText
from typing import Any

from app.reporting.channels.base import BaseChannel

REQUIRED_FIELDS = ("smtp_host", "smtp_port", "from_address", "to_address")


class EmailChannel(BaseChannel):
    """Email notification channel via SMTP."""

    def validate_config(self, config: dict[str, Any]) -> None:
        missing = [f for f in REQUIRED_FIELDS if f not in config]
        if missing:
            raise ValueError(f"Missing required email config: {', '.join(missing)}")
        if not isinstance(config["smtp_port"], int):
            raise ValueError("smtp_port must be an integer")

    def send(self, config: dict[str, Any], title: str, message: str) -> None:
        self.validate_config(config)

        msg = MIMEText(message)
        msg["Subject"] = title
        msg["From"] = config["from_address"]
        msg["To"] = config["to_address"]

        host = config["smtp_host"]
        port = config["smtp_port"]
        username = config.get("smtp_username")
        password = config.get("smtp_password")

        with smtplib.SMTP(host, port, timeout=30) as server:
            server.ehlo()
            if username and password:
                server.starttls()
                server.login(username, password)
            server.send_message(msg)
