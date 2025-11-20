"""Test configuration and fixtures."""
import os
import sys

# Set environment variables before any imports
os.environ["DATABASE_URL"] = "postgresql://test:test@localhost:5432/test"
os.environ["REDIS_URL"] = "redis://localhost:6379"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-testing-only"
os.environ["JWT_ALGORITHM"] = "HS256"
os.environ["ENVIRONMENT"] = "test"
os.environ["USE_SECRETS_MANAGER"] = "false"

# Add parent directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
