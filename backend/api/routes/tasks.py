"""Task routes."""
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.database import get_db
from backend.api.deps import get_current_active_user, get_task_service
from backend.models import User, Task, Dataset, TrainingJob, ModelVersion
from backend.schemas.task import TaskCreate, TaskUpdate, TaskResponse, TaskDetail
from backend.services.interfaces import ITaskService
from backend.middleware.rate_limiter import limiter

router = APIRouter()


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def create_task(
    request: Request,
    task_data: TaskCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    task_service: ITaskService = Depends(get_task_service),
):
    """
    Create a new fine-tuning task.

    **Authentication**: Required
    **Rate Limit**: 10 requests per minute

    Creates a task owned by the current user. The task will be used to organize
    datasets, training jobs, and model versions.
    """
    task = await task_service.create_task(db, current_user.id, task_data)
    return task


@router.get("/", response_model=List[TaskResponse])
@limiter.limit("30/minute")
async def list_tasks(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    task_service: ITaskService = Depends(get_task_service),
):
    """
    List user's tasks.

    **Authentication**: Required
    **Rate Limit**: 30 requests per minute

    Returns all tasks owned by the current user with pagination support.
    """
    tasks = await task_service.list_tasks(db, current_user.id, skip, limit)
    return tasks


@router.get("/{task_id}", response_model=TaskDetail)
@limiter.limit("30/minute")
async def get_task(
    request: Request,
    task_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    task_service: ITaskService = Depends(get_task_service),
):
    """
    Get task details.

    **Authentication**: Required
    **Authorization**: Must own the task
    **Rate Limit**: 30 requests per minute

    Returns detailed task information including counts of related resources.
    """
    task = await task_service.get_task(db, task_id, current_user.id)

    # Get counts of related resources
    dataset_count = db.query(func.count(Dataset.id)).filter(Dataset.task_id == task_id).scalar()
    training_job_count = db.query(func.count(TrainingJob.id)).filter(TrainingJob.task_id == task_id).scalar()
    model_version_count = db.query(func.count(ModelVersion.id)).filter(ModelVersion.task_id == task_id).scalar()

    # Convert to TaskDetail response
    task_detail = TaskDetail(
        id=task.id,
        user_id=task.user_id,
        name=task.name,
        description=task.description,
        task_type=task.task_type,
        config=task.config,
        created_at=task.created_at,
        updated_at=task.updated_at,
        dataset_count=dataset_count or 0,
        training_job_count=training_job_count or 0,
        model_version_count=model_version_count or 0,
    )

    return task_detail


@router.patch("/{task_id}", response_model=TaskResponse)
@limiter.limit("10/minute")
async def update_task(
    request: Request,
    task_id: UUID,
    task_data: TaskUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    task_service: ITaskService = Depends(get_task_service),
):
    """
    Update task.

    **Authentication**: Required
    **Authorization**: Must own the task
    **Rate Limit**: 10 requests per minute

    Updates task fields. Only provided fields will be updated.
    """
    task = await task_service.update_task(db, task_id, current_user.id, task_data)
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("5/minute")
async def delete_task(
    request: Request,
    task_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    task_service: ITaskService = Depends(get_task_service),
):
    """
    Delete task and all related data.

    **Authentication**: Required
    **Authorization**: Must own the task
    **Rate Limit**: 5 requests per minute

    **Warning**: This will cascade delete all datasets, training jobs, model versions,
    and deployments associated with this task.
    """
    await task_service.delete_task(db, task_id, current_user.id)
    return None
