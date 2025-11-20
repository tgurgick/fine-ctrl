"""Tests for training API endpoints."""
import pytest
from uuid import uuid4


class TestTrainingEndpoints:
    """Test training job endpoints."""

    def test_create_training_job(self, client, auth_headers, test_task, test_dataset):
        """Test creating a new training job."""
        response = client.post(
            "/api/v1/training/jobs",
            json={
                "task_id": str(test_task.id),
                "dataset_id": str(test_dataset.id),
                "config": {"epochs": 3},
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["task_id"] == str(test_task.id)
        assert data["dataset_id"] == str(test_dataset.id)
        assert data["status"] == "queued"
        assert "id" in data

    def test_list_training_jobs(self, client, auth_headers, test_task, test_training_job):
        """Test listing training jobs for a task."""
        response = client.get(
            f"/api/v1/training/jobs/task/{test_task.id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert data[0]["task_id"] == str(test_task.id)

    def test_get_training_job(self, client, auth_headers, test_training_job):
        """Test getting training job details."""
        response = client.get(
            f"/api/v1/training/jobs/{test_training_job.id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_training_job.id)
        assert data["status"] == "queued"

    def test_update_training_job(self, client, auth_headers, test_training_job):
        """Test updating training job status."""
        response = client.patch(
            f"/api/v1/training/jobs/{test_training_job.id}",
            json={
                "status": "training",
                "metrics": {"loss": 0.5},
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "training"
        assert data["metrics"]["loss"] == 0.5

    def test_cancel_training_job(self, client, auth_headers, test_training_job):
        """Test cancelling a training job."""
        response = client.post(
            f"/api/v1/training/jobs/{test_training_job.id}/cancel",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "cancelled"

    def test_cancel_completed_job_fails(self, client, auth_headers, db, test_training_job):
        """Test that cancelling a completed job fails."""
        # Update job to completed status
        test_training_job.status = "completed"
        db.commit()

        response = client.post(
            f"/api/v1/training/jobs/{test_training_job.id}/cancel",
            headers=auth_headers,
        )
        assert response.status_code == 400

    def test_create_model_version(self, client, auth_headers, test_task, test_training_job):
        """Test creating a model version."""
        response = client.post(
            "/api/v1/training/models",
            json={
                "task_id": str(test_task.id),
                "training_job_id": str(test_training_job.id),
                "version": "v1.0",
                "s3_weights_path": "s3://bucket/weights.bin",
                "s3_adapter_path": "s3://bucket/adapter.bin",
                "inference_config": {},
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["version"] == "v1.0"
        assert data["status"] == "ready"

    def test_list_model_versions(self, client, auth_headers, test_task, test_model_version):
        """Test listing model versions for a task."""
        response = client.get(
            f"/api/v1/training/models/task/{test_task.id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert data[0]["task_id"] == str(test_task.id)

    def test_get_model_version(self, client, auth_headers, test_model_version):
        """Test getting model version details."""
        response = client.get(
            f"/api/v1/training/models/{test_model_version.id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_model_version.id)
        assert data["version"] == "v1.0"
