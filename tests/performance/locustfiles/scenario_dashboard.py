"""Dashboard & analytics — read-heavy stress test.

Tests: dashboard stats, attention dashboard, portfolio overview, analytics.
All endpoints are read-only (95%+ reads).
"""

from common import UPCPBaseUser
from locust import between, task


class DashboardUser(UPCPBaseUser):
    """Dashboard-focused workload: stats, attention, analytics."""

    wait_time = between(0.5, 2.0)

    def on_start(self) -> None:
        super().on_start()
        self.project_id = self.ensure_project()

    # ── Dashboard (40%) ───────────────────────────────────────

    @task(15)
    def dashboard_stats(self):
        self.api_get("/api/v1/dashboard/stats")

    @task(12)
    def attention_dashboard(self):
        self.api_get("/api/v1/dashboard/attention")

    @task(8)
    def portfolio_overview(self):
        self.api_get("/api/v1/portfolio/overview")

    # ── Project Health (20%) ──────────────────────────────────

    @task(10)
    def project_health(self):
        self.api_get(f"/api/v1/projects/{self.project_id}/health")

    # ── Analytics (15%) ───────────────────────────────────────

    @task(8)
    def analytics_overview(self):
        self.api_get(f"/api/v1/projects/{self.project_id}/analytics")

    @task(5)
    def analytics_velocity(self):
        self.api_get(f"/api/v1/projects/{self.project_id}/analytics/velocity")

    @task(2)
    def analytics_agent_performance(self):
        self.api_get(f"/api/v1/projects/{self.project_id}/analytics/agents")

    # ── Audit (15%) ───────────────────────────────────────────

    @task(8)
    def audit_events(self):
        self.api_get(f"/api/v1/projects/{self.project_id}/audit-events")

    @task(5)
    def audit_filtered(self):
        self.api_get(f"/api/v1/projects/{self.project_id}/audit-events?limit=20&offset=0")

    # ── Notifications (10%) ───────────────────────────────────

    @task(5)
    def list_notifications(self):
        self.api_get("/api/v1/notifications")

    @task(3)
    def unread_count(self):
        self.api_get("/api/v1/notifications/unread-count")

    @task(2)
    def mark_all_read(self):
        self.api_post("/api/v1/notifications/mark-all-read")
