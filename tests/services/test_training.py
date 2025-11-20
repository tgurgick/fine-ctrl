"""Tests for training service."""
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from uuid import uuid4
from datetime import datetime

from backend.services.training import TrainingService
from backend.models import TrainingJob, Dataset, Task, ModelVersion, User
from backend.schemas.training import (
    TrainingJobCreate,
    TrainingJobUpdate,
    ModelVersionCreate,
)


@pytest.fixture
def mock_db():
    """Mock database session."""
    return Mock()


@pytest.fixture
def training_service():
    """Training service instance."""
    return TrainingService()


@pytest.fixture
def test_user_id():
    """Test user ID."""
    return uuid4()


@pytest.fixture
def test_task(test_user_id):
    """Test task."""
    task = Task(
        id=uuid4(),
        user_id=test_user_id,
        name="Test Task",
        description="Test task description",
    )
    return task


@pytest.fixture
def test_dataset(test_user_id, test_task):
    """Test dataset."""
    dataset = Dataset(
        id=uuid4(),
        user_id=test_user_id,
        task_id=test_task.id,
        name="Test Dataset",
        split="train",
    )
    return dataset


@pytest.fixture
def test_job(test_user_id, test_task, test_dataset):
    """Test training job."""
    job = TrainingJob(
        id=uuid4(),
        user_id=test_user_id,
        task_id=test_task.id,
        dataset_id=test_dataset.id,
        status="queued",
        config={},
    )
    return job


class TestTrainingServiceCreate:
    """Tests for creating training jobs."""

    @pytest.mark.asyncio
    async def test_create_training_job_success(
        self, training_service, mock_db, test_user_id, test_task, test_dataset
    ):
        """Test successful job creation."""
        # Setup mocks
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            test_task,
            test_dataset,
        ]
        mock_db.query.return_value.filter.return_value.count.return_value = 0

        job_data = TrainingJobCreate(
            task_id=test_task.id,
            dataset_id=test_dataset.id,
            config={"num_epochs": 3},
        )

        with patch.object(training_service, '_start_training_async', new=AsyncMock()):
            job = await training_service.create_training_job(
                mock_db, test_user_id, job_data
            )

        assert mock_db.add.called
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_create_training_job_task_not_found(
        self, training_service, mock_db, test_user_id, test_dataset
    ):
        """Test job creation with non-existent task."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        job_data = TrainingJobCreate(
            task_id=uuid4(),
            dataset_id=test_dataset.id,
        )

        with pytest.raises(ValueError, match="Task not found"):
            await training_service.create_training_job(
                mock_db, test_user_id, job_data
            )

    @pytest.mark.asyncio
    async def test_create_training_job_dataset_not_found(
        self, training_service, mock_db, test_user_id, test_task
    ):
        """Test job creation with non-existent dataset."""
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            test_task,
            None,
        ]

        job_data = TrainingJobCreate(
            task_id=test_task.id,
            dataset_id=uuid4(),
        )

        with pytest.raises(ValueError, match="Dataset not found"):
            await training_service.create_training_job(
                mock_db, test_user_id, job_data
            )

    @pytest.mark.asyncio
    async def test_create_training_job_exceeds_limit(
        self, training_service, mock_db, test_user_id, test_task, test_dataset
    ):
        """Test job creation exceeding resource limits."""
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            test_task,
            test_dataset,
        ]
        # Simulate max jobs reached
        mock_db.query.return_value.filter.return_value.count.return_value = 10

        job_data = TrainingJobCreate(
            task_id=test_task.id,
            dataset_id=test_dataset.id,
        )

        with pytest.raises(ValueError, match="Maximum active training jobs reached"):
            await training_service.create_training_job(
                mock_db, test_user_id, job_data
            )


class TestTrainingServiceGet:
    """Tests for getting training jobs."""

    @pytest.mark.asyncio
    async def test_get_training_job_success(
        self, training_service, mock_db, test_user_id, test_job
    ):
        """Test successful job retrieval."""
        mock_db.query.return_value.filter.return_value.first.return_value = test_job

        job = await training_service.get_training_job(
            mock_db, test_job.id, test_user_id
        )

        assert job == test_job

    @pytest.mark.asyncio
    async def test_get_training_job_not_found(
        self, training_service, mock_db, test_user_id
    ):
        """Test job retrieval for non-existent job."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(ValueError, match="Training job not found"):
            await training_service.get_training_job(
                mock_db, uuid4(), test_user_id
            )

    @pytest.mark.asyncio
    async def test_list_training_jobs(
        self, training_service, mock_db, test_user_id, test_task, test_job
    ):
        """Test listing training jobs."""
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [
            test_job
        ]

        jobs = await training_service.list_training_jobs(
            mock_db, test_task.id, test_user_id
        )

        assert len(jobs) == 1
        assert jobs[0] == test_job


