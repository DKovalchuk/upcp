"""SubjectStateService — SPEC-0029 §3.3 / TASK-0174 (red → green).

Cache-aside subject lookup extracted from ``middleware._user_state`` —
D4 parity, outcomes identical for the three states. Contract: key
``auth:user:{user_id}``, TTL 60 s; hit → return (no DB, no write-back);
miss / corrupt / outage → DB via ``UserRepository`` + best-effort write;
DB failure on a miss propagates (a state cannot be invented), while a
cache HIT still answers with the DB down; a corrupt value (not one of
active|unknown|disabled) = miss + rewrite (the
``permissions._resolve_user_permissions`` parse-fail precedent — recorded
deviation from middleware's verbatim-garbage→401; see task evidence).

AC3 cache-spy: cold call = 1 DB read + 1 cache write; warm = 0 reads.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Iterator
from uuid import uuid4

import app.shared.redis as shared_redis
import pytest
from app.identity.cache_provider import AuthCacheProvider
from app.identity.models import User
from app.identity.repositories import UserRepository
from app.identity.subject_state import _USER_STATE_TTL_SECONDS, SubjectStateService
from sqlalchemy.orm import Session


class _MemRedis:
    """In-memory redis stand-in with TTL support (no live Redis in unit tests)."""

    def __init__(self) -> None:
        self.store: dict[str, str] = {}
        self.expires: dict[str, float | None] = {}
        self.ttls: dict[str, int | None] = {}
        self.set_calls = 0

    def get(self, key: str):  # noqa: ANN201
        if key not in self.store:
            return None
        exp = self.expires.get(key)
        if exp is not None and exp <= time.time():
            self.store.pop(key, None)
            self.expires.pop(key, None)
            return None
        return self.store[key]

    def set(self, key: str, value: str, ex: int | None = None) -> None:
        self.set_calls += 1
        self.store[key] = value
        self.ttls[key] = ex
        self.expires[key] = time.time() + ex if ex else None

    def delete(self, key: str) -> None:
        self.store.pop(key, None)
        self.expires.pop(key, None)


class _BrokenRedis:
    def get(self, key: str):  # noqa: ANN201
        raise ConnectionError("redis down")

    def set(self, key: str, value: str, ex: int | None = None) -> None:
        raise ConnectionError("redis down")


class _GetOkSetBrokenRedis(_MemRedis):
    """Reads work, writes fail — partial outage must still serve states."""

    def set(self, key: str, value: str, ex: int | None = None) -> None:
        raise ConnectionError("redis write down")


class _SpyUserRepository:
    """Counting stub — the AC3 cache-spy asserts exact DB-read counts."""

    def __init__(self, state: str = "active", error: Exception | None = None) -> None:
        self.state = state
        self.error = error
        self.calls: list[str] = []

    def get_auth_state(self, user_id: str) -> str:
        self.calls.append(user_id)
        if self.error is not None:
            raise self.error
        return self.state


class _ExplodingCache:
    """Violates the provider's never-raise contract — service must still cope."""

    def get(self, key: str) -> str:
        raise ConnectionError("cache exploded")

    def set(self, key: str, value: str, ttl_seconds: int) -> None:
        raise ConnectionError("cache exploded")


@pytest.fixture()
def mem_redis(monkeypatch: pytest.MonkeyPatch) -> Iterator[_MemRedis]:
    fake = _MemRedis()
    monkeypatch.setattr(shared_redis, "get_redis_client", lambda: fake)
    yield fake


def _key(user_id: str) -> str:
    return f"auth:user:{user_id}"


def _seed_user(db: Session, *, active: bool) -> str:
    user = User(
        email=f"ss-{uuid4().hex[:10]}@test.local",
        password_hash="x" * 60,
        display_name="SS",
        is_active=active,
    )
    db.add(user)
    db.commit()
    return str(user.id)


# ── AC3: cache policy — cold read, warm hit, exact counts ───────────


def test_cold_then_warm_cache_spy(mem_redis: _MemRedis) -> None:
    """Cold: exactly 1 DB read + 1 cache write (TTL 60); warm: 0 DB reads."""
    assert _USER_STATE_TTL_SECONDS == 60, "SPEC-0027 §3.2 TTL contract"
    repo = _SpyUserRepository(state="active")
    service = SubjectStateService(repo, AuthCacheProvider())
    uid = str(uuid4())

    assert service.get(uid) == "active"
    assert repo.calls == [uid], f"cold call must read the DB once, got {repo.calls}"
    assert mem_redis.store[_key(uid)] == "active"
    assert mem_redis.ttls[_key(uid)] == 60
    assert mem_redis.set_calls == 1

    assert service.get(uid) == "active"
    assert repo.calls == [uid], f"warm call re-queried the DB: {repo.calls}"
    assert mem_redis.set_calls == 1, "a hit must not write the cache again"


def test_cache_hit_returns_without_db_read(mem_redis: _MemRedis) -> None:
    """Pre-warmed cache → served verbatim, repository never invoked."""
    uid = str(uuid4())
    mem_redis.store[_key(uid)] = "disabled"
    repo = _SpyUserRepository(state="active")
    service = SubjectStateService(repo, AuthCacheProvider())

    assert service.get(uid) == "disabled"
    assert repo.calls == []


@pytest.mark.parametrize("state", ["unknown", "disabled"])
def test_negative_states_are_cached(state: str, mem_redis: _MemRedis) -> None:
    """Negative caching parity: unknown/disabled are stored like active."""
    repo = _SpyUserRepository(state=state)
    service = SubjectStateService(repo, AuthCacheProvider())
    uid = str(uuid4())

    assert service.get(uid) == state
    assert mem_redis.store[_key(uid)] == state
    assert service.get(uid) == state
    assert len(repo.calls) == 1


