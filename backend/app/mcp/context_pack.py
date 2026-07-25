"""Context pack generator for AI agents."""

from typing import Any

from app.delivery.service import TaskService
from app.gitread.service import GitLinkService
from app.projects.service import ProjectService
from app.shared.database import SessionLocal


class ContextPackGenerator:
    """Generate markdown context packs for AI agents."""

    def generate_project_context(
        self,
        project_id: str,
        session: Any | None = None,
    ) -> str:
        """Generate context pack for a project.

        If *session* is provided it is used directly (FastAPI DI).
        Otherwise a new SessionLocal is created for backward compatibility.
        """
        own_session = session is None
        sess = session if session is not None else SessionLocal()
        try:
            project_service = ProjectService(sess)
            project = project_service.get(project_id)

            # Get tasks via project features
            task_service = TaskService(sess)
            tasks, _ = task_service.list_tasks_by_project(project_id, limit=100)

            # Get git links
            git_service = GitLinkService(sess)
            git_links = git_service.list_by_entity("project", project_id)

            # Build markdown
            lines = [
                f"# Project: {project.name}",
                "",
                f"**Slug:** {project.slug}",
                f"**Status:** {project.status}",
                f"**Description:** {project.description or 'No description'}",
                "",
                "## Tasks",
                "",
            ]

            if tasks:
                for task in tasks:
                    lines.append(f"- [{task.status}] {task.title} (priority: {task.priority})")
            else:
                lines.append("No tasks found.")

            lines.extend(["", "## Git Links", ""])

            if git_links:
                for link in git_links:
                    lines.append(f"- {link.git_type}: {link.git_id}")
            else:
                lines.append("No git links.")

            lines.extend(
                [
                    "",
                    "## Context Pack Generated",
                    "",
                    "This context pack provides a summary of the project for AI agents.",
                    "Use this information to understand the project structure and status.",
                ]
            )

            return "\n".join(lines)
        finally:
            if own_session:
                sess.close()


def get_context_pack(project_id: str | None = None) -> str:
    """Get context pack for a project or default."""
    if project_id:
        generator = ContextPackGenerator()
        return generator.generate_project_context(project_id)
    else:
        return "# Context Pack\n\nNo project selected."
