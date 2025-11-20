"""API key routes."""
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.api.deps import get_current_active_user
from backend.models import User
from backend.schemas.api_key import (
    APIKeyCreate,
    APIKeyResponse,
    APIKeyCreated,
)
from backend.services.api_keys import api_key_service

router = APIRouter()


@router.post("/", response_model=APIKeyCreated, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    key_data: APIKeyCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Create a new API key.

    WARNING: The plaintext key is only returned once!
    Store it securely, it cannot be retrieved later.

    Args:
        key_data: API key creation data
        current_user: Current authenticated user
        db: Database session

    Returns:
        APIKeyCreated with plaintext key (only shown once!)
    """
    api_key, plaintext_key = await api_key_service.create_api_key(
        db, current_user.id, key_data
    )

    # Return response with plaintext key
    return APIKeyCreated(
        id=api_key.id,
        user_id=api_key.user_id,
        name=api_key.name,
        key_prefix=api_key.key_prefix,
        is_active=api_key.is_active,
        scopes=api_key.scopes,
        total_requests=api_key.total_requests,
        total_tokens=api_key.total_tokens,
        last_used_at=api_key.last_used_at,
        expires_at=api_key.expires_at,
        revoked_at=api_key.revoked_at,
        created_at=api_key.created_at,
        updated_at=api_key.updated_at,
        key=plaintext_key,  # Only returned once!
    )


@router.get("/", response_model=List[APIKeyResponse])
async def list_api_keys(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    List user's API keys.

    Args:
        current_user: Current authenticated user
        db: Database session

    Returns:
        List of API keys (without hashes)
    """
    return await api_key_service.list_api_keys(db, current_user.id)


@router.get("/{key_id}", response_model=APIKeyResponse)
async def get_api_key(
    key_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Get API key details.

    Args:
        key_id: API key ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        API key details

    Raises:
        HTTPException: 404 if not found or access denied
    """
    return await api_key_service.get_api_key(db, key_id, current_user.id)


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    key_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Revoke an API key.

    Args:
        key_id: API key ID
        current_user: Current authenticated user
        db: Database session

    Raises:
        HTTPException: 404 if not found or access denied
    """
    await api_key_service.revoke_api_key(db, key_id, current_user.id)
    return
