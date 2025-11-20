"""Deployment routes."""
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.api.deps import get_current_active_user, get_deployment_service
from backend.models import User, Deployment
from backend.schemas.deployment import (
    DeploymentCreate,
    DeploymentResponse,
    DeploymentUpdate,
    InferenceRequest,
    InferenceResponse,
)
from backend.services.interfaces import IDeploymentService
from backend.middleware.rate_limiter import limiter

router = APIRouter()


@router.post("/", response_model=DeploymentResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def create_deployment(
    request: Request,
    deployment_data: DeploymentCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    deployment_service: IDeploymentService = Depends(get_deployment_service),
):
    """
    Deploy a model version.

    **Authentication**: Required
    **Authorization**: Must own the model version
    **Rate Limit**: 5 requests per minute

    Creates a deployment for the specified model version. The model will be deployed
    to Modal and an endpoint URL will be returned for inference.
    """
    deployment = await deployment_service.create_deployment(
        db, current_user.id, deployment_data
    )
    return deployment


@router.get("/", response_model=List[DeploymentResponse])
@limiter.limit("30/minute")
async def list_deployments(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    deployment_service: IDeploymentService = Depends(get_deployment_service),
):
    """
    List user's deployments.

    **Authentication**: Required
    **Rate Limit**: 30 requests per minute

    Returns all deployments owned by the current user.
    """
    deployments = await deployment_service.list_deployments(
        db, current_user.id, skip, limit
    )
    return deployments


@router.get("/{deployment_id}", response_model=DeploymentResponse)
@limiter.limit("30/minute")
async def get_deployment(
    request: Request,
    deployment_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    deployment_service: IDeploymentService = Depends(get_deployment_service),
):
    """
    Get deployment details.

    **Authentication**: Required
    **Authorization**: Must own the deployment
    **Rate Limit**: 30 requests per minute

    Returns detailed information about a deployment including endpoint URL and status.
    """
    deployment = await deployment_service.get_deployment(
        db, deployment_id, current_user.id
    )
    return deployment


@router.patch("/{deployment_id}", response_model=DeploymentResponse)
@limiter.limit("10/minute")
async def update_deployment(
    request: Request,
    deployment_id: UUID,
    update_data: DeploymentUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    deployment_service: IDeploymentService = Depends(get_deployment_service),
):
    """
    Update deployment settings.

    **Authentication**: Required
    **Authorization**: Must own the deployment
    **Rate Limit**: 10 requests per minute

    Updates deployment configuration such as name or public access settings.
    """
    deployment = await deployment_service.update_deployment(
        db, deployment_id, current_user.id, update_data
    )
    return deployment


@router.post("/{deployment_id}/deactivate", response_model=DeploymentResponse)
@limiter.limit("5/minute")
async def deactivate_deployment(
    request: Request,
    deployment_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    deployment_service: IDeploymentService = Depends(get_deployment_service),
):
    """
    Deactivate a deployment.

    **Authentication**: Required
    **Authorization**: Must own the deployment
    **Rate Limit**: 5 requests per minute

    Deactivates the deployment and stops serving inference requests.
    The deployment can be reactivated later if needed.
    """
    deployment = await deployment_service.deactivate_deployment(
        db, deployment_id, current_user.id
    )
    return deployment


@router.post("/{deployment_id}/infer", response_model=InferenceResponse)
@limiter.limit("100/minute")
async def run_inference(
    request: Request,
    deployment_id: UUID,
    inference_request: InferenceRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Run inference on a deployed model.

    **Authentication**: Required
    **Authorization**: Must own the deployment OR deployment must be public
    **Rate Limit**: 100 requests per minute

    **Note**: Actual inference implementation will be completed in WP-6.
    This endpoint currently validates deployment access and returns a placeholder.

    Sends input to the deployed model and returns the prediction.
    """
    # Verify deployment exists and is active
    deployment = db.query(Deployment).filter(Deployment.id == deployment_id).first()
    if not deployment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deployment not found",
        )

    # Check authorization (must own OR deployment must be public)
    if not deployment.is_public and deployment.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deployment not found or access denied",
        )

    # Check if deployment is active
    if deployment.status != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Deployment is not active (status: {deployment.status})",
        )

    # Placeholder - actual inference will be implemented in WP-6
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Inference not yet implemented (WP-6). Deployment is configured correctly.",
    )
