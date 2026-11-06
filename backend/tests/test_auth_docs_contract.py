"""Auth docs ↔ code route contract — SPEC-0027 §3.4 finding 4 / TASK-0148.

Doc-literal half of the retired ``tests/test_public_paths.py`` (TASK-0170
deleted that file together with the ``PUBLIC_PATHS`` dictionary): paths the
auth doc documents as ```METHOD /path``` must equal real code routes
(finding 4: docs claimed ``/api/v1/auth/*`` which does not exist).

The dead-exemption half («every PUBLIC_PATHS entry resolves to a route»)
died with the dictionary itself — publicness is declared in
``app/api/registry.py`` and covered by ``test_api_surface_registry.py`` /
``test_auth_enumeration.py`` (SPEC-0028 D2/AC1).
"""

from __future__ import annotations

import re
from pathlib import Path

_DOCS = Path(__file__).resolve().parents[2] / "docs" / "security" / "auth-rbac.md"
_DOC_PATH_RE = re.compile(r"`(?:POST|GET)\s+(/[^`\s]+)`")


def _registered_paths() -> set[str]:
    """OpenAPI paths — FastAPI 0.138 keeps ``include_router`` results as lazy
    ``_IncludedRouter`` wrappers without ``.path``; the generated schema is the
    public, stable enumeration of registered routes (docs/redoc/openapi.json
    are not part of it)."""
    from app.main import app

    return set(app.openapi()["paths"])


def test_auth_docs_paths_match_code_routes() -> None:
    """Doc-literal (AC4): documented `METHOD /path` strings == real routes."""
    docs = _DOCS.read_text(encoding="utf-8")
    doc_paths = set(_DOC_PATH_RE.findall(docs))
    routes = _registered_paths()

    assert "/auth/logout" in doc_paths, "docs must document the real logout path"
    assert "/auth/logout" in routes, "code must expose /auth/logout"
    phantom = sorted(p for p in doc_paths if p not in routes)
    assert not phantom, f"docs document paths the code does not serve: {phantom}"
