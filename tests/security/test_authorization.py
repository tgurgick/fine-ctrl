"""Security tests for authorization and IDOR (Insecure Direct Object Reference) vulnerabilities."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from uuid import uuid4

from backend.main import app
from backend.models.api_key import APIKey
from backend.services.auth import AuthService
from backend.services.api_keys import APIKeyService


client = TestClient(app)


class TestIDORPrevention:
    """Test Insecure Direct Object Reference (IDOR) vulnerabilities."""

    def test_cannot_access_other_users_api_keys(self, db: Session):
        """Verify users cannot access other users' API keys."""
        auth_service = AuthService()
        api_key_service = APIKeyService()

        # Create two users
        user1 = auth_service.register(db, "user1@example.com", "Password1!", "User 1")
        user2 = auth_service.register(db, "user2@example.com", "Password2!", "User 2")

        # User 1 creates an API key
        user1_key, _ = api_key_service.create_api_key(
            db,
            user1.id,
            "User 1 Key",
            expires_in_days=30
        )

        # User 2 logs in
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": "user2@example.com", "password": "Password2!"}
        )
        user2_token = login_response.json()["access_token"]

        # User 2 tries to access User 1's API key
        response = client.get(
            f"/api/v1/api-keys/{user1_key.id}",
            headers={"Authorization": f"Bearer {user2_token}"}
        )

        # Should return 404 (not 403 to prevent enumeration)
        assert response.status_code == 404

    def test_cannot_delete_other_users_api_keys(self, db: Session):
        """Verify users cannot delete other users' API keys."""
        auth_service = AuthService()
        api_key_service = APIKeyService()

        # Create two users
        user1 = auth_service.register(db, "alice@example.com", "Password1!", "Alice")
        user2 = auth_service.register(db, "bob@example.com", "Password2!", "Bob")

        # User 1 creates an API key
        user1_key, _ = api_key_service.create_api_key(
            db,
            user1.id,
            "Alice's Key",
            expires_in_days=30
        )

        # User 2 logs in
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": "bob@example.com", "password": "Password2!"}
        )
        user2_token = login_response.json()["access_token"]

        # User 2 tries to delete User 1's API key
        response = client.delete(
            f"/api/v1/api-keys/{user1_key.id}",
            headers={"Authorization": f"Bearer {user2_token}"}
        )

        # Should return 404
        assert response.status_code == 404

        # Verify key still exists
        key = api_key_service.get_api_key(db, user1_key.id, user1.id)
        assert key is not None

    def test_cannot_list_other_users_api_keys(self, db: Session):
        """Verify users can only see their own API keys."""
        auth_service = AuthService()
        api_key_service = APIKeyService()

        # Create two users with API keys
        user1 = auth_service.register(db, "eve@example.com", "Password1!", "Eve")
        user2 = auth_service.register(db, "mallory@example.com", "Password2!", "Mallory")

        # Each user creates API keys
        api_key_service.create_api_key(db, user1.id, "Eve's Key", expires_in_days=30)
        api_key_service.create_api_key(db, user1.id, "Eve's Key 2", expires_in_days=30)
        api_key_service.create_api_key(db, user2.id, "Mallory's Key", expires_in_days=30)

        # User 1 logs in and lists keys
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": "eve@example.com", "password": "Password1!"}
        )
        user1_token = login_response.json()["access_token"]

        response = client.get(
            "/api/v1/api-keys",
            headers={"Authorization": f"Bearer {user1_token}"}
        )

        assert response.status_code == 200
        api_keys = response.json()

        # Should only see own keys (2)
        assert len(api_keys) == 2
        for key in api_keys:
            assert key["name"] in ["Eve's Key", "Eve's Key 2"]

    def test_cannot_use_uuid_guessing_to_access_resources(self, db: Session):
        """Test that random UUID guessing doesn't expose resources."""
        # User logs in
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "attacker@example.com",
                "password": "Password1!",
                "full_name": "Attacker"
            }
        )

        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": "attacker@example.com", "password": "Password1!"}
        )
        token = login_response.json()["access_token"]

        # Try random UUIDs
        random_uuids = [str(uuid4()) for _ in range(10)]

        for random_id in random_uuids:
            response = client.get(
                f"/api/v1/api-keys/{random_id}",
                headers={"Authorization": f"Bearer {token}"}
            )

            # Should return 404 (not 500 or 403)
            assert response.status_code == 404


