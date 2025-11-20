"""Mock service implementations for WP-2.

These are temporary implementations that will be replaced by real services
in later work packages (WP-3, WP-4, WP-5, WP-6).

The mock services implement the service interfaces and perform basic CRUD
operations directly on the database.
"""

from typing import List, Optional
from uuid import UUID, uuid4
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from backend.services.interfaces import (
    ITaskService,
    IDatasetService,
    ITrainingService,
    IDeploymentService,
)
from backend.models import (
    Task,
    Dataset,
    TrainingExample,
    TrainingJob,
    ModelVersion,
    Deployment,
)
from backend.schemas.task import TaskCreate, TaskUpdate
from backend.schemas.dataset import DatasetCreate, TrainingExampleCreate
from backend.schemas.training import (
    TrainingJobCreate,
    TrainingJobUpdate,
    ModelVersionCreate,
    ModelVersionUpdate,
)
from backend.schemas.deployment import DeploymentCreate, DeploymentUpdate


class MockTaskService(ITaskService):
    """Mock implementation of task service."""

    async def create_task(
        self, db: Session, user_id: UUID, task_data: TaskCreate
    ) -> Task:
        """Create a new task."""
        task = Task(
            id=uuid4(),
            user_id=user_id,
            name=task_data.name,
            description=task_data.description,
            task_type=task_data.task_type,
            config=task_data.config or {},
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        return task

    async def get_task(self, db: Session, task_id: UUID, user_id: UUID) -> Task:
        """Get task by ID (with ownership check)."""
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found",
            )
        if task.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resource not found or access denied",
            )
        return task

    async def list_tasks(
        self, db: Session, user_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Task]:
        """List user's tasks."""
        return (
            db.query(Task)
            .filter(Task.user_id == user_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    async def update_task(
        self, db: Session, task_id: UUID, user_id: UUID, task_data: TaskUpdate
    ) -> Task:
        """Update task."""
        task = await self.get_task(db, task_id, user_id)

        # Update only provided fields
        if task_data.name is not None:
            task.name = task_data.name
        if task_data.description is not None:
            task.description = task_data.description
        if task_data.task_type is not None:
            task.task_type = task_data.task_type
        if task_data.config is not None:
            task.config = task_data.config

        db.commit()
        db.refresh(task)
        return task

    async def delete_task(self, db: Session, task_id: UUID, user_id: UUID) -> None:
        """Delete task."""
        task = await self.get_task(db, task_id, user_id)
        db.delete(task)
        db.commit()


class MockDatasetService(IDatasetService):
    """Mock implementation of dataset service."""

    async def create_dataset(
        self, db: Session, user_id: UUID, dataset_data: DatasetCreate
    ) -> Dataset:
        """Create a new dataset with examples."""
        # Verify task ownership
        task = db.query(Task).filter(Task.id == dataset_data.task_id).first()
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found",
            )
        if task.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found or access denied",
            )

        # Create dataset
        dataset = Dataset(
            id=uuid4(),
            task_id=dataset_data.task_id,
            version=dataset_data.version,
            stats=dataset_data.stats or {},
        )
        db.add(dataset)
        db.flush()

        # Create examples
        for example_data in dataset_data.examples:
            example = TrainingExample(
                id=uuid4(),
                dataset_id=dataset.id,
                input=example_data.input,
                output=example_data.output,
                example_metadata=example_data.example_metadata or {},
            )
            db.add(example)

        db.commit()
        db.refresh(dataset)
        return dataset

    async def get_dataset(
        self, db: Session, dataset_id: UUID, user_id: UUID
    ) -> Dataset:
        """Get dataset by ID."""
        dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
        if not dataset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dataset not found",
            )

        # Check ownership via task
        task = db.query(Task).filter(Task.id == dataset.task_id).first()
        if task and task.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resource not found or access denied",
            )

        return dataset

    async def list_datasets(
        self, db: Session, task_id: UUID, user_id: UUID
    ) -> List[Dataset]:
        """List datasets for a task."""
        # Verify task ownership
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found",
            )
        if task.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found or access denied",
            )

        return db.query(Dataset).filter(Dataset.task_id == task_id).all()

    async def add_examples(
        self,
        db: Session,
        dataset_id: UUID,
        user_id: UUID,
        examples: List[TrainingExampleCreate],
    ) -> List[TrainingExample]:
        """Add examples to dataset."""
        # Verify dataset ownership
        dataset = await self.get_dataset(db, dataset_id, user_id)

        # Create examples
        created_examples = []
        for example_data in examples:
            example = TrainingExample(
                id=uuid4(),
                dataset_id=dataset.id,
                input=example_data.input,
                output=example_data.output,
                example_metadata=example_data.example_metadata or {},
            )
            db.add(example)
            created_examples.append(example)

        db.commit()
        for example in created_examples:
            db.refresh(example)

        return created_examples


