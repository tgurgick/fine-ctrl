"""Dataset routes."""
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.database import get_db
from backend.api.deps import get_current_active_user, get_dataset_service
from backend.models import User, TrainingExample
from backend.schemas.dataset import (
    DatasetCreate,
    DatasetResponse,
    DatasetDetail,
    TrainingExampleCreate,
    TrainingExampleResponse,
)
from backend.services.interfaces import IDatasetService
from backend.middleware.rate_limiter import limiter

router = APIRouter()


@router.post("/", response_model=DatasetResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def create_dataset(
    request: Request,
    dataset_data: DatasetCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    dataset_service: IDatasetService = Depends(get_dataset_service),
):
    """
    Create a new dataset with training examples.

    **Authentication**: Required
    **Authorization**: Must own the task
    **Rate Limit**: 10 requests per minute

    Creates a dataset with initial training examples for the specified task.
    """
    dataset = await dataset_service.create_dataset(db, current_user.id, dataset_data)
    return dataset


@router.get("/task/{task_id}", response_model=List[DatasetResponse])
@limiter.limit("30/minute")
async def list_datasets(
    request: Request,
    task_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    dataset_service: IDatasetService = Depends(get_dataset_service),
):
    """
    List datasets for a task.

    **Authentication**: Required
    **Authorization**: Must own the task
    **Rate Limit**: 30 requests per minute

    Returns all datasets associated with the specified task.
    """
    datasets = await dataset_service.list_datasets(db, task_id, current_user.id)
    return datasets


@router.get("/{dataset_id}", response_model=DatasetDetail)
@limiter.limit("30/minute")
async def get_dataset(
    request: Request,
    dataset_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    dataset_service: IDatasetService = Depends(get_dataset_service),
):
    """
    Get dataset with examples.

    **Authentication**: Required
    **Authorization**: Must own the dataset (via task ownership)
    **Rate Limit**: 30 requests per minute

    Returns detailed dataset information including all training examples.
    """
    dataset = await dataset_service.get_dataset(db, dataset_id, current_user.id)

    # Get examples for the dataset
    examples = db.query(TrainingExample).filter(TrainingExample.dataset_id == dataset_id).all()
    example_count = len(examples)

    # Convert to DatasetDetail response
    dataset_detail = DatasetDetail(
        id=dataset.id,
        task_id=dataset.task_id,
        version=dataset.version,
        stats=dataset.stats,
        created_at=dataset.created_at,
        updated_at=dataset.updated_at,
        examples=[
            TrainingExampleResponse(
                id=ex.id,
                dataset_id=ex.dataset_id,
                input=ex.input,
                output=ex.output,
                example_metadata=ex.example_metadata,
                created_at=ex.created_at,
            )
            for ex in examples
        ],
        example_count=example_count,
    )

    return dataset_detail


@router.post("/{dataset_id}/examples", response_model=List[TrainingExampleResponse], status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def add_examples(
    request: Request,
    dataset_id: UUID,
    examples: List[TrainingExampleCreate],
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    dataset_service: IDatasetService = Depends(get_dataset_service),
):
    """
    Add training examples to an existing dataset.

    **Authentication**: Required
    **Authorization**: Must own the dataset (via task ownership)
    **Rate Limit**: 10 requests per minute

    Adds new training examples to the specified dataset.
    """
    created_examples = await dataset_service.add_examples(
        db, dataset_id, current_user.id, examples
    )
    return created_examples
