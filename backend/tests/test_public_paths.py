"""PUBLIC_PATHS + auth-docs contracts — SPEC-0027 §3.4 / TASK-0148.

Finding 5: ``PUBLIC_PATHS`` listed ``/mcp/health``, which is not a
registered route (404) — an exemption that can never be served.
Regression: every PUBLIC_PATHS entry must resolve to a route on the real
app (static docs allowlisted); plus a doc-literal contract — paths the
auth doc documents as ```METHOD /path` `` must equal the code routes
(finding 4: docs claimed ``/api/v1/auth/*`` which does not exist).
"""

from __future__ import annotations

import re
from pathlib import Path

from app.identity.middleware import PUBLIC_PATHS

_DOCS = Path(__file__).resolve().parents[2] / "docs" / "security" / "auth-rbac.md"
# FastAPI serves these without an explicit endpoint — whitelisted per AC7
_STATIC_ALLOWLIST = {"/docs", "/redoc", "/openapi.json"}
_DOC_PATH_RE = re.compile(r"`(?:POST|GET)\s+(/[^`\s]+)`")


def _registered_paths() -> set[str]:
    """OpenAPI paths — FastAPI 0.138 keeps ``include_router`` results as lazy
    ``_IncludedRouter`` wrappers without ``.path``; the generated schema is the
    public, stable enumeration of registered routes (docs/redoc/openapi.json
    are not part of it — covered by the static allowlist, per AC7)."""
    from app.main import app

    return set(app.openapi()["paths"])


def test_every_public_path_is_a_registered_route() -> None:
    """AC7: no dead exemptions — each PUBLIC_PATHS entry must actually serve."""
    routes = _registered_paths()
    missing = {p for p in PUBLIC_PATHS if p not in routes and p not in _STATIC_ALLOWLIST}
    assert not missing, f"PUBLIC_PATHS entries without a registered route: {sorted(missing)}"
    assert "/mcp/health" not in PUBLIC_PATHS, "finding 5: dead /mcp/health must be removed"


def test_auth_docs_paths_match_code_routes() -> None:
    """Doc-literal (AC4): documented `METHOD /path` strings == real routes."""
    docs = _DOCS.read_text(encoding="utf-8")
    doc_paths = set(_DOC_PATH_RE.findall(docs))
    routes = _registered_paths()

    assert "/auth/logout" in doc_paths, "docs must document the real logout path"
    assert "/auth/logout" in routes, "code must expose /auth/logout"
    phantom = sorted(p for p in doc_paths if p not in routes)
    assert not phantom, f"docs document paths the code does not serve: {phantom}"
