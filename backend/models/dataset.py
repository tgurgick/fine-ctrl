"""Dataset model."""
from sqlalchemy import Column, Integer, JSON, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from backend.database import Base
from backend.models.base import UUIDMixin, TimestampMixin


class Dataset(Base, UUIDMixin, TimestampMixin):
    """Training dataset model."""

    __tablename__ = "datasets"

    task_id = Column(PGUUID(as_uuid=True), ForeignKey("tasks.id"), nullable=False)
    version = Column(Integer, nullable=False, default=1)
    stats = Column(JSON, nullable=True)  # Diversity, balance, category distribution

    # Relationships
    task = relationship("Task", back_populates="datasets")
    training_examples = relationship(
        "TrainingExample", back_populates="dataset", cascade="all, delete-orphan"
    )
    training_jobs = relationship("TrainingJob", back_populates="dataset")

    def __repr__(self) -> str:
        return f"<Dataset(id={self.id}, task_id={self.task_id}, version={self.version})>"


class TrainingExample(Base, UUIDMixin, TimestampMixin):
    """Individual training example."""

    __tablename__ = "training_examples"

    dataset_id = Column(PGUUID(as_uuid=True), ForeignKey("datasets.id"), nullable=False)
    input = Column(Text, nullable=False)
    output = Column(Text, nullable=False)
    example_metadata = Column(JSON, nullable=True)

    # Relationships
    dataset = relationship("Dataset", back_populates="training_examples")

    def __repr__(self) -> str:
        return f"<TrainingExample(id={self.id}, dataset_id={self.dataset_id})>"
