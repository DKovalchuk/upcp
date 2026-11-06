"""HTTP-level tests for quality state transitions — TASK-0160 (AC1 gaps).

Covers the previously untested HTTP surface of backend/app/api/v1/quality.py:
- evidence verification endpoints (agent-verify / human-accept / reject)
- review-round lifecycle endpoints (start / findings / verdict)
- POST /tasks/{id}/submit-review, including the task transition to
  ``ready_for_review`` introduced by this batch (see service.py).
"""

import pytest
from app.api.v1.delivery import router as delivery_router
from app.api.v1.projects import router as projects_router
from app.api.v1.quality import router as quality_router
from app.api.v1.structure import router as structure_router
from fastapi.testclient import TestClient

from tests.conftest import make_test_app


@pytest.fixture()
def client() -> TestClient:
    app = make_test_app(projects_router, structure_router, delivery_router, quality_router)
    return TestClient(app)


def _seed_task(client: TestClient, *, status: str | None = None) -> str:
    """Create project → feature → task through the API; return task id."""
    pid = client.post("/api/v1/projects", json={"name": "P"}).json()["id"]
    fid = client.post(f"/api/v1/projects/{pid}/features", json={"name": "F"}).json()["id"]
    payload: dict[str, str] = {"title": "T"}
    if status is not None:
        payload["status"] = status
    resp = client.post(f"/api/v1/features/{fid}/tasks", json=payload)
    assert resp.status_code == 201
    return resp.json()["id"]


def _seed_evidence(client: TestClient, task_id: str) -> str:
    resp = client.post(
        f"/api/v1/tasks/{task_id}/evidence",
        json={
            "type": "note",
            "title": "E",
            "created_by_type": "agent",
            "created_by_id": "a1",
        },
    )
    assert resp.status_code == 201
    return resp.json()["id"]


def _seed_round(client: TestClient, task_id: str) -> str:
    resp = client.post(
        f"/api/v1/tasks/{task_id}/review-rounds",
        json={"reviewer_type": "human", "reviewer_id": "h1"},
    )
    assert resp.status_code == 201
    assert resp.json()["state"] == "pending"
    return resp.json()["id"]


# ── Evidence transitions ──


class TestEvidenceTransitionEndpoints:
    def test_agent_verify_returns_200_and_changes_state(self, client: TestClient) -> None:
        eid = _seed_evidence(client, _seed_task(client))
        resp = client.post(f"/api/v1/evidence/{eid}/agent-verify", json={"notes": "checked"})
        assert resp.status_code == 200
        assert resp.json()["verification_state"] == "agent_verified"
        assert resp.json()["verified_by_type"] == "agent"

    def test_agent_verify_unknown_id_404(self, client: TestClient) -> None:
        resp = client.post("/api/v1/evidence/does-not-exist/agent-verify")
        assert resp.status_code == 404

    def test_agent_verify_already_verified_409(self, client: TestClient) -> None:
        eid = _seed_evidence(client, _seed_task(client))
        first = client.post(f"/api/v1/evidence/{eid}/agent-verify")
        assert first.status_code == 200
        second = client.post(f"/api/v1/evidence/{eid}/agent-verify")
        assert second.status_code == 409

    def test_human_accept_returns_200_and_changes_state(self, client: TestClient) -> None:
        eid = _seed_evidence(client, _seed_task(client))
        resp = client.post(f"/api/v1/evidence/{eid}/human-accept")
        assert resp.status_code == 200
        assert resp.json()["verification_state"] == "human_accepted"

    def test_human_accept_unknown_id_404(self, client: TestClient) -> None:
        resp = client.post("/api/v1/evidence/does-not-exist/human-accept")
        assert resp.status_code == 404

    def test_human_accept_already_accepted_409(self, client: TestClient) -> None:
        eid = _seed_evidence(client, _seed_task(client))
        assert client.post(f"/api/v1/evidence/{eid}/human-accept").status_code == 200
        resp = client.post(f"/api/v1/evidence/{eid}/human-accept")
        assert resp.status_code == 409

    def test_reject_returns_200_and_changes_state(self, client: TestClient) -> None:
        eid = _seed_evidence(client, _seed_task(client))
        resp = client.post(f"/api/v1/evidence/{eid}/reject", json={"reason": "stale"})
        assert resp.status_code == 200
        assert resp.json()["verification_state"] == "rejected"

    def test_reject_unknown_id_404(self, client: TestClient) -> None:
        resp = client.post("/api/v1/evidence/does-not-exist/reject")
        assert resp.status_code == 404

    def test_reject_after_accept_409(self, client: TestClient) -> None:
        eid = _seed_evidence(client, _seed_task(client))
        assert client.post(f"/api/v1/evidence/{eid}/human-accept").status_code == 200
        resp = client.post(f"/api/v1/evidence/{eid}/reject")
        assert resp.status_code == 409


# ── Review round lifecycle ──


