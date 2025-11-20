"""API key schemas."""
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class APIKeyBase(BaseModel):
    """Base API key schema."""

    name: str = Field(..., min_length=1, max_length=255)


class APIKeyCreate(APIKeyBase):
    """API key creation request."""

    scopes: Optional[str] = "*"
    expires_at: Optional[datetime] = None


class APIKeyUpdate(BaseModel):
    """API key update request."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    is_active: Optional[bool] = None


class APIKeyResponse(APIKeyBase):
    """API key response schema (without key hash)."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    key_prefix: str
    is_active: bool
    scopes: str
    total_requests: int = 0
    total_tokens: int = 0
    last_used_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class APIKeyCreated(APIKeyResponse):
    """API key creation response with plaintext key.

    This is the ONLY time the plaintext key is returned.
    """

    key: str  # Only returned on creation
