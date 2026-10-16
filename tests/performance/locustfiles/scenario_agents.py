"""Agent operations — stress test for agent self-service and workflow.

Tests: agent me, inbox, playbook, claim, heartbeat, clarification.
Simulates multiple concurrent agents working on tasks.
"""

import random
import string

from common import UPCPBaseUser
from locust import between, task


def _sfx() -> str:
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=6))


class AgentWorkflowUser(UPCPBaseUser):
    """Agent-focused workload: self-service + task workflow operations."""

    wait_time = between(0.5, 2.0)

    def on_start(self) -> None:
        super().on_start()
        self.project_id = self.ensure_project()
        self._task_ids: list[str] = []

    def _ensure_tasks(self, count: int = 5) -> list[str]:
        features_resp = self.api_get(f"/api/v1/projects/{self.project_id}/features")
        features = features_resp if isinstance(features_resp, list) else []
        if not features:
            data = self.api_post(
                f"/api/v1/projects/{self.project_id}/features",
                json={"name": f"Feature {_sfx()}", "description": "Agent test"},
            )
            if data:
                features = [data]

        while len(self._task_ids) < count and features:
            feat = random.choice(features)
            data = self.api_post(
                f"/api/v1/features/{feat['id']}/tasks",
                json={"title": f"Task {_sfx()}", "status": "backlog"},
            )
            if data:
                self._task_ids.append(data["id"])
            else:
                break
        return self._task_ids

    # ── Agent Self-Service (30%) ──────────────────────────────

    @task(10)
    def agent_me(self):
        self.api_get("/api/v1/agent/me")

    @task(8)
    def agent_inbox(self):
        self.api_get("/api/v1/agent/inbox")

    @task(7)
    def agent_playbook(self):
        self.api_get("/api/v1/agent/playbook")

    @task(5)
    def agent_detail(self):
        self.api_get("/api/v1/agents")

    # ── Task Claims (25%) ─────────────────────────────────────

    @task(10)
    def claim_task(self):
        tasks = self._ensure_tasks()
        backlog = [t for t in tasks if t]
        if backlog:
            task_id = random.choice(backlog)
            self.api_post(f"/api/v1/tasks/{task_id}/claim")

    @task(8)
    def release_task(self):
        tasks = self._ensure_tasks()
        if tasks:
            task_id = random.choice(tasks)
            self.api_post(f"/api/v1/tasks/{task_id}/release")

    @task(7)
    def send_heartbeat(self):
        tasks = self._ensure_tasks()
        if tasks:
            task_id = random.choice(tasks)
            self.api_post(
                f"/api/v1/tasks/{task_id}/heartbeat",
                json={
                    "progress_percent": random.randint(0, 100),
                    "current_step": "Working on implementation",
                    "next_step": "Testing",
                },
            )

    # ── Clarifications (15%) ──────────────────────────────────

    @task(8)
    def list_clarifications(self):
        self.api_get(f"/api/v1/projects/{self.project_id}/clarifications")

    @task(4)
    def create_clarification(self):
        tasks = self._ensure_tasks()
        if tasks:
            self.api_post(
                f"/api/v1/tasks/{random.choice(tasks)}/clarifications",
                json={
                    "question": f"Clarification needed {_sfx()}",
                    "blocking": False,
                },
            )

    @task(3)
    def answer_clarification(self):
        self.api_get(f"/api/v1/projects/{self.project_id}/clarifications")

    # ── Evidence (15%) ────────────────────────────────────────

    @task(8)
    def list_evidence(self):
        tasks = self._ensure_tasks()
        if tasks:
            self.api_get(f"/api/v1/tasks/{random.choice(tasks)}/evidence")

    @task(4)
    def attach_evidence(self):
        tasks = self._ensure_tasks()
        if tasks:
            self.api_post(
                f"/api/v1/tasks/{random.choice(tasks)}/evidence",
                json={
                    "type": "link",
                    "title": f"Evidence {_sfx()}",
                    "url": "https://example.com/proof",
                },
            )

    @task(3)
    def submit_for_review(self):
        tasks = self._ensure_tasks()
        if tasks:
            self.api_post(f"/api/v1/tasks/{random.choice(tasks)}/submit-for-review")

    # ── Reviews (15%) ─────────────────────────────────────────

    @task(8)
    def list_review_rounds(self):
        tasks = self._ensure_tasks()
        if tasks:
            self.api_get(f"/api/v1/tasks/{random.choice(tasks)}/review-rounds")

    @task(4)
    def submit_review(self):
        tasks = self._ensure_tasks()
        if tasks:
            self.api_post(
                f"/api/v1/tasks/{random.choice(tasks)}/submit-review",
                json={"verdict": "approved", "confidence": 90, "summary": "Looks good"},
            )

    @task(3)
    def list_findings(self):
        tasks = self._ensure_tasks()
        if tasks:
            self.api_get(f"/api/v1/tasks/{random.choice(tasks)}/review-rounds")
