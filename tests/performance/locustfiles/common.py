"""Shared utilities for UPCP Locust performance tests.

Provides authentication helpers, data setup, pre-test validation,
and common request patterns following load-testing best practices.
"""

import json
import os
import random
import string

try:
    from locust import between
    from locust.contrib.fasthttp import FastHttpUser

    _LOCUST_AVAILABLE = True
except ImportError:
    _LOCUST_AVAILABLE = False

BASE_URL = os.getenv("LOCUST_HOST", "http://app:8080")


def check_target_health(host: str, timeout: int = 10) -> bool:
    """Verify target environment is healthy before starting tests."""
    import urllib.error
    import urllib.request

    url = f"{host}/health"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read())
            if data.get("status") == "ok":
                return True
            print(f"WARNING: Health check returned status={data.get('status')}")
            return False
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        print(f"WARNING: Health check failed: {e}")
        return False


def _random_suffix(length: int = 8) -> str:
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=length))


_BASE_CLASS = FastHttpUser if _LOCUST_AVAILABLE else object


class UPCPBaseUser(_BASE_CLASS):  # type: ignore[misc]
    """Base user with auth and common helpers for all UPCP scenarios.

    Provides:
    - Automatic auth (setup/login)
    - Pre-test health check
    - JSON response helpers with error tracking
    """

    abstract = True
    wait_time = between(0.5, 2.0) if _LOCUST_AVAILABLE else None
    _health_checked = False

    def on_start(self) -> None:
        """Authenticate on session start."""
        self.token: str | None = None
        self.project_id: str | None = None
        self._ensure_user()

        # Pre-test health check (once per Locust process)
        if not UPCPBaseUser._health_checked:
            UPCPBaseUser._health_checked = True
            if not check_target_health(self.environment.host or BASE_URL):
                print("WARNING: Target health check failed — tests may produce invalid results")

    def _ensure_user(self) -> None:
        """Create or login a test user and obtain a JWT token."""
        username = f"perf_user_{_random_suffix()}"
        password = "TestPassword123!"

        # Try setup first (first run creates admin)
        resp = self.client.post(
            "/auth/setup",
            json={"username": username, "password": password},
            name="/auth/setup",
        )
        if resp.status_code in (200, 201):
            self.token = resp.json().get("access_token")
            return

        # Login
        resp = self.client.post(
            "/auth/login",
            json={"username": username, "password": password},
            name="/auth/login",
        )
        if resp.status_code == 200:
            self.token = resp.json().get("access_token")

    def auth_headers(self) -> dict[str, str]:
        """Return Authorization headers."""
        if self.token:
            return {"Authorization": f"Bearer {self.token}"}
        return {}

    def ensure_project(self) -> str:
        """Create a project if none exists, return project_id."""
        if self.project_id:
            return self.project_id

        resp = self.client.post(
            "/api/v1/projects",
            json={
                "name": f"Load Test Project {_random_suffix()}",
                "description": "Auto-generated for performance testing",
            },
            headers=self.auth_headers(),
            name="/api/v1/projects [POST]",
        )
        if resp.status_code in (200, 201):
            self.project_id = resp.json()["id"]
            return self.project_id

        # Fallback: list and pick first
        resp = self.client.get(
            "/api/v1/projects",
            headers=self.auth_headers(),
            name="/api/v1/projects [GET]",
        )
        if resp.status_code == 200:
            projects = resp.json()
            if isinstance(projects, list) and projects:
                self.project_id = projects[0]["id"]
                return self.project_id

        return ""

    def api_get(self, path: str, **kwargs) -> dict | list | None:
        """GET with auth, return parsed JSON."""
        resp = self.client.get(path, headers=self.auth_headers(), name=f"GET {path}", **kwargs)
        if resp.status_code == 200:
            return resp.json()
        return None

    def api_post(self, path: str, json: dict | None = None, **kwargs) -> dict | None:
        """POST with auth, return parsed JSON."""
        resp = self.client.post(
            path, json=json, headers=self.auth_headers(), name=f"POST {path}", **kwargs
        )
        if resp.status_code in (200, 201):
            return resp.json()
        return None

    def api_patch(self, path: str, json: dict | None = None, **kwargs) -> dict | None:
        """PATCH with auth, return parsed JSON."""
        resp = self.client.patch(
            path, json=json, headers=self.auth_headers(), name=f"PATCH {path}", **kwargs
        )
        if resp.status_code == 200:
            return resp.json()
        return None
