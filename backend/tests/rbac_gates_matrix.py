"""RBAC Phase-B gate matrix + test plumbing — TASK-0172.

Data-only module (no ``test_`` prefix → not collected): the inventory
table from ``tasks/TASK-0172-rbac-coverage.md`` as parametrization source
for ``test_rbac_gates_coverage.py`` (36 ``require_permission`` route gates)
and ``test_rbac_role_gates.py`` (seed drift guard). Also the shared
resource chain and request helper the positive cases use.

Contains no gate-factory imports — both test files import factories
inside tests so the suite collects before the implementation (red phase).
"""

from __future__ import annotations

import json
from typing import NamedTuple

from app.api.v1.analytics import router as analytics_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.delivery import router as delivery_router
from app.api.v1.gitread import router as gitread_router
from app.api.v1.notification_channels import router as notification_channels_router
from app.api.v1.notifications import router as notifications_router
from app.api.v1.projects import router as projects_router
from app.api.v1.quality import router as quality_router
from app.api.v1.search import router as search_router
from app.api.v1.structure import router as structure_router
from fastapi.testclient import TestClient

# Routers covering every Phase-B gate + the AC2 read-regression set.
ROUTERS = (
    projects_router,
    structure_router,
    delivery_router,
    quality_router,
    notification_channels_router,
    notifications_router,
    gitread_router,
    dashboard_router,
    analytics_router,
    search_router,
)


class Gate(NamedTuple):
    """One gated route: id, HTTP method, router-relative path, (action,
    resource) pair, JSON body (``None`` = no body), setup-chain resources
    a positive call needs to exist first. Path/body ``{key}`` placeholders
    resolve from the chain (or to ``"missing"`` dummies for denials)."""

    id: str
    method: str
    path: str
    action: str
    resource: str
    body: dict | None
    needs: tuple[str, ...]