class MockTrainingService(ITrainingService):
    """Mock implementation of training service."""

    async def create_training_job(
        self, db: Session, user_id: UUID, job_data: TrainingJobCreate
    ) -> TrainingJob:
        """Create and queue a training job."""
        # Verify task ownership
        task = db.query(Task).filter(Task.id == job_data.task_id).first()
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found",
            )
        if task.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found or access denied",
            )

        # Verify dataset ownership
        dataset = db.query(Dataset).filter(Dataset.id == job_data.dataset_id).first()
        if not dataset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dataset not found",
            )
        if dataset.task_id != job_data.task_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Dataset does not belong to this task",
            )

        # Create training job
        job = TrainingJob(
            id=uuid4(),
            user_id=user_id,
            task_id=job_data.task_id,
            dataset_id=job_data.dataset_id,
            status="queued",
            config=job_data.config or {},
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        return job

    async def get_training_job(
        self, db: Session, job_id: UUID, user_id: UUID
    ) -> TrainingJob:
        """Get training job by ID."""
        job = db.query(TrainingJob).filter(TrainingJob.id == job_id).first()
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Training job not found",
            )
        if job.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resource not found or access denied",
            )
        return job

    async def list_training_jobs(
        self, db: Session, task_id: UUID, user_id: UUID
    ) -> List[TrainingJob]:
        """List training jobs for a task."""
        # Verify task ownership
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found",
            )
        if task.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found or access denied",
            )

        return db.query(TrainingJob).filter(TrainingJob.task_id == task_id).all()

    async def update_training_job(
        self, db: Session, job_id: UUID, user_id: UUID, update_data: TrainingJobUpdate
    ) -> TrainingJob:
        """Update training job status/metrics."""
        job = await self.get_training_job(db, job_id, user_id)

        if update_data.status is not None:
            job.status = update_data.status
        if update_data.metrics is not None:
            job.metrics = update_data.metrics
        if update_data.error_message is not None:
            job.error_message = update_data.error_message

        db.commit()
        db.refresh(job)
        return job

    async def cancel_training_job(
        self, db: Session, job_id: UUID, user_id: UUID
    ) -> TrainingJob:
        """Cancel a training job."""
        job = await self.get_training_job(db, job_id, user_id)

        # Only allow cancelling jobs that are queued or training
        if job.status not in ["queued", "training"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot cancel job with status: {job.status}",
            )

        job.status = "cancelled"
        db.commit()
        db.refresh(job)
        return job

    async def create_model_version(
        self, db: Session, user_id: UUID, version_data: ModelVersionCreate
    ) -> ModelVersion:
        """Create a model version after training."""
        # Verify task ownership
        task = db.query(Task).filter(Task.id == version_data.task_id).first()
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found",
            )
        if task.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found or access denied",
            )

        # Verify training job ownership
        job = (
            db.query(TrainingJob)
            .filter(TrainingJob.id == version_data.training_job_id)
            .first()
        )
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Training job not found",
            )
        if job.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Training job not found or access denied",
            )

        # Create model version
        model_version = ModelVersion(
            id=uuid4(),
            user_id=user_id,
            task_id=version_data.task_id,
            training_job_id=version_data.training_job_id,
            version=version_data.version,
            status="ready",
            s3_weights_path=version_data.s3_weights_path,
            s3_adapter_path=version_data.s3_adapter_path,
            inference_config=version_data.inference_config or {},
        )
        db.add(model_version)
        db.commit()
        db.refresh(model_version)
        return model_version

    async def update_model_version(
        self,
        db: Session,
        version_id: UUID,
        user_id: UUID,
        update_data: ModelVersionUpdate,
    ) -> ModelVersion:
        """Update model version."""
        model_version = (
            db.query(ModelVersion).filter(ModelVersion.id == version_id).first()
        )
        if not model_version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Model version not found",
            )
        if model_version.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resource not found or access denied",
            )

        if update_data.status is not None:
            model_version.status = update_data.status
        if update_data.s3_weights_path is not None:
            model_version.s3_weights_path = update_data.s3_weights_path
        if update_data.s3_adapter_path is not None:
            model_version.s3_adapter_path = update_data.s3_adapter_path
        if update_data.eval_results is not None:
            model_version.eval_results = update_data.eval_results
        if update_data.inference_config is not None:
            model_version.inference_config = update_data.inference_config

        db.commit()
        db.refresh(model_version)
        return model_version