def test_expired_cache_entry_falls_through_to_db(mem_redis: _MemRedis) -> None:
    """TTL edge: an entry past its TTL reads as a miss → DB + rewrite."""
    uid = str(uuid4())
    mem_redis.store[_key(uid)] = "active"
    mem_redis.expires[_key(uid)] = time.time() - 1  # expired one second ago
    repo = _SpyUserRepository(state="disabled")
    service = SubjectStateService(repo, AuthCacheProvider())

    assert service.get(uid) == "disabled"
    assert repo.calls == [uid]
    assert mem_redis.store[_key(uid)] == "disabled"


def test_corrupt_cache_value_falls_back_to_db_and_rewrites(mem_redis: _MemRedis) -> None:
    """Parse-fail boundary (permissions._resolve_user_permissions precedent):
    garbage is not a state → treat as miss, DB wins, cache rewritten."""
    uid = str(uuid4())
    mem_redis.store[_key(uid)] = "not-a-state"
    repo = _SpyUserRepository(state="active")
    service = SubjectStateService(repo, AuthCacheProvider())

    assert service.get(uid) == "active"
    assert repo.calls == [uid]
    assert mem_redis.store[_key(uid)] == "active"


# ── Outage directions: cache down → DB; DB down → cache/propagate ───


def test_redis_outage_falls_back_to_db_and_warns(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """AC3/AC5: Redis unreachable → correctness from the DB, no exception,
    structured warning; nothing can be cached, so every call re-reads."""
    monkeypatch.setattr(shared_redis, "get_redis_client", lambda: _BrokenRedis())
    repo = _SpyUserRepository(state="active")
    service = SubjectStateService(repo, AuthCacheProvider())
    uid = str(uuid4())

    with caplog.at_level(logging.WARNING, logger="app.identity.cache_provider"):
        assert service.get(uid) == "active"
        assert service.get(uid) == "active"

    assert repo.calls == [uid, uid], "outage must not bypass the DB"
    actions = [getattr(r, "action", "") for r in caplog.records]
    assert "auth.cache_get_failed" in actions, f"missing get warning: {actions}"
    assert "auth.cache_set_failed" in actions, f"missing set warning: {actions}"


def test_write_failure_still_returns_state(monkeypatch: pytest.MonkeyPatch) -> None:
    """Partial outage: reads miss, writes fail — state still served."""
    monkeypatch.setattr(shared_redis, "get_redis_client", lambda: _GetOkSetBrokenRedis())
    repo = _SpyUserRepository(state="disabled")
    service = SubjectStateService(repo, AuthCacheProvider())
    uid = str(uuid4())

    assert service.get(uid) == "disabled"
    assert repo.calls == [uid]


def test_exploding_cache_stub_never_breaks_service(caplog: pytest.LogCaptureFixture) -> None:
    """Service-level guarantee (brief): ANY cache failure → DB, even a
    cache impl that violates the provider's never-raise contract."""
    repo = _SpyUserRepository(state="active")
    service = SubjectStateService(repo, _ExplodingCache())  # type: ignore[arg-type]
    uid = str(uuid4())

    with caplog.at_level(logging.WARNING, logger="app.identity.subject_state"):
        assert service.get(uid) == "active"

    assert repo.calls == [uid]
    actions = [getattr(r, "action", "") for r in caplog.records]
    assert "auth.subject_state_cache_unavailable" in actions, actions


def test_dead_db_directions(mem_redis: _MemRedis) -> None:
    """DB down (both fallback directions): a miss PROPAGATES — the state
    cannot be invented (parity: ``_user_state`` raises too) — while a warm
    cache still answers without touching the DB."""
    repo = _SpyUserRepository(error=RuntimeError("db down"))
    service = SubjectStateService(repo, AuthCacheProvider())
    uid = str(uuid4())

    with pytest.raises(RuntimeError, match="db down"):
        service.get(uid)
    assert repo.calls == [uid]
    mem_redis.store[_key(uid)] = "active"
    assert service.get(uid) == "active"
    assert repo.calls == [uid], "a cache hit must not touch the dead DB"


# ── Integration: real DB via the repository seam, both cache states ─


def test_integration_real_db_fake_cache(db_session: Session, mem_redis: _MemRedis) -> None:
    """Real repo + fake Redis: cold → DB+write; warm → cache-only (user
    deleted in between); evicted → DB again (authoritative)."""
    uid = _seed_user(db_session, active=True)
    service = SubjectStateService(UserRepository(), AuthCacheProvider())

    assert service.get(uid) == "active"
    assert mem_redis.store[_key(uid)] == "active"

    db_session.query(User).filter_by(id=uid).delete()
    db_session.commit()
    assert service.get(uid) == "active", "within TTL the cache must answer alone"

    mem_redis.delete(_key(uid))  # TTL expiry / eviction
    assert service.get(uid) == "unknown", "DB is authoritative after eviction"
    assert mem_redis.store[_key(uid)] == "unknown"


def test_integration_broken_cache_real_db(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Redis down + real DB: every state comes from the DB, warning logged."""
    monkeypatch.setattr(shared_redis, "get_redis_client", lambda: _BrokenRedis())
    active_uid = _seed_user(db_session, active=True)
    disabled_uid = _seed_user(db_session, active=False)
    service = SubjectStateService(UserRepository(), AuthCacheProvider())

    with caplog.at_level(logging.WARNING, logger="app.identity.cache_provider"):
        assert service.get(active_uid) == "active"
        assert service.get(disabled_uid) == "disabled"
        assert service.get(str(uuid4())) == "unknown"

    actions = [getattr(r, "action", "") for r in caplog.records]
    assert "auth.cache_get_failed" in actions, actions
