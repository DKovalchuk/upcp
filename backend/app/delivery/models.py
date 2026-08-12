from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.database import Base
from app.shared.text import new_id, utcnow


class Feature(Base):
    __tablename__ = "feature"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("project.id", ondelete="CASCADE"), nullable=False
    )
    component_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("component.id", ondelete="SET NULL"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="backlog")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )


class Task(Base):
    __tablename__ = "task"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    feature_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("feature.id", ondelete="CASCADE"), nullable=False
    )
    component_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("component.id", ondelete="SET NULL"), nullable=True
    )
    module_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("module.id", ondelete="SET NULL"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="backlog")
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    assignee_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    assignee_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )


class Subtask(Base):
    __tablename__ = "subtask"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    task_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("task.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="todo")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )


class ClarificationRequest(Base):
    __tablename__ = "clarification_request"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    task_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("task.id", ondelete="CASCADE"), nullable=False
    )
    author_type: Mapped[str] = mapped_column(String(50), nullable=False)
    author_id: Mapped[str] = mapped_column(String(36), nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    context: Mapped[str | None] = mapped_column(Text, nullable=True)
    blocking: Mapped[bool] = mapped_column(default=False)
    state: Mapped[str] = mapped_column(String(50), nullable=False, default="open")
    answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    answered_by: Mapped[str | None] = mapped_column(String(36), nullable=True)
    answered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class TaskDependency(Base):
    __tablename__ = "task_dependency"
    __table_args__ = (
        UniqueConstraint("task_id", "blocked_by_task_id", name="uq_task_dependency_pair"),
        CheckConstraint("task_id != blocked_by_task_id", name="ck_no_self_dependency"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    task_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("task.id", ondelete="CASCADE"), nullable=False
    )
    blocked_by_task_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("task.id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class TaskClaim(Base):
    __tablename__ = "task_claim"
    __table_args__ = (
        Index(
            "uq_task_claim_active",
            "task_id",
            unique=True,
            sqlite_where=text("state = 'active'"),
            postgresql_where=text("state = 'active'"),
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    task_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("task.id", ondelete="CASCADE"), nullable=False
    )
    agent_id: Mapped[str] = mapped_column(String(255), nullable=False)
    state: Mapped[str] = mapped_column(String(50), nullable=False, default="active")
    claimed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    released_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_heartbeat_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    context_snapshot: Mapped[str | None] = mapped_column(Text, nullable=True)


class Heartbeat(Base):
    __tablename__ = "heartbeat"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    claim_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("task_claim.id", ondelete="CASCADE"), nullable=False
    )
    progress_percent: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    current_step: Mapped[str] = mapped_column(String(255), nullable=False)
    next_step: Mapped[str] = mapped_column(String(255), nullable=False)
    blockers: Mapped[str | None] = mapped_column(Text, nullable=True)
    eta: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class AgentInboxEvent(Base):
    __tablename__ = "agent_inbox_event"
    __table_args__ = (
        Index("ix_agent_inbox_event_agent_id", "agent_id"),
        Index("ix_agent_inbox_event_created_at", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    agent_id: Mapped[str] = mapped_column(String(255), nullable=False)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    task_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_read: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
