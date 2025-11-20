"""Evaluation and feedback routes."""
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.api.deps import get_current_active_user
from backend.models import User, ModelVersion
from backend.schemas.evaluation import (
    EvaluationRequest,
    EvaluationResponse,
    FeedbackCreate,
    FeedbackResponse,
    FeedbackAnalysis,
)
from backend.middleware.rate_limiter import limiter

router = APIRouter()


@router.post("/evaluate", response_model=EvaluationResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def evaluate_model(
    request: Request,
    eval_request: EvaluationRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Evaluate a model version.

    **Authentication**: Required
    **Authorization**: Must own the model version
    **Rate Limit**: 5 requests per minute

    **Note**: This endpoint is a placeholder for WP-5 (Evaluation Service).
    Full evaluation functionality will be implemented in that work package.

    Runs evaluation on the model using a test dataset and returns metrics.
    """
    # Verify model version ownership
    model = db.query(ModelVersion).filter(
        ModelVersion.id == eval_request.model_version_id
    ).first()
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

    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Model evaluation not yet implemented (WP-5)",
    )


@router.post("/feedback", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("20/minute")
async def submit_feedback(
    request: Request,
    feedback_data: FeedbackCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Submit feedback on model output.

    **Authentication**: Required
    **Authorization**: Must own the model version
    **Rate Limit**: 20 requests per minute

    **Note**: This endpoint is a placeholder for WP-5 (Evaluation Service).
    Full feedback functionality will be implemented in that work package.

    Allows users to provide feedback on model predictions to improve future versions.
    """
    # Verify model version ownership
    model = db.query(ModelVersion).filter(
        ModelVersion.id == feedback_data.model_version_id
    ).first()
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

    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Feedback submission not yet implemented (WP-5)",
    )


@router.get("/feedback/model/{model_version_id}", response_model=List[FeedbackResponse])
@limiter.limit("30/minute")
async def list_feedback(
    request: Request,
    model_version_id: UUID,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    List feedback for a model version.

    **Authentication**: Required
    **Authorization**: Must own the model version
    **Rate Limit**: 30 requests per minute

    **Note**: This endpoint is a placeholder for WP-5 (Evaluation Service).

    Returns all feedback submitted for the specified model version.
    """
    # Verify model version ownership
    model = db.query(ModelVersion).filter(
        ModelVersion.id == model_version_id
    ).first()
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

    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Feedback listing not yet implemented (WP-5)",
    )


@router.get("/feedback/model/{model_version_id}/analysis", response_model=FeedbackAnalysis)
@limiter.limit("30/minute")
async def analyze_feedback(
    request: Request,
    model_version_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Analyze feedback patterns for a model version.

    **Authentication**: Required
    **Authorization**: Must own the model version
    **Rate Limit**: 30 requests per minute

    **Note**: This endpoint is a placeholder for WP-5 (Evaluation Service).

    Returns aggregated feedback analysis including sentiment breakdown and common issues.
    """
    # Verify model version ownership
    model = db.query(ModelVersion).filter(
        ModelVersion.id == model_version_id
    ).first()
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

    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Feedback analysis not yet implemented (WP-5)",
    )
