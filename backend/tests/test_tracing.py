"""Tests for distributed tracing."""


class TestTracing:
    def test_get_tracer_returns_tracer(self) -> None:
        from app.shared.tracing import get_tracer

        tracer = get_tracer("test")
        assert tracer is not None

    def test_tracer_creates_span(self) -> None:
        from app.shared.tracing import get_tracer

        tracer = get_tracer("test-span")
        with tracer.start_as_current_span("test-operation") as span:
            span.set_attribute("test.key", "test-value")
            assert span.is_recording()


class TestTracingMiddleware:
    def test_middleware_allows_requests(self) -> None:
        from app.shared.tracing_middleware import TracingMiddleware
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        app = FastAPI()
        app.add_middleware(TracingMiddleware)

        @app.get("/test")
        async def test_route() -> dict:
            return {"ok": True}

        client = TestClient(app)
        resp = client.get("/test")
        assert resp.status_code == 200
        assert resp.json() == {"ok": True}
