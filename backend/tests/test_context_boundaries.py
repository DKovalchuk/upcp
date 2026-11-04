"""Context-boundary contract gate — AGENTS §5 / SPEC-0029 §3.7 (S29.7), TASK-0177.

Audits twice reported «no cross-context violations» while real violations sat
in the code (SPEC-0029 finding 9): this gate makes boundary violations a TEST
FAILURE. Stdlib ``ast`` rules (no import-linter — the existing pytest gate, no
new infra) scan every source under ``backend/app`` and are compared against an
exact BASELINE of what exists today; TASK-0176 shrinks it in the same batch.
Set-equality means NEW violations and STALE baseline entries both fail.

Rules (foreign-* compare against the module's own top-level context; ``shared``
and the context's own code are always allowed):
  foreign-model    ``app.<ctx>.models`` imported from outside ``<ctx>``
  foreign-internal another context's non-public module (public surface =
                   ``service``/``schemas``/``dependencies``/``__init__`` allowed)
  session-local    ``SessionLocal`` outside ``app/shared/`` + ``identity/repositories.py``
  redis            ``app.shared.redis``/``get_redis_client`` outside ``shared/redis.py``
                   + ``identity/cache_provider.py`` (identity files tolerated if
                   absent) + BASELINE

``task_ref`` legend: ``TASK-xxxx`` = owner task; ``backlog`` = real violation
without an owner (finding); ``—`` = structurally accepted (composition root).
Tests are exempt by design — they are what catches violations.
"""

import ast
from pathlib import Path

import pytest

from tests.context_boundary_baseline import BASELINE

APP_DIR = Path(__file__).resolve().parents[1] / "app"
PUBLIC_SURFACE = frozenset({"service", "schemas", "dependencies", "__init__"})
SESSION_ALLOWED = ("shared/", "identity/repositories.py")  # prefix, exact file
REDIS_ALLOWED = frozenset({"shared/redis.py", "identity/cache_provider.py"})


def _context_of(rel_path: str) -> str | None:
    """Top-level context of a module path relative to backend/app (None = app root)."""
    parts = rel_path.split("/")
    return parts[0] if len(parts) > 1 else None


def _app_imports(tree: ast.Module) -> list[str]:
    """Module paths of every absolute ``app.*`` import, incl. lazy/nested ones."""
    found: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.extend(a.name for a in node.names if a.name == "app" or a.name.startswith("app."))
        elif (
            isinstance(node, ast.ImportFrom)
            and node.level == 0
            and node.module
            and (node.module == "app" or node.module.startswith("app."))
        ):
            found.append(node.module)
    return found


def _foreign_model_imports(source: str, own_context: str | None) -> list[str]:
    """Rule 1: foreign ``<ctx>.models`` imports (sorted, deduped)."""
    tree = ast.parse(source)
    out: set[str] = set()
    for mod in _app_imports(tree):
        parts = mod.split(".")
        if len(parts) >= 3 and parts[2] == "models":
            out.add(mod)
        elif len(parts) == 2:  # `from app.<ctx> import models`
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module == mod:
                    out.update(f"{mod}.{a.name}" for a in node.names if a.name == "models")
    return sorted(m for m in out if m.split(".")[1] not in {own_context, "shared"})


def _foreign_internal_imports(source: str, own_context: str | None) -> list[str]:
    """Rule 2: another context's modules outside its public surface (models = rule 1)."""
    tree = ast.parse(source)
    out: set[str] = set()
    for mod in _app_imports(tree):
        parts = mod.split(".")
        if len(parts) < 3:
            continue  # `app.<ctx>` package import == __init__ surface
        other, name = parts[1], parts[2]
        if other == own_context or other == "shared" or name == "models":
            continue
        if name not in PUBLIC_SURFACE:
            out.add(mod)
    return sorted(out)


def _sessionlocal_refs(source: str, rel_path: str) -> list[int]:
    """Rule 3: line numbers referencing SessionLocal (empty inside whitelist)."""
    if any(rel_path.startswith(p) if p.endswith("/") else rel_path == p for p in SESSION_ALLOWED):
        return []
    tree = ast.parse(source)
    lines: set[int] = set()
    for node in ast.walk(tree):
        if (
            (isinstance(node, ast.Name) and node.id == "SessionLocal")
            or (isinstance(node, ast.Attribute) and node.attr == "SessionLocal")
            or (
                isinstance(node, ast.ImportFrom)
                and any(a.name == "SessionLocal" for a in node.names)
            )
        ):
            lines.add(node.lineno)
    return sorted(lines)  # docstring/comment mentions are not AST references


def _redis_refs(source: str, rel_path: str) -> list[str]:
    """Rule 4: markers for direct cache access (empty inside whitelist)."""
    if rel_path in REDIS_ALLOWED:
        return []
    tree = ast.parse(source)
    if any(m.startswith("app.shared.redis") for m in _app_imports(tree)):
        return ["app.shared.redis"]
    for node in ast.walk(tree):
        if (isinstance(node, ast.Name) and node.id == "get_redis_client") or (
            isinstance(node, ast.Attribute) and node.attr == "get_redis_client"
        ):
            return ["get_redis_client"]
    return []


def _scan(rel_path: str, source: str) -> set[tuple[str, str]]:
    """All (rule, module) violations of one backend/app module (SyntaxError propagates)."""
    own = _context_of(rel_path)
    out = {("foreign-model", m) for m in _foreign_model_imports(source, own)}
    out |= {("foreign-internal", m) for m in _foreign_internal_imports(source, own)}
    if _sessionlocal_refs(source, rel_path):
        out.add(("session-local", "SessionLocal"))
    out |= {("redis", m) for m in _redis_refs(source, rel_path)}
    return out


