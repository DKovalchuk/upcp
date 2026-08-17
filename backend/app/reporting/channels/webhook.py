import hashlib
import hmac
import json
import time
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

from app.reporting.channels.base import BaseChannel

REQUIRED_FIELDS = ("url",)
MAX_RETRIES = 3
RETRY_DELAY = 2


class WebhookChannel(BaseChannel):
    """Webhook notification channel via HTTP POST."""

    def validate_config(self, config: dict[str, Any]) -> None:
        missing = [f for f in REQUIRED_FIELDS if f not in config]
        if missing:
            raise ValueError(f"Missing required webhook config: {', '.join(missing)}")
        url = config["url"]
        if not url.startswith(("http://", "https://")):
            raise ValueError("Webhook URL must start with http:// or https://")

    def send(self, config: dict[str, Any], title: str, message: str) -> None:
        self.validate_config(config)

        payload = json.dumps({"title": title, "message": message}).encode()
        secret = config.get("secret", "")

        headers = {"Content-Type": "application/json"}
        if secret:
            signature = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
            headers["X-Webhook-Signature"] = f"sha256={signature}"

        req = Request(config["url"], data=payload, headers=headers, method="POST")

        last_error: Exception | None = None
        for attempt in range(MAX_RETRIES):
            try:
                with urlopen(req, timeout=30) as resp:  # nosec B310 — webhook only uses HTTP(S)
                    if resp.status < 400:
                        return
                last_error = RuntimeError(f"HTTP {resp.status}")
            except (URLError, OSError) as exc:
                last_error = exc
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY * (attempt + 1))

        raise RuntimeError(f"Webhook delivery failed after {MAX_RETRIES} retries: {last_error}")
