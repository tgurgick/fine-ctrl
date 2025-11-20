"""User model."""
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from backend.database import Base
from backend.models.base import UUIDMixin, TimestampMixin


class User(Base, UUIDMixin, TimestampMixin):
    """User model."""

    __tablename__ = "users"

    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    plan = Column(String(50), nullable=False, default="free")  # free, pro, enterprise
    is_active = Column(String(1), nullable=False, default="1")  # "1" or "0" for boolean
    deleted_at = Column(DateTime, nullable=True)

    # Relationships - foreign_keys are defined in child models via UserOwnedResource
    tasks = relationship("Task", backref="owner", cascade="all, delete-orphan")
    training_jobs = relationship(
        "TrainingJob", backref="owner_user", cascade="all, delete-orphan"
    )
    deployments = relationship(
        "Deployment", backref="owner_deployment", cascade="all, delete-orphan"
    )
    api_keys = relationship("APIKey", backref="owner_api_key", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, plan={self.plan})>"
