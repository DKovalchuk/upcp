"""HTTP-level tests for the notification endpoints — closes AUDIT M16 gap T2 (SPEC-0022).

``test_notification.py`` covers the model/service layer only; the routes in
``app/api/v1/notifications.py`` had no HTTP-level coverage. The route-contract
tests additionally pin ``POST /api/v1/notifications/read-all`` so the perf
scenario 404 class (``scenario_dashboard.py`` calling ``mark-all-read``) cannot
regress.

Uses the shared conftest engine only: ``make_test_app`` (drop+create) + the
``db_session`` fixture — no local sqlite engine, no local ``_db`` fixture
(enforced repo-wide by ``test_db_fixture_contract.py``).
"""

import re
from pathlib import Path

from app.api.v1.notifications import router as notifications_router
from app.reporting.models import Notification
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.conftest import make_test_app

_SCENARIO_PATH = (
    Path(__file__).resolve().parents[2]
    / "tests"
    / "performance"
    / "locustfiles"
    / "scenario_dashboard.py"
)

# Bucket the endpoints read when no ?user_id= is supplied — matches the
# frontend, which never sends user_id on REST notification calls.
_DEFAULT_USER = "default"

_LIST_KEYS = {"id", "type", "title", "message", "entity_type", "entity_id", "is_read", "created_at"}


def _client() -> TestClient:
    """Fresh app on the shared conftest engine (drop+create, then router)."""
    return TestClient(make_test_app(notifications_router))


def _seed(db_session: Session, rows: list[tuple[str, bool]]) -> list[str]:
    """Insert ``(user_id, is_read)`` notifications and commit.

    Committed up-front so request-scoped rollbacks inside the app (e.g. the
    404 path) cannot discard the fixture's data.
    """
    ids: list[str] = []
    for user_id, is_read in rows:
        row = Notification(
            user_id=user_id,
            type="info",
            title="seeded",
            message="seeded message",
            is_read=is_read,
        )
        db_session.add(row)
        db_session.flush()
        ids.append(row.id)
    db_session.commit()
    return ids


class TestListNotifications:
    def test_list_returns_seeded_rows(self, db_session: Session) -> None:
        """GET /notifications → 200 with the items contract, scoped to one user."""
        client = _client()
        ids = _seed(
            db_session,
            [(_DEFAULT_USER, False), (_DEFAULT_USER, True), ("other-user", False)],
        )

        resp = client.get("/api/v1/notifications")

        assert resp.status_code == 200
        body = resp.json()
        # NOTE: unlike the other list endpoints (projects, audit, quality…),
        # this one returns NO {total, offset, limit} envelope — list_by_user
        # has no count/offset support (service.py is outside this task's
        # ownership). Deviation recorded for TASK-0160; reconcile together
        # with the follow-up pagination task (PRD §6.3 documents limit=50).
        assert set(body) == {"items"}
        items = body["items"]
        # other-user's row must not leak into the default bucket.
        assert {i["id"] for i in items} == {ids[0], ids[1]}
        item = next(i for i in items if i["id"] == ids[0])
        assert set(item) == _LIST_KEYS
        assert item["is_read"] is False
        assert item["created_at"] is not None

    def test_list_unread_only_filter(self, db_session: Session) -> None:
        """GET /notifications?unread_only=true returns only unread rows (frontend contract)."""
        client = _client()
        _seed(db_session, [(_DEFAULT_USER, False), (_DEFAULT_USER, True)])

        resp = client.get("/api/v1/notifications", params={"unread_only": "true"})

        assert resp.status_code == 200
        items = resp.json()["items"]
        assert items
        assert all(i["is_read"] is False for i in items)

    def test_list_empty_bucket(self, db_session: Session) -> None:
        """GET /notifications for an untouched user → 200 with an empty list."""
        client = _client()
        _seed(db_session, [("other-user", False)])

        resp = client.get("/api/v1/notifications")

        assert resp.status_code == 200
        assert resp.json() == {"items": []}


