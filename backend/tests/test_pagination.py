from app.shared.pagination import PaginatedResponse, PaginationParams, pagination_dependency
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient


def test_pagination_defaults() -> None:
    app = FastAPI()

    @app.get("/items")
    def list_items(p: PaginationParams = Depends(pagination_dependency)) -> dict[str, int]:  # noqa: B008
        return {"offset": p.offset, "limit": p.limit}

    client = TestClient(app)
    resp = client.get("/items")
    assert resp.status_code == 200
    body = resp.json()
    assert body["offset"] == 0
    assert body["limit"] == 20


def test_pagination_custom_params() -> None:
    app = FastAPI()

    @app.get("/items")
    def list_items(p: PaginationParams = Depends(pagination_dependency)) -> dict[str, int]:  # noqa: B008
        return {"offset": p.offset, "limit": p.limit}

    client = TestClient(app)
    resp = client.get("/items?offset=10&limit=5")
    body = resp.json()
    assert body["offset"] == 10
    assert body["limit"] == 5


def test_pagination_limit_rejects_over_max() -> None:
    app = FastAPI()

    @app.get("/items")
    def list_items(p: PaginationParams = Depends(pagination_dependency)) -> dict[str, int]:  # noqa: B008
        return {"offset": p.offset, "limit": p.limit}

    client = TestClient(app, raise_server_exceptions=False)
    resp = client.get("/items?limit=9999")
    assert resp.status_code == 422


def test_paginated_response_schema() -> None:
    resp = PaginatedResponse(
        items=[{"id": "1"}],
        total=1,
        offset=0,
        limit=20,
    )
    data = resp.model_dump()
    assert data["items"] == [{"id": "1"}]
    assert data["total"] == 1
