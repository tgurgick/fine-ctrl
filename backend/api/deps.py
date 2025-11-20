"""API dependencies for dependency injection."""
from typing import Generator, Optional
from uuid import UUID
from fastapi import Depends, HTTPException, status, Security, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import User
from backend.services.auth import auth_service
from backend.services.api_keys import api_key_service
from backend.services.task import task_service
from backend.services.dataset import dataset_service
from backend.services.training import training_service
from backend.services.deployment import deployment_service
from backend.services.evaluation import evaluation_service
from backend.services.interfaces import (
    ITaskService,
    IDatasetService,
    ITrainingService,
    IDeploymentService,
)

# Security scheme for JWT bearer tokens
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security),
    x_api_key: Optional[str] = Header(None),
    db: Session = Depends(get_db),
) -> User:
    """
    Get current user from JWT token or API key.

    Supports two authentication methods:
    1. JWT Bearer token: Authorization: Bearer <token>
    2. API Key: X-API-Key: <api_key>

    Args:
        credentials: HTTP bearer token credentials (JWT)
        x_api_key: API key from X-API-Key header
        db: Database session

    Returns:
        Current authenticated user

    Raises:
        HTTPException: 401 if authentication fails
    """
    # Try API key authentication first
    if x_api_key:
        user = await api_key_service.verify_api_key(db, x_api_key)
        if user:
            return user
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Try JWT authentication
    if credentials:
        token = credentials.credentials
        return await auth_service.get_current_user(db, token)

    # No authentication provided
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required (JWT or API key)",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Get current active user.

    Args:
        current_user: Current authenticated user

    Returns:
        Current user if active

    Raises:
        HTTPException: 403 if user is inactive
    """
    if current_user.is_active != "1":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    return current_user


async def verify_resource_ownership(
    resource_id: UUID,
    user_id: UUID,
    resource_user_id: UUID,
) -> None:
    """
    Verify that user owns the requested resource.

    This prevents IDOR (Insecure Direct Object Reference) vulnerabilities.

    Args:
        resource_id: ID of the resource being accessed
        user_id: ID of the current user
        resource_user_id: user_id field from the resource

    Raises:
        HTTPException: 404 if user doesn't own the resource
    """
    if user_id != resource_user_id:
        # Return 404 instead of 403 to avoid leaking resource existence
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resource not found or access denied",
        )


def check_plan_limits(user: User, action: str) -> None:
    """
    Check if user's plan allows the requested action.

    Args:
        user: Current user
        action: Action being attempted (e.g., "create_task", "deploy_model")

    Raises:
        HTTPException: 403 if plan limits exceeded
    """
    # TODO: Implement plan-based rate limiting
    # Free plan: 1 task, 5 deployments
    # Pro plan: 10 tasks, 50 deployments
    # Enterprise: unlimited

    # Stub implementation
    pass


# Service dependency injection
def get_task_service() -> ITaskService:
    """Get task service instance."""
    return task_service


def get_dataset_service() -> IDatasetService:
    """Get dataset service instance."""
    return dataset_service


def get_training_service() -> ITrainingService:
    """Get training service instance."""
    return training_service


def get_deployment_service() -> IDeploymentService:
    """Get deployment service instance."""
    return deployment_service
