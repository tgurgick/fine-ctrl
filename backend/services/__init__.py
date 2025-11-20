"""Services package."""
from backend.services.interfaces import (
    IAuthService,
    ITaskService,
    IDatasetService,
    ITrainingService,
    IDeploymentService,
    IAPIKeyService,
)

# Import service implementations
from backend.services.auth import auth_service
from backend.services.api_keys import api_key_service
from backend.services.agent import agent_service
from backend.services.task import task_service
from backend.services.dataset import dataset_service
from backend.services.training import training_service
from backend.services.evaluation import evaluation_service
from backend.services.deployment import deployment_service

__all__ = [
    # Interfaces
    "IAuthService",
    "ITaskService",
    "IDatasetService",
    "ITrainingService",
    "IDeploymentService",
    "IAPIKeyService",
    # Service instances
    "auth_service",
    "api_key_service",
    "agent_service",
    "task_service",
    "dataset_service",
    "training_service",
    "evaluation_service",
    "deployment_service",
]
