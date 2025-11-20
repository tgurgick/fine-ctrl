"""Task model."""
from sqlalchemy import Column, String, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from backend.database import Base
from backend.models.base import UUIDMixin, TimestampMixin, UserOwnedResource


class Task(Base, UUIDMixin, TimestampMixin, UserOwnedResource):
    """Fine-tuning task model."""

    __tablename__ = "tasks"

    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    task_type = Column(
        String(50), nullable=True
    )  # classification, extraction, generation, etc.
    config = Column(JSON, nullable=True)  # Agent-generated configuration

    # Relationships
    datasets = relationship("Dataset", back_populates="task", cascade="all, delete-orphan")
    training_jobs = relationship(
        "TrainingJob", back_populates="task", cascade="all, delete-orphan"
    )
    model_versions = relationship(
        "ModelVersion", back_populates="task", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Task(id={self.id}, name={self.name}, task_type={self.task_type})>"
