"""Tests for training utilities."""
import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from uuid import uuid4

from training.utils import S3Manager, ProgressTracker, load_dataset_from_jsonl, format_examples_for_training


class TestS3Manager:
    """Tests for S3Manager."""

    def test_validate_s3_path_valid(self):
        """Test valid S3 paths."""
        user_id = uuid4()
        dataset_id = uuid4()

        valid_paths = [
            f"finetune-models/{user_id}/datasets/{dataset_id}/train.jsonl",
            f"finetune-models/{user_id}/models/{dataset_id}/model.bin",
            f"finetune-models/{user_id}/adapters/{dataset_id}/adapter_config.json",
        ]

        for path in valid_paths:
            assert S3Manager.validate_s3_path(path) is True

    def test_validate_s3_path_with_s3_prefix(self):
        """Test S3 path with s3:// prefix."""
        user_id = uuid4()
        dataset_id = uuid4()
        path = f"s3://finetune-models/{user_id}/datasets/{dataset_id}/train.jsonl"

        assert S3Manager.validate_s3_path(path) is True

    def test_validate_s3_path_directory_traversal(self):
        """Test that directory traversal is blocked."""
        user_id = uuid4()
        dataset_id = uuid4()

        invalid_paths = [
            f"finetune-models/{user_id}/datasets/{dataset_id}/../../../etc/passwd",
            f"finetune-models/{user_id}/../other-user/datasets/{dataset_id}/train.jsonl",
            f"../finetune-models/{user_id}/datasets/{dataset_id}/train.jsonl",
        ]

        for path in invalid_paths:
            with pytest.raises(ValueError, match="directory traversal"):
                S3Manager.validate_s3_path(path)

    def test_validate_s3_path_absolute_path(self):
        """Test that absolute paths are blocked."""
        invalid_path = "/etc/passwd"

        with pytest.raises(ValueError, match="directory traversal"):
            S3Manager.validate_s3_path(invalid_path)

    def test_validate_s3_path_wrong_format(self):
        """Test that incorrectly formatted paths are rejected."""
        invalid_paths = [
            "wrong-bucket/user/datasets/id/file.txt",
            "finetune-models/not-a-uuid/datasets/id/file.txt",
            "finetune-models/user-id/wrong-type/id/file.txt",
            "finetune-models/user-id/datasets/not-a-uuid/file.txt",
        ]

        for path in invalid_paths:
            with pytest.raises(ValueError, match="Invalid S3 path format"):
                S3Manager.validate_s3_path(path)

    @patch("training.utils.boto3.client")
    def test_download_file_success(self, mock_boto_client):
        """Test successful file download."""
        mock_s3 = Mock()
        mock_boto_client.return_value = mock_s3

        s3_manager = S3Manager()
        user_id = uuid4()
        dataset_id = uuid4()
        s3_path = f"finetune-models/{user_id}/datasets/{dataset_id}/train.jsonl"

        s3_manager.download_file(s3_path, "/tmp/local.jsonl")

        mock_s3.download_file.assert_called_once_with(
            "finetune-models",
            f"{user_id}/datasets/{dataset_id}/train.jsonl",
            "/tmp/local.jsonl",
        )

    @patch("training.utils.boto3.client")
    def test_download_file_invalid_path(self, mock_boto_client):
        """Test download with invalid path."""
        s3_manager = S3Manager()

        with pytest.raises(ValueError, match="Invalid S3 path"):
            s3_manager.download_file("../etc/passwd", "/tmp/file")

    @patch("training.utils.boto3.client")
    def test_upload_file_success(self, mock_boto_client):
        """Test successful file upload."""
        mock_s3 = Mock()
        mock_boto_client.return_value = mock_s3

        s3_manager = S3Manager()
        user_id = uuid4()
        model_id = uuid4()
        s3_path = f"finetune-models/{user_id}/models/{model_id}/model.bin"

        s3_manager.upload_file("/tmp/model.bin", s3_path)

        mock_s3.upload_file.assert_called_once_with(
            "/tmp/model.bin",
            "finetune-models",
            f"{user_id}/models/{model_id}/model.bin",
        )

    @patch("training.utils.boto3.client")
    def test_upload_file_invalid_path(self, mock_boto_client):
        """Test upload with invalid path."""
        s3_manager = S3Manager()

        with pytest.raises(ValueError, match="Invalid S3 path"):
            s3_manager.upload_file("/tmp/file", "../etc/passwd")