class TestResourceOwnership:
    """Test resource ownership enforcement."""

    def test_api_key_ownership_verified_on_all_operations(self, db: Session):
        """Verify ownership is checked for all CRUD operations."""
        auth_service = AuthService()
        api_key_service = APIKeyService()

        # Create owner and attacker
        owner = auth_service.register(db, "owner@example.com", "Password1!", "Owner")
        attacker = auth_service.register(db, "attacker@example.com", "Password2!", "Attacker")

        # Owner creates API key
        owner_key, _ = api_key_service.create_api_key(
            db,
            owner.id,
            "Owner's Key",
            expires_in_days=30
        )

        # Attacker logs in
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": "attacker@example.com", "password": "Password2!"}
        )
        attacker_token = login_response.json()["access_token"]

        # Test all operations
        operations = [
            ("GET", f"/api/v1/api-keys/{owner_key.id}", None),
            ("DELETE", f"/api/v1/api-keys/{owner_key.id}", None),
        ]

        for method, endpoint, data in operations:
            if method == "GET":
                response = client.get(
                    endpoint,
                    headers={"Authorization": f"Bearer {attacker_token}"}
                )
            elif method == "DELETE":
                response = client.delete(
                    endpoint,
                    headers={"Authorization": f"Bearer {attacker_token}"}
                )

            # All should return 404
            assert response.status_code == 404, f"{method} {endpoint} should deny access"


class TestAuthorizationBypass:
    """Test for authorization bypass vulnerabilities."""

    def test_cannot_bypass_authz_with_modified_jwt(self, db: Session):
        """Test that modifying JWT claims doesn't bypass authorization."""
        from jose import jwt
        from backend.config import settings

        # Register user
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "victim@example.com",
                "password": "Password1!",
                "full_name": "Victim"
            }
        )

        # Create another user and get their ID
        response2 = client.post(
            "/api/v1/auth/register",
            json={
                "email": "attacker2@example.com",
                "password": "Password2!",
                "full_name": "Attacker"
            }
        )

        # Get attacker's token
        login = client.post(
            "/api/v1/auth/login",
            json={"email": "attacker2@example.com", "password": "Password2!"}
        )
        token = login.json()["access_token"]

        # Decode token
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )

        # Try to modify user ID (this would fail signature verification)
        # Just verify the signature is actually checked
        payload["sub"] = "00000000-0000-0000-0000-000000000000"

        # Re-encode with WRONG secret
        malicious_token = jwt.encode(
            payload,
            "wrong-secret",
            algorithm=settings.JWT_ALGORITHM
        )

        # Try to use malicious token
        response = client.get(
            "/api/v1/api-keys",
            headers={"Authorization": f"Bearer {malicious_token}"}
        )

        # Should be rejected
        assert response.status_code == 401

    def test_parameter_pollution_does_not_bypass_authz(self, db: Session):
        """Test parameter pollution attacks."""
        auth_service = AuthService()

        # Create user
        user = auth_service.register(db, "test@example.com", "Password1!", "Test")

        # Login
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "Password1!"}
        )
        token = login_response.json()["access_token"]

        # Try parameter pollution
        random_id = str(uuid4())
        response = client.get(
            f"/api/v1/api-keys/{random_id}?user_id={user.id}",
            headers={"Authorization": f"Bearer {token}"}
        )

        # Should still check ownership properly
        assert response.status_code == 404


class TestPrivilegeEscalation:
    """Test for privilege escalation vulnerabilities."""

    def test_cannot_escalate_to_admin(self, db: Session):
        """Verify users cannot elevate privileges."""
        # Register regular user
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "regular@example.com",
                "password": "Password1!",
                "full_name": "Regular User",
                "is_admin": True  # Try to inject admin flag
            }
        )

        assert response.status_code == 200

        # Login
        login = client.post(
            "/api/v1/auth/login",
            json={"email": "regular@example.com", "password": "Password1!"}
        )

        token = login.json()["access_token"]

        # Decode token and verify not admin
        from jose import jwt
        payload = jwt.decode(token, options={"verify_signature": False})

        # Should not have admin privileges
        assert payload.get("is_admin") != True

    def test_plan_limits_cannot_be_bypassed(self, db: Session):
        """Verify plan-based limits are enforced."""
        # Register free tier user
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "free@example.com",
                "password": "Password1!",
                "full_name": "Free User",
                "plan": "enterprise"  # Try to inject enterprise plan
            }
        )

        # Login
        login = client.post(
            "/api/v1/auth/login",
            json={"email": "free@example.com", "password": "Password1!"}
        )

        token = login.json()["access_token"]

        # Decode token
        from jose import jwt
        payload = jwt.decode(token, options={"verify_signature": False})

        # Should be free plan (default)
        assert payload.get("plan") == "free"


# Pytest fixtures
@pytest.fixture
def db():
    """Database session fixture."""
    from backend.database import SessionLocal
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        db.query(APIKey).delete()
        db.commit()