# Data table — deliberately one row per gate; kept unformatted (fmt: off)
# so the inventory stays diffable line-by-line against the task file.
# fmt: off
GATES: tuple[Gate, ...] = (
    Gate("structure-component-create", "post", "/projects/{project}/components", "create", "component", {"name": "Gate-Comp"}, ("project",)),
    Gate("structure-component-update", "patch", "/components/{component}", "update", "component", {"name": "Gate-Comp-2"}, ("component",)),
    Gate("structure-component-delete", "delete", "/components/{component}", "delete", "component", None, ("component",)),
    Gate("structure-module-create", "post", "/components/{component}/modules", "create", "module", {"name": "Gate-Mod"}, ("component",)),
    Gate("structure-module-update", "patch", "/modules/{module}", "update", "module", {"name": "Gate-Mod-2"}, ("module",)),
    Gate("structure-module-delete", "delete", "/modules/{module}", "delete", "module", None, ("module",)),
    Gate("delivery-feature-delete", "delete", "/features/{feature}", "delete", "feature", None, ("feature",)),
    Gate("delivery-task-bulk", "patch", "/tasks/bulk", "update", "task", {"task_ids": ["{task}"], "updates": {"priority": 7}}, ("task",)),
    Gate("delivery-task-delete", "delete", "/tasks/{task}", "delete", "task", None, ("task",)),
    Gate("delivery-subtask-delete", "delete", "/subtasks/{subtask}", "delete", "subtask", None, ("subtask",)),
    Gate("quality-ac-create", "post", "/tasks/{task}/acceptance-criteria", "create", "acceptance_criteria", {"description": "Gate AC"}, ("task",)),
    Gate("quality-ac-update", "patch", "/acceptance-criteria/{ac}", "update", "acceptance_criteria", {"description": "Gate AC 2"}, ("ac",)),
    Gate("quality-ac-delete", "delete", "/acceptance-criteria/{ac}", "delete", "acceptance_criteria", None, ("ac",)),
    Gate("quality-dod-create", "post", "/tasks/{task}/dod-items", "create", "dod_item", {"name": "Gate DoD"}, ("task",)),
    Gate("quality-dod-update", "patch", "/dod-items/{dod}", "update", "dod_item", {"name": "Gate DoD 2"}, ("dod",)),
    Gate("quality-dod-delete", "delete", "/dod-items/{dod}", "delete", "dod_item", None, ("dod",)),
    Gate("quality-task-complete", "post", "/tasks/{task}/complete", "update", "task", {}, ("task",)),
    Gate("quality-submit-review", "post", "/tasks/{task_ip}/submit-review", "create", "review_round", {}, ("task_ip",)),
    Gate("quality-evidence-create", "post", "/tasks/{task}/evidence", "create", "evidence", {"type": "test", "title": "Gate Ev", "created_by_type": "human", "created_by_id": "gate"}, ("task",)),
    Gate("quality-evidence-agent-verify", "post", "/evidence/{evidence}/agent-verify", "update", "evidence", {}, ("evidence",)),
    Gate("quality-evidence-human-accept", "post", "/evidence/{evidence}/human-accept", "update", "evidence", {}, ("evidence",)),
    Gate("quality-evidence-reject", "post", "/evidence/{evidence}/reject", "update", "evidence", {"reason": "gate"}, ("evidence",)),
    Gate("quality-evidence-upload", "post", "/tasks/{task}/evidence/upload", "create", "evidence", None, ("task",)),
    Gate("quality-round-create", "post", "/tasks/{task}/review-rounds", "create", "review_round", {"reviewer_type": "human", "reviewer_id": "gate-rev"}, ("task",)),
    Gate("quality-round-start", "post", "/review-rounds/{round}/start", "update", "review_round", {}, ("round",)),
    Gate("quality-finding-create", "post", "/review-rounds/{round}/findings", "create", "review_finding", {"severity": "minor", "category": "other", "message": "Gate finding"}, ("round",)),
    Gate("quality-verdict", "post", "/review-rounds/{round_started}/verdict", "update", "review_round", {"verdict": "approve", "confidence": 90, "summary": "Gate verdict"}, ("round_started",)),
    Gate("channel-create", "post", "/notification-channels", "create", "notification_channel", {"channel_type": "webhook", "name": "Gate-CH", "config": {"url": "https://hooks.example.test/gate"}}, ()),
    Gate("channel-update", "patch", "/notification-channels/{channel}", "update", "notification_channel", {"name": "Gate-CH-2"}, ("channel",)),
    Gate("channel-delete", "delete", "/notification-channels/{channel}", "delete", "notification_channel", None, ("channel",)),
    Gate("channel-toggle", "post", "/notification-channels/{channel}/toggle", "update", "notification_channel", {}, ("channel",)),
    Gate("channel-test", "post", "/notification-channels/{channel}/test", "update", "notification_channel", {}, ("channel",)),
    Gate("gitread-provider-create", "post", "/projects/{project}/git-providers", "create", "git_provider", {"name": "Gate-GP", "provider_type": "local", "url": "/tmp/gate-repo"}, ("project",)),
    Gate("gitread-provider-update", "patch", "/git-providers/{provider}", "update", "git_provider", {"name": "Gate-GP-2"}, ("provider",)),
    Gate("gitread-provider-delete", "delete", "/git-providers/{provider}", "delete", "git_provider", None, ("provider",)),
    Gate("gitread-link-delete", "delete", "/git-links/{link}", "delete", "git_link", None, ("link",)),
)
# fmt: on

DUMMY_IDS: dict[str, str] = {
    k: "missing"
    for k in (
        "project",
        "component",
        "module",
        "feature",
        "task",
        "task_ip",
        "subtask",
        "ac",
        "dod",
        "evidence",
        "round",
        "round_started",
        "channel",
        "provider",
        "link",
    )
}
_MULTIPART_SUFFIX = "/evidence/upload"


def _subst(text: str, ids: dict[str, str]) -> str:
    """``{key}`` replacement without str.format (bodies may contain braces)."""
    for key, value in ids.items():
        text = text.replace("{" + key + "}", value)
    return text


