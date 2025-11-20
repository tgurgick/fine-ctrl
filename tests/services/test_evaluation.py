"""Tests for evaluation service."""
import pytest
from uuid import uuid4
from datetime import datetime
from sqlalchemy.orm import Session

from backend.models import (
    User,
    Task,
    Dataset,
    TrainingExample,
    TrainingJob,
    ModelVersion,
    Feedback,
)
from backend.schemas.evaluation import FeedbackCreate
from backend.services.evaluation import EvaluationService
from evaluation.metrics import MetricsCalculator
from evaluation.selectors import SampleSelector


@pytest.fixture
def db_session():
    """Mock database session for testing."""
    # This is a mock - in real tests, you'd use a test database
    class MockSession:
        def __init__(self):
            self._data = {}
            self._queries = []

        def query(self, model):
            """Mock query method."""
            self._queries.append(model)
            return self

        def filter(self, *args, **kwargs):
            """Mock filter method."""
            return self

        def first(self):
            """Mock first method."""
            return self._data.get("first")

        def all(self):
            """Mock all method."""
            return self._data.get("all", [])

        def add(self, obj):
            """Mock add method."""
            self._data["added"] = obj

        def commit(self):
            """Mock commit method."""
            # Simulate database auto-populating id and created_at
            if "added" in self._data:
                obj = self._data["added"]
                if not hasattr(obj, "id") or obj.id is None:
                    obj.id = uuid4()
                if hasattr(obj, "created_at") and obj.created_at is None:
                    obj.created_at = datetime.utcnow()

        def refresh(self, obj):
            """Mock refresh method."""
            # Simulate refreshing object from database
            if not hasattr(obj, "id") or obj.id is None:
                obj.id = uuid4()
            if hasattr(obj, "created_at") and obj.created_at is None:
                obj.created_at = datetime.utcnow()

    return MockSession()


@pytest.fixture
def evaluation_service():
    """Create evaluation service instance."""
    return EvaluationService()


@pytest.fixture
def sample_user():
    """Create a sample user."""
    user = User(
        id=uuid4(),
        email="test@example.com",
        hashed_password="hashed",
        plan="free",
    )
    return user


@pytest.fixture
def sample_task(sample_user):
    """Create a sample task."""
    task = Task(
        id=uuid4(),
        user_id=sample_user.id,
        name="Test Classification Task",
        description="Classify sentiment",
        task_type="classification",
    )
    return task


@pytest.fixture
def sample_dataset(sample_task):
    """Create a sample dataset with examples."""
    dataset = Dataset(
        id=uuid4(),
        task_id=sample_task.id,
        version=1,
    )
    return dataset


@pytest.fixture
def sample_training_examples(sample_dataset):
    """Create sample training examples."""
    examples = [
        TrainingExample(
            id=uuid4(),
            dataset_id=sample_dataset.id,
            input="This is great!",
            output="positive",
        ),
        TrainingExample(
            id=uuid4(),
            dataset_id=sample_dataset.id,
            input="This is terrible!",
            output="negative",
        ),
        TrainingExample(
            id=uuid4(),
            dataset_id=sample_dataset.id,
            input="This is okay.",
            output="neutral",
        ),
        TrainingExample(
            id=uuid4(),
            dataset_id=sample_dataset.id,
            input="I love this!",
            output="positive",
        ),
        TrainingExample(
            id=uuid4(),
            dataset_id=sample_dataset.id,
            input="Not good.",
            output="negative",
        ),
    ]
    return examples


@pytest.fixture
def sample_model_version(sample_task, sample_user):
    """Create a sample model version."""
    training_job = TrainingJob(
        id=uuid4(),
        user_id=sample_user.id,
        task_id=sample_task.id,
        dataset_id=uuid4(),
        status="completed",
    )

    model_version = ModelVersion(
        id=uuid4(),
        user_id=sample_user.id,
        task_id=sample_task.id,
        training_job_id=training_job.id,
        version="v1.0.0",
        status="training",
    )
    model_version.training_job = training_job

    return model_version


