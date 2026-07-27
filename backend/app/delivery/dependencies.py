"""Task dependency graph utilities — TASK-0073."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.delivery.models import TaskDependency


def detect_cycle(deps: list[TaskDependency]) -> bool:
    """Detect if a set of dependencies contains a cycle.

    Uses DFS-based cycle detection on the directed graph where
    an edge task_id → blocked_by_task_id means "task is blocked by X".
    """
    graph: dict[str, set[str]] = {}
    for dep in deps:
        graph.setdefault(dep.task_id, set()).add(dep.blocked_by_task_id)
        graph.setdefault(dep.blocked_by_task_id, set())

    WHITE, GRAY, BLACK = 0, 1, 2
    color: dict[str, int] = {node: WHITE for node in graph}

    def dfs(node: str) -> bool:
        color[node] = GRAY
        for neighbor in graph.get(node, set()):
            if color.get(neighbor, WHITE) == GRAY:
                return True
            if color.get(neighbor, WHITE) == WHITE and dfs(neighbor):
                return True
        color[node] = BLACK
        return False

    return any(dfs(node) for node, c in color.items() if c == WHITE)