class TestReviewRoundLifecycleEndpoints:
    def test_create_round_201_pending(self, client: TestClient) -> None:
        tid = _seed_task(client)
        resp = client.post(
            f"/api/v1/tasks/{tid}/review-rounds",
            json={"reviewer_type": "human", "reviewer_id": "h1"},
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["state"] == "pending"
        assert body["task_id"] == tid

    def test_start_round_200_in_progress(self, client: TestClient) -> None:
        rid = _seed_round(client, _seed_task(client))
        resp = client.post(f"/api/v1/review-rounds/{rid}/start")
        assert resp.status_code == 200
        assert resp.json()["state"] == "in_progress"

    def test_start_completed_round_409(self, client: TestClient) -> None:
        rid = _seed_round(client, _seed_task(client))
        assert client.post(f"/api/v1/review-rounds/{rid}/start").status_code == 200
        verdict = client.post(
            f"/api/v1/review-rounds/{rid}/verdict",
            json={"verdict": "approve", "confidence": 95, "summary": "good"},
        )
        assert verdict.status_code == 200
        resp = client.post(f"/api/v1/review-rounds/{rid}/start")
        assert resp.status_code == 409

    def test_start_unknown_round_404(self, client: TestClient) -> None:
        resp = client.post("/api/v1/review-rounds/does-not-exist/start")
        assert resp.status_code == 404

    def test_add_finding_201(self, client: TestClient) -> None:
        rid = _seed_round(client, _seed_task(client))
        resp = client.post(
            f"/api/v1/review-rounds/{rid}/findings",
            json={"severity": "minor", "category": "style", "message": "nit"},
        )
        assert resp.status_code == 201
        assert resp.json()["review_round_id"] == rid

    def test_add_finding_wrong_state_409(self, client: TestClient) -> None:
        rid = _seed_round(client, _seed_task(client))
        assert client.post(f"/api/v1/review-rounds/{rid}/start").status_code == 200
        assert (
            client.post(
                f"/api/v1/review-rounds/{rid}/verdict",
                json={"verdict": "approve", "confidence": 90, "summary": "ok"},
            ).status_code
            == 200
        )
        resp = client.post(
            f"/api/v1/review-rounds/{rid}/findings",
            json={"severity": "major", "category": "correctness", "message": "late finding"},
        )
        assert resp.status_code == 409

    def test_add_finding_unknown_round_404(self, client: TestClient) -> None:
        resp = client.post(
            "/api/v1/review-rounds/does-not-exist/findings",
            json={"severity": "minor", "category": "style", "message": "nit"},
        )
        assert resp.status_code == 404

    def test_verdict_200_completed(self, client: TestClient) -> None:
        rid = _seed_round(client, _seed_task(client))
        assert client.post(f"/api/v1/review-rounds/{rid}/start").status_code == 200
        resp = client.post(
            f"/api/v1/review-rounds/{rid}/verdict",
            json={"verdict": "approve", "confidence": 88, "summary": "ship it"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["state"] == "completed"
        assert body["verdict"] == "approve"
        assert body["completed_at"] is not None

    def test_verdict_while_pending_409(self, client: TestClient) -> None:
        rid = _seed_round(client, _seed_task(client))
        resp = client.post(
            f"/api/v1/review-rounds/{rid}/verdict",
            json={"verdict": "reject", "confidence": 50, "summary": "too early"},
        )
        assert resp.status_code == 409

    def test_verdict_unknown_round_404(self, client: TestClient) -> None:
        resp = client.post(
            "/api/v1/review-rounds/does-not-exist/verdict",
            json={"verdict": "approve", "confidence": 90, "summary": "ok"},
        )
        assert resp.status_code == 404


# ── POST /tasks/{id}/submit-review — gate + task transition ──


class TestSubmitReviewTaskTransition:
    def test_submit_review_transitions_in_progress_task(self, client: TestClient) -> None:
        """Gate-passing in_progress task → 201 AND status ready_for_review."""
        tid = _seed_task(client, status="in_progress")
        resp = client.post(f"/api/v1/tasks/{tid}/submit-review")
        assert resp.status_code == 201
        assert resp.json()["state"] == "pending"
        task = client.get(f"/api/v1/tasks/{tid}").json()
        assert task["status"] == "ready_for_review"

    def test_submit_review_already_ready_for_review(self, client: TestClient) -> None:
        """Task already in ready_for_review submits fine and stays there."""
        tid = _seed_task(client, status="ready_for_review")
        resp = client.post(f"/api/v1/tasks/{tid}/submit-review")
        assert resp.status_code == 201
        task = client.get(f"/api/v1/tasks/{tid}").json()
        assert task["status"] == "ready_for_review"

    def test_submit_review_claimed_task_transitions(self, client: TestClient) -> None:
        """Gate accepts claimed tasks, so they must reach ready_for_review too."""
        tid = _seed_task(client, status="claimed")
        resp = client.post(f"/api/v1/tasks/{tid}/submit-review")
        assert resp.status_code == 201
        task = client.get(f"/api/v1/tasks/{tid}").json()
        assert task["status"] == "ready_for_review"

    def test_submit_review_gate_failure_returns_400(self, client: TestClient) -> None:
        """DoD not passed → 400 and no partial task transition."""
        tid = _seed_task(client, status="in_progress")
        assert (
            client.post(f"/api/v1/tasks/{tid}/dod-items", json={"name": "Tests pass"}).status_code
            == 201
        )
        resp = client.post(f"/api/v1/tasks/{tid}/submit-review")
        assert resp.status_code == 400
        task = client.get(f"/api/v1/tasks/{tid}").json()
        assert task["status"] == "in_progress"

    def test_submit_review_unknown_task_404(self, client: TestClient) -> None:
        resp = client.post("/api/v1/tasks/does-not-exist/submit-review")
        assert resp.status_code == 404