def call_gate(client: TestClient, gate: Gate, headers: dict, ids: dict[str, str]):
    """Issue the gate's request; ``ids`` are DUMMY_IDS for denial cases."""
    path = "/api/v1" + _subst(gate.path, ids)  # gate paths are router-relative
    kwargs: dict = {"headers": headers}
    if gate.path.endswith(_MULTIPART_SUFFIX):
        kwargs["files"] = {"file": ("gate.txt", b"gate evidence", "text/plain")}
        kwargs["data"] = {"title": "Gate upload"}
    elif gate.body is not None:
        kwargs["json"] = json.loads(_subst(json.dumps(gate.body), ids))
    return getattr(client, gate.method)(path, **kwargs)


class Chain:
    """Lazy resource chain for positive calls; built through a superuser client."""

    def __init__(self, client: TestClient, admin_headers: dict) -> None:
        self._c, self._h, self._made = client, admin_headers, {}

    def id(self, key: str) -> str:
        if key not in self._made:
            self._made[key] = self._make(key)
        return self._made[key]

    def _post(self, path: str, body: dict) -> dict:
        resp = self._c.post(path, json=body, headers=self._h)
        assert resp.status_code in (200, 201), f"chain {path}: {resp.status_code} {resp.text[:200]}"
        return resp.json()

    def _make(self, key: str) -> str:
        if key == "project":
            return self._post("/api/v1/projects", {"name": "Gate-Proj"})["id"]
        if key == "component":
            return self._post(
                f"/api/v1/projects/{self.id('project')}/components", {"name": "Gate-Comp"}
            )["id"]
        if key == "module":
            return self._post(
                f"/api/v1/components/{self.id('component')}/modules", {"name": "Gate-Mod"}
            )["id"]
        if key == "feature":
            return self._post(
                f"/api/v1/projects/{self.id('project')}/features", {"name": "Gate-Feat"}
            )["id"]
        if key == "task":
            return self._post(
                f"/api/v1/features/{self.id('feature')}/tasks", {"title": "Gate-Task"}
            )["id"]
        if key == "task_ip":
            return self._post(
                f"/api/v1/features/{self.id('feature')}/tasks",
                {"title": "Gate-Task-IP", "status": "in_progress"},
            )["id"]
        if key == "subtask":
            return self._post(f"/api/v1/tasks/{self.id('task')}/subtasks", {"title": "Gate-Sub"})[
                "id"
            ]
        if key == "ac":
            return self._post(
                f"/api/v1/tasks/{self.id('task')}/acceptance-criteria", {"description": "Gate AC"}
            )["id"]
        if key == "dod":
            return self._post(f"/api/v1/tasks/{self.id('task')}/dod-items", {"name": "Gate DoD"})[
                "id"
            ]
        if key == "evidence":
            return self._post(
                f"/api/v1/tasks/{self.id('task')}/evidence",
                {
                    "type": "test",
                    "title": "Gate Ev",
                    "created_by_type": "human",
                    "created_by_id": "gate",
                },
            )["id"]
        if key == "round":
            return self._post(
                f"/api/v1/tasks/{self.id('task')}/review-rounds",
                {"reviewer_type": "human", "reviewer_id": "gate-rev"},
            )["id"]
        if key == "round_started":
            round_id = self.id("round")
            resp = self._c.post(f"/api/v1/review-rounds/{round_id}/start", headers=self._h)
            assert resp.status_code == 200, (
                f"chain start round: {resp.status_code} {resp.text[:200]}"
            )
            return round_id
        if key == "channel":
            return self._post(
                "/api/v1/notification-channels",
                {
                    "channel_type": "webhook",
                    "name": "Gate-CH",
                    "config": {"url": "https://hooks.example.test/gate"},
                },
            )["id"]
        if key == "provider":
            return self._post(
                f"/api/v1/projects/{self.id('project')}/git-providers",
                {"name": "Gate-GP", "provider_type": "local", "url": "/tmp/gate-repo"},
            )["id"]
        if key == "link":
            return self._post(
                "/api/v1/git-links",
                {
                    "entity_type": "task",
                    "entity_id": "gate-entity",
                    "git_type": "provider",
                    "git_id": "gate-provider",
                },
            )["id"]
        raise AssertionError(f"unknown chain resource {key}")
