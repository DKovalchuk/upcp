import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Table
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.database import Base


def _new_id() -> str:
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    return datetime.now(UTC)


user_role = Table(
    "user_role",
    Base.metadata,
    Column("user_id", String(36), ForeignKey("rbac_user.id"), primary_key=True),
    Column("role_id", String(36), ForeignKey("rbac_role.id"), primary_key=True),
)

role_permission = Table(
    "role_permission",
    Base.metadata,
    Column("role_id", String(36), ForeignKey("rbac_role.id"), primary_key=True),
    Column("permission_id", String(36), ForeignKey("rbac_permission.id"), primary_key=True),
)


class RBACUser(Base):
    __tablename__ = "rbac_user"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    username: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class RBACRole(Base):
    __tablename__ = "rbac_role"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)


class RBACPermission(Base):
    __tablename__ = "rbac_permission"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)


def get_current_user() -> RBACUser:
    """Placeholder: returns a default admin user. Real auth added later."""
    return RBACUser(
        id="00000000-0000-0000-0000-000000000001",
        username="admin",
        email="admin@upcp.local",
        is_active=True,
    )
