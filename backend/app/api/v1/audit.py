import contextlib
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from app.audit.schemas import AuditEventResponse
from app.audit.service import AuditService
from app.shared.database import get_session
from app.shared.pagination import PaginationParams, pagination_dependency

router = APIRouter(tags=["audit"])


@router.get(
    "/projects/{project_id}/audit-events",
    summary="List audit events",
    description="List audit events for a project with filtering by event type, entity type, and date range.",
)
def list_audit_events(
    project_id: str,
    pagination: PaginationParams = Depends(pagination_dependency),  # noqa: B008
    session: Session = Depends(get_session),  # noqa: B008
    event_type: str | None = Query(None),
    entity_type: str | None = Query(None),
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
) -> dict[str, object]:
    """List audit events for a project with filtering and pagination."""
    service = AuditService(session)

    # Parse date strings to datetime objects
    parsed_date_from: datetime | None = None
    parsed_date_to: datetime | None = None
    if date_from:
        with contextlib.suppress(ValueError):
            parsed_date_from = datetime.fromisoformat(date_from)
    if date_to:
        with contextlib.suppress(ValueError):
            parsed_date_to = datetime.fromisoformat(date_to)

    events, total = service.list_events(
        project_id,
        event_type=event_type,
        entity_type=entity_type,
        date_from=parsed_date_from,
        date_to=parsed_date_to,
        offset=pagination.offset,
        limit=pagination.limit,
    )

    items = [
        AuditEventResponse(
            id=event.id,
            timestamp=event.timestamp.isoformat(),
            event_type=event.event_type,
            entity_type=event.entity_type,
            entity_id=event.entity_id,
            actor_type=event.actor_type,
            actor_id=event.actor_id,
            payload=event.payload,
            note=event.note,
        ).model_dump()
        for event in events
    ]

    return {
        "items": items,
        "total": total,
        "offset": pagination.offset,
        "limit": pagination.limit,
    }


@router.get(
    "/audit/export",
    summary="Export audit events",
    description="Export audit events as CSV or JSON.",
    response_model=None,
)
def export_audit_events(
    project_id: str = Query(...),
    format: str = Query("json", pattern=r"^(csv|json)$"),
    session: Session = Depends(get_session),  # noqa: B008
) -> dict[str, object] | PlainTextResponse:
    """Export all audit events for a project as CSV or JSON."""
    service = AuditService(session)
    events, _ = service.list_events(project_id, offset=0, limit=10000)

    if format == "csv":
        import csv
        import io

        output = io.StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=[
                "timestamp",
                "event_type",
                "entity_type",
                "entity_id",
                "actor_type",
                "actor_id",
                "note",
            ],
        )
        writer.writeheader()
        for e in events:
            writer.writerow(
                {
                    "timestamp": e.timestamp.isoformat(),
                    "event_type": e.event_type,
                    "entity_type": e.entity_type,
                    "entity_id": e.entity_id,
                    "actor_type": e.actor_type,
                    "actor_id": e.actor_id,
                    "note": e.note or "",
                }
            )

        return PlainTextResponse(content=output.getvalue(), media_type="text/csv")

    return {
        "items": [
            {
                "id": e.id,
                "timestamp": e.timestamp.isoformat(),
                "event_type": e.event_type,
                "entity_type": e.entity_type,
                "entity_id": e.entity_id,
                "actor_type": e.actor_type,
                "actor_id": e.actor_id,
                "note": e.note,
            }
            for e in events
        ],
        "total": len(events),
    }
