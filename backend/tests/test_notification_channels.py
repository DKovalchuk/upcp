"""Tests for notification channels — TASK-0101."""

import pytest
from app.reporting.channel_service import ChannelService
from app.reporting.channels.email import EmailChannel
from app.reporting.channels.webhook import WebhookChannel
from app.reporting.models import Notification, NotificationChannel, NotificationDelivery
from app.shared.database import Base
from app.shared.errors import NotFound, ValidationError
from app.shared.text import new_id
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(bind=engine)
    session = TestSession()
    yield session
    session.close()
    engine.dispose()


# ── Model Tests ──────────────────────────────────────────────


class TestNotificationChannelModel:
    def test_create_channel(self, db_session: Session):
        ch = NotificationChannel(
            id=new_id(),
            channel_type="email",
            name="Dev Alerts",
            config={
                "smtp_host": "smtp.example.com",
                "smtp_port": 587,
                "from_address": "a@b.com",
                "to_address": "c@d.com",
            },
            is_active=True,
        )
        db_session.add(ch)
        db_session.commit()
        assert ch.id
        assert ch.channel_type == "email"
        assert ch.is_active is True

    def test_create_delivery(self, db_session: Session):
        notif = Notification(
            id=new_id(),
            user_id="u1",
            type="test",
            title="T",
            message="M",
        )
        ch = NotificationChannel(
            id=new_id(),
            channel_type="webhook",
            name="WH",
            config={"url": "https://hook.example.com"},
            is_active=True,
        )
        db_session.add_all([notif, ch])
        db_session.flush()

        delivery = NotificationDelivery(
            id=new_id(),
            notification_id=notif.id,
            channel_id=ch.id,
            status="sent",
        )
        db_session.add(delivery)
        db_session.commit()
        assert delivery.status == "sent"
        assert delivery.notification_id == notif.id


# ── Channel Implementation Tests ─────────────────────────────


class TestEmailChannel:
    def test_validate_config_missing_fields(self):
        ch = EmailChannel()
        with pytest.raises(ValueError, match="Missing required"):
            ch.validate_config({})

    def test_validate_config_invalid_port(self):
        ch = EmailChannel()
        with pytest.raises(ValueError, match="smtp_port must be an integer"):
            ch.validate_config(
                {
                    "smtp_host": "smtp.example.com",
                    "smtp_port": "not-a-port",
                    "from_address": "a@b.com",
                    "to_address": "c@d.com",
                }
            )

    def test_validate_config_valid(self):
        ch = EmailChannel()
        ch.validate_config(
            {
                "smtp_host": "smtp.example.com",
                "smtp_port": 587,
                "from_address": "a@b.com",
                "to_address": "c@d.com",
            }
        )


class TestWebhookChannel:
    def test_validate_config_missing_url(self):
        ch = WebhookChannel()
        with pytest.raises(ValueError, match="Missing required"):
            ch.validate_config({})

    def test_validate_config_invalid_url(self):
        ch = WebhookChannel()
        with pytest.raises(ValueError, match="must start with http"):
            ch.validate_config({"url": "ftp://bad"})

    def test_validate_config_valid(self):
        ch = WebhookChannel()
        ch.validate_config({"url": "https://hooks.example.com"})


# ── Service Tests ────────────────────────────────────────────


class TestChannelService:
    def test_create_and_list(self, db_session: Session):
        svc = ChannelService(db_session)
        ch = svc.create(
            "email",
            "Test Email",
            {
                "smtp_host": "smtp.example.com",
                "smtp_port": 587,
                "from_address": "a@b.com",
                "to_address": "c@d.com",
            },
        )
        assert ch.name == "Test Email"
        channels = svc.list_all()
        assert len(channels) == 1

    def test_create_invalid_type(self, db_session: Session):
        svc = ChannelService(db_session)
        with pytest.raises(ValidationError):
            svc.create("sms", "SMS", {})

    def test_get_not_found(self, db_session: Session):
        svc = ChannelService(db_session)
        with pytest.raises(NotFound):
            svc.get("nonexistent")

    def test_delete(self, db_session: Session):
        svc = ChannelService(db_session)
        ch = svc.create("webhook", "WH", {"url": "https://example.com"})
        svc.delete(ch.id)
        assert len(svc.list_all()) == 0

    def test_toggle_active(self, db_session: Session):
        svc = ChannelService(db_session)
        ch = svc.create("webhook", "WH", {"url": "https://example.com"})
        assert ch.is_active is True
        ch2 = svc.toggle_active(ch.id)
        assert ch2.is_active is False
