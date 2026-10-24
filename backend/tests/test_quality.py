import tempfile
from unittest.mock import patch

from app.api.v1.delivery import router as delivery_router
from app.api.v1.projects import router as projects_router
from app.api.v1.quality import router as quality_router
from app.api.v1.structure import router as structure_router
from app.shared.database import Base, get_session
from app.shared.errors import register_error_handlers
from fastapi import FastAPI
from fastapi.testclient import TestClient

from tests.conftest import _test_engine as _engine

# Shared engine/session from conftest (TASK-0112 engine dedup).
from tests.conftest import _TestSession as _Session


def _override():
    s = _Session()
    try:
        yield s
        s.commit()
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()


_upload_tmp = tempfile.mkdtemp(prefix="upcp_test_uploads_")


def _app() -> FastAPI:
    Base.metadata.drop_all(bind=_engine)
    Base.metadata.create_all(bind=_engine)
    app = FastAPI()
    register_error_handlers(app)
    app.include_router(projects_router, prefix="/api/v1")
    app.include_router(structure_router, prefix="/api/v1")
    app.include_router(delivery_router, prefix="/api/v1")
    app.include_router(quality_router, prefix="/api/v1")
    app.dependency_overrides[get_session] = _override
    return app


def _task_id(c: TestClient) -> str:
    pid = c.post("/api/v1/projects", json={"name": "P"}).json()["id"]
    fid = c.post(f"/api/v1/projects/{pid}/features", json={"name": "F"}).json()["id"]
    return c.post(f"/api/v1/features/{fid}/tasks", json={"title": "T"}).json()["id"]


# ── Acceptance Criterion ──


def test_create_ac() -> None:
    c = TestClient(_app())
    tid = _task_id(c)
    resp = c.post(f"/api/v1/tasks/{tid}/acceptance-criteria", json={"description": "Must work"})
    assert resp.status_code == 201
    assert resp.json()["status"] == "pending"


def test_update_ac_status() -> None:
    c = TestClient(_app())
    tid = _task_id(c)
    acid = c.post(f"/api/v1/tasks/{tid}/acceptance-criteria", json={"description": "X"}).json()[
        "id"
    ]
    resp = c.patch(f"/api/v1/acceptance-criteria/{acid}", json={"status": "passed"})
    assert resp.json()["status"] == "passed"


def test_delete_ac() -> None:
    c = TestClient(_app())
    tid = _task_id(c)
    acid = c.post(f"/api/v1/tasks/{tid}/acceptance-criteria", json={"description": "X"}).json()[
        "id"
    ]
    assert c.delete(f"/api/v1/acceptance-criteria/{acid}").status_code == 204


def test_list_acs() -> None:
    c = TestClient(_app())
    tid = _task_id(c)
    c.post(f"/api/v1/tasks/{tid}/acceptance-criteria", json={"description": "A"})
    c.post(f"/api/v1/tasks/{tid}/acceptance-criteria", json={"description": "B"})
    body = c.get(f"/api/v1/tasks/{tid}/acceptance-criteria").json()
    assert len(body["items"]) == 2
    assert body["total"] == 2


# ── DoD Item ──


def test_create_dod() -> None:
    c = TestClient(_app())
    tid = _task_id(c)
    resp = c.post(f"/api/v1/tasks/{tid}/dod-items", json={"name": "Tests pass"})
    assert resp.status_code == 201
    assert resp.json()["status"] == "pending"


def test_update_dod_status() -> None:
    c = TestClient(_app())
    tid = _task_id(c)
    did = c.post(f"/api/v1/tasks/{tid}/dod-items", json={"name": "X"}).json()["id"]
    resp = c.patch(f"/api/v1/dod-items/{did}", json={"status": "passed"})
    assert resp.json()["status"] == "passed"


def test_delete_dod() -> None:
    c = TestClient(_app())
    tid = _task_id(c)
    did = c.post(f"/api/v1/tasks/{tid}/dod-items", json={"name": "X"}).json()["id"]
    assert c.delete(f"/api/v1/dod-items/{did}").status_code == 204


