"""Training job routes."""
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.api.deps import get_current_active_user
from backend.models import User
from backend.schemas.training import (
    TrainingJobCreate,
    TrainingJobResponse,
    ModelVersionResponse,
)

router = APIRouter()


@router.post("/jobs", response_model=TrainingJobResponse, status_code=status.HTTP_201_CREATED)
async def create_training_job(
    job_data: TrainingJobCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Create and queue a training job.

    To be implemented in WP-3 (Training Pipeline).
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Training job creation not yet implemented (WP-3)",
    )


@router.get("/jobs/task/{task_id}", response_model=List[TrainingJobResponse])
async def list_training_jobs(
    task_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    List training jobs for a task.

    To be implemented in WP-3.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Training job listing not yet implemented (WP-3)",
    )


@router.get("/jobs/{job_id}", response_model=TrainingJobResponse)
async def get_training_job(
    job_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Get training job status and metrics.

    To be implemented in WP-3.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Training job retrieval not yet implemented (WP-3)",
    )


@router.post("/jobs/{job_id}/cancel", response_model=TrainingJobResponse)
async def cancel_training_job(
    job_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Cancel a running training job.

    To be implemented in WP-3.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Training job cancellation not yet implemented (WP-3)",
    )


@router.get("/models/task/{task_id}", response_model=List[ModelVersionResponse])
async def list_model_versions(
    task_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    List model versions for a task.

    To be implemented in WP-4 (Evaluation).
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Model version listing not yet implemented (WP-4)",
    )