class TestProgressTracker:
    """Tests for ProgressTracker."""

    @patch("training.utils.redis.from_url")
    def test_publish_progress(self, mock_redis):
        """Test publishing progress update."""
        mock_client = Mock()
        mock_redis.return_value = mock_client

        job_id = str(uuid4())
        tracker = ProgressTracker("redis://localhost", job_id)

        tracker.publish_progress(
            status="training",
            progress=50,
            metrics={"loss": 0.5},
            message="Training step 100",
        )

        # Verify Redis publish was called
        mock_client.publish.assert_called_once()
        channel, data = mock_client.publish.call_args[0]

        assert channel == f"training:{job_id}:progress"
        parsed_data = json.loads(data)
        assert parsed_data["status"] == "training"
        assert parsed_data["progress"] == 50
        assert parsed_data["metrics"]["loss"] == 0.5
        assert parsed_data["message"] == "Training step 100"

    @patch("training.utils.redis.from_url")
    def test_publish_error(self, mock_redis):
        """Test publishing error."""
        mock_client = Mock()
        mock_redis.return_value = mock_client

        job_id = str(uuid4())
        tracker = ProgressTracker("redis://localhost", job_id)

        tracker.publish_error("Training failed: OOM")

        mock_client.publish.assert_called_once()
        channel, data = mock_client.publish.call_args[0]

        parsed_data = json.loads(data)
        assert parsed_data["status"] == "failed"
        assert "Training failed" in parsed_data["message"]

    @patch("training.utils.redis.from_url")
    def test_publish_completion(self, mock_redis):
        """Test publishing completion."""
        mock_client = Mock()
        mock_redis.return_value = mock_client

        job_id = str(uuid4())
        tracker = ProgressTracker("redis://localhost", job_id)

        metrics = {"final_loss": 0.1, "accuracy": 0.95}
        tracker.publish_completion(metrics)

        mock_client.publish.assert_called_once()
        channel, data = mock_client.publish.call_args[0]

        parsed_data = json.loads(data)
        assert parsed_data["status"] == "completed"
        assert parsed_data["progress"] == 100
        assert parsed_data["metrics"] == metrics


class TestDatasetLoading:
    """Tests for dataset loading and formatting."""

    def test_load_dataset_from_jsonl(self, tmp_path):
        """Test loading dataset from JSONL file."""
        # Create test JSONL file
        dataset_file = tmp_path / "train.jsonl"
        examples = [
            {"input": "Question 1", "output": "Answer 1"},
            {"input": "Question 2", "output": "Answer 2"},
        ]

        with open(dataset_file, "w") as f:
            for example in examples:
                f.write(json.dumps(example) + "\n")

        # Load dataset
        loaded = load_dataset_from_jsonl(str(dataset_file))

        assert len(loaded) == 2
        assert loaded[0]["input"] == "Question 1"
        assert loaded[1]["output"] == "Answer 2"

    def test_load_dataset_from_jsonl_empty_lines(self, tmp_path):
        """Test loading dataset with empty lines."""
        dataset_file = tmp_path / "train.jsonl"

        with open(dataset_file, "w") as f:
            f.write('{"input": "Q1", "output": "A1"}\n')
            f.write("\n")  # Empty line
            f.write('{"input": "Q2", "output": "A2"}\n')

        loaded = load_dataset_from_jsonl(str(dataset_file))

        assert len(loaded) == 2

    def test_format_examples_for_training(self):
        """Test formatting examples for training."""
        examples = [
            {"input": "What is Python?", "output": "A programming language"},
            {"input": "What is AI?", "output": "Artificial Intelligence"},
        ]

        formatted = format_examples_for_training(examples)

        assert len(formatted) == 2
        assert "### Instruction:" in formatted[0]["text"]
        assert "### Response:" in formatted[0]["text"]
        assert "What is Python?" in formatted[0]["text"]
        assert "A programming language" in formatted[0]["text"]