class TestMarkRead:
    def test_mark_read_flips_flag(self, db_session: Session) -> None:
        """POST /notifications/{id}/read → 200, is_read true, persisted on re-read."""
        client = _client()
        (notification_id,) = _seed(db_session, [(_DEFAULT_USER, False)])

        resp = client.post(f"/api/v1/notifications/{notification_id}/read")

        assert resp.status_code == 200
        assert resp.json() == {"id": notification_id, "is_read": True}
        listed = client.get("/api/v1/notifications").json()["items"]
        assert next(i for i in listed if i["id"] == notification_id)["is_read"] is True

    def test_mark_read_unknown_id_returns_404(self, db_session: Session) -> None:
        """POST /notifications/{unknown}/read → 404 with the not-found message."""
        client = _client()
        _seed(db_session, [(_DEFAULT_USER, False)])

        resp = client.post("/api/v1/notifications/does-not-exist/read")

        assert resp.status_code == 404
        assert "not found" in resp.text.lower()


class TestMarkAllRead:
    def test_read_all_marks_unread_of_default_user(self, db_session: Session) -> None:
        """POST /notifications/read-all → 200, all seeded unread become read, others untouched."""
        client = _client()
        _seed(
            db_session,
            [
                (_DEFAULT_USER, False),
                (_DEFAULT_USER, False),
                (_DEFAULT_USER, True),  # already read → not counted
                ("other-user", False),  # different bucket → untouched
            ],
        )

        resp = client.post("/api/v1/notifications/read-all")

        assert resp.status_code == 200
        assert resp.json() == {"count": 2}
        mine = client.get("/api/v1/notifications").json()["items"]
        assert mine and all(i["is_read"] for i in mine)
        theirs = client.get("/api/v1/notifications", params={"user_id": "other-user"}).json()[
            "items"
        ]
        assert [i["is_read"] for i in theirs] == [False]

    def test_unread_count_lifecycle(self, db_session: Session) -> None:
        """GET /unread-count matches the seeded unread, then drops to 0 after read-all."""
        client = _client()
        _seed(db_session, [(_DEFAULT_USER, False), (_DEFAULT_USER, False), ("other-user", False)])

        assert client.get("/api/v1/notifications/unread-count").json() == {"count": 2}

        client.post("/api/v1/notifications/read-all")

        assert client.get("/api/v1/notifications/unread-count").json() == {"count": 0}

    def test_read_all_without_unread_returns_zero(self, db_session: Session) -> None:
        """POST /notifications/read-all is idempotent → 200 {count: 0}."""
        client = _client()
        _seed(db_session, [(_DEFAULT_USER, True)])

        resp = client.post("/api/v1/notifications/read-all")

        assert resp.status_code == 200
        assert resp.json() == {"count": 0}


def _normalize(path: str) -> str:
    """Collapse path params ({project_id}, {self.project_id}) to a wildcard."""
    return re.sub(r"\{[^}]+\}", "*", path)


class TestRouteContract:
    """Guards the 404 class found in the perf scenario (AUDIT M16 / SPEC-0022)."""

    def test_app_registers_read_all_route(self) -> None:
        """The real ASGI app exposes POST /api/v1/notifications/read-all."""
        from app.main import app as main_app  # production wiring, not the test app

        operations = main_app.openapi()["paths"].get("/api/v1/notifications/read-all", {})
        assert "post" in operations, "POST /api/v1/notifications/read-all must stay registered"

    def test_locust_scenario_urls_resolve(self) -> None:
        """Every URL the perf scenario calls exists on the real app.

        Scope: all scenario URLs — pins the class of bug that made the
        scenario POST a non-existent ``/notifications/mark-all-read`` and
        GET three non-existent ``/projects/{id}/analytics*`` paths
        (404s under load, ~15% of the dashboard scenario weight).
        """
        from app.main import app as main_app  # production wiring, not the test app

        registered = {
            (method.upper(), _normalize(path))
            for path, operations in main_app.openapi()["paths"].items()
            for method in operations
        }
        source = _SCENARIO_PATH.read_text(encoding="utf-8")
        calls = re.findall(r'self\.api_(get|post|patch|delete)\(\s*f?"([^"]+)"', source)
        scenario_urls = [(method.upper(), url.split("?")[0]) for method, url in calls]
        assert scenario_urls, "the perf scenario must exercise the API"
        missing = [
            f"{method} {url}"
            for method, url in scenario_urls
            if (method, _normalize(url)) not in registered
        ]
        assert not missing, (
            "scenario_dashboard.py calls URLs that match no app route "
            f"(they 404 under load): {missing}"
        )
