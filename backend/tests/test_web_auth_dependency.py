"""web_auth dependency — SPEC-0028 S28.2 / TASK-0169 (red → green).

Default-deny for the web surface as a FastAPI route dependency: the 401
shapes are byte-parity with ``AuthMiddleware``'s JWT branch (missing /
invalid / denylisted / dead subject), the subject-rejection observability
(metric + structured warning + span attrs) is copied from
``middleware._reject_subject``, and the whole synchronous pipeline runs
in ONE ``run_in_threadpool`` hop (S28.2 — unlike the middleware's
blocking in-loop I/O).

``web_auth`` is imported at module level on purpose: before the
implementation exists the RED phase is a collection error for this file.
"""

from __future__ import annotations

import hashlib
import logging
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import app.shared.redis as shared_redis
import httpx
import jwt
import pytest
from app.identity.auth import _get_token_service
from app.identity.models import User
from app.identity.token_service import TokenService
from app.identity.web_auth import web_auth
from app.shared.config import get_settings
from app.shared.database import Base
from app.shared.metrics import auth_subject_rejections_total, auth_token_denials_total
from fastapi import Depends, FastAPI, Request
from fastapi.testclient import TestClient

from tests.conftest import _test_engine, _TestSession

TS = TokenService(secret_key="web-auth-test-secret")
_SECRET = "web-auth-test-secret"
_PATH = "/api/v1/protected"
_MISSING = "Missing authentication token"
_INVALID = "Invalid or expired token"


# ── Fakes/seams ──────────────────────────────────────────────────────


class _MemRedis:
    """In-memory redis stand-in — denylist + auth:user cache."""

    def __init__(self) -> None:
        self.store: dict[str, str] = {}
        self.ttls: dict[str, int | None] = {}

    def get(self, key: str):  # noqa: ANN001
        return self.store.get(key)

    def set(self, key: str, value: str, ex: int | None = None) -> None:  # noqa: ANN001
        self.store[key] = value
        self.ttls[key] = ex


class _BrokenRedis:
    """Redis refuses connections — the AC5 fail-open path."""

    def get(self, key: str):  # noqa: ANN001
        raise ConnectionError("redis down")

    def set(self, key: str, value: str, ex: int | None = None) -> None:  # noqa: ANN001
        raise ConnectionError("redis down")


class _RecordingSpan:
    """Span spy: records set_attributes without a real tracer."""

    def __init__(self) -> None:
        self.attributes: dict[str, object] = {}

    def is_recording(self) -> bool:
        return True

    def set_attributes(self, attributes: dict[str, object]) -> None:
        self.attributes.update(attributes)


def _enable_auth(monkeypatch: pytest.MonkeyPatch) -> None:
    """conftest defaults disable_auth=true (hermetic) — the guard must be ON."""
    monkeypatch.setattr(get_settings(), "disable_auth", False)


def _seed_subject(*, active: bool) -> str:
    Base.metadata.create_all(bind=_test_engine)
    session = _TestSession()
    try:
        user = User(
            email=f"wa-{uuid4().hex[:10]}@webauth.local",
            password_hash="x" * 60,
            display_name="WA",
            is_active=active,
        )
        session.add(user)
        session.commit()
        return str(user.id)
    finally:
        session.close()


def _cleanup_subjects() -> None:
    session = _TestSession()
    try:
        session.query(User).filter(User.email.like("wa-%@webauth.local")).delete()
        session.commit()
    finally:
        session.close()


def _rejection_count(reason: str) -> float:
    return float(auth_subject_rejections_total.labels(reason=reason)._value.get())


def _denial_count() -> float:
    return float(auth_token_denials_total.labels(reason="logout")._value.get())


def _deny_key(token: str) -> str:
    return "auth:deny:" + hashlib.sha256(token.encode()).hexdigest()


def _sub_of(token: str) -> str:
    payload = jwt.decode(token, _SECRET, algorithms=["HS256"], options={"verify_exp": False})
    return str(payload["sub"])


def _build_app() -> FastAPI:
    """App-level blanket (raw routes, no public part) — SPEC-0028 D2."""
    app = FastAPI(dependencies=[Depends(web_auth)])
    app.dependency_overrides[_get_token_service] = lambda: TS

    @app.get(_PATH)
    async def protected(request: Request) -> dict:
        return {
            "user_id": getattr(request.state, "user_id", None),
            "auth_type": getattr(request.state, "auth_type", None),
            "api_surface": getattr(request.state, "api_surface", None),
        }

    return app


