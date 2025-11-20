"""Deployment routes."""
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.api.deps import get_current_active_user
from backend.models import User
from backend.schemas.deployment import (
    DeploymentCreate,
    DeploymentResponse,
    InferenceRequest,
    InferenceResponse,
)

router = APIRouter()


@router.post("/", response_model=DeploymentResponse, status_code=status.HTTP_201_CREATED)
async def create_deployment(
    deployment_data: DeploymentCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Deploy a model version.

    To be implemented in WP-6 (Deployment).
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Deployment creation not yet implemented (WP-6)",
    )


@router.get("/", response_model=List[DeploymentResponse])
async def list_deployments(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    List user's deployments.

    To be implemented in WP-6.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Deployment listing not yet implemented (WP-6)",
    )


@router.get("/{deployment_id}", response_model=DeploymentResponse)
async def get_deployment(
    deployment_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Get deployment details.

    To be implemented in WP-6.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Deployment retrieval not yet implemented (WP-6)",
    )


@router.post("/{deployment_id}/deactivate", response_model=DeploymentResponse)
async def deactivate_deployment(
    deployment_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Deactivate a deployment.

    To be implemented in WP-6.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Deployment deactivation not yet implemented (WP-6)",
    )


@router.post("/{deployment_id}/infer", response_model=InferenceResponse)
async def run_inference(
    deployment_id: UUID,
    request: InferenceRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Run inference on a deployed model.

    To be implemented in WP-6.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Inference not yet implemented (WP-6)",
    )
