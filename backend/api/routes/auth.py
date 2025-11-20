"""Authentication routes."""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.schemas.auth import UserRegister, UserLogin, Token, TokenRefresh, AccessToken
from backend.schemas.user import UserResponse
from backend.services.auth import auth_service
from backend.middleware.rate_limiter import limiter
from backend.api.deps import get_current_user
from backend.models import User

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def register(
    request: Request,
    user_data: UserRegister,
    db: Session = Depends(get_db),
):
    """
    Register a new user.

    Args:
        user_data: User registration data (email, password)
        db: Database session

    Returns:
        Created user object

    Raises:
        HTTPException: 400 if email already exists
    """
    user = await auth_service.register(db, user_data)
    return user


@router.post("/login", response_model=Token)
@limiter.limit("5/minute")
async def login(
    request: Request,
    credentials: UserLogin,
    db: Session = Depends(get_db),
):
    """
    Login and receive access + refresh tokens.

    Args:
        credentials: User login credentials (email, password)
        db: Database session

    Returns:
        Token object with access_token (15min) and refresh_token (30d)

    Raises:
        HTTPException: 401 if credentials are invalid
    """
    return await auth_service.login(db, credentials)


@router.post("/refresh", response_model=AccessToken)
@limiter.limit("10/minute")
async def refresh_token(
    request: Request,
    token_data: TokenRefresh,
    db: Session = Depends(get_db),
):
    """
    Refresh access token using refresh token.

    Args:
        token_data: Refresh token
        db: Database session

    Returns:
        New access token

    Raises:
        HTTPException: 401 if refresh token is invalid or expired
    """
    new_access_token = await auth_service.refresh_token(db, token_data.refresh_token)
    return AccessToken(access_token=new_access_token, token_type="bearer")


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout():
    """
    Logout endpoint.

    JWT tokens are stateless, so logout is handled client-side by
    deleting the tokens. This endpoint exists for consistency and
    future server-side token revocation if needed.
    """
    # Client should delete tokens
    # For stateless JWT, no server-side action needed
    # Future: Could implement token blacklist if required
    return


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
):
    """
    Get current authenticated user's profile.

    Args:
        current_user: Current authenticated user from JWT token

    Returns:
        User profile information

    Raises:
        HTTPException: 401 if not authenticated
    """
    return current_user
