from app.shared.ids import EntityId
from app.shared.schemas import ErrorResponse, HealthResponse


def test_error_response_schema() -> None:
    resp = ErrorResponse(error="not_found", detail="project not found")
    data = resp.model_dump()
    assert data["error"] == "not_found"
    assert data["detail"] == "project not found"


def test_health_response_schema() -> None:
    resp = HealthResponse(
        status="ok",
        service="upcp-backend",
        db={"status": "ok", "latency_ms": 1.23},
        redis={"status": "ok"},
    )
    data = resp.model_dump()
    assert data["status"] == "ok"
    assert data["service"] == "upcp-backend"
    assert data["db"]["status"] == "ok"
    assert data["db"]["latency_ms"] == 1.23
    assert data["redis"]["status"] == "ok"


def test_entity_id_is_str() -> None:
    eid = EntityId("abc-123")
    assert str(eid) == "abc-123"


def test_entity_id_type_alias() -> None:
    eid: EntityId = EntityId("proj-1")
    assert eid == "proj-1"
