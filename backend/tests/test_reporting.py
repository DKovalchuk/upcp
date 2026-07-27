from datetime import UTC, datetime

from app.audit.models import AuditEvent  # noqa: F401

# Import all models to ensure all tables are created
from app.reporting.models import Report
from app.reporting.service import ReportingService
from app.shared.database import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def _in_memory_db() -> sessionmaker:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)


def test_report_has_required_columns() -> None:
    cols = {c.name for c in Report.__table__.columns}
    expected = {
        "id",
        "project_id",
        "report_type",
        "content",
        "summary",
        "created_at",
    }
    assert expected.issubset(cols)


def test_create_report() -> None:
    SessionLocal = _in_memory_db()
    session = SessionLocal()
    service = ReportingService(session)

    report = service.create_report(
        project_id="proj-1",
        report_type="daily",
        content={"task_counts": {"todo": 5, "done": 3}},
    )

    assert report.id is not None
    assert report.project_id == "proj-1"
    assert report.report_type == "daily"
    assert report.content == {"task_counts": {"todo": 5, "done": 3}}
    assert report.created_at <= datetime.now(UTC)
    session.close()


def test_get_report() -> None:
    SessionLocal = _in_memory_db()
    session = SessionLocal()
    service = ReportingService(session)

    report = service.create_report(
        project_id="proj-1",
        report_type="daily",
    )

    retrieved = service.get_report(report.id)
    assert retrieved is not None
    assert retrieved.id == report.id
    session.close()


def test_list_reports() -> None:
    SessionLocal = _in_memory_db()
    session = SessionLocal()
    service = ReportingService(session)

    # Create multiple reports
    for i in range(5):
        service.create_report(
            project_id=f"proj-{i % 2}",
            report_type="daily",
        )

    # List all reports
    reports, total = service.list_reports()
    assert total == 5
    assert len(reports) == 5

    # List reports for specific project
    reports, total = service.list_reports(project_id="proj-0")
    assert total == 3
    assert len(reports) == 3

    # Test pagination
    reports, total = service.list_reports(offset=0, limit=2)
    assert total == 5
    assert len(reports) == 2
    session.close()


def test_update_report_summary() -> None:
    SessionLocal = _in_memory_db()
    session = SessionLocal()
    service = ReportingService(session)

    report = service.create_report(
        project_id="proj-1",
        report_type="daily",
    )

    updated = service.update_report_summary(report.id, "This is a summary")
    assert updated.summary == "This is a summary"
    session.close()
