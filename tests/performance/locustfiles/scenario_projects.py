"""Project CRUD operations — stress test for project lifecycle.

Tests: list, get, create, update, delete, components, modules.
Weight: 30% reads, 10% writes (realistic read-heavy pattern).
"""

import random
import string

from common import UPCPBaseUser
from locust import between, task


def _sfx() -> str:
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=6))


class ProjectCRUDUser(UPCPBaseUser):
    """Project-focused workload: CRUD + structure operations."""

    wait_time = between(0.2, 1.0)

    def on_start(self) -> None:
        super().on_start()
        self.project_id = self.ensure_project()
        self._component_ids: list[str] = []

    def _ensure_components(self) -> list[str]:
        if self._component_ids:
            return self._component_ids
        for _ in range(3):
            data = self.api_post(
                f"/api/v1/projects/{self.project_id}/components",
                json={"name": f"Comp {_sfx()}", "description": "Load test"},
            )
            if data:
                self._component_ids.append(data["id"])
        return self._component_ids

    # ── Reads (30%) ───────────────────────────────────────────

    @task(10)
    def list_projects(self):
        self.api_get("/api/v1/projects")

    @task(8)
    def get_project(self):
        self.api_get(f"/api/v1/projects/{self.project_id}")

    @task(5)
    def list_components(self):
        self.api_get(f"/api/v1/projects/{self.project_id}/components")

    @task(4)
    def list_modules(self):
        comps = self._ensure_components()
        if comps:
            self.api_get(f"/api/v1/components/{random.choice(comps)}/modules")

    @task(3)
    def project_health(self):
        self.api_get(f"/api/v1/projects/{self.project_id}/health")

    # ── Writes (10%) ──────────────────────────────────────────

    @task(3)
    def create_project(self):
        self.api_post(
            "/api/v1/projects",
            json={"name": f"Perf {_sfx()}", "description": "Load test"},
        )

    @task(2)
    def update_project(self):
        self.api_patch(
            f"/api/v1/projects/{self.project_id}",
            json={"description": f"Updated {_sfx()}"},
        )

    @task(2)
    def create_component(self):
        self.api_post(
            f"/api/v1/projects/{self.project_id}/components",
            json={"name": f"Comp {_sfx()}"},
        )

    @task(2)
    def create_module(self):
        comps = self._ensure_components()
        if comps:
            self.api_post(
                f"/api/v1/components/{random.choice(comps)}/modules",
                json={"name": f"Mod {_sfx()}"},
            )
