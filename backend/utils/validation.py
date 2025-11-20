"""Input validation and sanitization utilities."""
import re
from typing import Optional
from fastapi import HTTPException, status


class InputValidator:
    """Input validation and sanitization utilities."""

    # Common XSS patterns
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe",
        r"<object",
        r"<embed",
    ]

    # SQL injection patterns
    SQL_PATTERNS = [
        r"(\bUNION\b.*\bSELECT\b)",
        r"(\bDROP\b.*\bTABLE\b)",
        r"(\bINSERT\b.*\bINTO\b)",
        r"(\bUPDATE\b.*\bSET\b)",
        r"(\bDELETE\b.*\bFROM\b)",
        r"(--)",
        r"(/\*.*\*/)",
    ]

    # Path traversal patterns
    PATH_TRAVERSAL_PATTERNS = [
        r"\.\./",
        r"\.\.",
        r"%2e%2e",
        r"%252e",
    ]

    @classmethod
    def sanitize_string(cls, value: Optional[str], max_length: int = 10000) -> Optional[str]:
        """
        Sanitize string input.

        Args:
            value: Input string
            max_length: Maximum allowed length

        Returns:
            Sanitized string

        Raises:
            HTTPException: 400 if input is too long
        """
        if value is None:
            return None

        # Check length
        if len(value) > max_length:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Input too long (max {max_length} characters)",
            )

        # Remove null bytes
        value = value.replace("\x00", "")

        return value.strip()

    @classmethod
    def check_xss(cls, value: str) -> None:
        """
        Check for XSS patterns.

        Args:
            value: Input string

        Raises:
            HTTPException: 400 if XSS pattern detected
        """
        value_lower = value.lower()

        for pattern in cls.XSS_PATTERNS:
            if re.search(pattern, value_lower, re.IGNORECASE):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid input: potential XSS detected",
                )

    @classmethod
    def check_sql_injection(cls, value: str) -> None:
        """
        Check for SQL injection patterns.

        Note: This is a defense-in-depth measure. Primary protection
        comes from using parameterized queries via SQLAlchemy ORM.

        Args:
            value: Input string

        Raises:
            HTTPException: 400 if SQL injection pattern detected
        """
        value_upper = value.upper()

        for pattern in cls.SQL_PATTERNS:
            if re.search(pattern, value_upper, re.IGNORECASE):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid input: potential SQL injection detected",
                )

    @classmethod
    def check_path_traversal(cls, value: str) -> None:
        """
        Check for path traversal patterns.

        Args:
            value: Input string

        Raises:
            HTTPException: 400 if path traversal pattern detected
        """
        value_lower = value.lower()

        for pattern in cls.PATH_TRAVERSAL_PATTERNS:
            if re.search(pattern, value_lower, re.IGNORECASE):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid input: path traversal not allowed",
                )

    @classmethod
    def validate_email(cls, email: str) -> None:
        """
        Validate email format.

        Args:
            email: Email address

        Raises:
            HTTPException: 400 if email format is invalid
        """
        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

        if not re.match(email_pattern, email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid email format",
            )

        # Check for common typos
        if email.count("@") != 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid email format",
            )

    @classmethod
    def validate_password_strength(cls, password: str) -> None:
        """
        Validate password strength.

        Requirements:
        - At least 8 characters
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one digit

        Args:
            password: Password string

        Raises:
            HTTPException: 400 if password is weak
        """
        if len(password) < 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 8 characters long",
            )

        if not re.search(r"[A-Z]", password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must contain at least one uppercase letter",
            )

        if not re.search(r"[a-z]", password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must contain at least one lowercase letter",
            )

        if not re.search(r"\d", password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must contain at least one digit",
            )

    @classmethod
    def sanitize_filename(cls, filename: str) -> str:
        """
        Sanitize filename to prevent directory traversal.

        Args:
            filename: Original filename

        Returns:
            Sanitized filename

        Raises:
            HTTPException: 400 if filename is invalid
        """
        # Remove path components
        filename = filename.split("/")[-1].split("\\")[-1]

        # Check for path traversal
        cls.check_path_traversal(filename)

        # Remove non-alphanumeric characters (except .-_)
        filename = re.sub(r"[^a-zA-Z0-9._-]", "_", filename)

        # Ensure not empty
        if not filename or filename in (".", ".."):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid filename",
            )

        return filename


# Create singleton instance
input_validator = InputValidator()