def test_list_dods() -> None:
    c = TestClient(_app())
    tid = _task_id(c)
    c.post(f"/api/v1/tasks/{tid}/dod-items", json={"name": "A"})
    body = c.get(f"/api/v1/tasks/{tid}/dod-items").json()
    assert len(body["items"]) == 1
    assert body["total"] == 1


# ── Quality Gate ──


def test_complete_task_with_all_dod_passed() -> None:
    c = TestClient(_app())
    tid = _task_id(c)
    did = c.post(f"/api/v1/tasks/{tid}/dod-items", json={"name": "X"}).json()["id"]
    c.patch(f"/api/v1/dod-items/{did}", json={"status": "passed"})
    resp = c.post(f"/api/v1/tasks/{tid}/complete")
    assert resp.status_code == 200
    assert resp.json()["status"] == "done"


def test_complete_task_fails_when_dod_not_passed() -> None:
    c = TestClient(_app())
    tid = _task_id(c)
    c.post(f"/api/v1/tasks/{tid}/dod-items", json={"name": "X"})
    resp = c.post(f"/api/v1/tasks/{tid}/complete")
    assert resp.status_code == 400


def test_complete_task_without_dod_succeeds() -> None:
    c = TestClient(_app())
    tid = _task_id(c)
    resp = c.post(f"/api/v1/tasks/{tid}/complete")
    assert resp.status_code == 200
    assert resp.json()["status"] == "done"


# ── Evidence File Upload ──


def test_upload_evidence_file() -> None:
    c = TestClient(_app())
    tid = _task_id(c)
    from app.shared.config import Settings

    mock_settings = Settings()
    mock_settings.upload_dir = _upload_tmp
    mock_settings.max_upload_size_bytes = 10 * 1024 * 1024
    with patch("app.api.v1.quality.get_settings", return_value=mock_settings):
        resp = c.post(
            f"/api/v1/tasks/{tid}/evidence/upload",
            data={"title": "Test upload"},
            files={"file": ("test.txt", b"hello evidence", "text/plain")},
        )
    assert resp.status_code == 201
    body = resp.json()
    assert body["type"] == "file"
    assert body["file_name"] == "test.txt"
    assert body["file_size"] == 14


def test_upload_evidence_rejects_bad_type() -> None:
    c = TestClient(_app())
    tid = _task_id(c)
    from app.shared.config import Settings

    mock_settings = Settings()
    mock_settings.upload_dir = _upload_tmp
    mock_settings.max_upload_size_bytes = 10 * 1024 * 1024
    with patch("app.api.v1.quality.get_settings", return_value=mock_settings):
        resp = c.post(
            f"/api/v1/tasks/{tid}/evidence/upload",
            data={"title": "bad"},
            files={"file": ("hack.exe", b"MZ", "application/octet-stream")},
        )
    assert resp.status_code == 422


def test_upload_evidence_rejects_oversized() -> None:
    c = TestClient(_app())
    tid = _task_id(c)
    big = b"x" * (11 * 1024 * 1024)
    from app.shared.config import Settings

    mock_settings = Settings()
    mock_settings.upload_dir = _upload_tmp
    mock_settings.max_upload_size_bytes = 10 * 1024 * 1024
    with patch("app.api.v1.quality.get_settings", return_value=mock_settings):
        resp = c.post(
            f"/api/v1/tasks/{tid}/evidence/upload",
            data={"title": "big"},
            files={"file": ("big.pdf", big, "application/pdf")},
        )
    assert resp.status_code == 422


def test_upload_evidence_task_not_found() -> None:
    c = TestClient(_app())
    from app.shared.config import Settings

    mock_settings = Settings()
    mock_settings.upload_dir = _upload_tmp
    mock_settings.max_upload_size_bytes = 10 * 1024 * 1024
    with patch("app.api.v1.quality.get_settings", return_value=mock_settings):
        resp = c.post(
            "/api/v1/tasks/nonexistent/evidence/upload",
            data={"title": "test"},
            files={"file": ("test.txt", b"data", "text/plain")},
        )
    # Nonexistent task → 404: EvidenceService validates task existence
    # before file I/O (TASK-0112; formerly accepted as 201 orphan rows
    # on FK-off sqlite engines, then 500 under the shared FK-on engine).
    assert resp.status_code == 404
