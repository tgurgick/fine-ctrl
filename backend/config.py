"""
Configuration module with dual-mode secret management.

Development mode: Uses .env file
Production mode: Uses AWS Secrets Manager
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings with dual-mode secret management."""

    # Environment
    ENVIRONMENT: str = "development"
    USE_SECRETS_MANAGER: bool = False

    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_RELOAD: bool = True

    # Database
    DATABASE_URL: str

    # Redis
    REDIS_URL: str
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""

    # JWT Configuration
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ISSUER: str = "finetune-platform.com"
    JWT_AUDIENCE: str = "finetune-api"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # CORS
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True

    # S3/MinIO
    S3_ENDPOINT_URL: Optional[str] = "http://localhost:9000"
    S3_ACCESS_KEY_ID: str = "minioadmin"
    S3_SECRET_ACCESS_KEY: str = "minioadmin"
    S3_BUCKET: str = "finetune-models"
    S3_REGION: str = "us-east-1"

    # Anthropic (optional for development)
    ANTHROPIC_API_KEY: Optional[str] = None
    AGENT_MODEL: str = "claude-sonnet-4-20250514"

    # Modal (optional for development)
    MODAL_TOKEN_ID: Optional[str] = None
    MODAL_TOKEN_SECRET: Optional[str] = None
    MODAL_INFERENCE_BASE_URL: Optional[str] = None

    # Logging
    LOG_LEVEL: str = "INFO"

    # Security Limits
    MAX_FREE_TRAINING_JOBS: int = 5
    MAX_PRO_TRAINING_JOBS: int = 50

    # Cost Controls
    MAX_CLAUDE_API_COST_PER_DAY_FREE: float = 1.0
    MAX_CLAUDE_API_COST_PER_DAY_PRO: float = 10.0

    class Config:
        env_file = ".env"
        case_sensitive = True

    def get_secret(self, secret_name: str, env_var: str) -> str:
        """
        Get secret from AWS Secrets Manager or environment variable.

        Args:
            secret_name: Name of secret in AWS Secrets Manager
            env_var: Environment variable name for development mode

        Returns:
            Secret value

        Raises:
            ValueError: If secret not found
        """
        if self.USE_SECRETS_MANAGER:
            # Production: Use AWS Secrets Manager
            try:
                from backend.services.secrets import secrets_manager
                return secrets_manager.get_secret(secret_name)
            except ImportError:
                raise ValueError(
                    "AWS Secrets Manager enabled but secrets service not available. "
                    "Install boto3 or set USE_SECRETS_MANAGER=false"
                )
        else:
            # Development: Use environment variable
            value = getattr(self, env_var, None)
            if value is None:
                raise ValueError(f"Missing environment variable: {env_var}")
            return value

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.ENVIRONMENT == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.ENVIRONMENT == "production"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Convenience export
settings = get_settings()
