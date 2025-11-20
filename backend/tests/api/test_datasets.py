"""Tests for dataset API endpoints."""
import pytest
from uuid import uuid4


class TestDatasetEndpoints:
    """Test dataset CRUD endpoints."""

    def test_create_dataset(self, client, auth_headers, test_task):
        """Test creating a new dataset."""
        response = client.post(
            "/api/v1/datasets/",
            json={
                "task_id": str(test_task.id),
                "version": 1,
                "examples": [
                    {
                        "input": "Test input 1",
                        "output": "Test output 1",
                        "example_metadata": {},
                    },
                    {
                        "input": "Test input 2",
                        "output": "Test output 2",
                        "example_metadata": {},
                    },
                ],
                "stats": {"count": 2},
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["task_id"] == str(test_task.id)
        assert data["version"] == 1
        assert "id" in data

    def test_create_dataset_without_auth(self, client, test_task):
        """Test creating dataset without authentication."""
        response = client.post(
            "/api/v1/datasets/",
            json={
                "task_id": str(test_task.id),
                "version": 1,
                "examples": [
                    {"input": "Test", "output": "Test"},
                ],
            },
        )
        assert response.status_code == 401

    def test_list_datasets_for_task(self, client, auth_headers, test_task, test_dataset):
        """Test listing datasets for a task."""
        response = client.get(
            f"/api/v1/datasets/task/{test_task.id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert data[0]["task_id"] == str(test_task.id)

    def test_get_dataset_with_examples(self, client, auth_headers, test_dataset):
        """Test getting dataset details with examples."""
        response = client.get(
            f"/api/v1/datasets/{test_dataset.id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_dataset.id)
        assert "examples" in data
        assert len(data["examples"]) == 2
        assert data["example_count"] == 2

    def test_add_examples_to_dataset(self, client, auth_headers, test_dataset):
        """Test adding examples to an existing dataset."""
        response = client.post(
            f"/api/v1/datasets/{test_dataset.id}/examples",
            json=[
                {
                    "input": "New input",
                    "output": "New output",
                    "example_metadata": {},
                },
            ],
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["input"] == "New input"

    def test_unauthorized_access_to_dataset(self, client, db, test_dataset):
        """Test that users cannot access other users' datasets."""
        from backend.models import User
        from backend.services.auth import auth_service

        other_user = User(
            id=uuid4(),
            email="other@example.com",
            hashed_password=auth_service.hash_password("password"),
            full_name="Other User",
            is_active="1",
        )
        db.add(other_user)
        db.commit()

        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "other@example.com",
                "password": "password",
            },
        )
        other_headers = {"Authorization": f"Bearer {response.json()['access_token']}"}

        response = client.get(
            f"/api/v1/datasets/{test_dataset.id}",
            headers=other_headers,
        )
        assert response.status_code == 404
