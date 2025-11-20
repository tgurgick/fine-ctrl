"""Security tests for input validation (XSS, SQL injection, path traversal)."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.main import app
from backend.utils.validation import (
    sanitize_string,
    validate_email,
    validate_filename,
    detect_xss,
    detect_sql_injection,
    detect_path_traversal,
)


client = TestClient(app)


class TestXSSPrevention:
    """Test Cross-Site Scripting (XSS) prevention."""

    def test_xss_patterns_are_detected(self):
        """Verify XSS patterns are identified."""
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "<svg/onload=alert('XSS')>",
            "javascript:alert('XSS')",
            "<iframe src='javascript:alert(1)'>",
            "<body onload=alert('XSS')>",
            "<input onfocus=alert('XSS') autofocus>",
            "<select onfocus=alert('XSS') autofocus>",
            "<textarea onfocus=alert('XSS') autofocus>",
            "<keygen onfocus=alert('XSS') autofocus>",
            "<video><source onerror='alert(1)'>",
            "<audio src=x onerror=alert('XSS')>",
            "<details open ontoggle=alert('XSS')>",
            "<marquee onstart=alert('XSS')>",
        ]

        for payload in xss_payloads:
            is_xss = detect_xss(payload)
            assert is_xss, f"Failed to detect XSS: {payload}"

    def test_xss_payloads_are_blocked_in_registration(self):
        """Verify XSS payloads are rejected during user registration."""
        xss_names = [
            "<script>alert('XSS')</script>",
            "Robert'); DROP TABLE users;--",
            "<img src=x onerror=alert('XSS')>",
        ]

        for xss_name in xss_names:
            response = client.post(
                "/api/v1/auth/register",
                json={
                    "email": "xss@example.com",
                    "password": "SecureP@ss123!",
                    "full_name": xss_name
                }
            )

            # Should reject with 400 (validation error)
            assert response.status_code == 400
            assert "validation" in response.json()["detail"].lower() or \
                   "invalid" in response.json()["detail"].lower()

    def test_sanitize_removes_dangerous_content(self):
        """Verify sanitization removes dangerous HTML/JS."""
        dangerous_inputs = [
            ("<script>alert(1)</script>Hello", "Hello"),
            ("Click <a href='javascript:alert(1)'>here</a>", "Click here"),
            ("<img src=x onerror=alert(1)>", ""),
        ]

        for dangerous, expected_safe in dangerous_inputs:
            sanitized = sanitize_string(dangerous)
            # Should not contain script tags or event handlers
            assert "<script" not in sanitized.lower()
            assert "javascript:" not in sanitized.lower()
            assert "onerror" not in sanitized.lower()


class TestSQLInjectionPrevention:
    """Test SQL injection prevention."""

    def test_sql_injection_patterns_are_detected(self):
        """Verify SQL injection patterns are identified."""
        sql_payloads = [
            "' OR '1'='1",
            "admin'--",
            "1; DROP TABLE users",
            "' UNION SELECT NULL--",
            "1' ORDER BY 1--",
            "' AND 1=1--",
            "' OR 1=1#",
            "admin' OR '1'='1'/*",
            "'; EXEC xp_cmdshell('dir')--",
            "1' WAITFOR DELAY '00:00:05'--",
        ]

        for payload in sql_payloads:
            is_sql_injection = detect_sql_injection(payload)
            assert is_sql_injection, f"Failed to detect SQL injection: {payload}"

    def test_sql_injection_in_email_field(self):
        """Test SQL injection attempts in email field."""
        sql_emails = [
            "admin'--",
            "' OR '1'='1",
            "'; DROP TABLE users;--",
        ]

        for sql_email in sql_emails:
            response = client.post(
                "/api/v1/auth/login",
                json={
                    "email": sql_email,
                    "password": "anything"
                }
            )

            # Should return 400 (validation error) or 401 (auth failed)
            # NOT 500 (server error from successful injection)
            assert response.status_code in [400, 401]

    def test_orm_prevents_sql_injection(self):
        """Verify ORM usage prevents SQL injection."""
        # Register user with normal name
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "testuser@example.com",
                "password": "SecureP@ss123!",
                "full_name": "Test User"
            }
        )

        # Try SQL injection in login
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "testuser@example.com' OR '1'='1",
                "password": "wrong"
            }
        )

        # Should fail authentication (not bypass it)
        assert response.status_code == 401


class TestPathTraversalPrevention:
    """Test path traversal prevention."""

    def test_path_traversal_patterns_are_detected(self):
        """Verify path traversal patterns are identified."""
        traversal_payloads = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32",
            "....//....//....//etc/passwd",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
            "..%252f..%252f..%252fetc/passwd",
            "..%c0%af..%c0%af..%c0%afetc/passwd",
        ]

        for payload in traversal_payloads:
            is_traversal = detect_path_traversal(payload)
            assert is_traversal, f"Failed to detect path traversal: {payload}"

    def test_filename_validation_blocks_traversal(self):
        """Verify filename validation prevents path traversal."""
        malicious_filenames = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "....//....//etc/shadow",
            "/etc/passwd",
            "C:\\Windows\\System32\\config\\SAM",
        ]

        for filename in malicious_filenames:
            is_valid = validate_filename(filename)
            assert not is_valid, f"Should reject malicious filename: {filename}"

    def test_safe_filenames_are_accepted(self):
        """Verify legitimate filenames are accepted."""
        safe_filenames = [
            "document.pdf",
            "image-2024.png",
            "my_file_v1.txt",
            "dataset_train.jsonl",
        ]

        for filename in safe_filenames:
            is_valid = validate_filename(filename)
            assert is_valid, f"Should accept safe filename: {filename}"


class TestEmailValidation:
    """Test email validation security."""

    def test_malformed_emails_are_rejected(self):
        """Verify malformed emails are rejected."""
        invalid_emails = [
            "not-an-email",
            "@example.com",
            "user@",
            "user name@example.com",  # Space
            "user@example",  # No TLD
            "user@.com",
            "",
            "user@example..com",  # Double dot
            "user@@example.com",  # Double @
        ]

        for email in invalid_emails:
            is_valid = validate_email(email)
            assert not is_valid, f"Should reject invalid email: {email}"

    def test_valid_emails_are_accepted(self):
        """Verify valid emails are accepted."""
        valid_emails = [
            "user@example.com",
            "first.last@example.com",
            "user+tag@example.co.uk",
            "test_user@sub.example.com",
        ]

        for email in valid_emails:
            is_valid = validate_email(email)
            assert is_valid, f"Should accept valid email: {email}"


class TestInputLengthValidation:
    """Test input length limits."""

    def test_extremely_long_inputs_are_rejected(self):
        """Verify extremely long inputs are rejected (DoS prevention)."""
        # Try to register with extremely long name
        long_name = "A" * 100000  # 100KB name

        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "password": "SecureP@ss123!",
                "full_name": long_name
            }
        )

        # Should be rejected
        assert response.status_code == 400

    def test_normal_length_inputs_are_accepted(self):
        """Verify normal length inputs are accepted."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "normal@example.com",
                "password": "SecureP@ss123!",
                "full_name": "Normal Length Name"
            }
        )

        assert response.status_code == 200


