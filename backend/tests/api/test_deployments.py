"""Tests for deployment API endpoints."""
import pytest
from uuid import uuid4


class TestDeploymentEndpoints:
    """Test deployment endpoints."""

    def test_create_deployment(self, client, auth_headers, test_model_version):
        """Test creating a new deployment."""
        response = client.post(
            "/api/v1/deployments/",
            json={
                "model_version_id": str(test_model_version.id),
                "name": "Test Deployment",
                "is_public": False,
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["model_version_id"] == str(test_model_version.id)
        assert data["name"] == "Test Deployment"
        assert data["status"] == "active"
        assert "endpoint_url" in data
        assert "id" in data

    def test_list_deployments(self, client, auth_headers, test_deployment):
        """Test listing user's deployments."""
        response = client.get(
            "/api/v1/deployments/",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert data[0]["name"] == "Test Deployment"

    def test_get_deployment(self, client, auth_headers, test_deployment):
        """Test getting deployment details."""
        response = client.get(
            f"/api/v1/deployments/{test_deployment.id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_deployment.id)
        assert data["status"] == "active"
        assert "endpoint_url" in data

    def test_update_deployment(self, client, auth_headers, test_deployment):
        """Test updating deployment settings."""
        response = client.patch(
            f"/api/v1/deployments/{test_deployment.id}",
            json={
                "name": "Updated Deployment",
                "is_public": True,
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Deployment"
        assert data["is_public"] is True

    def test_deactivate_deployment(self, client, auth_headers, test_deployment):
        """Test deactivating a deployment."""
        response = client.post(
            f"/api/v1/deployments/{test_deployment.id}/deactivate",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "inactive"

    def test_inference_requires_active_deployment(self, client, auth_headers, db, test_deployment):
        """Test that inference requires active deployment."""
        # Deactivate deployment
        test_deployment.status = "inactive"
        db.commit()

        response = client.post(
            f"/api/v1/deployments/{test_deployment.id}/infer",
            json={"input": "Test input"},
            headers=auth_headers,
        )
        assert response.status_code == 400

    def test_public_deployment_access(self, client, db, test_deployment):
        """Test that public deployments can be accessed by other users."""
        # Make deployment public
        test_deployment.is_public = True
        db.commit()

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
        other_headers = {"Authorization": f"Bearer {response.json()['access_token']}"}

        # Try to access public deployment (should get 501 placeholder response)
        response = client.post(
            f"/api/v1/deployments/{test_deployment.id}/infer",
            json={"input": "Test input"},
            headers=other_headers,
        )
        assert response.status_code == 501  # Not implemented yet, but authorized

    def test_private_deployment_unauthorized(self, client, db, test_deployment):
        """Test that private deployments cannot be accessed by other users."""
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

        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "other@example.com",
                "password": "password",
            },
        )
        other_headers = {"Authorization": f"Bearer {response.json()['access_token']}"}

        # Try to access private deployment
        response = client.post(
            f"/api/v1/deployments/{test_deployment.id}/infer",
            json={"input": "Test input"},
            headers=other_headers,
        )
        assert response.status_code == 404  # Should return 404 to prevent IDOR
