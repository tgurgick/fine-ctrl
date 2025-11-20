"""Deployment schemas."""
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class DeploymentBase(BaseModel):
    """Base deployment schema."""

    model_version_id: UUID
    name: str = Field(..., min_length=1, max_length=255)


class DeploymentCreate(DeploymentBase):
    """Deployment creation request."""

    deployment_config: Optional[Dict[str, Any]] = None


class DeploymentUpdate(BaseModel):
    """Deployment update request."""

    status: Optional[str] = Field(
        None, pattern="^(deploying|active|inactive|failed)$"
    )
    endpoint_url: Optional[str] = Field(None, max_length=512)
    deployment_config: Optional[Dict[str, Any]] = None


class DeploymentResponse(DeploymentBase):
    """Deployment response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    status: str
    endpoint_url: Optional[str] = None
    deployment_config: Optional[Dict[str, Any]] = None
    total_requests: int = 0
    total_tokens: int = 0
    total_cost: int = 0
    deployed_at: Optional[datetime] = None
    deactivated_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class InferenceRequest(BaseModel):
    """Inference request schema."""

    prompt: str = Field(..., min_length=1)
    max_tokens: Optional[int] = Field(None, ge=1, le=4096)
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    top_p: Optional[float] = Field(None, ge=0.0, le=1.0)


class InferenceResponse(BaseModel):
    """Inference response schema."""

    text: str
    tokens_used: int
    cost_cents: int
    model_version: str
