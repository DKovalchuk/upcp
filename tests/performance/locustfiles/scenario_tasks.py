"""Task workflow operations — stress test for delivery lifecycle.

Tests: feature CRUD, task CRUD, task status transitions, subtasks.
Simulates real agent workflow: create → work → submit → done.
"""

import random
import string

from common import UPCPBaseUser
from locust import between, task


def _sfx() -> str:
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=6))


class TaskWorkflowUser(UPCPBaseUser):
    """Task-focused workload: delivery CRUD + status transitions."""

    wait_time = between(0.3, 1.5)

    def on_start(self) -> None:
        super().on_start()
        self.project_id = self.ensure_project()
        self._feature_ids: list[str] = []
        self._task_ids: list[str] = []

    def _ensure_features(self, count: int = 3) -> list[str]:
        while len(self._feature_ids) < count:
            data = self.api_post(
                f"/api/v1/projects/{self.project_id}/features",
                json={"name": f"Feature {_sfx()}", "description": "Load test"},
            )
            if data:
                self._feature_ids.append(data["id"])
            else:
                break
        return self._feature_ids

    def _ensure_tasks(self, count: int = 5) -> list[str]:
        features = self._ensure_features()
        while len(self._task_ids) < count and features:
            feat_id = random.choice(features)
            data = self.api_post(
                f"/api/v1/features/{feat_id}/tasks",
                json={
                    "title": f"Task {_sfx()}",
                    "description": "Load test",
                    "status": "backlog",
                },
            )
            if data:
                self._task_ids.append(data["id"])
            else:
                break
        return self._task_ids

    # ── Feature Reads (15%) ───────────────────────────────────

    @task(8)
    def list_features(self):
        self.api_get(f"/api/v1/projects/{self.project_id}/features")

    @task(5)
    def list_tasks(self):
        self.api_get(f"/api/v1/projects/{self.project_id}/tasks")

    @task(2)
    def get_task_detail(self):
        tasks = self._ensure_tasks()
        if tasks:
            self.api_get(f"/api/v1/tasks/{random.choice(tasks)}")

    # ── Feature Writes (10%) ──────────────────────────────────

    @task(3)
    def create_feature(self):
        self.api_post(
            f"/api/v1/projects/{self.project_id}/features",
            json={"name": f"Feature {_sfx()}", "description": "Load test"},
        )

    @task(2)
    def update_feature(self):
        features = self._ensure_features()
        if features:
            self.api_patch(
                f"/api/v1/features/{random.choice(features)}",
                json={"description": f"Updated {_sfx()}"},
            )

    # ── Task Writes (15%) ─────────────────────────────────────

    @task(4)
    def create_task(self):
        features = self._ensure_features()
        if features:
            self.api_post(
                f"/api/v1/features/{random.choice(features)}/tasks",
                json={
                    "title": f"Task {_sfx()}",
                    "description": "Load test",
                    "status": "backlog",
                },
            )

    @task(3)
    def update_task_status(self):
        tasks = self._ensure_tasks()
        if tasks:
            statuses = ["backlog", "in_progress", "review", "done"]
            self.api_patch(
                f"/api/v1/tasks/{random.choice(tasks)}",
                json={"status": random.choice(statuses)},
            )

    @task(2)
    def update_task_priority(self):
        tasks = self._ensure_tasks()
        if tasks:
            self.api_patch(
                f"/api/v1/tasks/{random.choice(tasks)}",
                json={"priority": random.randint(0, 3)},
            )

    @task(2)
    def create_subtask(self):
        tasks = self._ensure_tasks()
        if tasks:
            self.api_post(
                f"/api/v1/tasks/{random.choice(tasks)}/subtasks",
                json={"title": f"Subtask {_sfx()}", "status": "todo"},
            )

    # ── Quality Reads (10%) ───────────────────────────────────

    @task(3)
    def list_acceptance_criteria(self):
        tasks = self._ensure_tasks()
        if tasks:
            self.api_get(f"/api/v1/tasks/{random.choice(tasks)}/acceptance-criteria")

    @task(3)
    def list_dod_items(self):
        tasks = self._ensure_tasks()
        if tasks:
            self.api_get(f"/api/v1/tasks/{random.choice(tasks)}/dod-items")

    @task(2)
    def list_evidence(self):
        tasks = self._ensure_tasks()
        if tasks:
            self.api_get(f"/api/v1/tasks/{random.choice(tasks)}/evidence")

    @task(2)
    def list_review_rounds(self):
        tasks = self._ensure_tasks()
        if tasks:
            self.api_get(f"/api/v1/tasks/{random.choice(tasks)}/review-rounds")
