"""Evaluation and feedback schemas."""
from uuid import UUID
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


# Evaluation Request/Response Schemas
class EvaluationRequest(BaseModel):
    """Request to evaluate a model."""

    model_version_id: UUID
    test_dataset_id: UUID


class EvaluationMetrics(BaseModel):
    """Evaluation metrics for classification tasks."""

    accuracy: float = Field(..., ge=0.0, le=1.0)
    precision: float = Field(..., ge=0.0, le=1.0)
    recall: float = Field(..., ge=0.0, le=1.0)
    f1_score: float = Field(..., ge=0.0, le=1.0)
    confusion_matrix: List[List[int]] = Field(..., description="Confusion matrix")
    per_category_metrics: Dict[str, Dict[str, float]] = Field(
        default_factory=dict, description="Per-category precision, recall, F1"
    )
    total_examples: int = Field(..., ge=0)


class EvaluationResult(BaseModel):
    """Complete evaluation results."""

    model_version_id: UUID
    test_dataset_id: UUID
    metrics: EvaluationMetrics
    evaluated_at: datetime
    sample_predictions: Optional[List[Dict[str, Any]]] = Field(
        default=None, description="Sample predictions for review"
    )


# Feedback Schemas
class FeedbackCreate(BaseModel):
    """Create feedback on a model output."""

    model_version_id: UUID
    example_input: str = Field(..., min_length=1)
    model_output: str = Field(..., min_length=1)
    user_rating: str = Field(
        ..., description="Rating: excellent, good, fair, or poor"
    )
    user_comment: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "model_version_id": "123e4567-e89b-12d3-a456-426614174000",
                "example_input": "What is machine learning?",
                "model_output": "Machine learning is a subset of AI...",
                "user_rating": "excellent",
                "user_comment": "Very comprehensive answer",
            }
        }


class FeedbackResponse(BaseModel):
    """Feedback response."""

    id: UUID
    model_version_id: UUID
    user_id: UUID
    example_input: str
    model_output: str
    user_rating: str
    user_comment: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class FeedbackSample(BaseModel):
    """A sample for collecting user feedback."""

    example_input: str
    model_output: str
    ground_truth: Optional[str] = None
    category: Optional[str] = None
    confidence: Optional[float] = None


class FeedbackAnalysis(BaseModel):
    """Analysis of feedback patterns."""

    total_feedback_count: int
    rating_distribution: Dict[str, int] = Field(
        default_factory=dict, description="Count by rating (excellent, good, fair, poor)"
    )
    average_rating_score: float = Field(
        ..., description="Numerical score: excellent=4, good=3, fair=2, poor=1"
    )
    common_issues: List[str] = Field(
        default_factory=list, description="Common patterns in negative feedback"
    )
    strengths: List[str] = Field(
        default_factory=list, description="Common patterns in positive feedback"
    )
    feedback_by_category: Optional[Dict[str, Dict[str, Any]]] = Field(
        default=None, description="Feedback broken down by output category"
    )


# Sample Selection Schemas
class SampleSelectionRequest(BaseModel):
    """Request to select diverse samples for feedback."""

    model_version_id: UUID
    count: int = Field(default=10, ge=1, le=100)
    strategy: str = Field(
        default="diverse",
        description="Selection strategy: diverse, uncertain, balanced",
    )


class SampleSelectionResponse(BaseModel):
    """Response with selected samples."""

    model_version_id: UUID
    samples: List[FeedbackSample]
    selection_strategy: str
