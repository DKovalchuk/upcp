"""Shared helpers for UPCP seed scripts.

Provides env-overridable config, login with auto-refresh, and a rate-limited
API wrapper. The app enforces 100 req/min per IP on /api/v1 (default route),
5/min on login, 10/min on refresh — see app/shared/rate_limit.py. The wrapper
paces requests under the default limit and transparently refreshes an
expired access token (lifetime 15 min — long seed runs outlive it).

Env: SEED_BASE, SEED_EMAIL, SEED_PASSWORD.
"""

from __future__ import annotations

import os
import time
from collections import deque

import requests

BASE = os.getenv("SEED_BASE", "http://127.0.0.1:38080")
SEED_EMAIL = os.getenv("SEED_EMAIL", "admin@example.com")
SEED_PASSWORD = os.getenv("SEED_PASSWORD", "admin123")

# Stay safely under the app's 100 req/min default bucket.
_RATE_LIMIT = 90
_RATE_WINDOW = 60.0

# Seed scripts run as `python scripts/<name>.py` → sys.path[0] is scripts/,
# so sibling imports work regardless of CWD.
_RATE_TS: deque[float] = deque()


def _pace() -> None:
    """Sleep as needed to keep request rate under the app's limit."""
    now = time.monotonic()
    while _RATE_TS and now - _RATE_TS[0] >= _RATE_WINDOW:
        _RATE_TS.popleft()
    if len(_RATE_TS) >= _RATE_LIMIT:
        time.sleep(_RATE_WINDOW - (now - _RATE_TS[0]) + 0.05)
        now = time.monotonic()
        while _RATE_TS and now - _RATE_TS[0] >= _RATE_WINDOW:
            _RATE_TS.popleft()
    _RATE_TS.append(time.monotonic())


class Session:
    """Authenticated API client: pacing, 429 retry, transparent token refresh."""

    def __init__(self) -> None:
        self._user: str | None = None
        self._password: str | None = None
        self._access: str = ""
        self._refresh: str = ""
        self.login(SEED_EMAIL, SEED_PASSWORD)

    def login(self, email: str, password: str) -> None:
        self._user, self._password = email, password
        r = requests.post(f"{BASE}/auth/login", json={"email": email, "password": password})
        r.raise_for_status()
        data = r.json()
        self._access, self._refresh = data["access_token"], data["refresh_token"]

    def _try_refresh(self) -> bool:
        r = requests.post(f"{BASE}/auth/refresh", json={"refresh_token": self._refresh})
        if r.status_code != 200:
            return False
        data = r.json()
        self._access, self._refresh = data["access_token"], data["refresh_token"]
        return True

    @property
    def user_id(self) -> str:
        return str(self.request("GET", "/auth/me")["id"])

    def _headers(self, agent_token: str | None) -> dict[str, str]:
        if agent_token:
            return {"X-Agent-Token": agent_token}
        return {"Authorization": f"Bearer {self._access}"}

    def request(
        self,
        method: str,
        path: str,
        *,
        agent_token: str | None = None,
        expect: tuple[int, ...] = (200, 201, 204),
        retries: int = 3,
        **kw: object,
    ) -> dict[str, object] | None:
        """Perform a paced request. Returns parsed JSON, or None + WARN print
        when the final status is outside *expect* (script-friendly: a single
        unexpected response never aborts the whole seed run)."""
        url = f"{BASE}{path}"
        for attempt in range(retries):
            _pace()
            r = requests.request(  # noqa: S113 — timeout handled by pacing loop
                method, url, headers=self._headers(agent_token), **kw  # type: ignore[arg-type]
            )
            if (r.status_code == 401 and agent_token is None
                    and attempt + 1 < retries and self._try_refresh()):
                continue
            if r.status_code == 429 and attempt + 1 < retries:
                wait = float(r.headers.get("Retry-After", 60))
                print(f"  … 429 {method} {path}, waiting {wait:.0f}s")
                time.sleep(wait + 1)
                continue
            break
        if r.status_code not in expect:
            print(f"  WARN {method.upper()} {path} → {r.status_code}: {r.text[:160]}")
            return None
        if r.status_code == 204 or not r.content:
            return {}
        return r.json()  # type: ignore[no-any-return]

    # Convenience wrappers -------------------------------------------------

    def get(self, path: str, **kw: object) -> dict[str, object] | None:
        return self.request("GET", path, **kw)

    def post(self, path: str, data: object | None = None, **kw: object) -> dict[str, object] | None:
        return self.request("POST", path, json=data, **kw)

    def patch(self, path: str, data: object, **kw: object) -> dict[str, object] | None:
        return self.request("PATCH", path, json=data, **kw)


def section(title: str) -> None:
    print(f"\n── {title} " + "─" * max(0, 58 - len(title)))
