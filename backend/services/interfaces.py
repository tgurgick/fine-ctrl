"""Service interfaces (Abstract Base Classes)."""
from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session

from backend.models import (
    User,
    Task,
    Dataset,
    TrainingExample,
    TrainingJob,
    ModelVersion,
    Deployment,
    APIKey,
)
from backend.schemas.auth import Token, UserRegister, UserLogin
from backend.schemas.task import TaskCreate, TaskUpdate
from backend.schemas.dataset import DatasetCreate, TrainingExampleCreate
from backend.schemas.training import (
    TrainingJobCreate,
    TrainingJobUpdate,
    ModelVersionCreate,
    ModelVersionUpdate,
)
from backend.schemas.deployment import DeploymentCreate, DeploymentUpdate
from backend.schemas.api_key import APIKeyCreate


class IAuthService(ABC):
    """Authentication service interface."""

    @abstractmethod
    async def register(self, db: Session, user_data: UserRegister) -> User:
        """Register a new user."""
        pass

    @abstractmethod
    async def login(self, db: Session, credentials: UserLogin) -> Token:
        """Authenticate user and return tokens."""
        pass

    @abstractmethod
    async def refresh_token(self, db: Session, refresh_token: str) -> str:
        """Refresh access token using refresh token."""
        pass

    @abstractmethod
    async def get_current_user(self, db: Session, token: str) -> User:
        """Get current user from JWT token."""
        pass

    @abstractmethod
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash."""
        pass

    @abstractmethod
    def hash_password(self, password: str) -> str:
        """Hash password."""
        pass


class ITaskService(ABC):
    """Task service interface."""

    @abstractmethod
    async def create_task(
        self, db: Session, user_id: UUID, task_data: TaskCreate
    ) -> Task:
        """Create a new task."""
        pass

    @abstractmethod
    async def get_task(self, db: Session, task_id: UUID, user_id: UUID) -> Task:
        """Get task by ID (with ownership check)."""
        pass

    @abstractmethod
    async def list_tasks(
        self, db: Session, user_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Task]:
        """List user's tasks."""
        pass

    @abstractmethod
    async def update_task(
        self, db: Session, task_id: UUID, user_id: UUID, task_data: TaskUpdate
    ) -> Task:
        """Update task."""
        pass

    @abstractmethod
    async def delete_task(self, db: Session, task_id: UUID, user_id: UUID) -> None:
        """Delete task."""
        pass


class IDatasetService(ABC):
    """Dataset service interface."""

    @abstractmethod
    async def create_dataset(
        self, db: Session, user_id: UUID, dataset_data: DatasetCreate
    ) -> Dataset:
        """Create a new dataset with examples."""
        pass

    @abstractmethod
    async def get_dataset(
        self, db: Session, dataset_id: UUID, user_id: UUID
    ) -> Dataset:
        """Get dataset by ID."""
        pass

    @abstractmethod
    async def list_datasets(
        self, db: Session, task_id: UUID, user_id: UUID
    ) -> List[Dataset]:
        """List datasets for a task."""
        pass

    @abstractmethod
    async def add_examples(
        self,
        db: Session,
        dataset_id: UUID,
        user_id: UUID,
        examples: List[TrainingExampleCreate],
    ) -> List[TrainingExample]:
        """Add examples to dataset."""
        pass


class ITrainingService(ABC):
    """Training service interface."""

    @abstractmethod
    async def create_training_job(
        self, db: Session, user_id: UUID, job_data: TrainingJobCreate
    ) -> TrainingJob:
        """Create and queue a training job."""
        pass

    @abstractmethod
    async def get_training_job(
        self, db: Session, job_id: UUID, user_id: UUID
    ) -> TrainingJob:
        """Get training job by ID."""
        pass

    @abstractmethod
    async def list_training_jobs(
        self, db: Session, task_id: UUID, user_id: UUID
    ) -> List[TrainingJob]:
        """List training jobs for a task."""
        pass

    @abstractmethod
    async def update_training_job(
        self, db: Session, job_id: UUID, user_id: UUID, update_data: TrainingJobUpdate
    ) -> TrainingJob:
        """Update training job status/metrics."""
        pass

    @abstractmethod
    async def cancel_training_job(
        self, db: Session, job_id: UUID, user_id: UUID
    ) -> TrainingJob:
        """Cancel a training job."""
        pass

    @abstractmethod
    async def create_model_version(
        self, db: Session, user_id: UUID, version_data: ModelVersionCreate
    ) -> ModelVersion:
        """Create a model version after training."""
        pass

    @abstractmethod
    async def update_model_version(
        self,
        db: Session,
        version_id: UUID,
        user_id: UUID,
        update_data: ModelVersionUpdate,
    ) -> ModelVersion:
        """Update model version."""
        pass


class IDeploymentService(ABC):
    """Deployment service interface."""

    @abstractmethod
    async def create_deployment(
        self, db: Session, user_id: UUID, deployment_data: DeploymentCreate
    ) -> Deployment:
        """Create and deploy a model version."""
        pass

    @abstractmethod
    async def get_deployment(
        self, db: Session, deployment_id: UUID, user_id: UUID
    ) -> Deployment:
        """Get deployment by ID."""
        pass

    @abstractmethod
    async def list_deployments(
        self, db: Session, user_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Deployment]:
        """List user's deployments."""
        pass

    @abstractmethod
    async def update_deployment(
        self,
        db: Session,
        deployment_id: UUID,
        user_id: UUID,
        update_data: DeploymentUpdate,
    ) -> Deployment:
        """Update deployment."""
        pass

    @abstractmethod
    async def deactivate_deployment(
        self, db: Session, deployment_id: UUID, user_id: UUID
    ) -> Deployment:
        """Deactivate a deployment."""
        pass


class IAPIKeyService(ABC):
    """API key service interface."""

    @abstractmethod
    async def create_api_key(
        self, db: Session, user_id: UUID, key_data: APIKeyCreate
    ) -> tuple[APIKey, str]:
        """Create API key and return (key_object, plaintext_key)."""
        pass

    @abstractmethod
    async def get_api_key(
        self, db: Session, key_id: UUID, user_id: UUID
    ) -> APIKey:
        """Get API key by ID."""
        pass

    @abstractmethod
    async def list_api_keys(
        self, db: Session, user_id: UUID
    ) -> List[APIKey]:
        """List user's API keys."""
        pass

    @abstractmethod
    async def revoke_api_key(
        self, db: Session, key_id: UUID, user_id: UUID
    ) -> APIKey:
        """Revoke an API key."""
        pass

    @abstractmethod
    async def verify_api_key(self, db: Session, plaintext_key: str) -> Optional[User]:
        """Verify API key and return associated user."""
        pass