class TestTrainingServiceUpdate:
    """Tests for updating training jobs."""

    @pytest.mark.asyncio
    async def test_update_training_job_status(
        self, training_service, mock_db, test_user_id, test_job
    ):
        """Test updating job status."""
        mock_db.query.return_value.filter.return_value.first.return_value = test_job

        update_data = TrainingJobUpdate(
            status="training",
            metrics={"loss": 0.5},
        )

        job = await training_service.update_training_job(
            mock_db, test_job.id, test_user_id, update_data
        )

        assert job.status == "training"
        assert job.metrics == {"loss": 0.5}
        assert job.started_at is not None
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_update_training_job_completion(
        self, training_service, mock_db, test_user_id, test_job
    ):
        """Test updating job to completed status."""
        mock_db.query.return_value.filter.return_value.first.return_value = test_job

        update_data = TrainingJobUpdate(
            status="completed",
            metrics={"final_loss": 0.1},
        )

        job = await training_service.update_training_job(
            mock_db, test_job.id, test_user_id, update_data
        )

        assert job.status == "completed"
        assert job.completed_at is not None
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_cancel_training_job(
        self, training_service, mock_db, test_user_id, test_job
    ):
        """Test cancelling a training job."""
        test_job.status = "training"
        mock_db.query.return_value.filter.return_value.first.return_value = test_job

        job = await training_service.cancel_training_job(
            mock_db, test_job.id, test_user_id
        )

        assert job.status == "cancelled"
        assert job.completed_at is not None
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_cancel_completed_job_fails(
        self, training_service, mock_db, test_user_id, test_job
    ):
        """Test that completed jobs cannot be cancelled."""
        test_job.status = "completed"
        mock_db.query.return_value.filter.return_value.first.return_value = test_job

        with pytest.raises(ValueError, match="Cannot cancel job"):
            await training_service.cancel_training_job(
                mock_db, test_job.id, test_user_id
            )


class TestTrainingServiceModelVersion:
    """Tests for model version management."""

    @pytest.mark.asyncio
    async def test_create_model_version_success(
        self, training_service, mock_db, test_user_id, test_job
    ):
        """Test successful model version creation."""
        test_job.status = "completed"
        mock_db.query.return_value.filter.return_value.first.return_value = test_job

        version_data = ModelVersionCreate(
            task_id=test_job.task_id,
            training_job_id=test_job.id,
            version="v1.0",
            s3_adapter_path="s3://bucket/adapter",
        )

        version = await training_service.create_model_version(
            mock_db, test_user_id, version_data
        )

        assert mock_db.add.called
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_create_model_version_job_not_completed(
        self, training_service, mock_db, test_user_id, test_job
    ):
        """Test model version creation with incomplete job."""
        test_job.status = "training"
        mock_db.query.return_value.filter.return_value.first.return_value = test_job

        version_data = ModelVersionCreate(
            task_id=test_job.task_id,
            training_job_id=test_job.id,
            version="v1.0",
        )

        with pytest.raises(ValueError, match="Training job must be completed"):
            await training_service.create_model_version(
                mock_db, test_user_id, version_data
            )


class TestS3PathBuilding:
    """Tests for S3 path building."""

    def test_build_s3_path_valid(self, training_service):
        """Test building valid S3 paths."""
        user_id = uuid4()
        resource_id = uuid4()

        path = training_service._build_s3_path(
            user_id, "datasets", resource_id, "train.jsonl"
        )

        assert path.startswith("finetune-models/")
        assert str(user_id) in path
        assert "datasets" in path
        assert str(resource_id) in path
        assert "train.jsonl" in path

    def test_build_s3_path_invalid_type(self, training_service):
        """Test building S3 path with invalid resource type."""
        user_id = uuid4()
        resource_id = uuid4()

        with pytest.raises(ValueError, match="Invalid resource type"):
            training_service._build_s3_path(
                user_id, "invalid", resource_id, "file.txt"
            )

    def test_build_s3_path_sanitizes_filename(self, training_service):
        """Test that filenames are sanitized."""
        user_id = uuid4()
        resource_id = uuid4()

        # Try directory traversal
        path = training_service._build_s3_path(
            user_id, "datasets", resource_id, "../../../etc/passwd"
        )

        assert ".." not in path
        assert "etcpasswd" in path  # Slashes removed


class TestModalIntegration:
    """Tests for Modal integration."""

    @pytest.mark.asyncio
    async def test_start_training_async_success(
        self, training_service, mock_db, test_job, test_dataset
    ):
        """Test successful training start."""
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            test_job,
            test_dataset,
        ]

        with patch("backend.services.training.Function") as mock_function:
            mock_train = MagicMock()
            mock_train.remote.return_value = {
                "status": "completed",
                "metrics": {"loss": 0.1},
                "model_path": "s3://bucket/model",
            }
            mock_function.lookup.return_value = mock_train

            with patch.object(
                training_service, '_subscribe_to_progress', new=AsyncMock()
            ):
                await training_service._start_training_async(mock_db, test_job.id)

        assert test_job.status == "completed"
        assert test_job.metrics == {"loss": 0.1}
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_start_training_async_modal_error(
        self, training_service, mock_db, test_job, test_dataset
    ):
        """Test training with Modal error."""
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            test_job,
            test_dataset,
        ]

        with patch("backend.services.training.Function") as mock_function:
            mock_function.lookup.side_effect = Exception("Modal error")

            with patch.object(
                training_service, '_subscribe_to_progress', new=AsyncMock()
            ):
                await training_service._start_training_async(mock_db, test_job.id)

        assert test_job.status == "failed"
        assert "Modal error" in test_job.error_message
        assert mock_db.commit.called
