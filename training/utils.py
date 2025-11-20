"""Training utility functions."""
import os
import re
import json
import boto3
from pathlib import Path
from typing import List, Dict, Any, Optional
import redis


class S3Manager:
    """S3 manager with path validation for security."""

    # Allowed S3 path pattern: finetune-models/<user_id>/<resource_type>/<resource_id>/...
    PATH_PATTERN = re.compile(
        r"^finetune-models/[a-f0-9\-]{36}/(datasets|models|adapters)/[a-f0-9\-]{36}/[\w\-\.]+$"
    )

    def __init__(
        self,
        endpoint_url: Optional[str] = None,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        region_name: str = "us-east-1",
    ):
        """Initialize S3 client."""
        self.s3_client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region_name,
        )

    @staticmethod
    def validate_s3_path(s3_path: str) -> bool:
        """
        Validate S3 path to prevent directory traversal and unauthorized access.

        Security: Ensures paths follow expected pattern and prevents:
        - Directory traversal (../)
        - Absolute paths
        - Access to other users' data

        Args:
            s3_path: S3 path to validate (without s3:// prefix)

        Returns:
            True if path is valid

        Raises:
            ValueError: If path is invalid
        """
        # Remove s3:// prefix if present
        if s3_path.startswith("s3://"):
            s3_path = s3_path[5:]

        # Check for directory traversal attempts
        if ".." in s3_path or s3_path.startswith("/"):
            raise ValueError(f"Invalid S3 path: directory traversal detected in {s3_path}")

        # Validate against pattern
        if not S3Manager.PATH_PATTERN.match(s3_path):
            raise ValueError(
                f"Invalid S3 path format: {s3_path}. "
                "Expected: finetune-models/<user_id>/<resource_type>/<resource_id>/filename"
            )

        return True

    def download_file(self, s3_path: str, local_path: str) -> None:
        """
        Download file from S3 with path validation.

        Args:
            s3_path: S3 path (e.g., "finetune-models/user-id/datasets/dataset-id/train.jsonl")
            local_path: Local file path to save to
        """
        # Validate path
        self.validate_s3_path(s3_path)

        # Extract bucket and key
        parts = s3_path.split("/", 1)
        bucket = parts[0]
        key = parts[1] if len(parts) > 1 else ""

        # Download
        self.s3_client.download_file(bucket, key, local_path)

    def upload_file(self, local_path: str, s3_path: str) -> None:
        """
        Upload file to S3 with path validation.

        Args:
            local_path: Local file path to upload
            s3_path: S3 destination path
        """
        # Validate path
        self.validate_s3_path(s3_path)

        # Extract bucket and key
        parts = s3_path.split("/", 1)
        bucket = parts[0]
        key = parts[1] if len(parts) > 1 else ""

        # Upload
        self.s3_client.upload_file(local_path, bucket, key)

    def upload_directory(self, local_dir: str, s3_prefix: str) -> List[str]:
        """
        Upload directory to S3.

        Args:
            local_dir: Local directory path
            s3_prefix: S3 prefix (will be validated for each file)

        Returns:
            List of uploaded S3 paths
        """
        uploaded = []
        local_path = Path(local_dir)

        for file_path in local_path.rglob("*"):
            if file_path.is_file():
                relative_path = file_path.relative_to(local_path)
                s3_path = f"{s3_prefix}/{relative_path}"
                self.upload_file(str(file_path), s3_path)
                uploaded.append(s3_path)

        return uploaded


class ProgressTracker:
    """Progress tracker using Redis pub/sub."""

    def __init__(self, redis_url: str, job_id: str):
        """
        Initialize progress tracker.

        Args:
            redis_url: Redis connection URL
            job_id: Training job ID
        """
        self.redis_client = redis.from_url(redis_url)
        self.channel = f"training:{job_id}:progress"
        self.job_id = job_id

    def publish_progress(
        self,
        status: str,
        progress: float,
        metrics: Optional[Dict[str, Any]] = None,
        message: Optional[str] = None,
    ) -> None:
        """
        Publish progress update.

        Args:
            status: Status (training, evaluating, completed, failed)
            progress: Progress percentage (0-100)
            metrics: Training metrics (loss, accuracy, etc.)
            message: Optional message
        """
        update = {
            "job_id": self.job_id,
            "status": status,
            "progress": progress,
            "metrics": metrics or {},
            "message": message or "",
        }

        self.redis_client.publish(self.channel, json.dumps(update))

    def publish_error(self, error_message: str) -> None:
        """Publish error."""
        self.publish_progress(
            status="failed",
            progress=0,
            message=error_message,
        )

    def publish_completion(self, metrics: Dict[str, Any]) -> None:
        """Publish training completion."""
        self.publish_progress(
            status="completed",
            progress=100,
            metrics=metrics,
            message="Training completed successfully",
        )


def load_dataset_from_jsonl(file_path: str) -> List[Dict[str, str]]:
    """
    Load dataset from JSONL file.

    Args:
        file_path: Path to JSONL file

    Returns:
        List of examples (each with 'input' and 'output')
    """
    examples = []
    with open(file_path, "r") as f:
        for line in f:
            if line.strip():
                examples.append(json.loads(line))
    return examples


def format_examples_for_training(examples: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    Format examples for training.

    Args:
        examples: List of examples with 'input' and 'output'

    Returns:
        List of formatted examples with 'text' field
    """
    formatted = []
    for example in examples:
        # Format as instruction-following
        text = f"### Instruction:\n{example['input']}\n\n### Response:\n{example['output']}"
        formatted.append({"text": text})
    return formatted
