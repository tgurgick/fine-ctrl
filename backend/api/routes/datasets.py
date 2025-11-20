"""Dataset routes."""
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.api.deps import get_current_active_user
from backend.models import User
from backend.schemas.dataset import (
    DatasetCreate,
    DatasetResponse,
    DatasetDetail,
    TrainingExampleCreate,
)

router = APIRouter()


@router.post("/", response_model=DatasetResponse, status_code=status.HTTP_201_CREATED)
async def create_dataset(
    dataset_data: DatasetCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Create a new dataset with training examples.

    To be implemented in WP-2 (Dataset Generation).
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Dataset creation not yet implemented (WP-2)",
    )


@router.get("/task/{task_id}", response_model=List[DatasetResponse])
async def list_datasets(
    task_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    List datasets for a task.

    To be implemented in WP-2.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Dataset listing not yet implemented (WP-2)",
    )


@router.get("/{dataset_id}", response_model=DatasetDetail)
async def get_dataset(
    dataset_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Get dataset with examples.

    To be implemented in WP-2.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Dataset retrieval not yet implemented (WP-2)",
    )
