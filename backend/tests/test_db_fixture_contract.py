"""Local `_db` fixture hermeticity contract — TASK-0159 Finding 3 (xdist).

CI runs `pytest backend/tests -n auto`; workers share the test engine/file.
A fixture that only `create_all`s inherits ANOTHER worker's committed rows
(create_all on existing tables is a no-op) — observed as
`UNIQUE constraint failed: project.slug ('test')` in pipeline #508
(test_stale_reaper) even after fe4835d fixed the shared conftest `_db`.

Canonical pattern (conftest): `drop_all` BEFORE `create_all` at setup.
Teardown drops are tolerated but never a substitute — teardown runs after
the damage and races other workers. This contract sweeps every local `_db`
fixture in backend/tests so the class cannot regress file-by-file.
"""

from __future__ import annotations

import re
from pathlib import Path

_TESTS_DIR = Path(__file__).resolve().parent


def _db_fixture_bodies(source: str) -> list[tuple[int, str]]:
    """(start_line, body) per `_db` fixture — body runs until the next
    top-level def/class/decorator."""
    bodies: list[tuple[int, str]] = []
    lines = source.splitlines()
    for i, line in enumerate(lines):
        if "def _db(" not in line:
            continue
        body_lines = [line]
        for follow in lines[i + 1 :]:
            if re.match(r"^(def |class |@)", follow):
                break
            body_lines.append(follow)
        bodies.append((i + 1, "\n".join(body_lines)))
    return bodies


def test_every_local_db_fixture_drops_before_create() -> None:
    """drop_all must precede create_all at setup of every `_db` fixture."""
    # Compare STATEMENT positions (Base.metadata.*_all) so prose/comments
    # mentioning the calls cannot mask or fake an ordering violation.
    stmt = re.compile(r"^\s*Base\.metadata\.(drop_all|create_all)\b", flags=re.M)
    offenders: dict[str, list[int]] = {}
    for path in sorted(_TESTS_DIR.glob("test_*.py")):
        source = path.read_text(encoding="utf-8")
        for line_no, body in _db_fixture_bodies(source):
            calls = [(m.group(1), m.start()) for m in stmt.finditer(body)]
            if not any(kind == "create_all" for kind, _ in calls):
                continue
            first_drop = next((pos for kind, pos in calls if kind == "drop_all"), None)
            first_create = next(pos for kind, pos in calls if kind == "create_all")
            if first_drop is None or first_drop > first_create:
                offenders.setdefault(path.name, []).append(line_no)

    assert not offenders, (
        "_db fixtures must drop_all BEFORE create_all at setup — with xdist the "
        "engine is shared across workers, so create-only setup inherits committed "
        "rows from another worker (UNIQUE slug 'test', CI pipeline #508). "
        f"Offenders (file: line of def _db): {offenders}"
    )
