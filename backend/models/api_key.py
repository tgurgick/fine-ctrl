"""API key model."""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from backend.database import Base
from backend.models.base import UUIDMixin, TimestampMixin, UserOwnedResource


class APIKey(Base, UUIDMixin, TimestampMixin, UserOwnedResource):
    """API key for programmatic access."""

    __tablename__ = "api_keys"

    name = Column(String(255), nullable=False)
    key_hash = Column(String(255), nullable=False, unique=True, index=True)
    key_prefix = Column(
        String(20), nullable=False
    )  # First 8 chars for identification

    is_active = Column(Boolean, nullable=False, default=True)
    last_used_at = Column(DateTime, nullable=True)

    # Usage tracking
    total_requests = Column(Integer, nullable=False, default=0)
    total_tokens = Column(Integer, nullable=False, default=0)

    expires_at = Column(DateTime, nullable=True)
    revoked_at = Column(DateTime, nullable=True)

    # Scopes/permissions (JSON array of strings)
    scopes = Column(String(512), nullable=False, default="*")  # "*" or "tasks:read,..."

    def is_valid(self) -> bool:
        """Check if API key is valid and not expired."""
        if not self.is_active or self.revoked_at is not None:
            return False

        if self.expires_at is not None and datetime.utcnow() > self.expires_at:
            return False

        return True

    def __repr__(self) -> str:
        return f"<APIKey(id={self.id}, name={self.name}, prefix={self.key_prefix})>"