# Tests for MetricsCalculator
class TestMetricsCalculator:
    """Test metrics calculator."""

    def test_calculate_classification_metrics_perfect_accuracy(self):
        """Test metrics with perfect predictions."""
        predictions = ["positive", "negative", "neutral", "positive", "negative"]
        ground_truth = ["positive", "negative", "neutral", "positive", "negative"]

        metrics = MetricsCalculator.calculate_classification_metrics(
            predictions, ground_truth
        )

        assert metrics["accuracy"] == 1.0
        assert metrics["precision"] == 1.0
        assert metrics["recall"] == 1.0
        assert metrics["f1_score"] == 1.0
        assert metrics["total_examples"] == 5

    def test_calculate_classification_metrics_with_errors(self):
        """Test metrics with some prediction errors."""
        predictions = ["positive", "positive", "neutral", "positive", "negative"]
        ground_truth = ["positive", "negative", "neutral", "positive", "negative"]

        metrics = MetricsCalculator.calculate_classification_metrics(
            predictions, ground_truth
        )

        # 4 out of 5 correct = 80% accuracy
        assert metrics["accuracy"] == 0.8
        assert metrics["total_examples"] == 5
        assert "confusion_matrix" in metrics
        assert "per_category_metrics" in metrics

    def test_confusion_matrix_calculation(self):
        """Test confusion matrix is calculated correctly."""
        predictions = ["A", "B", "A", "B"]
        ground_truth = ["A", "A", "B", "B"]

        metrics = MetricsCalculator.calculate_classification_metrics(
            predictions, ground_truth
        )

        confusion_matrix = metrics["confusion_matrix"]

        # Matrix should be 2x2 for classes A and B
        assert len(confusion_matrix) == 2
        assert len(confusion_matrix[0]) == 2

        # Check diagonal (correct predictions)
        # A->A: 1, A->B: 1, B->A: 1, B->B: 1
        assert confusion_matrix[0][0] == 1  # True A predicted as A
        assert confusion_matrix[1][1] == 1  # True B predicted as B

    def test_per_category_metrics(self):
        """Test per-category metrics are calculated."""
        predictions = ["positive", "negative", "positive"]
        ground_truth = ["positive", "negative", "positive"]

        metrics = MetricsCalculator.calculate_classification_metrics(
            predictions, ground_truth
        )

        per_category = metrics["per_category_metrics"]

        assert "positive" in per_category
        assert "negative" in per_category

        # All correct, so precision/recall/F1 should be 1.0 for both
        assert per_category["positive"]["precision"] == 1.0
        assert per_category["positive"]["recall"] == 1.0
        assert per_category["positive"]["f1_score"] == 1.0

    def test_empty_predictions_raises_error(self):
        """Test that empty predictions raise an error."""
        with pytest.raises(ValueError, match="Cannot calculate metrics for empty"):
            MetricsCalculator.calculate_classification_metrics([], [])

    def test_mismatched_lengths_raises_error(self):
        """Test that mismatched prediction/ground_truth lengths raise error."""
        with pytest.raises(ValueError, match="Length mismatch"):
            MetricsCalculator.calculate_classification_metrics(
                ["A", "B"],
                ["A"],
            )

    def test_category_distribution(self):
        """Test category distribution calculation."""
        examples = ["A", "A", "B", "C", "A"]

        distribution = MetricsCalculator.calculate_category_distribution(examples)

        assert distribution["A"]["count"] == 3
        assert distribution["A"]["percentage"] == 60.0
        assert distribution["B"]["count"] == 1
        assert distribution["C"]["count"] == 1

    def test_identify_misclassification_patterns(self):
        """Test misclassification pattern identification."""
        predictions = ["A", "B", "A", "B", "C", "A"]
        ground_truth = ["A", "A", "B", "B", "C", "B"]

        patterns = MetricsCalculator.identify_misclassification_patterns(
            predictions, ground_truth, top_n=3
        )

        # Should identify B->A and A->B misclassifications
        assert len(patterns) > 0
        assert all("true_label" in p for p in patterns)
        assert all("predicted_label" in p for p in patterns)