class MockDeploymentService(IDeploymentService):
    """Mock implementation of deployment service."""

    async def create_deployment(
        self, db: Session, user_id: UUID, deployment_data: DeploymentCreate
    ) -> Deployment:
        """Create and deploy a model version."""
        # Verify model version ownership
        model_version = (
            db.query(ModelVersion)
            .filter(ModelVersion.id == deployment_data.model_version_id)
            .first()
        )
        if not model_version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Model version not found",
            )
        if model_version.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Model version not found or access denied",
            )

        # Create deployment (mock - would actually deploy to Modal)
        deployment = Deployment(
            id=uuid4(),
            user_id=user_id,
            model_version_id=deployment_data.model_version_id,
            name=deployment_data.name,
            is_public=deployment_data.is_public,
            status="active",
            endpoint_url=f"https://mock-endpoint.modal.run/deployments/{uuid4()}",
        )
        db.add(deployment)
        db.commit()
        db.refresh(deployment)
        return deployment

    async def get_deployment(
        self, db: Session, deployment_id: UUID, user_id: UUID
    ) -> Deployment:
        """Get deployment by ID."""
        deployment = (
            db.query(Deployment).filter(Deployment.id == deployment_id).first()
        )
        if not deployment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Deployment not found",
            )
        if deployment.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resource not found or access denied",
            )
        return deployment

    async def list_deployments(
        self, db: Session, user_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Deployment]:
        """List user's deployments."""
        return (
            db.query(Deployment)
            .filter(Deployment.user_id == user_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    async def update_deployment(
        self,
        db: Session,
        deployment_id: UUID,
        user_id: UUID,
        update_data: DeploymentUpdate,
    ) -> Deployment:
        """Update deployment."""
        deployment = await self.get_deployment(db, deployment_id, user_id)

        if update_data.name is not None:
            deployment.name = update_data.name
        if update_data.is_public is not None:
            deployment.is_public = update_data.is_public
        if update_data.status is not None:
            deployment.status = update_data.status

        db.commit()
        db.refresh(deployment)
        return deployment

    async def deactivate_deployment(
        self, db: Session, deployment_id: UUID, user_id: UUID
    ) -> Deployment:
        """Deactivate a deployment."""
        deployment = await self.get_deployment(db, deployment_id, user_id)

        deployment.status = "inactive"
        db.commit()
        db.refresh(deployment)
        return deployment


# Service instances
task_service = MockTaskService()
dataset_service = MockDatasetService()
training_service = MockTrainingService()
deployment_service = MockDeploymentService()
