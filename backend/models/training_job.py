"""Training job model."""
from sqlalchemy import Column, String, JSON, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from backend.database import Base
from backend.models.base import UUIDMixin, TimestampMixin, UserOwnedResource


class TrainingJob(Base, UUIDMixin, TimestampMixin, UserOwnedResource):
    """Training job model."""

    __tablename__ = "training_jobs"

    task_id = Column(PGUUID(as_uuid=True), ForeignKey("tasks.id"), nullable=False)
    dataset_id = Column(PGUUID(as_uuid=True), ForeignKey("datasets.id"), nullable=False)

    status = Column(
        String(50), nullable=False, default="queued"
    )  # queued, training, evaluating, completed, failed, cancelled

    config = Column(JSON, nullable=True)  # Training hyperparameters
    metrics = Column(JSON, nullable=True)  # Loss, perplexity, etc.

    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)

    # Relationships
    task = relationship("Task", back_populates="training_jobs")
    dataset = relationship("Dataset", back_populates="training_jobs")
    model_version = relationship("ModelVersion", back_populates="training_job", uselist=False)

    def __repr__(self) -> str:
        return f"<TrainingJob(id={self.id}, status={self.status})>"
