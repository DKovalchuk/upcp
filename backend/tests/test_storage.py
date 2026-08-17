"""Tests for file storage adapter and upload validation."""

from pathlib import Path

import pytest
from app.shared.storage import LocalStorageAdapter, validate_upload


class TestValidateUpload:
    def test_valid_pdf(self):
        assert validate_upload("report.pdf", 1024) is None

    def test_valid_image(self):
        assert validate_upload("photo.jpg", 5000) is None

    def test_valid_json(self):
        assert validate_upload("data.json", 200) is None

    def test_disallowed_extension(self):
        err = validate_upload("malware.exe", 100)
        assert err is not None
        assert "not allowed" in err

    def test_disallowed_script(self):
        err = validate_upload("script.sh", 100)
        assert err is not None

    def test_too_large(self):
        err = validate_upload("big.pdf", 11 * 1024 * 1024)
        assert err is not None
        assert "too large" in err

    def test_exactly_max_size(self):
        assert validate_upload("exact.pdf", 10 * 1024 * 1024) is None

    def test_empty_filename_ext(self):
        err = validate_upload("noext", 100)
        assert err is not None


class TestLocalStorageAdapter:
    @pytest.fixture
    def adapter(self, tmp_path):
        return LocalStorageAdapter(base_dir=str(tmp_path))

    @pytest.mark.asyncio
    async def test_save_creates_file(self, adapter, tmp_path):
        path = await adapter.save("test.txt", b"hello world")
        assert Path(path).exists()
        assert Path(path).read_bytes() == b"hello world"

    @pytest.mark.asyncio
    async def test_save_returns_unique_names(self, adapter):
        p1 = await adapter.save("a.txt", b"one")
        p2 = await adapter.save("a.txt", b"two")
        assert p1 != p2

    @pytest.mark.asyncio
    async def test_delete_removes_file(self, adapter):
        path = await adapter.save("deleteme.txt", b"bye")
        assert Path(path).exists()
        await adapter.delete(path)
        assert not Path(path).exists()

    @pytest.mark.asyncio
    async def test_delete_nonexistent_is_noop(self, adapter):
        await adapter.delete("/nonexistent/file.txt")  # should not raise
