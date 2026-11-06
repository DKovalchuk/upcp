"""Search & pagination — stress test for search and list endpoints.

Tests: global search, paginated lists, filtering, sorting.
Focuses on database query performance under varied inputs.
"""

import random
import string

from common import UPCPBaseUser
from locust import between, task


def _sfx() -> str:
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=6))


class SearchUser(UPCPBaseUser):
    """Search and pagination workload: varied queries, large result sets."""

    wait_time = between(0.2, 0.8)

    QUERIES = [
        "task",
        "feature",
        "project",
        "component",
        "module",
        "test",
        "auth",
        "login",
        "dashboard",
        "search",
        "workflow",
        "evidence",
        "review",
        "notification",
    ]

    def on_start(self) -> None:
        super().on_start()
        self.project_id = self.ensure_project()

    # ── Global Search (40%) ───────────────────────────────────

    @task(15)
    def search_short(self):
        q = random.choice(self.QUERIES[:5])
        self.api_get(f"/api/v1/search?q={q}")

    @task(10)
    def search_medium(self):
        q = random.choice(self.QUERIES)
        self.api_get(f"/api/v1/search?q={q}")

    @task(5)
    def search_long(self):
        q = " ".join(random.choices(self.QUERIES, k=3))
        self.api_get(f"/api/v1/search?q={q}")

    @task(5)
    def search_special_chars(self):
        q = random.choice(["'", '"', "\\", "%", "_", "<", ">", "&"])
        self.api_get(f"/api/v1/search?q={q}")

    @task(5)
    def search_empty(self):
        self.api_get("/api/v1/search?q=")

    # ── Paginated Lists (35%) ─────────────────────────────────

    @task(10)
    def list_projects_page1(self):
        self.api_get("/api/v1/projects?offset=0&limit=20")

    @task(5)
    def list_projects_page2(self):
        self.api_get("/api/v1/projects?offset=20&limit=20")

    @task(5)
    def list_projects_large_page(self):
        self.api_get("/api/v1/projects?offset=0&limit=100")

    @task(5)
    def list_tasks_filtered(self):
        self.api_get(f"/api/v1/projects/{self.project_id}/tasks?status=done")

    @task(5)
    def list_tasks_sorted(self):
        self.api_get(f"/api/v1/projects/{self.project_id}/tasks?sort_by=created_at&order=desc")

    @task(5)
    def list_features_page(self):
        self.api_get(f"/api/v1/projects/{self.project_id}/features?offset=0&limit=50")

    # ── Entity Counts (15%) ───────────────────────────────────

    @task(8)
    def dashboard_stats(self):
        self.api_get("/api/v1/dashboard/stats")

    @task(4)
    def portfolio_overview(self):
        self.api_get("/api/v1/portfolio/overview")

    @task(3)
    def audit_count(self):
        self.api_get(f"/api/v1/projects/{self.project_id}/audit-events?limit=1")
