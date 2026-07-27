from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    display_name: str


class UserRead(BaseModel):
    id: str
    email: str
    display_name: str
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class OrganizationCreate(BaseModel):
    name: str
    slug: str


class OrganizationRead(BaseModel):
    id: str
    name: str
    slug: str
    is_default: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class MembershipRead(BaseModel):
    id: str
    user_id: str
    org_id: str
    role: str
    created_at: datetime

    model_config = {"from_attributes": True}
