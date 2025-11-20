"""Rate limiting middleware."""
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request


def get_user_identifier(request: Request) -> str:
    """
    Get user identifier for rate limiting.

    Uses the following priority:
    1. Authenticated user ID (from request.state.user if available)
    2. X-API-Key header
    3. Remote IP address

    Args:
        request: FastAPI request object

    Returns:
        User identifier string
    """
    # Check if user is authenticated (set by auth middleware)
    if hasattr(request.state, "user") and request.state.user:
        return f"user:{request.state.user.id}"

    # Check for API key header
    api_key = request.headers.get("X-API-Key")
    if api_key:
        # Use first 8 chars as identifier
        return f"apikey:{api_key[:8]}"

    # Fall back to IP address
    return get_remote_address(request)


# Create limiter instance
# Storage backend will use Redis if REDIS_URL is configured, otherwise in-memory
limiter = Limiter(
    key_func=get_user_identifier,
    default_limits=["100/minute", "1000/hour", "5000/day"],
    storage_uri="memory://",  # Will be overridden in main.py with Redis if available
)


# Rate limit tiers by plan
PLAN_LIMITS = {
    "free": {
        "requests_per_minute": 10,
        "requests_per_hour": 100,
        "requests_per_day": 500,
    },
    "pro": {
        "requests_per_minute": 60,
        "requests_per_hour": 1000,
        "requests_per_day": 10000,
    },
    "enterprise": {
        "requests_per_minute": 300,
        "requests_per_hour": 10000,
        "requests_per_day": 100000,
    },
}


def get_plan_limit(plan: str, period: str) -> str:
    """
    Get rate limit string for plan and period.

    Args:
        plan: User plan (free, pro, enterprise)
        period: Time period (minute, hour, day)

    Returns:
        Rate limit string (e.g., "10/minute")
    """
    limits = PLAN_LIMITS.get(plan, PLAN_LIMITS["free"])
    limit_key = f"requests_per_{period}"
    return f"{limits[limit_key]}/{period}"


# Endpoint-specific rate limits
ENDPOINT_LIMITS = {
    # Authentication endpoints (more permissive for login attempts)
    "/api/v1/auth/register": ["5/minute", "20/hour"],
    "/api/v1/auth/login": ["5/minute", "20/hour"],
    "/api/v1/auth/refresh": ["10/minute", "100/hour"],

    # API key endpoints
    "/api/v1/api-keys": ["10/minute", "100/hour"],

    # Training endpoints (resource-intensive)
    "/api/v1/training/jobs": ["5/minute", "20/hour"],

    # Deployment endpoints
    "/api/v1/deployments": ["10/minute", "100/hour"],

    # Inference endpoints (high volume)
    "/api/v1/deployments/{id}/infer": ["100/minute", "5000/hour"],
}
