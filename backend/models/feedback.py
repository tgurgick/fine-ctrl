"""Feedback model for storing user ratings on model outputs."""
from sqlalchemy import Column, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from backend.database import Base
from backend.models.base import UUIDMixin, TimestampMixin


class Feedback(Base, UUIDMixin, TimestampMixin):
    """User feedback on model outputs."""

    __tablename__ = "feedback"

    model_version_id = Column(
        PGUUID(as_uuid=True), ForeignKey("model_versions.id"), nullable=False
    )
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    example_input = Column(Text, nullable=False)
    model_output = Column(Text, nullable=False)
    user_rating = Column(
        String(20), nullable=False
    )  # "excellent", "good", "fair", "poor"
    user_comment = Column(Text, nullable=True)

    # Relationships
    model_version = relationship("ModelVersion", back_populates="feedback")
    user = relationship("User")

    def __repr__(self) -> str:
        return f"<Feedback(id={self.id}, model_version_id={self.model_version_id}, rating={self.user_rating})>"
