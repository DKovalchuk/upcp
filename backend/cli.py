"""Typer CLI for UPCP."""
import typer
from app.delivery.service import TaskService
from app.projects.service import ProjectService
from app.shared.database import SessionLocal

app = typer.Typer(name="upcp", help="UPCP CLI - Universal Project Control Plane")
session = SessionLocal()


@app.command()
def status() -> None:
    """Show UPCP status."""
    typer.echo("UPCP Status")
    typer.echo("Service: upcp-backend")
    typer.echo("Status: running")


project_app = typer.Typer(help="Project commands")
app.add_typer(project_app, name="project")


@project_app.command("list")
def project_list(
    offset: int = typer.Option(0, help="Offset for pagination"),
    limit: int = typer.Option(20, help="Limit for pagination"),
) -> None:
    """List all projects."""
    service = ProjectService(session)
    projects, total = service.list_projects(offset=offset, limit=limit)
    typer.echo(f"Projects ({total} total):")
    for p in projects:
        typer.echo(f"  - {p.name} ({p.slug}) [{p.status}]")


@project_app.command("get")
def project_get(project_id: str = typer.Argument(..., help="Project ID")) -> None:
    """Get project by ID."""
    service = ProjectService(session)
    try:
        project = service.get(project_id)
        typer.echo(f"Project: {project.name}")
        typer.echo(f"  Slug: {project.slug}")
        typer.echo(f"  Status: {project.status}")
        typer.echo(f"  Description: {project.description or 'No description'}")
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None


task_app = typer.Typer(help="Task commands")
app.add_typer(task_app, name="task")


@task_app.command("list")
def task_list(
    feature_id: str = typer.Argument(..., help="Feature ID"),
    offset: int = typer.Option(0, help="Offset for pagination"),
    limit: int = typer.Option(20, help="Limit for pagination"),
) -> None:
    """List tasks for a feature."""
    service = TaskService(session)
    tasks, total = service.list_tasks(feature_id, offset=offset, limit=limit)
    typer.echo(f"Tasks ({total} total):")
    for t in tasks:
        typer.echo(f"  - [{t.status}] {t.title} (priority: {t.priority})")


@task_app.command("get")
def task_get(task_id: str = typer.Argument(..., help="Task ID")) -> None:
    """Get task by ID."""
    service = TaskService(session)
    try:
        task = service.get(task_id)
        typer.echo(f"Task: {task.title}")
        typer.echo(f"  Status: {task.status}")
        typer.echo(f"  Priority: {task.priority}")
        typer.echo(f"  Description: {task.description or 'No description'}")
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None


if __name__ == "__main__":
    app()