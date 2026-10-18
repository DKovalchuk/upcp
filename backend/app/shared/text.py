import hashlib
import re
import uuid
from datetime import UTC, datetime


def slugify(name: str) -> str:
    slug = name.lower().strip()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")
    if not slug:
        # Names without ASCII alphanumerics (e.g. "проект 1", "!!!") must
        # still produce a valid non-empty slug — deterministic so duplicate
        # names still conflict like their ASCII counterparts (TASK-0142).
        digest = hashlib.sha256(name.encode("utf-8")).hexdigest()[:8]
        slug = f"item-{digest}"
    return slug


def new_id() -> str:
    return str(uuid.uuid4())


def utcnow() -> datetime:
    return datetime.now(UTC)
