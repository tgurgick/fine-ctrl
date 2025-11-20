"""Training job schemas."""
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class TrainingJobBase(BaseModel):
    """Base training job schema."""

    task_id: UUID
    dataset_id: UUID


class TrainingJobCreate(TrainingJobBase):
    """Training job creation request."""

    config: Optional[Dict[str, Any]] = None


class TrainingJobUpdate(BaseModel):
    """Training job update request."""

    status: Optional[str] = Field(
        None, pattern="^(queued|training|evaluating|completed|failed|cancelled)$"
    )
    metrics: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class TrainingJobResponse(TrainingJobBase):
    """Training job response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    status: str
    config: Optional[Dict[str, Any]] = None
    metrics: Optional[Dict[str, Any]] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ModelVersionBase(BaseModel):
    """Base model version schema."""

    task_id: UUID
    training_job_id: UUID
    version: str = Field(..., max_length=50)


class ModelVersionCreate(ModelVersionBase):
    """Model version creation request."""

    s3_weights_path: Optional[str] = None
    s3_adapter_path: Optional[str] = None
    inference_config: Optional[Dict[str, Any]] = None


class ModelVersionUpdate(BaseModel):
    """Model version update request."""

    status: Optional[str] = Field(
        None, pattern="^(training|evaluating|ready|failed)$"
    )
    s3_weights_path: Optional[str] = None
    s3_adapter_path: Optional[str] = None
    eval_results: Optional[Dict[str, Any]] = None
    inference_config: Optional[Dict[str, Any]] = None


class ModelVersionResponse(ModelVersionBase):
    """Model version response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    status: str
    s3_weights_path: Optional[str] = None
    s3_adapter_path: Optional[str] = None
    eval_results: Optional[Dict[str, Any]] = None
    inference_config: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
