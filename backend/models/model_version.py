"""Model version model."""
from sqlalchemy import Column, String, JSON, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from backend.database import Base
from backend.models.base import UUIDMixin, TimestampMixin, UserOwnedResource


class ModelVersion(Base, UUIDMixin, TimestampMixin, UserOwnedResource):
    """Trained model version."""

    __tablename__ = "model_versions"

    task_id = Column(PGUUID(as_uuid=True), ForeignKey("tasks.id"), nullable=False)
    training_job_id = Column(
        PGUUID(as_uuid=True), ForeignKey("training_jobs.id"), nullable=False
    )

    version = Column(String(50), nullable=False)  # e.g., "v1.0.0"
    status = Column(
        String(50), nullable=False, default="training"
    )  # training, evaluating, ready, failed

    s3_weights_path = Column(Text, nullable=True)  # S3 path to model weights
    s3_adapter_path = Column(Text, nullable=True)  # S3 path to LoRA adapter

    eval_results = Column(JSON, nullable=True)  # Accuracy, F1, precision, recall
    inference_config = Column(JSON, nullable=True)  # Temperature, max_tokens, etc.

    # Relationships
    task = relationship("Task", back_populates="model_versions")
    training_job = relationship("TrainingJob", back_populates="model_version")
    deployments = relationship(
        "Deployment", back_populates="model_version", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<ModelVersion(id={self.id}, version={self.version}, status={self.status})>"
