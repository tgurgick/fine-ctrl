"""Deployment model."""
from sqlalchemy import Column, String, JSON, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from backend.database import Base
from backend.models.base import UUIDMixin, TimestampMixin, UserOwnedResource


class Deployment(Base, UUIDMixin, TimestampMixin, UserOwnedResource):
    """Model deployment configuration."""

    __tablename__ = "deployments"

    model_version_id = Column(
        PGUUID(as_uuid=True), ForeignKey("model_versions.id"), nullable=False
    )

    name = Column(String(255), nullable=False)
    status = Column(
        String(50), nullable=False, default="deploying"
    )  # deploying, active, inactive, failed

    endpoint_url = Column(String(512), nullable=True)  # Modal/inference endpoint
    deployment_config = Column(JSON, nullable=True)  # GPU type, replicas, etc.

    # Usage tracking
    total_requests = Column(Integer, nullable=False, default=0)
    total_tokens = Column(Integer, nullable=False, default=0)
    total_cost = Column(Integer, nullable=False, default=0)  # In cents

    deployed_at = Column(DateTime, nullable=True)
    deactivated_at = Column(DateTime, nullable=True)

    # Relationships
    model_version = relationship("ModelVersion", back_populates="deployments")

    def __repr__(self) -> str:
        return f"<Deployment(id={self.id}, name={self.name}, status={self.status})>"
