"""Training job routes."""
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.api.deps import get_current_active_user, get_training_service, get_task_service
from backend.models import User, ModelVersion, Task
from backend.schemas.training import (
    TrainingJobCreate,
    TrainingJobResponse,
    TrainingJobUpdate,
    ModelVersionResponse,
    ModelVersionCreate,
)
from backend.services.interfaces import ITrainingService, ITaskService
from backend.middleware.rate_limiter import limiter

router = APIRouter()


@router.post("/jobs", response_model=TrainingJobResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def create_training_job(
    request: Request,
    job_data: TrainingJobCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    training_service: ITrainingService = Depends(get_training_service),
):
    """
    Create and queue a training job.

    **Authentication**: Required
    **Authorization**: Must own the task and dataset
    **Rate Limit**: 5 requests per minute

    Creates a new training job for the specified task and dataset. The job will be
    queued and executed asynchronously. Monitor the job status for progress updates.
    """
    job = await training_service.create_training_job(db, current_user.id, job_data)
    return job


@router.get("/jobs/task/{task_id}", response_model=List[TrainingJobResponse])
@limiter.limit("30/minute")
async def list_training_jobs(
    request: Request,
    task_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    training_service: ITrainingService = Depends(get_training_service),
):
    """
    List training jobs for a task.

    **Authentication**: Required
    **Authorization**: Must own the task
    **Rate Limit**: 30 requests per minute

    Returns all training jobs associated with the specified task.
    """
    jobs = await training_service.list_training_jobs(db, task_id, current_user.id)
    return jobs


@router.get("/jobs/{job_id}", response_model=TrainingJobResponse)
@limiter.limit("30/minute")
async def get_training_job(
    request: Request,
    job_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    training_service: ITrainingService = Depends(get_training_service),
):
    """
    Get training job status and metrics.

    **Authentication**: Required
    **Authorization**: Must own the training job
    **Rate Limit**: 30 requests per minute

    Returns detailed information about a training job including status, metrics,
    and error messages if applicable.
    """
    job = await training_service.get_training_job(db, job_id, current_user.id)
    return job


@router.patch("/jobs/{job_id}", response_model=TrainingJobResponse)
@limiter.limit("10/minute")
async def update_training_job(
    request: Request,
    job_id: UUID,
    update_data: TrainingJobUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    training_service: ITrainingService = Depends(get_training_service),
):
    """
    Update training job status and metrics.

    **Authentication**: Required
    **Authorization**: Must own the training job
    **Rate Limit**: 10 requests per minute

    Updates training job information. Typically used by the training service
    to update status and metrics as training progresses.
    """
    job = await training_service.update_training_job(db, job_id, current_user.id, update_data)
    return job


@router.post("/jobs/{job_id}/cancel", response_model=TrainingJobResponse)
@limiter.limit("5/minute")
async def cancel_training_job(
    request: Request,
    job_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    training_service: ITrainingService = Depends(get_training_service),
):
    """
    Cancel a running training job.

    **Authentication**: Required
    **Authorization**: Must own the training job
    **Rate Limit**: 5 requests per minute

    Cancels a training job that is currently queued or in progress.
    """
    job = await training_service.cancel_training_job(db, job_id, current_user.id)
    return job


@router.get("/models/task/{task_id}", response_model=List[ModelVersionResponse])
@limiter.limit("30/minute")
async def list_model_versions(
    request: Request,
    task_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    task_service: ITaskService = Depends(get_task_service),
):
    """
    List model versions for a task.

    **Authentication**: Required
    **Authorization**: Must own the task
    **Rate Limit**: 30 requests per minute

    Returns all trained model versions for the specified task.
    """
    # Verify task ownership
    await task_service.get_task(db, task_id, current_user.id)

    # Get model versions
    models = db.query(ModelVersion).filter(ModelVersion.task_id == task_id).all()
    return models


@router.post("/models", response_model=ModelVersionResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def create_model_version(
    request: Request,
    version_data: ModelVersionCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    training_service: ITrainingService = Depends(get_training_service),
):
    """
    Create a model version record.

    **Authentication**: Required
    **Authorization**: Must own the task and training job
    **Rate Limit**: 5 requests per minute

    Creates a model version record after successful training. This is typically
    called by the training service after model weights are saved.
    """
    model = await training_service.create_model_version(db, current_user.id, version_data)
    return model


@router.get("/models/{version_id}", response_model=ModelVersionResponse)
@limiter.limit("30/minute")
async def get_model_version(
    request: Request,
    version_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Get model version details.

    **Authentication**: Required
    **Authorization**: Must own the model version
    **Rate Limit**: 30 requests per minute

    Returns detailed information about a model version including evaluation results.
    """
    model = db.query(ModelVersion).filter(ModelVersion.id == version_id).first()
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model version not found",
        )
    if model.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resource not found or access denied",
        )
    return model