# Tests for SampleSelector
class TestSampleSelector:
    """Test sample selector."""

    def test_select_diverse_samples(self):
        """Test diverse sample selection."""
        examples = [
            {"input": "test1", "output": "A", "category": "cat1", "is_correct": True},
            {"input": "test2", "output": "B", "category": "cat2", "is_correct": False},
            {"input": "test3", "output": "A", "category": "cat1", "is_correct": True},
            {"input": "test4", "output": "C", "category": "cat3", "is_correct": True},
            {"input": "test5", "output": "B", "category": "cat2", "is_correct": False},
        ]

        selected = SampleSelector.select_diverse_samples(examples, count=3)

        assert len(selected) == 3
        # Should include diverse categories
        categories = set(ex.get("category") for ex in selected)
        assert len(categories) >= 2

    def test_select_uncertain_samples(self):
        """Test uncertain sample selection."""
        examples = [
            {"input": "test1", "confidence": 0.9},
            {"input": "test2", "confidence": 0.3},
            {"input": "test3", "confidence": 0.5},
            {"input": "test4", "confidence": 0.7},
        ]

        selected = SampleSelector.select_diverse_samples(
            examples, count=2, strategy="uncertain"
        )

        assert len(selected) == 2
        # Should select lowest confidence first
        assert selected[0]["confidence"] <= 0.5

    def test_select_balanced_samples(self):
        """Test balanced sample selection."""
        examples = [
            {"input": "test1", "category": "A"},
            {"input": "test2", "category": "A"},
            {"input": "test3", "category": "B"},
            {"input": "test4", "category": "B"},
            {"input": "test5", "category": "C"},
            {"input": "test6", "category": "C"},
        ]

        selected = SampleSelector.select_diverse_samples(
            examples, count=6, strategy="balanced"
        )

        assert len(selected) == 6
        # Should have balanced representation
        categories = [ex.get("category") for ex in selected]
        from collections import Counter
        category_counts = Counter(categories)
        # Each category should have roughly equal representation
        assert category_counts["A"] == 2
        assert category_counts["B"] == 2
        assert category_counts["C"] == 2

    def test_select_misclassified_samples(self):
        """Test misclassified sample selection."""
        examples = [
            {"input": "test1", "is_correct": True},
            {"input": "test2", "is_correct": False},
            {"input": "test3", "is_correct": True},
            {"input": "test4", "is_correct": False},
        ]

        selected = SampleSelector.select_misclassified_samples(examples, count=10)

        # Should only return misclassified examples
        assert len(selected) == 2
        assert all(not ex.get("is_correct") for ex in selected)

    def test_select_edge_cases(self):
        """Test edge case selection."""
        examples = [
            {"input": "test1", "confidence": 0.9, "is_correct": True},
            {"input": "test2", "confidence": 0.4, "is_correct": True},
            {"input": "test3", "confidence": 0.8, "is_correct": False},
            {"input": "test4", "confidence": 0.5, "is_correct": True},
        ]

        selected = SampleSelector.select_edge_cases(examples, count=3)

        # Should select low confidence or incorrect predictions
        assert len(selected) <= 3
        for ex in selected:
            assert ex["confidence"] < 0.6 or not ex.get("is_correct", True)


