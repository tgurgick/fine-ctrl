"""Base models and mixins for database entities."""
from datetime import datetime
from uuid import UUID, uuid4
from sqlalchemy import Column, DateTime, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Session
from fastapi import HTTPException

from backend.database import Base


class UserOwnedResource:
    """
    Mixin for resources owned by a user.

    Provides user_id column and helper method for ownership verification.
    """

    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)

    @classmethod
    async def get_by_id_and_user(
        cls, db: Session, resource_id: UUID, user_id: UUID
    ):
        """
        Get resource by ID and verify user ownership.

        Args:
            db: Database session
            resource_id: Resource ID to fetch
            user_id: User ID to verify ownership

        Returns:
            Resource instance if found and owned by user

        Raises:
            HTTPException: 404 if not found or access denied
        """
        resource = (
            db.query(cls)
            .filter(cls.id == resource_id, cls.user_id == user_id)
            .first()
        )

        if not resource:
            raise HTTPException(
                status_code=404, detail="Resource not found or access denied"
            )

        return resource


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps."""

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class UUIDMixin:
    """Mixin for UUID primary key."""

    id = Column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4, nullable=False
    )
