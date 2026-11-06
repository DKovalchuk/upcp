"""Tests for Evidence file upload — TASK-0116 (S22.2)."""

from __future__ import annotations

import io
import uuid

import pytest
from app.delivery.models import Feature, Task  # noqa: F401
from app.projects.models import Project  # noqa: F401
from app.quality.service import EvidenceService
from app.shared.database import Base
from app.shared.errors import NotFound, ValidationError
from starlette.datastructures import Headers, UploadFile

from tests.conftest import _test_engine, _TestSession


@pytest.fixture()
def _db():
    import app.audit.models  # noqa: F401
    import app.delivery.models  # noqa: F401
    import app.gitread.models  # noqa: F401
    import app.identity.agents  # noqa: F401
    import app.identity.models  # noqa: F401
    import app.identity.rbac  # noqa: F401
    import app.projects.models  # noqa: F401
    import app.quality.models  # noqa: F401
    import app.reporting.models  # noqa: F401
    import app.structure.models  # noqa: F401

    Base.metadata.drop_all(bind=_test_engine)
    Base.metadata.create_all(bind=_test_engine)
    yield
    Base.metadata.drop_all(bind=_test_engine)


@pytest.fixture()
def session(_db):
    s = _TestSession()
    try:
        yield s
        s.rollback()
    finally:
        s.close()


@pytest.fixture()
def task_id(session) -> str:
    """Create a project + feature + task and return the task ID."""
    prefix = uuid.uuid4().hex[:6]
    p = Project(name=f"P-{prefix}", slug=f"p-{prefix}")
    session.add(p)
    session.flush()
    f = Feature(project_id=p.id, name=f"F-{prefix}", slug=f"f-{prefix}")
    session.add(f)
    session.flush()
    t = Task(feature_id=f.id, title=f"T-{prefix}", status="in_progress")
    session.add(t)
    session.flush()
    return t.id


def _make_upload(
    content: bytes,
    filename: str = "screenshot.png",
    content_type: str = "image/png",
) -> UploadFile:
    """Create a Starlette UploadFile from bytes."""
    headers = Headers({"content-type": content_type})
    return UploadFile(filename=filename, file=io.BytesIO(content), headers=headers)


class TestUploadFileValid:
    """Test successful file upload creates evidence with file metadata."""

    def test_upload_creates_evidence_with_file_fields(self, session, task_id):
        svc = EvidenceService(session)
        content = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100  # Fake PNG header
        upload = _make_upload(content, "test.png", "image/png")

        e = svc.upload_file(
            task_id=task_id,
            file=upload,
            title="Screenshot",
            created_by_type="human",
            created_by_id="user-1",
            storage_dir="/tmp/test-uploads",
        )

        assert e.file_name == "test.png"
        assert e.file_size == len(content)
        assert e.content_type == "image/png"
        assert e.file_path is not None
        assert e.file_path.startswith("/")
        assert e.title == "Screenshot"
        assert e.type == "file"

    def test_upload_stores_file_on_disk(self, session, task_id, tmp_path):
        svc = EvidenceService(session)
        content = b"Hello, this is a text file content."
        upload = _make_upload(content, "notes.txt", "text/plain")

        e = svc.upload_file(
            task_id=task_id,
            file=upload,
            title="Notes",
            created_by_type="human",
            created_by_id="user-1",
            storage_dir=str(tmp_path),
        )

        from pathlib import Path

        stored = Path(e.file_path)
        assert stored.exists()
        assert stored.read_bytes() == content

    def test_upload_returns_evidence_with_verification_state(self, session, task_id):
        svc = EvidenceService(session)
        upload = _make_upload(b"test", "t.txt", "text/plain")

        e = svc.upload_file(
            task_id=task_id,
            file=upload,
            title="T",
            created_by_type="human",
            created_by_id="user-1",
            storage_dir="/tmp/test-uploads",
        )

        assert e.verification_state == "unverified"
        assert e.created_by_type == "human"
        assert e.created_by_id == "user-1"


class TestUploadFileValidation:
    """Test upload validation: size, type, missing file."""

    def test_upload_rejects_oversized_file(self, session, task_id):
        svc = EvidenceService(session)
        big_content = b"\x00" * (10 * 1024 * 1024 + 1)  # 10MB + 1 byte
        upload = _make_upload(big_content, "huge.png", "image/png")

        with pytest.raises(ValidationError, match="10MB"):
            svc.upload_file(
                task_id=task_id,
                file=upload,
                title="Huge",
                created_by_type="human",
                created_by_id="user-1",
                storage_dir="/tmp/test-uploads",
                max_size_bytes=10 * 1024 * 1024,
            )

    def test_upload_rejects_disallowed_file_type(self, session, task_id):
        svc = EvidenceService(session)
        upload = _make_upload(b"MZ\x90\x00", "virus.exe", "application/x-msdownload")

        with pytest.raises(ValidationError, match="not allowed"):
            svc.upload_file(
                task_id=task_id,
                file=upload,
                title="Virus",
                created_by_type="human",
                created_by_id="user-1",
                storage_dir="/tmp/test-uploads",
            )

    def test_upload_rejects_oversized_by_extension(self, session, task_id):
        svc = EvidenceService(session)
        upload = _make_upload(b"\x00" * 50, "archive.zip", "application/zip")

        with pytest.raises(ValidationError, match="not allowed"):
            svc.upload_file(
                task_id=task_id,
                file=upload,
                title="Archive",
                created_by_type="human",
                created_by_id="user-1",
                storage_dir="/tmp/test-uploads",
            )


class TestDownloadFile:
    """Test file download returns correct data."""

    def test_download_returns_path_and_content_type(self, session, task_id, tmp_path):
        svc = EvidenceService(session)
        content = b"download me"
        upload = _make_upload(content, "doc.pdf", "application/pdf")

        e = svc.upload_file(
            task_id=task_id,
            file=upload,
            title="Doc",
            created_by_type="human",
            created_by_id="user-1",
            storage_dir=str(tmp_path),
        )

        path, ct = svc.get_file(e.id)
        assert str(path).endswith("doc.pdf") or "doc.pdf" in str(path)
        assert ct == "application/pdf"

    def test_download_nonexistent_evidence_raises(self, session):
        svc = EvidenceService(session)
        with pytest.raises(NotFound):
            svc.get_file("nonexistent-id")

    def test_download_evidence_without_file_raises(self, session, task_id):
        svc = EvidenceService(session)
        e = svc.create(
            task_id=task_id,
            type="url",
            title="URL evidence",
            created_by_type="human",
            created_by_id="user-1",
            url="https://example.com",
        )

        with pytest.raises(ValidationError, match="no file"):
            svc.get_file(e.id)
