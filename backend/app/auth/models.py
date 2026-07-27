from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Table
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.database import Base
from app.shared.text import new_id, utcnow

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

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    username: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class RBACRole(Base):
    __tablename__ = "rbac_role"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)


class RBACPermission(Base):
    __tablename__ = "rbac_permission"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
