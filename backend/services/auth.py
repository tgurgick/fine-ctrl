"""Authentication service implementation."""
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID
import bcrypt
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from backend.config import settings
from backend.models import User
from backend.schemas.auth import Token, UserRegister, UserLogin, TokenData
from backend.services.interfaces import IAuthService
from backend.utils.validation import input_validator


class AuthService(IAuthService):
    """Authentication service with JWT and bcrypt."""

    def __init__(self):
        self.jwt_secret = settings.JWT_SECRET_KEY
        self.jwt_algorithm = "HS256"
        self.access_token_expire_minutes = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_token_expire_days = settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS

    async def register(self, db: Session, user_data: UserRegister) -> User:
        """
        Register a new user.

        Args:
            db: Database session
            user_data: User registration data (email, password)

        Returns:
            Created user

        Raises:
            HTTPException: 400 if email already exists
        """
        # Validate email format
        input_validator.validate_email(user_data.email)

        # Validate password strength
        input_validator.validate_password_strength(user_data.password)

        # Check if user already exists
        existing_user = db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        # Hash password
        hashed_password = self.hash_password(user_data.password)

        # Create user
        user = User(
            email=user_data.email,
            hashed_password=hashed_password,
            plan="free",
            is_active="1",
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        return user

    async def login(self, db: Session, credentials: UserLogin) -> Token:
        """
        Authenticate user and return JWT tokens.

        Args:
            db: Database session
            credentials: User login credentials (email, password)

        Returns:
            Token object with access and refresh tokens

        Raises:
            HTTPException: 401 if credentials are invalid
        """
        # Get user by email
        user = db.query(User).filter(User.email == credentials.email).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
            )

        # Verify password
        if not self.verify_password(credentials.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
            )

        # Check if user is active
        if user.is_active != "1":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive",
            )

        # Generate tokens
        access_token = self._create_access_token(user)
        refresh_token = self._create_refresh_token(user)

        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
        )

    async def refresh_token(self, db: Session, refresh_token: str) -> str:
        """
        Generate new access token using refresh token.

        Args:
            db: Database session
            refresh_token: Valid refresh token

        Returns:
            New access token

        Raises:
            HTTPException: 401 if refresh token is invalid or expired
        """
        try:
            payload = jwt.decode(
                refresh_token, self.jwt_secret, algorithms=[self.jwt_algorithm]
            )
            user_id: str = payload.get("sub")
            token_type: str = payload.get("type")

            if user_id is None or token_type != "refresh":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid refresh token",
                )

            # Get user from database
            user = db.query(User).filter(User.id == UUID(user_id)).first()
            if not user or user.is_active != "1":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid refresh token",
                )

            # Generate new access token
            return self._create_access_token(user)

        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

    async def get_current_user(self, db: Session, token: str) -> User:
        """
        Get current user from JWT access token.

        Args:
            db: Database session
            token: JWT access token

        Returns:
            Current authenticated user

        Raises:
            HTTPException: 401 if token is invalid or user not found
        """
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            user_id: str = payload.get("sub")
            token_type: str = payload.get("type")

            if user_id is None or token_type != "access":
                raise credentials_exception

            # Get user from database
            user = db.query(User).filter(User.id == UUID(user_id)).first()
            if user is None:
                raise credentials_exception

            return user

        except JWTError:
            raise credentials_exception

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify password against bcrypt hash.

        Args:
            plain_password: Plain text password
            hashed_password: Bcrypt hashed password

        Returns:
            True if password matches, False otherwise
        """
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )

    def hash_password(self, password: str) -> str:
        """
        Hash password using bcrypt with 12 rounds.

        Args:
            password: Plain text password

        Returns:
            Bcrypt hashed password
        """
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')

    def _create_access_token(self, user: User) -> str:
        """
        Create JWT access token (short-lived: 15 minutes).

        Args:
            user: User object

        Returns:
            JWT access token
        """
        expires_delta = timedelta(minutes=self.access_token_expire_minutes)
        expire = datetime.utcnow() + expires_delta

        to_encode = {
            "sub": str(user.id),
            "email": user.email,
            "plan": user.plan,
            "type": "access",
            "exp": expire,
            "iat": datetime.utcnow(),
        }

        encoded_jwt = jwt.encode(
            to_encode, self.jwt_secret, algorithm=self.jwt_algorithm
        )
        return encoded_jwt

    def _create_refresh_token(self, user: User) -> str:
        """
        Create JWT refresh token (long-lived: 30 days).

        Args:
            user: User object

        Returns:
            JWT refresh token
        """
        expires_delta = timedelta(days=self.refresh_token_expire_days)
        expire = datetime.utcnow() + expires_delta

        to_encode = {
            "sub": str(user.id),
            "type": "refresh",
            "exp": expire,
            "iat": datetime.utcnow(),
        }

        encoded_jwt = jwt.encode(
            to_encode, self.jwt_secret, algorithm=self.jwt_algorithm
        )
        return encoded_jwt


# Create singleton instance
auth_service = AuthService()
