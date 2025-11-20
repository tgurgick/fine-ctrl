"""API routes package."""
from backend.api.routes import (
    auth,
    tasks,
    datasets,
    training,
    deployments,
    api_keys,
)

__all__ = [
    "auth",
    "tasks",
    "datasets",
    "training",
    "deployments",
    "api_keys",
]
