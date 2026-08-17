"""Storage adapters for file uploads."""

import logging
import os
import uuid
from pathlib import Path
from typing import Protocol

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = frozenset(
    {
        "pdf",
        "png",
        "jpg",
        "jpeg",
        "gif",
        "webp",
        "txt",
        "csv",
        "json",
        "md",
        "xml",
        "yaml",
        "yml",
    }
)
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


class StorageAdapter(Protocol):
    async def save(self, filename: str, data: bytes) -> str:
        """Save file, return stored path."""
        ...

    async def delete(self, path: str) -> None:
        """Delete file by stored path."""
        ...


class LocalStorageAdapter:
    """Local filesystem storage."""

    def __init__(self, base_dir: str | None = None) -> None:
        resolved = base_dir or os.getenv("UPCP_UPLOAD_DIR") or "data/uploads"
        self._base_dir = Path(resolved)
        self._base_dir.mkdir(parents=True, exist_ok=True)

    async def save(self, filename: str, data: bytes) -> str:
        ext = Path(filename).suffix.lower().lstrip(".")
        safe_name = f"{uuid.uuid4().hex}.{ext}"
        dest = self._base_dir / safe_name
        dest.write_bytes(data)
        logger.info("Stored upload: %s (%d bytes)", dest, len(data))
        return str(dest)

    async def delete(self, path: str) -> None:
        target = Path(path)
        if target.exists():
            target.unlink()
            logger.info("Deleted upload: %s", path)


def get_storage_adapter() -> LocalStorageAdapter:
    """Factory for storage adapter. Extend for S3 in production."""
    return LocalStorageAdapter()


def get_upload_dir() -> str:
    """Get upload directory path from env."""
    return os.getenv("UPCP_UPLOAD_DIR") or "data/uploads"


def validate_upload(filename: str, size: int) -> str | None:
    """Validate file type and size. Returns error message or None."""
    ext = Path(filename).suffix.lower().lstrip(".")
    if ext not in ALLOWED_EXTENSIONS:
        return f"File type '{ext}' not allowed. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
    if size > MAX_FILE_SIZE:
        max_mb = MAX_FILE_SIZE // (1024 * 1024)
        return f"File too large ({size // (1024 * 1024)}MB). Maximum: {max_mb}MB"
    return None
