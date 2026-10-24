"""API tests for notification channels PATCH — TASK-0109 (AC4: edit channel)."""

from app.api.v1.notification_channels import router as channels_router
from app.reporting.models import NotificationChannel  # noqa: F401
from app.shared.database import Base, get_session
from app.shared.errors import register_error_handlers
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

_test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = sessionmaker(bind=_test_engine)


def _override_session():
    session = TestSessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def _test_app() -> FastAPI:
    Base.metadata.drop_all(bind=_test_engine)
    Base.metadata.create_all(bind=_test_engine)
    app = FastAPI()
    register_error_handlers(app)
    app.include_router(channels_router, prefix="/api/v1")
    app.dependency_overrides[get_session] = _override_session
    return app


def _create_webhook_channel(client: TestClient) -> dict:
    resp = client.post(
        "/api/v1/notification-channels",
        json={
            "channel_type": "webhook",
            "name": "Ops",
            "config": {"url": "https://hooks.example.com/a"},
        },
    )
    assert resp.status_code == 201
    return resp.json()


def test_patch_channel_name_and_config() -> None:
    """PATCH updates name and config, and the change persists."""
    client = TestClient(_test_app())
    ch = _create_webhook_channel(client)

    resp = client.patch(
        f"/api/v1/notification-channels/{ch['id']}",
        json={"name": "Ops alerts", "config": {"url": "https://hooks.example.com/b"}},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Ops alerts"
    assert data["config"] == {"url": "https://hooks.example.com/b"}

    listed = client.get("/api/v1/notification-channels").json()["items"]
    updated = next(c for c in listed if c["id"] == ch["id"])
    assert updated["name"] == "Ops alerts"
    assert updated["config"] == {"url": "https://hooks.example.com/b"}


def test_patch_channel_name_only_keeps_config() -> None:
    """PATCH with only a name leaves the config untouched."""
    client = TestClient(_test_app())
    ch = _create_webhook_channel(client)

    resp = client.patch(f"/api/v1/notification-channels/{ch['id']}", json={"name": "Ops2"})
    assert resp.status_code == 200
    assert resp.json()["config"] == {"url": "https://hooks.example.com/a"}


def test_patch_channel_not_found() -> None:
    """PATCH on an unknown channel returns 404."""
    client = TestClient(_test_app())
    resp = client.patch("/api/v1/notification-channels/nonexistent", json={"name": "x"})
    assert resp.status_code == 404


def test_patch_channel_invalid_config() -> None:
    """PATCH with a config failing channel validation returns 422."""
    client = TestClient(_test_app())
    ch = _create_webhook_channel(client)

    resp = client.patch(f"/api/v1/notification-channels/{ch['id']}", json={"config": {}})
    assert resp.status_code == 422
