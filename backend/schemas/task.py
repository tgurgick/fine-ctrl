"""Task schemas."""
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class TaskBase(BaseModel):
    """Base task schema."""

    name: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    task_type: Optional[str] = Field(None, max_length=50)


class TaskCreate(TaskBase):
    """Task creation request."""

    config: Optional[Dict[str, Any]] = None


class TaskUpdate(BaseModel):
    """Task update request."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, min_length=1)
    task_type: Optional[str] = Field(None, max_length=50)
    config: Optional[Dict[str, Any]] = None


class TaskResponse(TaskBase):
    """Task response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    config: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime


class TaskDetail(TaskResponse):
    """Detailed task response with related entities."""

    dataset_count: Optional[int] = 0
    training_job_count: Optional[int] = 0
    model_version_count: Optional[int] = 0
