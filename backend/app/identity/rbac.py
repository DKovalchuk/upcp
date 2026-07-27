"""RBAC models — Role, Permission, RoleBinding."""

from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.database import Base
from app.shared.text import new_id, utcnow


class Role(Base):
    __tablename__ = "iam_role"
    __table_args__ = (
        CheckConstraint(
            "scope IN ('global', 'org', 'project')",
            name="ck_iam_role_scope",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    scope: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Permission(Base):
    __tablename__ = "iam_permission"
    __table_args__ = (UniqueConstraint("action", "resource"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    resource: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class RolePermission(Base):
    __tablename__ = "iam_role_permission"

    role_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("iam_role.id", ondelete="CASCADE"), primary_key=True
    )
    permission_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("iam_permission.id", ondelete="CASCADE"), primary_key=True
    )


class RoleBinding(Base):
    __tablename__ = "iam_role_binding"
    __table_args__ = (
        UniqueConstraint("user_id", "role_id", "org_id"),
        Index("ix_iam_role_binding_user_id", "user_id"),
        Index("ix_iam_role_binding_role_id", "role_id"),
        Index("ix_iam_role_binding_org_id", "org_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("user_account.id", ondelete="CASCADE"), nullable=False
    )
    role_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("iam_role.id", ondelete="CASCADE"), nullable=False
    )
    org_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("organization.id", ondelete="CASCADE"), nullable=True
    )
    project_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
