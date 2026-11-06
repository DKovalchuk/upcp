"""AuthCacheProvider — SPEC-0029 §3.2 / TASK-0174 (red → green).

Provider contract (S29.2): the ONLY Redis access point of the auth-path
layering pilot (AC1: identity Redis access lives here + shared/redis.py);
it wraps ``app.shared.redis.get_redis_client``, imported LAZILY inside
each method so tests patch ``app.shared.redis.get_redis_client`` (the
denylist test-seam pattern), returns ``str | None`` and NEVER raises to
callers — every failure degrades to a structured warning
(``action=auth.cache_{get,set,delete}_failed``) plus a miss/no-op.

TTL/eviction policy belongs to the services (D1), not here: the provider
only forwards ``ttl_seconds`` as the Redis ``ex`` argument.
"""

from __future__ import annotations

import logging
from collections.abc import Iterator

import app.shared.redis as shared_redis
import pytest
from app.identity.cache_provider import AuthCacheProvider

CACHE_GET_FAILED = "auth.cache_get_failed"
CACHE_SET_FAILED = "auth.cache_set_failed"
CACHE_DELETE_FAILED = "auth.cache_delete_failed"


class _MemRedis:
    """In-memory redis stand-in — hermetic tests must not need a live Redis."""

    def __init__(self) -> None:
        self.store: dict[str, object] = {}
        self.ttls: dict[str, int | None] = {}

    def get(self, key: str):  # noqa: ANN201
        return self.store.get(key)

    def set(self, key: str, value: object, ex: int | None = None) -> None:
        self.store[key] = value
        self.ttls[key] = ex

    def delete(self, key: str) -> None:
        self.store.pop(key, None)


class _BrokenRedis:
    """Redis refuses connections — the never-raise path."""

    def get(self, key: str):  # noqa: ANN201
        raise ConnectionError("redis down")

    def set(self, key: str, value: object, ex: int | None = None) -> None:
        raise ConnectionError("redis down")

    def delete(self, key: str) -> None:
        raise ConnectionError("redis down")


class _BytesRedis(_MemRedis):
    """A client without decode_responses — raw bytes on the wire."""

    def get(self, key: str):  # noqa: ANN201
        raw = self.store.get(key)
        return None if raw is None else str(raw).encode()


@pytest.fixture()
def mem_redis(monkeypatch: pytest.MonkeyPatch) -> Iterator[_MemRedis]:
    fake = _MemRedis()
    monkeypatch.setattr(shared_redis, "get_redis_client", lambda: fake)
    yield fake


def _patch_broken(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(shared_redis, "get_redis_client", lambda: _BrokenRedis())


# ── Happy path: hit / miss / bytes / TTL forwarding ─────────────────


def test_get_returns_cached_value(mem_redis: _MemRedis) -> None:
    mem_redis.store["auth:user:u1"] = "active"
    assert AuthCacheProvider().get("auth:user:u1") == "active"


def test_get_miss_returns_none(mem_redis: _MemRedis) -> None:
    assert AuthCacheProvider().get("auth:user:missing") is None


def test_get_decodes_bytes_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    """A client without decode_responses must not leak ``b'active'`` into state."""
    fake = _BytesRedis()
    fake.store["k"] = "active"
    monkeypatch.setattr(shared_redis, "get_redis_client", lambda: fake)
    assert AuthCacheProvider().get("k") == "active"


def test_set_forwards_value_and_ttl(mem_redis: _MemRedis) -> None:
    AuthCacheProvider().set("auth:user:u1", "active", 60)
    assert mem_redis.store["auth:user:u1"] == "active"
    assert mem_redis.ttls["auth:user:u1"] == 60


def test_delete_removes_key(mem_redis: _MemRedis) -> None:
    mem_redis.store["auth:user:u1"] = "active"
    AuthCacheProvider().delete("auth:user:u1")
    assert "auth:user:u1" not in mem_redis.store


# ── Never raises: outage degrades to a structured warning ───────────


def test_get_failure_returns_none_and_warns(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    _patch_broken(monkeypatch)
    with caplog.at_level(logging.WARNING, logger="app.identity.cache_provider"):
        result = AuthCacheProvider().get("auth:user:u1")
    assert result is None, "an outage must read as a cache miss, never raise"
    actions = [getattr(r, "action", "") for r in caplog.records]
    assert CACHE_GET_FAILED in actions, f"expected {CACHE_GET_FAILED}, got {actions}"


def test_set_failure_swallowed_with_warning(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    _patch_broken(monkeypatch)
    with caplog.at_level(logging.WARNING, logger="app.identity.cache_provider"):
        AuthCacheProvider().set("auth:user:u1", "active", 60)  # must not raise
    actions = [getattr(r, "action", "") for r in caplog.records]
    assert CACHE_SET_FAILED in actions, f"expected {CACHE_SET_FAILED}, got {actions}"


def test_delete_failure_swallowed_with_warning(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    _patch_broken(monkeypatch)
    with caplog.at_level(logging.WARNING, logger="app.identity.cache_provider"):
        AuthCacheProvider().delete("auth:user:u1")  # must not raise
    actions = [getattr(r, "action", "") for r in caplog.records]
    assert CACHE_DELETE_FAILED in actions, f"expected {CACHE_DELETE_FAILED}, got {actions}"


def test_lazy_redis_import_is_patched_through_shared_module(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The seam: patching ``app.shared.redis.get_redis_client`` after the
    provider module was imported still redirects it (lazy import per call)."""
    fake = _MemRedis()
    fake.store["k"] = "active"
    monkeypatch.setattr(shared_redis, "get_redis_client", lambda: fake)
    assert AuthCacheProvider().get("k") == "active"