@pytest.mark.parametrize(
    "source,own,expected",
    [
        # positive — top-level, statement and lazy/function forms
        ("from app.delivery.models import Task", "identity", ["app.delivery.models"]),
        ("import app.delivery.models", "identity", ["app.delivery.models"]),
        (
            "def f():\n    from app.quality.models import Evidence",
            "identity",
            ["app.quality.models"],
        ),
        ("from app.delivery import models", "identity", ["app.delivery.models"]),
        # negative — own context, shared, non-models module
        ("from app.delivery.models import Task", "delivery", []),
        ("from app.shared.database import Base", "identity", []),
        ("from app.delivery.schemas import TaskCreate", "identity", []),
    ],
)
def test_foreign_model_rule(source: str, own: str | None, expected: list[str]) -> None:
    """Rule 1 detects foreign model imports in every syntactic form, and only those."""
    assert _foreign_model_imports(source, own) == expected


@pytest.mark.parametrize(
    "source,own,expected",
    [
        # positive — internal module of another context
        (
            "from app.delivery.lifecycle import validate_transition",
            "identity",
            ["app.delivery.lifecycle"],
        ),
        ("from app.identity.denylist import is_token_denied", "mcp", ["app.identity.denylist"]),
        ("from app.gitread.adapters import push_link", "delivery", ["app.gitread.adapters"]),
        # negative — public surface of another context is allowed
        ("from app.delivery.service import TaskService", "identity", []),
        ("from app.delivery.schemas import TaskCreate", "identity", []),
        ("from app.delivery.dependencies import get_task", "identity", []),
        ("from app.delivery import TaskService", "identity", []),
        # negative — own context, shared, rule-1 territory
        ("from app.delivery.lifecycle import validate_transition", "delivery", []),
        ("from app.shared.config import get_settings", "identity", []),
        ("from app.delivery.models import Task", "identity", []),
    ],
)
def test_foreign_internal_rule(source: str, own: str | None, expected: list[str]) -> None:
    """Rule 2 bans foreign internals but allows the declared public surface."""
    assert _foreign_internal_imports(source, own) == expected


def test_sessionlocal_rule_detects_references_outside_whitelist() -> None:
    """Rule 3: imports and uses count; whitelist files and prose mentions do not."""
    src = "from app.shared.database import SessionLocal\ndef f():\n    return SessionLocal()"
    assert _sessionlocal_refs(src, "identity/agent_auth.py") == [1, 3]
    assert _sessionlocal_refs(src, "mcp/tools.py") == [1, 3]
    assert _sessionlocal_refs(src, "shared/database.py") == []
    assert _sessionlocal_refs(src, "identity/repositories.py") == []  # tolerated if absent
    assert _sessionlocal_refs('"""Uses SessionLocal lazily."""', "mcp/tools.py") == []


def test_redis_rule_detects_direct_access_outside_whitelist() -> None:
    """Rule 4: importing the module or calling the client outside the whitelist fails."""
    src = "from app.shared.redis import get_redis_client\ndef f():\n    return get_redis_client()"
    assert _redis_refs(src, "identity/permissions.py") == ["app.shared.redis"]
    assert _redis_refs(src, "shared/rate_limit.py") == ["app.shared.redis"]
    assert _redis_refs(src, "shared/redis.py") == []
    assert _redis_refs(src, "identity/cache_provider.py") == []  # tolerated if absent


def test_scan_attributes_each_violation_to_its_rule() -> None:
    """Mutation check: one synthetic module exercises all four rules at once."""
    src = (
        "from app.shared.database import SessionLocal\n"
        "from app.shared.redis import get_redis_client\n"
        "from app.delivery.models import Task\n"
        "from app.delivery.lifecycle import validate_transition\n"
    )
    assert _scan("identity/synthetic.py", src) == {
        ("foreign-model", "app.delivery.models"),
        ("foreign-internal", "app.delivery.lifecycle"),
        ("session-local", "SessionLocal"),
        ("redis", "app.shared.redis"),
    }


def test_new_violation_is_not_covered_by_baseline() -> None:
    """Mutation check (AC): a violation absent from BASELINE ⇒ the gate fails."""
    fresh = {
        ("identity/synthetic.py", *key)
        for key in _scan("identity/synthetic.py", "from app.delivery.models import Task\n")
    }
    assert fresh, "synthetic violation must be detected"
    assert fresh.isdisjoint(BASELINE), "no glob-wide baseline entry may hide a new violation"


def test_baseline_entries_are_documented() -> None:
    """Every exception carries a reason and a task reference (goal 2 of the task)."""
    for (file, rule, module), (reason, task_ref) in BASELINE.items():
        assert reason.strip() and task_ref.strip(), f"undocumented: {file}/{rule}/{module}"


def test_context_boundaries_match_documented_baseline() -> None:
    """The gate: current violations == BASELINE exactly (no new, none stale)."""
    actual: set[tuple[str, str, str]] = set()
    for path in sorted(APP_DIR.rglob("*.py")):
        rel = path.relative_to(APP_DIR).as_posix()
        actual |= {(rel, *key) for key in _scan(rel, path.read_text(encoding="utf-8"))}
    new = sorted(actual - set(BASELINE))
    stale = sorted(set(BASELINE) - actual)
    assert not new, (
        f"NEW context-boundary violations (fix the import or document in BASELINE "
        f"with reason + task ref): {new}"
    )
    assert not stale, f"STALE BASELINE entries (violation gone — remove them): {stale}"
