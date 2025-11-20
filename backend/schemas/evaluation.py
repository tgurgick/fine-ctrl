"""Evaluation and feedback schemas."""
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class FeedbackBase(BaseModel):
    """Base feedback schema."""

    model_version_id: UUID
    example_input: str = Field(..., min_length=1)
    model_output: str = Field(..., min_length=1)
    rating: str = Field(..., pattern="^(positive|negative|neutral)$")
    comment: Optional[str] = None


class FeedbackCreate(FeedbackBase):
    """Feedback creation request."""

    pass


class FeedbackResponse(FeedbackBase):
    """Feedback response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    created_at: datetime


class EvaluationRequest(BaseModel):
    """Request to evaluate a model."""

    model_version_id: UUID
    test_dataset_id: Optional[UUID] = None  # If None, use holdout from training


class EvaluationMetrics(BaseModel):
    """Evaluation metrics results."""

    accuracy: Optional[float] = None
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1_score: Optional[float] = None
    confusion_matrix: Optional[Dict[str, Any]] = None
    per_category_metrics: Optional[Dict[str, Any]] = None


class EvaluationResponse(BaseModel):
    """Evaluation results response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    model_version_id: UUID
    test_dataset_id: Optional[UUID] = None
    metrics: EvaluationMetrics
    sample_predictions: Optional[List[Dict[str, Any]]] = None
    created_at: datetime
    completed_at: Optional[datetime] = None


class FeedbackAnalysis(BaseModel):
    """Aggregated feedback analysis."""

    total_feedback_count: int
    positive_count: int
    negative_count: int
    neutral_count: int
    positive_percentage: float
    common_issues: Optional[List[str]] = None
    sample_feedback: Optional[List[FeedbackResponse]] = None
