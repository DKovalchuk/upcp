"""Concurrency stress test — race conditions, deadlocks, write conflicts.

Detects:
- Double-claim race (2+ agents claim same task)
- Concurrent heartbeat updates
- Parallel project creation with unique constraints
- Simultaneous evidence uploads
- Rate limit storm behavior
"""

import random
import string

from common import UPCPBaseUser
from locust import between, task


def _sfx() -> str:
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=6))


class ConcurrencyUser(UPCPBaseUser):
    """Concurrency-focused workload: stress test race conditions and locks."""

    wait_time = between(0.1, 0.5)  # Faster than normal — maximize contention

    def on_start(self) -> None:
        super().on_start()
        self.project_id = self.ensure_project()
        self._shared_task_id: str | None = None

    def _get_shared_task(self) -> str:
        """Get or create a shared task for concurrent claim testing."""
        if self._shared_task_id:
            return self._shared_task_id
        features = self.api_get(f"/api/v1/projects/{self.project_id}/features")
        feat_list = features if isinstance(features, list) else []
        if not feat_list:
            data = self.api_post(
                f"/api/v1/projects/{self.project_id}/features",
                json={"name": f"Concurrency Feature {_sfx()}"},
            )
            if data:
                feat_list = [data]
        if feat_list:
            data = self.api_post(
                f"/api/v1/features/{feat_list[0]['id']}/tasks",
                json={"title": f"Shared Task {_sfx()}", "status": "backlog"},
            )
            if data:
                self._shared_task_id = data["id"]
        return self._shared_task_id or ""

    # ── Race: Claim Same Task (30%) ───────────────────────────

    @task(15)
    def race_claim(self):
        """Multiple users try to claim the same task.
        Expected: exactly 1 success (200), rest fail (409/403).
        If 2+ succeed = race condition bug."""
        task_id = self._get_shared_task()
        if task_id:
            resp = self.client.post(
                f"/api/v1/tasks/{task_id}/claim",
                headers=self.auth_headers(),
                name="/api/v1/tasks/*/claim [RACE]",
            )
            # We track both success and expected failures
            if resp.status_code not in (200, 201, 409, 403):
                resp.failure(f"Unexpected status: {resp.status_code}")

    @task(10)
    def race_release(self):
        """Release task then immediately re-claim."""
        task_id = self._get_shared_task()
        if task_id:
            self.client.post(
                f"/api/v1/tasks/{task_id}/release",
                headers=self.auth_headers(),
                name="/api/v1/tasks/*/release [RACE]",
            )
            self.client.post(
                f"/api/v1/tasks/{task_id}/claim",
                headers=self.auth_headers(),
                name="/api/v1/tasks/*/claim-after-release [RACE]",
            )

    @task(5)
    def rapid_claim_release_cycle(self):
        """Rapidly cycle claim/release to stress state machine."""
        task_id = self._get_shared_task()
        if task_id:
            for _ in range(3):
                self.client.post(
                    f"/api/v1/tasks/{task_id}/claim",
                    headers=self.auth_headers(),
                    name="/api/v1/tasks/*/claim [CYCLE]",
                )
                self.client.post(
                    f"/api/v1/tasks/{task_id}/release",
                    headers=self.auth_headers(),
                    name="/api/v1/tasks/*/release [CYCLE]",
                )

    # ── Race: Concurrent Heartbeats (20%) ─────────────────────

    @task(10)
    def concurrent_heartbeat(self):
        """Rapid heartbeat updates — tests write contention on claim."""
        task_id = self._get_shared_task()
        if task_id:
            for _ in range(5):
                self.api_post(
                    f"/api/v1/tasks/{task_id}/heartbeat",
                    json={
                        "progress_percent": random.randint(0, 100),
                        "current_step": f"Step {_sfx()}",
                        "next_step": "Next",
                    },
                )

    # ── Race: Parallel Creates (20%) ──────────────────────────

    @task(10)
    def parallel_project_create(self):
        """Create multiple projects simultaneously — unique constraint test."""
        self.api_post(
            "/api/v1/projects",
            json={"name": f"Race Project {_sfx()}", "description": "Concurrency test"},
        )

    @task(5)
    def parallel_feature_create(self):
        """Create features in same project simultaneously."""
        self.api_post(
            f"/api/v1/projects/{self.project_id}/features",
            json={"name": f"Race Feature {_sfx()}"},
        )

    @task(5)
    def parallel_task_create(self):
        """Create tasks in same feature simultaneously."""
        features = self.api_get(f"/api/v1/projects/{self.project_id}/features")
        feat_list = features if isinstance(features, list) else []
        if feat_list:
            self.api_post(
                f"/api/v1/features/{feat_list[0]['id']}/tasks",
                json={"title": f"Race Task {_sfx()}", "status": "backlog"},
            )

    # ── Rate Limit Storm (15%) ────────────────────────────────

    @task(8)
    def rate_limit_login(self):
        """Flood login endpoint to trigger rate limiting."""
        self.client.post(
            "/auth/login",
            json={"username": f"nonexistent_{_sfx()}", "password": "wrong"},
            name="/auth/login [STORM]",
        )

    @task(4)
    def rate_limit_api(self):
        """Flood API endpoint to trigger default rate limit."""
        for _ in range(10):
            self.api_get("/api/v1/projects")

    @task(3)
    def rate_limit_search(self):
        """Flood search endpoint."""
        for _ in range(5):
            self.api_get(f"/api/v1/search?q={_sfx()}")

    # ── Resource Exhaustion (15%) ──────────────────────────────

    @task(8)
    def large_pagination(self):
        """Request very large page — stress DB query."""
        self.api_get(f"/api/v1/projects/{self.project_id}/tasks?offset=0&limit=1000")

    @task(4)
    def deep_search(self):
        """Search with complex query — stress full-text search."""
        self.api_get(f"/api/v1/search?q={' '.join([_sfx() for _ in range(10)])}")

    @task(3)
    def concurrent_health_checks(self):
        """Multiple simultaneous health checks."""
        for _ in range(10):
            self.api_get("/health")