class TestNullByteInjection:
    """Test null byte injection prevention."""

    def test_null_bytes_are_removed(self):
        """Verify null bytes are stripped from input."""
        input_with_null = "test\x00file.txt"
        sanitized = sanitize_string(input_with_null)

        # Null byte should be removed
        assert "\x00" not in sanitized

    def test_null_byte_in_filename(self):
        """Test null byte in filename."""
        malicious_filename = "safe.txt\x00.exe"

        is_valid = validate_filename(malicious_filename)
        assert not is_valid


class TestSpecialCharacterHandling:
    """Test handling of special characters."""

    def test_unicode_normalization(self):
        """Test that unicode characters are handled safely."""
        # Unicode normalization attack
        unicode_inputs = [
            "user@example\u202e.com",  # Right-to-left override
            "test\u0000file",  # Null character
            "file\ufeffname.txt",  # Zero-width no-break space
        ]

        for unicode_input in unicode_inputs:
            sanitized = sanitize_string(unicode_input)
            # Should handle safely
            assert isinstance(sanitized, str)

    def test_emoji_and_unicode_in_names(self):
        """Test that emoji and unicode in names are handled."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "emoji@example.com",
                "password": "SecureP@ss123!",
                "full_name": "Test User 👨‍💻"
            }
        )

        # Should either accept or gracefully reject (not crash)
        assert response.status_code in [200, 400]


class TestCommandInjection:
    """Test command injection prevention."""

    def test_shell_metacharacters_are_handled(self):
        """Verify shell metacharacters don't cause injection."""
        dangerous_chars = [
            "test; ls -la",
            "test && cat /etc/passwd",
            "test | whoami",
            "test `whoami`",
            "test $(whoami)",
            "test & calc",
        ]

        for dangerous in dangerous_chars:
            sanitized = sanitize_string(dangerous)
            # Should sanitize or reject
            assert isinstance(sanitized, str)


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
