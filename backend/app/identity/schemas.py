from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    display_name: str = Field(min_length=1, max_length=255)


class UserRead(BaseModel):
    """Safe user representation — never leaks is_superuser."""

    id: str
    email: str
    display_name: str
    is_active: bool
    email_verified: bool
    last_login_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserReadAdmin(UserRead):
    """Admin view — includes privileged fields."""

    is_superuser: bool
    failed_login_attempts: int
    locked_until: datetime | None
    password_changed_at: datetime | None


class OrganizationCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    slug: str = Field(min_length=1, max_length=255, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class OrganizationRead(BaseModel):
    id: str
    name: str
    slug: str
    is_default: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MembershipRead(BaseModel):
    id: str
    user_id: str
    org_id: str
    role: str
    created_at: datetime

    model_config = {"from_attributes": True}


class LoginAuditRead(BaseModel):
    id: str
    user_id: str | None
    email: str
    action: str
    ip_address: str | None
    user_agent: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
