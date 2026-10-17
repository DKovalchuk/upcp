"""Mixed realistic workload — combines all API operations with realistic weights.

This is the primary scenario for baseline measurements and nightly smoke tests.
Weight distribution reflects expected real-world usage patterns.
"""

import random
import string

from common import UPCPBaseUser
from locust import between, task


def _suffix(length: int = 6) -> str:
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=length))


class MixedWorkloadUser(UPCPBaseUser):
    """Realistic mixed workload across all UPCP API endpoints."""

    wait_time = between(0.3, 1.5)

    def on_start(self) -> None:
        super().on_start()
        self.project_id = self.ensure_project()
        self._component_id: str | None = None
        self._module_id: str | None = None
        self._feature_id: str | None = None
        self._task_id: str | None = None

    def _ensure_component(self) -> str:
        if self._component_id:
            return self._component_id
        data = self.api_post(
            f"/api/v1/projects/{self.project_id}/components",
            json={"name": f"Component {_suffix()}", "description": "Load test"},
        )
        if data:
            self._component_id = data["id"]
        return self._component_id or ""

    def _ensure_module(self) -> str:
        if self._module_id:
            return self._module_id
        component_id = self._ensure_component()
        if not component_id:
            return ""
        data = self.api_post(
            f"/api/v1/components/{component_id}/modules",
            json={"name": f"Module {_suffix()}", "description": "Load test"},
        )
        if data:
            self._module_id = data["id"]
        return self._module_id or ""

    def _ensure_feature(self) -> str:
        if self._feature_id:
            return self._feature_id
        data = self.api_post(
            f"/api/v1/projects/{self.project_id}/features",
            json={"name": f"Feature {_suffix()}", "description": "Load test"},
        )
        if data:
            self._feature_id = data["id"]
        return self._feature_id or ""

    def _ensure_task(self) -> str:
        if self._task_id:
            return self._task_id
        feature_id = self._ensure_feature()
        if not feature_id:
            return ""
        data = self.api_post(
            f"/api/v1/features/{feature_id}/tasks",
            json={"title": f"Task {_suffix()}", "description": "Load test", "status": "backlog"},
        )
        if data:
            self._task_id = data["id"]
        return self._task_id or ""

    # ── Project Operations (15%) ──────────────────────────────

    @task(5)
    def list_projects(self):
        self.api_get("/api/v1/projects")

    @task(3)
    def get_project(self):
        if self.project_id:
            self.api_get(f"/api/v1/projects/{self.project_id}")

    @task(1)
    def create_project(self):
        self.api_post(
            "/api/v1/projects",
            json={"name": f"Perf Project {_suffix()}", "description": "Load test"},
        )

    @task(1)
    def project_health(self):
        if self.project_id:
            self.api_get(f"/api/v1/projects/{self.project_id}/health")

    # ── Structure Operations (10%) ────────────────────────────

    @task(3)
    def list_components(self):
        if self.project_id:
            self.api_get(f"/api/v1/projects/{self.project_id}/components")

    @task(2)
    def list_modules(self):
        component_id = self._ensure_component()
        if component_id:
            self.api_get(f"/api/v1/components/{component_id}/modules")

    # ── Delivery Operations (25%) ─────────────────────────────

    @task(5)
    def list_features(self):
        if self.project_id:
            self.api_get(f"/api/v1/projects/{self.project_id}/features")

    @task(3)
    def list_tasks(self):
        if self.project_id:
            self.api_get(f"/api/v1/projects/{self.project_id}/tasks")

    @task(2)
    def get_task(self):
        task_id = self._ensure_task()
        if task_id:
            self.api_get(f"/api/v1/tasks/{task_id}")

    @task(1)
    def create_task(self):
        feature_id = self._ensure_feature()
        if feature_id:
            self.api_post(
                f"/api/v1/features/{feature_id}/tasks",
                json={
                    "title": f"Task {_suffix()}",
                    "description": "Created during load test",
                    "status": "backlog",
                },
            )

    @task(1)
    def update_task(self):
        task_id = self._ensure_task()
        if task_id:
            self.api_patch(
                f"/api/v1/tasks/{task_id}",
                json={"description": f"Updated {_suffix()}"},
            )

    # ── Dashboard & Analytics (15%) ───────────────────────────

    @task(5)
    def dashboard_stats(self):
        self.api_get("/api/v1/dashboard/stats")

    @task(3)
    def attention_dashboard(self):
        self.api_get("/api/v1/dashboard/attention")

    @task(2)
    def portfolio_overview(self):
        self.api_get("/api/v1/portfolio/overview")

    # ── Quality Operations (10%) ──────────────────────────────

    @task(3)
    def list_acceptance_criteria(self):
        task_id = self._ensure_task()
        if task_id:
            self.api_get(f"/api/v1/tasks/{task_id}/acceptance-criteria")

    @task(2)
    def list_dod_items(self):
        task_id = self._ensure_task()
        if task_id:
            self.api_get(f"/api/v1/tasks/{task_id}/dod-items")

    # ── Search (5%) ───────────────────────────────────────────

    @task(3)
    def search(self):
        queries = ["test", "task", "feature", "component", "project"]
        self.api_get(f"/api/v1/search?q={random.choice(queries)}")

    # ── Audit (5%) ────────────────────────────────────────────

    @task(2)
    def audit_events(self):
        if self.project_id:
            self.api_get(f"/api/v1/projects/{self.project_id}/audit-events")

    # ── Agent Self-Service (10%) ──────────────────────────────

    @task(2)
    def agent_me(self):
        self.api_get("/api/v1/agent/me")

    @task(1)
    def agent_inbox(self):
        self.api_get("/api/v1/agent/inbox")

    @task(1)
    def agent_playbook(self):
        self.api_get("/api/v1/agent/playbook")

    # ── Health (5%) ───────────────────────────────────────────

    @task(3)
    def health_check(self):
        self.api_get("/health")
