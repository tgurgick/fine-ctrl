"""Dataset schemas."""
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class TrainingExampleBase(BaseModel):
    """Base training example schema."""

    input: str = Field(..., min_length=1)
    output: str = Field(..., min_length=1)
    example_metadata: Optional[Dict[str, Any]] = None


class TrainingExampleCreate(TrainingExampleBase):
    """Training example creation request."""

    pass


class TrainingExampleResponse(TrainingExampleBase):
    """Training example response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    dataset_id: UUID
    created_at: datetime


class DatasetBase(BaseModel):
    """Base dataset schema."""

    task_id: UUID
    version: int = 1


class DatasetCreate(DatasetBase):
    """Dataset creation request."""

    examples: List[TrainingExampleCreate] = Field(..., min_items=1)
    stats: Optional[Dict[str, Any]] = None


class DatasetUpdate(BaseModel):
    """Dataset update request."""

    stats: Optional[Dict[str, Any]] = None


class DatasetResponse(DatasetBase):
    """Dataset response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    stats: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime


class DatasetDetail(DatasetResponse):
    """Detailed dataset with examples."""

    examples: List[TrainingExampleResponse] = []
    example_count: Optional[int] = 0
