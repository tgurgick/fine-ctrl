"""Security tests for authentication system."""
import pytest
from datetime import datetime, timedelta
from jose import jwt
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.main import app
from backend.config import settings
from backend.services.auth import AuthService
from backend.models.user import User


client = TestClient(app)


class TestPasswordSecurity:
    """Test password hashing and verification security."""

    def test_passwords_are_bcrypt_hashed(self, db: Session):
        """Verify passwords are hashed with bcrypt (not plaintext)."""
        auth_service = AuthService()

        # Create user
        email = "test@example.com"
        password = "SecureP@ssw0rd123"

        user = auth_service.register(db, email, password, "Test User")

        # Verify password is NOT stored in plaintext
        assert user.password_hash != password
        # Verify bcrypt hash format ($2b$)
        assert user.password_hash.startswith("$2b$")
        # Verify hash is 60 characters (bcrypt standard)
        assert len(user.password_hash) == 60

    def test_password_verification_timing_attack_resistant(self, db: Session):
        """Ensure password verification is timing-safe."""
        auth_service = AuthService()

        # Register user
        user = auth_service.register(db, "user@example.com", "Password123!", "Test")

        # Valid password check
        valid_start = datetime.utcnow()
        auth_service.verify_password("Password123!", user.password_hash)
        valid_duration = (datetime.utcnow() - valid_start).total_seconds()

        # Invalid password check (should take similar time due to bcrypt)
        invalid_start = datetime.utcnow()
        auth_service.verify_password("WrongPassword!", user.password_hash)
        invalid_duration = (datetime.utcnow() - invalid_start).total_seconds()

        # Times should be within 20% of each other (bcrypt constant-time)
        # Note: bcrypt naturally prevents timing attacks
        assert abs(valid_duration - invalid_duration) / valid_duration < 0.2


class TestJWTSecurity:
    """Test JWT token security."""

    def test_jwt_tokens_have_expiration(self):
        """Verify JWT tokens expire correctly."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "jwt@example.com",
                "password": "SecureP@ss123!",
                "full_name": "JWT Test"
            }
        )
        assert response.status_code == 200

        token = response.json()["access_token"]

        # Decode without verification to inspect claims
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )

        # Verify expiration claim exists
        assert "exp" in payload
        assert "iat" in payload  # Issued at

        # Verify expiration is in the future but not too far
        exp_time = datetime.fromtimestamp(payload["exp"])
        now = datetime.utcnow()

        assert exp_time > now
        # Access token should expire in ~15 minutes
        assert (exp_time - now).total_seconds() < 1800  # 30 minutes max

    def test_expired_tokens_are_rejected(self):
        """Verify expired tokens cannot be used."""
        # Create an expired token
        expired_time = datetime.utcnow() - timedelta(hours=1)
        payload = {
            "sub": "123",
            "email": "expired@example.com",
            "type": "access",
            "exp": expired_time,
            "iat": expired_time - timedelta(minutes=15)
        }

        expired_token = jwt.encode(
            payload,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM
        )

        # Try to use expired token
        response = client.get(
            "/api/v1/api-keys",
            headers={"Authorization": f"Bearer {expired_token}"}
        )

        assert response.status_code == 401
        assert "expired" in response.json()["detail"].lower()

    def test_refresh_token_cannot_be_used_as_access_token(self):
        """Ensure refresh tokens cannot access protected endpoints."""
        # Register and login
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "refresh@example.com",
                "password": "SecureP@ss123!",
                "full_name": "Refresh Test"
            }
        )

        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "refresh@example.com",
                "password": "SecureP@ss123!"
            }
        )

        refresh_token = login_response.json()["refresh_token"]

        # Try to use refresh token as access token
        response = client.get(
            "/api/v1/api-keys",
            headers={"Authorization": f"Bearer {refresh_token}"}
        )

        assert response.status_code == 401

    def test_token_signature_is_verified(self):
        """Verify tampered tokens are rejected."""
        # Get valid token
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "tamper@example.com",
                "password": "SecureP@ss123!",
                "full_name": "Tamper Test"
            }
        )

        token = response.json()["access_token"]

        # Tamper with token (change last character)
        tampered_token = token[:-5] + "XXXXX"

        # Try to use tampered token
        response = client.get(
            "/api/v1/api-keys",
            headers={"Authorization": f"Bearer {tampered_token}"}
        )

        assert response.status_code == 401


class TestAuthenticationBypass:
    """Test for authentication bypass vulnerabilities."""

    def test_cannot_access_protected_routes_without_auth(self):
        """Verify protected endpoints require authentication."""
        protected_endpoints = [
            ("/api/v1/api-keys", "GET"),
            ("/api/v1/api-keys", "POST"),
        ]

        for endpoint, method in protected_endpoints:
            if method == "GET":
                response = client.get(endpoint)
            elif method == "POST":
                response = client.post(endpoint, json={})

            assert response.status_code == 401, f"{method} {endpoint} should require auth"

    def test_cannot_bypass_auth_with_malformed_headers(self):
        """Test various auth bypass techniques."""
        bypass_attempts = [
            {},  # No header
            {"Authorization": ""},  # Empty
            {"Authorization": "Bearer"},  # No token
            {"Authorization": "Basic dGVzdDp0ZXN0"},  # Wrong scheme
            {"Authorization": "Bearer null"},  # Null token
            {"Authorization": "Bearer undefined"},  # Undefined token
            {"X-User-Id": "123"},  # Trying to spoof user ID
        ]

        for headers in bypass_attempts:
            response = client.get("/api/v1/api-keys", headers=headers)
            assert response.status_code == 401

    def test_sql_injection_in_login(self):
        """Test SQL injection attempts in login."""
        sql_payloads = [
            "admin'--",
            "admin' OR '1'='1",
            "' OR 1=1--",
            "admin'; DROP TABLE users;--",
        ]

        for payload in sql_payloads:
            response = client.post(
                "/api/v1/auth/login",
                json={
                    "email": payload,
                    "password": "anything"
                }
            )

            # Should return 401 (not 500 or success)
            assert response.status_code == 401


class TestSessionSecurity:
    """Test session and token security."""

    def test_tokens_contain_minimal_information(self):
        """Ensure tokens don't leak sensitive data."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "minimal@example.com",
                "password": "SecureP@ss123!",
                "full_name": "Minimal Test"
            }
        )

        token = response.json()["access_token"]

        # Decode token (without verification for inspection)
        payload = jwt.decode(
            token,
            options={"verify_signature": False}
        )

        # Should NOT contain sensitive data
        assert "password" not in payload
        assert "password_hash" not in payload

        # Should contain only necessary claims
        assert "sub" in payload  # User ID
        assert "email" in payload
        assert "type" in payload
        assert "exp" in payload

    def test_different_users_get_different_tokens(self):
        """Verify token uniqueness per user."""
        user1_response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "user1@example.com",
                "password": "SecureP@ss123!",
                "full_name": "User 1"
            }
        )

        user2_response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "user2@example.com",
                "password": "SecureP@ss123!",
                "full_name": "User 2"
            }
        )

        token1 = user1_response.json()["access_token"]
        token2 = user2_response.json()["access_token"]

        # Tokens should be different
        assert token1 != token2

        # Decode and verify different user IDs
        payload1 = jwt.decode(token1, options={"verify_signature": False})
        payload2 = jwt.decode(token2, options={"verify_signature": False})

        assert payload1["sub"] != payload2["sub"]
        assert payload1["email"] != payload2["email"]


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
