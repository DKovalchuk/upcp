"""Minimal HS256 JWT minting for security probes — stdlib only (TASK-0142).

Lets the suite build correctly-signed access tokens with crafted claims
(expired, wrong type, unknown subject) without adding a PyJWT dependency
to the test host. The signing secret is the test-stack secret
(UPCP_SECRET_KEY, default from docker-compose.test.yml / .env.test).
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
from datetime import UTC, datetime, timedelta


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def mint_access(
    sub: str,
    *,
    secret: str,
    exp_min: int = 5,
    iat_min: int = -1,
    typ: str = "access",
) -> str:
    """Mint an HS256 JWT for *sub* with explicit claim offsets (minutes).

    ``iat`` is always placed in the past so no library immaturity check can
    trip; ``exp_min`` goes negative to forge an expired-but-validly-signed
    token; ``typ`` forges the app-level ``type`` claim (access/refresh).
    """
    now = datetime.now(UTC)
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": sub,
        "type": typ,
        "iat": int((now + timedelta(minutes=iat_min)).timestamp()),
        "exp": int((now + timedelta(minutes=exp_min)).timestamp()),
    }
    head = _b64url(json.dumps(header, separators=(",", ":")).encode())
    body = _b64url(json.dumps(payload, separators=(",", ":")).encode())
    sig = hmac.new(secret.encode(), f"{head}.{body}".encode(), hashlib.sha256).digest()
    return f"{head}.{body}.{_b64url(sig)}"
