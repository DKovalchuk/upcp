"""Engine deduplication invariant — TASK-0112 (AC: shared engine only).

Every hermetic backend test file must get its DB session from
``tests/conftest.py`` (``db_session`` fixture / ``_test_engine`` /
``_TestSession`` / ``make_test_app``) instead of calling
``create_engine()`` itself.

Documented exceptions (intentional multi-engine scenarios, kept per
TASK-0112 разбор «dedup vs зафиксированные исключения»):

- ``test_agent_create_commit.py`` — two engine instances prove
  cross-connection commit visibility of agent creation.
- ``test_auth_commit_before_respond.py`` — same pattern for the auth
  commit-before-respond contract.

Live suites (root ``tests/security/``, ``tests/performance/``) run
against real databases and are out of this invariant's scope.
"""

from __future__ import annotations

import ast
import pathlib

TESTS_DIR = pathlib.Path(__file__).resolve().parent

# Files allowed to create their own engines (documented above).
ALLOWED_OWN_ENGINES = frozenset(
    {
        "test_agent_create_commit.py",
        "test_auth_commit_before_respond.py",
    }
)


def _own_engine_files() -> list[str]:
    violators: list[str] = []
    for path in sorted(TESTS_DIR.rglob("test_*.py")):
        if path.name in ALLOWED_OWN_ENGINES:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        has_own_engine = any(
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "create_engine"
            for node in ast.walk(tree)
        )
        if has_own_engine:
            violators.append(str(path.relative_to(TESTS_DIR)))
    return violators


def test_all_test_files_use_shared_engine() -> None:
    """AC: engine duplication eliminated — only conftest owns engines."""
    violators = _own_engine_files()
    assert violators == [], (
        "create_engine() outside tests/conftest.py — migrate to the shared "
        f"engine (db_session/_TestSession/make_test_app) or document an "
        f"exception in ALLOWED_OWN_ENGINES. Violators: {violators}"
    )
