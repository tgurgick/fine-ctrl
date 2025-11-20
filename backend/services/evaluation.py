"""Evaluation service combining metrics calculation and feedback management."""
from uuid import UUID
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.models import ModelVersion, Dataset, TrainingExample, Feedback, User
from backend.schemas.evaluation import (
    EvaluationMetrics,
    EvaluationResult,
    FeedbackCreate,
    FeedbackResponse,
    FeedbackSample,
    FeedbackAnalysis,
)
from evaluation.metrics import MetricsCalculator
from evaluation.selectors import SampleSelector


class EvaluationService:
    """
    Unified evaluation service handling metrics calculation and feedback management.

    This service combines evaluation and feedback functionality into a single service
    as per WP-5 requirements, removing the bloat of separate services.
    """

    def __init__(self):
        """Initialize evaluation service."""
        self.metrics_calculator = MetricsCalculator()
        self.sample_selector = SampleSelector()

    async def evaluate_model(
        self,
        db: Session,
        model_version_id: UUID,
        test_dataset_id: UUID,
        user_id: UUID,
    ) -> EvaluationResult:
        """
        Run full evaluation on a model version.

        This includes:
        1. Running inference on test dataset
        2. Computing metrics (accuracy, precision, recall, F1)
        3. Generating confusion matrix
        4. Storing results in database

        Args:
            db: Database session
            model_version_id: ID of model version to evaluate
            test_dataset_id: ID of test dataset
            user_id: ID of user (for authorization)

        Returns:
            EvaluationResult with metrics and sample predictions

        Raises:
            ValueError: If model or dataset not found, or user doesn't own resources
        """
        # Verify model version exists and user owns it
        model_version = (
            db.query(ModelVersion)
            .filter(
                ModelVersion.id == model_version_id,
                ModelVersion.user_id == user_id,
            )
            .first()
        )

        if not model_version:
            raise ValueError(f"Model version {model_version_id} not found or access denied")

        # Verify test dataset exists
        dataset = db.query(Dataset).filter(Dataset.id == test_dataset_id).first()

        if not dataset:
            raise ValueError(f"Dataset {test_dataset_id} not found")

        # Get test examples
        test_examples = (
            db.query(TrainingExample)
            .filter(TrainingExample.dataset_id == test_dataset_id)
            .all()
        )

        if not test_examples:
            raise ValueError(f"No examples found in dataset {test_dataset_id}")

        # Run inference and collect predictions
        # NOTE: In a real implementation, this would call the model's inference endpoint
        # For now, we'll simulate predictions based on the expected output format
        predictions = []
        ground_truth = []
        sample_predictions = []

        for example in test_examples:
            # TODO: Replace with actual model inference
            # predicted_output = await self._run_inference(model_version, example.input)

            # For now, use the example output as "prediction" (this is just for testing)
            predicted_output = example.output

            predictions.append(predicted_output)
            ground_truth.append(example.output)

            sample_predictions.append({
                "input": example.input,
                "predicted": predicted_output,
                "ground_truth": example.output,
                "is_correct": predicted_output == example.output,
            })

        # Calculate metrics
        metrics_dict = self.metrics_calculator.calculate_classification_metrics(
            predictions=predictions,
            ground_truth=ground_truth,
        )

        # Create EvaluationMetrics schema
        metrics = EvaluationMetrics(**metrics_dict)

        # Store evaluation results in model version
        model_version.eval_results = {
            "accuracy": metrics.accuracy,
            "precision": metrics.precision,
            "recall": metrics.recall,
            "f1_score": metrics.f1_score,
            "confusion_matrix": metrics.confusion_matrix,
            "per_category_metrics": metrics.per_category_metrics,
            "total_examples": metrics.total_examples,
            "evaluated_at": datetime.utcnow().isoformat(),
        }
        model_version.status = "ready"

        db.commit()
        db.refresh(model_version)

        # Return evaluation result
        return EvaluationResult(
            model_version_id=model_version_id,
            test_dataset_id=test_dataset_id,
            metrics=metrics,
            evaluated_at=datetime.utcnow(),
            sample_predictions=sample_predictions[:10],  # Return first 10 samples
        )

    async def select_feedback_samples(
        self,
        db: Session,
        model_version_id: UUID,
        user_id: UUID,
        count: int = 10,
        strategy: str = "diverse",
    ) -> List[FeedbackSample]:
        """
        Select diverse examples for user feedback.

        Args:
            db: Database session
            model_version_id: ID of model version
            user_id: ID of user (for authorization)
            count: Number of samples to select
            strategy: Selection strategy ("diverse", "uncertain", "balanced")

        Returns:
            List of feedback samples

        Raises:
            ValueError: If model not found or user doesn't own it
        """
        # Verify model version exists and user owns it
        model_version = (
            db.query(ModelVersion)
            .filter(
                ModelVersion.id == model_version_id,
                ModelVersion.user_id == user_id,
            )
            .first()
        )

        if not model_version:
            raise ValueError(f"Model version {model_version_id} not found or access denied")

        # Get evaluation results
        if not model_version.eval_results:
            raise ValueError(f"Model version {model_version_id} has not been evaluated yet")

        # Get test dataset from training job
        test_dataset_id = model_version.training_job.dataset_id
        test_examples = (
            db.query(TrainingExample)
            .filter(TrainingExample.dataset_id == test_dataset_id)
            .all()
        )

        # Prepare examples for selection
        examples_for_selection = []
        for example in test_examples:
            # TODO: Run actual inference to get predictions
            # For now, simulate with example output
            predicted_output = example.output

            examples_for_selection.append({
                "input": example.input,
                "output": predicted_output,
                "ground_truth": example.output,
                "is_correct": predicted_output == example.output,
                "confidence": 0.85,  # TODO: Get actual confidence from model
            })

        # Select samples using the specified strategy
        selected = self.sample_selector.select_diverse_samples(
            examples_for_selection,
            count=count,
            strategy=strategy,
        )

        # Convert to FeedbackSample schema
        feedback_samples = []
        for sample in selected:
            feedback_samples.append(
                FeedbackSample(
                    example_input=sample["input"],
                    model_output=sample["output"],
                    ground_truth=sample.get("ground_truth"),
                    confidence=sample.get("confidence"),
                )
            )

        return feedback_samples

    async def submit_feedback(
        self,
        db: Session,
        feedback_data: FeedbackCreate,
        user_id: UUID,
    ) -> FeedbackResponse:
        """
        Record user feedback on model output.

        Args:
            db: Database session
            feedback_data: Feedback data
            user_id: ID of user submitting feedback

        Returns:
            FeedbackResponse with stored feedback

        Raises:
            ValueError: If model not found or invalid rating
        """
        # Validate rating
        valid_ratings = ["excellent", "good", "fair", "poor"]
        if feedback_data.user_rating not in valid_ratings:
            raise ValueError(
                f"Invalid rating '{feedback_data.user_rating}'. Must be one of: {valid_ratings}"
            )

        # Verify model version exists
        model_version = (
            db.query(ModelVersion)
            .filter(ModelVersion.id == feedback_data.model_version_id)
            .first()
        )

        if not model_version:
            raise ValueError(f"Model version {feedback_data.model_version_id} not found")

        # Create feedback record
        feedback = Feedback(
            model_version_id=feedback_data.model_version_id,
            user_id=user_id,
            example_input=feedback_data.example_input,
            model_output=feedback_data.model_output,
            user_rating=feedback_data.user_rating,
            user_comment=feedback_data.user_comment,
        )

        db.add(feedback)
        db.commit()
        db.refresh(feedback)

        # Return feedback response
        return FeedbackResponse(
            id=feedback.id,
            model_version_id=feedback.model_version_id,
            user_id=feedback.user_id,
            example_input=feedback.example_input,
            model_output=feedback.model_output,
            user_rating=feedback.user_rating,
            user_comment=feedback.user_comment,
            created_at=feedback.created_at,
        )

    async def analyze_feedback(
        self,
        db: Session,
        model_version_id: UUID,
        user_id: UUID,
    ) -> FeedbackAnalysis:
        """
        Analyze patterns in user feedback.

        Args:
            db: Database session
            model_version_id: ID of model version
            user_id: ID of user (for authorization)

        Returns:
            FeedbackAnalysis with aggregated insights

        Raises:
            ValueError: If model not found or user doesn't own it
        """
        # Verify model version exists and user owns it
        model_version = (
            db.query(ModelVersion)
            .filter(
                ModelVersion.id == model_version_id,
                ModelVersion.user_id == user_id,
            )
            .first()
        )

        if not model_version:
            raise ValueError(f"Model version {model_version_id} not found or access denied")

        # Get all feedback for this model version
        feedback_records = (
            db.query(Feedback)
            .filter(Feedback.model_version_id == model_version_id)
            .all()
        )

        if not feedback_records:
            # Return empty analysis if no feedback
            return FeedbackAnalysis(
                total_feedback_count=0,
                rating_distribution={},
                average_rating_score=0.0,
                common_issues=[],
                strengths=[],
            )

        # Calculate rating distribution
        rating_distribution = {"excellent": 0, "good": 0, "fair": 0, "poor": 0}
        for feedback in feedback_records:
            rating_distribution[feedback.user_rating] += 1

        # Calculate average rating score
        rating_to_score = {"excellent": 4, "good": 3, "fair": 2, "poor": 1}
        total_score = sum(rating_to_score[f.user_rating] for f in feedback_records)
        average_rating_score = total_score / len(feedback_records)

        # Extract common issues from poor/fair feedback
        common_issues = []
        poor_feedback = [
            f for f in feedback_records if f.user_rating in ["poor", "fair"]
        ]
        if poor_feedback:
            # Simple keyword extraction from comments
            issues = self._extract_keywords_from_comments(
                [f.user_comment for f in poor_feedback if f.user_comment]
            )
            common_issues = issues[:5]  # Top 5 issues

        # Extract strengths from excellent/good feedback
        strengths = []
        good_feedback = [
            f for f in feedback_records if f.user_rating in ["excellent", "good"]
        ]
        if good_feedback:
            # Simple keyword extraction from comments
            strength_keywords = self._extract_keywords_from_comments(
                [f.user_comment for f in good_feedback if f.user_comment]
            )
            strengths = strength_keywords[:5]  # Top 5 strengths

        return FeedbackAnalysis(
            total_feedback_count=len(feedback_records),
            rating_distribution=rating_distribution,
            average_rating_score=round(average_rating_score, 2),
            common_issues=common_issues,
            strengths=strengths,
        )

    def _extract_keywords_from_comments(self, comments: List[str]) -> List[str]:
        """
        Extract common keywords/patterns from feedback comments.

        This is a simplified implementation. In production, you might use:
        - NLP libraries for better keyword extraction
        - Sentiment analysis
        - Topic modeling

        Args:
            comments: List of comment strings

        Returns:
            List of common keywords/phrases
        """
        if not comments:
            return []

        # Simple word frequency analysis
        from collections import Counter
        import re

        # Combine all comments
        all_text = " ".join(comments).lower()

        # Extract words (simple tokenization)
        words = re.findall(r'\b\w+\b', all_text)

        # Filter out common stop words
        stop_words = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
            "of", "with", "is", "was", "are", "were", "be", "been", "being",
            "have", "has", "had", "do", "does", "did", "will", "would", "could",
            "should", "may", "might", "must", "can", "it", "this", "that", "these",
            "those", "i", "you", "he", "she", "we", "they", "me", "him", "her",
            "us", "them", "my", "your", "his", "its", "our", "their",
        }

        meaningful_words = [w for w in words if w not in stop_words and len(w) > 3]

        # Get most common words
        word_counts = Counter(meaningful_words)
        common_words = [word for word, count in word_counts.most_common(10)]

        return common_words
