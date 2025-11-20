"""Tests for task API endpoints."""
import pytest
from uuid import uuid4


class TestTaskEndpoints:
    """Test task CRUD endpoints."""

    def test_create_task(self, client, auth_headers):
        """Test creating a new task."""
        response = client.post(
            "/api/v1/tasks/",
            json={
                "name": "New Task",
                "description": "Task description",
                "task_type": "classification",
                "config": {"key": "value"},
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "New Task"
        assert data["description"] == "Task description"
        assert data["task_type"] == "classification"
        assert "id" in data

    def test_create_task_without_auth(self, client):
        """Test creating task without authentication."""
        response = client.post(
            "/api/v1/tasks/",
            json={
                "name": "New Task",
                "description": "Task description",
            },
        )
        assert response.status_code == 401

    def test_list_tasks(self, client, auth_headers, test_task):
        """Test listing user's tasks."""
        response = client.get("/api/v1/tasks/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert data[0]["name"] == "Test Task"

    def test_get_task(self, client, auth_headers, test_task):
        """Test getting task details."""
        response = client.get(
            f"/api/v1/tasks/{test_task.id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_task.id)
        assert data["name"] == "Test Task"
        assert "dataset_count" in data
        assert "training_job_count" in data
        assert "model_version_count" in data

    def test_get_nonexistent_task(self, client, auth_headers):
        """Test getting non-existent task."""
        response = client.get(
            f"/api/v1/tasks/{uuid4()}",
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_update_task(self, client, auth_headers, test_task):
        """Test updating a task."""
        response = client.patch(
            f"/api/v1/tasks/{test_task.id}",
            json={"name": "Updated Task"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Task"

    def test_delete_task(self, client, auth_headers, test_task):
        """Test deleting a task."""
        response = client.delete(
            f"/api/v1/tasks/{test_task.id}",
            headers=auth_headers,
        )
        assert response.status_code == 204

        # Verify task is deleted
        response = client.get(
            f"/api/v1/tasks/{test_task.id}",
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_unauthorized_access_to_other_user_task(self, client, db, test_task):
        """Test that users cannot access other users' tasks."""
        # Create another user
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

        # Login as other user
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "other@example.com",
                "password": "password",
            },
        )
        assert response.status_code == 200
        other_headers = {"Authorization": f"Bearer {response.json()['access_token']}"}

        # Try to access test_task (owned by test_user)
        response = client.get(
            f"/api/v1/tasks/{test_task.id}",
            headers=other_headers,
        )
        assert response.status_code == 404  # Should return 404 to prevent IDOR
