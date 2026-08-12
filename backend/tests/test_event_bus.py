"""Tests for the in-process event bus."""

from unittest.mock import MagicMock

from app.shared.events import EventBus


class TestEventBus:
    def test_publish_calls_subscribed_handler(self) -> None:
        bus = EventBus()
        handler = MagicMock()
        bus.subscribe("task.created", handler)

        bus.publish("task.created", task_id="t1", title="Test")

        handler.assert_called_once_with(event_type="task.created", task_id="t1", title="Test")

    def test_publish_no_handler_is_noop(self) -> None:
        bus = EventBus()
        bus.publish("unknown.event", data="x")

    def test_multiple_handlers_called(self) -> None:
        bus = EventBus()
        h1 = MagicMock()
        h2 = MagicMock()
        bus.subscribe("test.event", h1)
        bus.subscribe("test.event", h2)

        bus.publish("test.event", value=42)

        h1.assert_called_once()
        h2.assert_called_once()

    def test_handler_error_does_not_break_other_handlers(self) -> None:
        bus = EventBus()
        bad = MagicMock(side_effect=RuntimeError("boom"))
        good = MagicMock()
        bus.subscribe("test.event", bad)
        bus.subscribe("test.event", good)

        bus.publish("test.event", x=1)

        good.assert_called_once()

    def test_unsubscribe(self) -> None:
        bus = EventBus()
        handler = MagicMock()
        bus.subscribe("test.event", handler)
        bus.unsubscribe("test.event", handler)

        bus.publish("test.event")

        handler.assert_not_called()

    def test_clear_removes_all_handlers(self) -> None:
        bus = EventBus()
        h1 = MagicMock()
        h2 = MagicMock()
        bus.subscribe("a", h1)
        bus.subscribe("b", h2)
        bus.clear()

        bus.publish("a")
        bus.publish("b")

        h1.assert_not_called()
        h2.assert_not_called()

    def test_handler_receives_all_kwargs(self) -> None:
        bus = EventBus()
        received = {}

        def capture(**kwargs):
            received.update(kwargs)

        bus.subscribe("test", capture)

        bus.publish("test", session="s1", entity_type="task", entity_id="t1")

        assert received["event_type"] == "test"
        assert received["session"] == "s1"
        assert received["entity_type"] == "task"
        assert received["entity_id"] == "t1"