# Tests for EvaluationService
class TestEvaluationService:
    """Test evaluation service."""

    @pytest.mark.asyncio
    async def test_submit_feedback_valid(self, evaluation_service, db_session, sample_user):
        """Test submitting valid feedback."""
        model_version_id = uuid4()

        # Setup mock data
        model_version = ModelVersion(
            id=model_version_id,
            user_id=sample_user.id,
            task_id=uuid4(),
            training_job_id=uuid4(),
            version="v1.0.0",
        )
        db_session._data["first"] = model_version

        feedback_data = FeedbackCreate(
            model_version_id=model_version_id,
            example_input="What is AI?",
            model_output="AI is artificial intelligence...",
            user_rating="excellent",
            user_comment="Very clear explanation",
        )

        result = await evaluation_service.submit_feedback(
            db_session, feedback_data, sample_user.id
        )

        assert result.model_version_id == model_version_id
        assert result.user_rating == "excellent"
        assert result.example_input == "What is AI?"

    @pytest.mark.asyncio
    async def test_submit_feedback_invalid_rating(
        self, evaluation_service, db_session, sample_user
    ):
        """Test submitting feedback with invalid rating."""
        model_version_id = uuid4()

        model_version = ModelVersion(
            id=model_version_id,
            user_id=sample_user.id,
            task_id=uuid4(),
            training_job_id=uuid4(),
            version="v1.0.0",
        )
        db_session._data["first"] = model_version

        feedback_data = FeedbackCreate(
            model_version_id=model_version_id,
            example_input="Test",
            model_output="Test output",
            user_rating="invalid_rating",  # Invalid rating
        )

        with pytest.raises(ValueError, match="Invalid rating"):
            await evaluation_service.submit_feedback(
                db_session, feedback_data, sample_user.id
            )

    @pytest.mark.asyncio
    async def test_analyze_feedback_empty(
        self, evaluation_service, db_session, sample_user
    ):
        """Test analyzing feedback when no feedback exists."""
        model_version_id = uuid4()

        model_version = ModelVersion(
            id=model_version_id,
            user_id=sample_user.id,
            task_id=uuid4(),
            training_job_id=uuid4(),
            version="v1.0.0",
        )
        db_session._data["first"] = model_version
        db_session._data["all"] = []  # No feedback

        analysis = await evaluation_service.analyze_feedback(
            db_session, model_version_id, sample_user.id
        )

        assert analysis.total_feedback_count == 0
        assert analysis.average_rating_score == 0.0
        assert len(analysis.common_issues) == 0
        assert len(analysis.strengths) == 0

    @pytest.mark.asyncio
    async def test_analyze_feedback_with_data(
        self, evaluation_service, db_session, sample_user
    ):
        """Test analyzing feedback with actual feedback data."""
        model_version_id = uuid4()

        model_version = ModelVersion(
            id=model_version_id,
            user_id=sample_user.id,
            task_id=uuid4(),
            training_job_id=uuid4(),
            version="v1.0.0",
        )
        db_session._data["first"] = model_version

        # Create mock feedback records
        feedback_records = [
            Feedback(
                id=uuid4(),
                model_version_id=model_version_id,
                user_id=sample_user.id,
                example_input="Test 1",
                model_output="Output 1",
                user_rating="excellent",
                user_comment="Great response",
            ),
            Feedback(
                id=uuid4(),
                model_version_id=model_version_id,
                user_id=sample_user.id,
                example_input="Test 2",
                model_output="Output 2",
                user_rating="good",
                user_comment="Good answer",
            ),
            Feedback(
                id=uuid4(),
                model_version_id=model_version_id,
                user_id=sample_user.id,
                example_input="Test 3",
                model_output="Output 3",
                user_rating="poor",
                user_comment="Incorrect information",
            ),
        ]
        db_session._data["all"] = feedback_records

        analysis = await evaluation_service.analyze_feedback(
            db_session, model_version_id, sample_user.id
        )

        assert analysis.total_feedback_count == 3
        assert analysis.rating_distribution["excellent"] == 1
        assert analysis.rating_distribution["good"] == 1
        assert analysis.rating_distribution["poor"] == 1
        # Average: (4 + 3 + 1) / 3 = 2.67
        assert 2.6 <= analysis.average_rating_score <= 2.7


def test_evaluation_service_initialization():
    """Test that evaluation service initializes correctly."""
    service = EvaluationService()

    assert service.metrics_calculator is not None
    assert service.sample_selector is not None
    assert isinstance(service.metrics_calculator, MetricsCalculator)
    assert isinstance(service.sample_selector, SampleSelector)
