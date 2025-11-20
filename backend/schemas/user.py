"""User schemas."""
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, ConfigDict


class UserBase(BaseModel):
    """Base user schema."""

    email: EmailStr


class UserCreate(BaseModel):
    """User creation schema."""

    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    """User update schema."""

    email: Optional[EmailStr] = None
    password: Optional[str] = None


class UserResponse(UserBase):
    """User response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    plan: str
    is_active: str
    created_at: datetime
    updated_at: datetime


class UserProfile(UserResponse):
    """Extended user profile with usage stats."""

    total_tasks: Optional[int] = 0
    total_deployments: Optional[int] = 0
    total_api_keys: Optional[int] = 0
