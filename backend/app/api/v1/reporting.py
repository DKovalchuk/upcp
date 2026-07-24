import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.reporting.models import Report
from app.reporting.schemas import ReportResponse, ReportSummary
from app.reporting.service import ReportingService
from app.shared.database import get_session
from app.shared.errors import NotFound
from app.shared.pagination import PaginationParams, pagination_dependency

logger = logging.getLogger(__name__)

router = APIRouter(tags=["reports"])


@router.post("/projects/{project_id}/reports/daily", response_model=ReportResponse, status_code=201)
def generate_daily_report(
    project_id: str,
    session: Session = Depends(get_session),  # noqa: B008
) -> ReportResponse:
    """Generate a daily report for a project."""
    service = ReportingService(session)
    report = service.generate_daily_report(project_id)
    return ReportResponse(
        id=report.id,
        project_id=report.project_id,
        report_type=report.report_type,
        content=report.content,
        summary=report.summary,
        created_at=report.created_at.isoformat(),
    )


@router.get("/reports/{report_id}", response_model=ReportResponse)
def get_report(
    report_id: str,
    session: Session = Depends(get_session),  # noqa: B008
) -> ReportResponse:
    """Get a report by ID."""
    service = ReportingService(session)
    report = service.get_report(report_id)
    if not report:
        raise NotFound(f"Report {report_id} not found")
    return ReportResponse(
        id=report.id,
        project_id=report.project_id,
        report_type=report.report_type,
        content=report.content,
        summary=report.summary,
        created_at=report.created_at.isoformat(),
    )


@router.get("/reports/{report_id}/markdown")
def export_report_markdown(
    report_id: str,
    session: Session = Depends(get_session),  # noqa: B008
) -> dict[str, str]:
    """Export a report as markdown."""
    service = ReportingService(session)
    report = service.get_report(report_id)
    if not report:
        raise NotFound(f"Report {report_id} not found")
    
    # Generate markdown from report content
    markdown = _generate_markdown(report)
    return {"markdown": markdown}


@router.post("/reports/{report_id}/summarize", response_model=ReportSummary)
def summarize_report(
    report_id: str,
    session: Session = Depends(get_session),  # noqa: B008
) -> ReportSummary:
    """Generate an LLM summary for a report."""
    from app.llm.gateway import LLMGateway
    from app.llm.redaction import Redactor
    from app.shared.errors import ValidationError
    
    service = ReportingService(session)
    report = service.get_report(report_id)
    if not report:
        raise NotFound(f"Report {report_id} not found")
    
    # Check if LLM is enabled
    try:
        gateway = LLMGateway()
    except ValueError as e:
        raise ValidationError(str(e)) from e
    
    if not gateway.is_enabled:
        raise ValidationError("LLM is not enabled in configuration")
    
    # Prepare text for summarization
    text = ""
    if report.content:
        # Convert report content to text
        if "project_name" in report.content:
            text += f"Project: {report.content['project_name']}\n"
        if "task_counts" in report.content and isinstance(report.content["task_counts"], dict):
            text += "Task counts:\n"
            for status, count in report.content["task_counts"].items():
                text += f"  - {status}: {count}\n"
        if "recent_changes" in report.content and isinstance(report.content["recent_changes"], list):
            text += "Recent changes:\n"
            for change in report.content["recent_changes"]:
                if isinstance(change, dict):
                    text += f"  - {change.get('title', 'Unknown')} ({change.get('status', 'unknown')})\n"
    
    if not text:
        raise ValidationError("Report has no content to summarize")
    
    # Redact secrets before sending to LLM
    redactor = Redactor()
    redaction_result = redactor.redact(text)
    
    if redaction_result.redaction_count > 0:
        logger.warning(f"Redacted {redaction_result.redaction_count} secrets before LLM summarization")
    
    # Generate summary using LLM
    try:
        summary = gateway.generate_summary(redaction_result.redacted_text)
    except NotImplementedError:
        raise ValidationError("LLM provider is not configured") from None
    except ValueError as e:
        raise ValidationError(str(e)) from e
    except Exception as e:
        raise ValidationError(f"LLM error: {str(e)}") from e
    
    # Update report with summary
    service.update_report_summary(report_id, summary)
    
    return ReportSummary(summary=summary)


@router.get("/projects/{project_id}/reports")
def list_project_reports(
    project_id: str,
    pagination: PaginationParams = Depends(pagination_dependency),  # noqa: B008
    session: Session = Depends(get_session),  # noqa: B008
) -> dict[str, object]:
    """List reports for a project."""
    service = ReportingService(session)
    reports, total = service.list_reports(
        project_id=project_id,
        offset=pagination.offset,
        limit=pagination.limit,
    )
    items = [
        {
            "id": r.id,
            "project_id": r.project_id,
            "report_type": r.report_type,
            "content": r.content,
            "summary": r.summary,
            "created_at": r.created_at.isoformat(),
        }
        for r in reports
    ]
    return {"items": items, "total": total, "offset": pagination.offset, "limit": pagination.limit}


def _generate_markdown(report: Report) -> str:
    """Generate markdown from report content."""
    lines = []
    lines.append(f"# {report.report_type.title()} Report")
    lines.append("")
    
    # Add project name if available in content
    if report.content and "project_name" in report.content:
        lines.append(f"**Project:** {report.content['project_name']}")
    else:
        lines.append(f"**Project ID:** {report.project_id}")
    
    lines.append(f"**Generated:** {report.created_at.isoformat()}")
    lines.append("")

    if report.content:
        # Task counts
        if "task_counts" in report.content and isinstance(report.content["task_counts"], dict):
            lines.append("## Task Status Summary")
            lines.append("")
            for status, count in report.content["task_counts"].items():
                lines.append(f"- **{status}**: {count}")
            lines.append("")

        # Recent changes
        if "recent_changes" in report.content and isinstance(report.content["recent_changes"], list):
            lines.append("## Recent Changes")
            lines.append("")
            for change in report.content["recent_changes"]:
                if isinstance(change, dict):
                    lines.append(f"- **{change.get('title', 'Unknown')}** ({change.get('status', 'unknown')}) - {change.get('updated_at', 'Unknown')}")
            lines.append("")

        # Blockers
        if "blockers" in report.content and isinstance(report.content["blockers"], list):
            lines.append("## Blockers")
            lines.append("")
            for blocker in report.content["blockers"]:
                lines.append(f"- {blocker}")
            lines.append("")

    if report.summary:
        lines.append("## Summary")
        lines.append("")
        lines.append(report.summary)
        lines.append("")

    return "\n".join(lines)