@pytest.fixture()
def web_client(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    """web_auth active (disable_auth flipped off) + test-secret token service."""
    _enable_auth(monkeypatch)
    Base.metadata.create_all(bind=_test_engine)  # cleanup below needs the table
    yield TestClient(_build_app())
    _cleanup_subjects()


@pytest.fixture()
def inert_client() -> Iterator[TestClient]:
    """Same app, hermetic flag left ON — the dependency must be a no-op."""
    Base.metadata.create_all(bind=_test_engine)
    yield TestClient(_build_app())
    _cleanup_subjects()


def _get(client: TestClient, token: str | None = None) -> httpx.Response:
    headers = {"Authorization": f"Bearer {token}"} if token is not None else {}
    return client.get(_PATH, headers=headers)


# ── Shapes: missing / invalid / expired ──────────────────────────────


def test_missing_header_401_shape(web_client: TestClient) -> None:
    resp = _get(web_client)
    assert resp.status_code == 401, resp.text
    assert resp.json() == {"detail": _MISSING}
    assert resp.headers.get("www-authenticate") == "Bearer"


@pytest.mark.parametrize(
    "header",
    ["Basic dXNlcjpwYXNz", "Bearer", "bearer lower-case-scheme"],
    ids=["basic-scheme", "bearer-no-space", "case-sensitive"],
)
def test_non_bearer_authorization_treated_as_missing(web_client: TestClient, header: str) -> None:
    """Parity with the middleware's startswith('Bearer ') check (byte-for-byte)."""
    resp = web_client.get(_PATH, headers={"Authorization": header})
    assert resp.status_code == 401, resp.text
    assert resp.json() == {"detail": _MISSING}
    assert resp.headers.get("www-authenticate") == "Bearer"


@pytest.mark.parametrize(
    "token",
    ["not-a-jwt", ""],
    ids=["garbage", "empty-after-prefix"],
)
def test_invalid_token_401_shape(web_client: TestClient, token: str) -> None:
    resp = _get(web_client, token)
    assert resp.status_code == 401, resp.text
    assert resp.json() == {"detail": _INVALID}
    assert resp.headers.get("www-authenticate") == "Bearer"


def test_expired_token_401_shape(web_client: TestClient) -> None:
    """Expiry is rejected before liveness — active subject, still 401 invalid."""
    sub = _seed_subject(active=True)
    token = TS.create_access_token(sub, expires_delta=timedelta(seconds=-1))
    resp = _get(web_client, token)
    assert resp.status_code == 401, resp.text
    assert resp.json() == {"detail": _INVALID}
    assert resp.headers.get("www-authenticate") == "Bearer"


# ── Denylist (SPEC-0027 §3.3) ────────────────────────────────────────


def test_denylisted_token_401_with_observability(
    web_client: TestClient, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """Logout-denylisted token → invalid shape + note_denied_token telemetry.

    Ordering pin: the denylist check runs BEFORE subject liveness, so the
    subject-rejection metric must not move on this path.
    """
    fake = _MemRedis()
    monkeypatch.setattr(shared_redis, "get_redis_client", lambda: fake)
    token = TS.create_access_token(str(uuid4()))
    fake.store[_deny_key(token)] = "1"

    subject_before = _rejection_count("unknown")
    denials_before = _denial_count()
    with caplog.at_level(logging.WARNING):
        resp = _get(web_client, token)

    assert resp.status_code == 401, resp.text
    assert resp.json() == {"detail": _INVALID}
    assert resp.headers.get("www-authenticate") == "Bearer"
    assert _denial_count() == denials_before + 1, "note_denied_token must bump the metric"
    assert _rejection_count("unknown") == subject_before, "denylist must reject before liveness"
    actions = [getattr(r, "action", "") for r in caplog.records]
    assert "auth.token_denied" in actions, actions
    assert token not in caplog.text, "AC11: the raw access token must never be logged"


# ── Subject liveness (SPEC-0027 §3.2) + observability ────────────────


def test_unknown_subject_401_observability(
    web_client: TestClient, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """Valid JWT, never-existing subject → invalid shape + full telemetry copy."""
    import opentelemetry.trace as otel_trace

    span = _RecordingSpan()
    monkeypatch.setattr(otel_trace, "get_current_span", lambda: span)

    sub = str(uuid4())
    token = TS.create_access_token(sub)
    before = _rejection_count("unknown")
    with caplog.at_level(logging.WARNING):
        resp = _get(web_client, token)

    assert resp.status_code == 401, resp.text
    assert resp.json() == {"detail": _INVALID}
    assert resp.headers.get("www-authenticate") == "Bearer"
    assert _rejection_count("unknown") == before + 1, "metric must count the rejection"

    warnings = [r for r in caplog.records if r.levelno >= logging.WARNING]
    rejected = [r for r in warnings if getattr(r, "action", "") == "auth.subject_rejected"]
    assert rejected, [getattr(r, "action", r.getMessage()) for r in warnings]
    assert rejected[0].entity_type == "jwt_subject"
    assert f"subject={sub}" in rejected[0].getMessage()
    assert "state=unknown" in rejected[0].getMessage()
    assert token not in caplog.text, "AC11: the raw access token must never be logged"
    assert span.attributes == {
        "upcp.auth.subject_rejected": True,
        "upcp.auth.subject_state": "unknown",
        "upcp.auth.sub": sub,
    }


def test_disabled_subject_401_with_metric(
    web_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """is_active=False → same invalid shape, reason=disabled counted."""
    sub = _seed_subject(active=False)
    before = _rejection_count("disabled")
    resp = _get(web_client, TS.create_access_token(sub))
    assert resp.status_code == 401, resp.text
    assert resp.json() == {"detail": _INVALID}
    assert resp.headers.get("www-authenticate") == "Bearer"
    assert _rejection_count("disabled") == before + 1


def test_empty_subject_401(web_client: TestClient) -> None:
    """Boundary: signed token with sub='' → liveness miss → 401 invalid."""
    now = datetime.now(UTC)
    token = str(
        jwt.encode(
            {
                "sub": "",
                "type": "access",
                "jti": str(uuid4()),
                "iat": now,
                "exp": now + timedelta(minutes=15),
            },
            _SECRET,
            algorithm="HS256",
        )
    )
    resp = _get(web_client, token)
    assert resp.status_code == 401, resp.text
    assert resp.json() == {"detail": _INVALID}


# ── Success path ─────────────────────────────────────────────────────


def test_success_sets_request_state(web_client: TestClient) -> None:
    sub = _seed_subject(active=True)
    resp = _get(web_client, TS.create_access_token(sub))
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["user_id"] == sub
    assert body["auth_type"] == "user"
    assert body["api_surface"] == "web"


# ── Conditions: disable_auth / Redis outage / threadpool ─────────────


def test_disable_auth_keeps_dependency_inert(inert_client: TestClient) -> None:
    """AC10 hermetic kill switch: no header AND garbage header both reach the route."""
    assert get_settings().disable_auth is True, "test precondition: hermetic mode"
    assert _get(inert_client).status_code == 200
    assert _get(inert_client, "garbage").status_code == 200
    assert _get(inert_client).json()["user_id"] is None


def test_redis_outage_fails_open_and_reaches_db(
    web_client: TestClient, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """Denylist outage → fail-open (AC5) with a warning; liveness still via DB."""
    monkeypatch.setattr(shared_redis, "get_redis_client", lambda: _BrokenRedis())
    sub = _seed_subject(active=True)
    with caplog.at_level(logging.WARNING):
        resp = _get(web_client, TS.create_access_token(sub))
    assert resp.status_code == 200, (
        f"denylist outage must fail open, got {resp.status_code}: {resp.text[:200]}"
    )
    actions = [getattr(r, "action", "") for r in caplog.records]
    assert "auth.denylist_unavailable" in actions, actions


def test_sync_pipeline_runs_in_threadpool(
    web_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """S28.2 performance rule: ONE run_in_threadpool hop for the whole sync
    pipeline; the header fast-path (no I/O) never enters the threadpool."""
    import app.identity.web_auth as web_auth_mod

    real = web_auth_mod.run_in_threadpool
    calls = {"n": 0}

    async def counting(func, *args, **kwargs):  # noqa: ANN001, ANN202
        calls["n"] += 1
        return await real(func, *args, **kwargs)

    monkeypatch.setattr(web_auth_mod, "run_in_threadpool", counting)

    assert _get(web_client).status_code == 401  # missing header → no pipeline
    assert calls["n"] == 0, "the header fast-path must not pay for a thread hop"

    sub = _seed_subject(active=True)
    assert _get(web_client, TS.create_access_token(sub)).status_code == 200
    assert calls["n"] == 1, f"exactly one threadpool hop per authorized request, got {calls['n']}"
