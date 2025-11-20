"""Training service orchestration."""
import os
import json
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List
from uuid import UUID
import logging

from sqlalchemy.orm import Session
import redis.asyncio as aioredis
from modal import Function

from backend.models import TrainingJob, ModelVersion, Dataset, Task
from backend.schemas.training import (
    TrainingJobCreate,
    TrainingJobUpdate,
    ModelVersionCreate,
    ModelVersionUpdate,
)
from backend.services.interfaces import ITrainingService
from backend.config import settings

logger = logging.getLogger(__name__)


class TrainingService(ITrainingService):
    """Training service for orchestrating QLoRA training on Modal."""

    def __init__(self):
        """Initialize training service."""
        self.redis_client: Optional[aioredis.Redis] = None
        self.modal_app_name = "finetune-training"
        self.modal_function_name = "train_model"

    async def _get_redis_client(self) -> aioredis.Redis:
        """Get Redis client for pub/sub."""
        if self.redis_client is None:
            self.redis_client = aioredis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
            )
        return self.redis_client

    async def create_training_job(
        self, db: Session, user_id: UUID, job_data: TrainingJobCreate
    ) -> TrainingJob:
        """
        Create and queue a training job.

        Args:
            db: Database session
            user_id: User ID
            job_data: Job creation data

        Returns:
            Created training job

        Security:
            - Verifies user owns the task and dataset
            - Enforces resource limits (max jobs per user)
        """
        # Verify task ownership
        task = db.query(Task).filter(
            Task.id == job_data.task_id,
            Task.user_id == user_id,
        ).first()
        if not task:
            raise ValueError("Task not found or access denied")

        # Verify dataset ownership
        dataset = db.query(Dataset).filter(
            Dataset.id == job_data.dataset_id,
            Dataset.user_id == user_id,
        ).first()
        if not dataset:
            raise ValueError("Dataset not found or access denied")

        # Check resource limits (max active training jobs)
        active_jobs_count = db.query(TrainingJob).filter(
            TrainingJob.user_id == user_id,
            TrainingJob.status.in_(["queued", "training"]),
        ).count()

        # TODO: Check user plan and apply appropriate limit
        max_jobs = settings.MAX_FREE_TRAINING_JOBS
        if active_jobs_count >= max_jobs:
            raise ValueError(
                f"Maximum active training jobs reached ({max_jobs}). "
                "Please wait for existing jobs to complete."
            )

        # Create job
        job = TrainingJob(
            user_id=user_id,
            task_id=job_data.task_id,
            dataset_id=job_data.dataset_id,
            status="queued",
            config=job_data.config or {},
        )

        db.add(job)
        db.commit()
        db.refresh(job)

        logger.info(f"Created training job {job.id} for user {user_id}")

        # Start training asynchronously
        asyncio.create_task(self._start_training_async(db, job.id))

        return job

    async def get_training_job(
        self, db: Session, job_id: UUID, user_id: UUID
    ) -> TrainingJob:
        """
        Get training job by ID.

        Args:
            db: Database session
            job_id: Job ID
            user_id: User ID

        Returns:
            Training job

        Security:
            - Verifies user owns the job
        """
        job = db.query(TrainingJob).filter(
            TrainingJob.id == job_id,
            TrainingJob.user_id == user_id,
        ).first()

        if not job:
            raise ValueError("Training job not found or access denied")

        return job

    async def list_training_jobs(
        self, db: Session, task_id: UUID, user_id: UUID
    ) -> List[TrainingJob]:
        """
        List training jobs for a task.

        Args:
            db: Database session
            task_id: Task ID
            user_id: User ID

        Returns:
            List of training jobs

        Security:
            - Only returns jobs owned by the user
        """
        jobs = db.query(TrainingJob).filter(
            TrainingJob.task_id == task_id,
            TrainingJob.user_id == user_id,
        ).order_by(TrainingJob.created_at.desc()).all()

        return jobs

    async def update_training_job(
        self, db: Session, job_id: UUID, user_id: UUID, update_data: TrainingJobUpdate
    ) -> TrainingJob:
        """
        Update training job status/metrics.

        Args:
            db: Database session
            job_id: Job ID
            user_id: User ID
            update_data: Update data

        Returns:
            Updated training job
        """
        job = await self.get_training_job(db, job_id, user_id)

        if update_data.status:
            job.status = update_data.status

            if update_data.status == "training" and not job.started_at:
                job.started_at = datetime.utcnow()
            elif update_data.status in ["completed", "failed", "cancelled"]:
                job.completed_at = datetime.utcnow()

        if update_data.metrics:
            job.metrics = update_data.metrics

        if update_data.error_message:
            job.error_message = update_data.error_message

        db.commit()
        db.refresh(job)

        return job

    async def cancel_training_job(
        self, db: Session, job_id: UUID, user_id: UUID
    ) -> TrainingJob:
        """
        Cancel a training job.

        Args:
            db: Database session
            job_id: Job ID
            user_id: User ID

        Returns:
            Cancelled training job
        """
        job = await self.get_training_job(db, job_id, user_id)

        if job.status not in ["queued", "training"]:
            raise ValueError(f"Cannot cancel job with status: {job.status}")

        job.status = "cancelled"
        job.completed_at = datetime.utcnow()

        db.commit()
        db.refresh(job)

        logger.info(f"Cancelled training job {job_id}")

        return job

    async def create_model_version(
        self, db: Session, user_id: UUID, version_data: ModelVersionCreate
    ) -> ModelVersion:
        """
        Create a model version after training.

        Args:
            db: Database session
            user_id: User ID
            version_data: Model version data

        Returns:
            Created model version
        """
        # Verify training job ownership
        job = await self.get_training_job(db, version_data.training_job_id, user_id)

        if job.status != "completed":
            raise ValueError("Training job must be completed to create model version")

        # Create model version
        version = ModelVersion(
            user_id=user_id,
            task_id=version_data.task_id,
            training_job_id=version_data.training_job_id,
            version=version_data.version,
            status="ready",
            s3_weights_path=version_data.s3_weights_path,
            s3_adapter_path=version_data.s3_adapter_path,
            inference_config=version_data.inference_config,
        )

        db.add(version)
        db.commit()
        db.refresh(version)

        return version

    async def update_model_version(
        self,
        db: Session,
        version_id: UUID,
        user_id: UUID,
        update_data: ModelVersionUpdate,
    ) -> ModelVersion:
        """
        Update model version.

        Args:
            db: Database session
            version_id: Model version ID
            user_id: User ID
            update_data: Update data

        Returns:
            Updated model version
        """
        version = db.query(ModelVersion).filter(
            ModelVersion.id == version_id,
            ModelVersion.user_id == user_id,
        ).first()

        if not version:
            raise ValueError("Model version not found or access denied")

        if update_data.status:
            version.status = update_data.status
        if update_data.s3_weights_path:
            version.s3_weights_path = update_data.s3_weights_path
        if update_data.s3_adapter_path:
            version.s3_adapter_path = update_data.s3_adapter_path
        if update_data.eval_results:
            version.eval_results = update_data.eval_results
        if update_data.inference_config:
            version.inference_config = update_data.inference_config

        db.commit()
        db.refresh(version)

        return version

    async def _start_training_async(self, db: Session, job_id: UUID) -> None:
        """
        Start training job asynchronously.

        This method:
        1. Prepares dataset and config
        2. Invokes Modal training function
        3. Subscribes to progress updates
        4. Updates job status

        Args:
            db: Database session
            job_id: Training job ID
        """
        try:
            # Get job
            job = db.query(TrainingJob).filter(TrainingJob.id == job_id).first()
            if not job:
                logger.error(f"Job {job_id} not found")
                return

            # Update status to training
            job.status = "training"
            job.started_at = datetime.utcnow()
            db.commit()

            # Get dataset
            dataset = db.query(Dataset).filter(Dataset.id == job.dataset_id).first()

            # Prepare S3 paths with validation
            dataset_s3_path = self._build_s3_path(
                job.user_id, "datasets", job.dataset_id, "train.jsonl"
            )
            output_s3_path = self._build_s3_path(
                job.user_id, "adapters", job_id, "adapter"
            )

            # Get training config
            config = job.config or {}

            # Subscribe to progress updates
            asyncio.create_task(
                self._subscribe_to_progress(db, job_id)
            )

            # Invoke Modal function
            logger.info(f"Invoking Modal training for job {job_id}")

            # Import Modal function dynamically
            try:
                train_function = Function.lookup(
                    self.modal_app_name,
                    self.modal_function_name,
                )

                # Call training function
                result = train_function.remote(
                    job_id=str(job_id),
                    dataset_s3_path=dataset_s3_path,
                    output_s3_path=output_s3_path,
                    config_dict=config,
                    redis_url=settings.REDIS_URL,
                )

                # Update job with results
                if result["status"] == "completed":
                    job.status = "completed"
                    job.metrics = result.get("metrics", {})
                    job.completed_at = datetime.utcnow()

                    # Create model version
                    version = ModelVersion(
                        user_id=job.user_id,
                        task_id=job.task_id,
                        training_job_id=job.id,
                        version=f"v1-{job.id}",
                        status="ready",
                        s3_adapter_path=result.get("model_path"),
                        inference_config=config,
                    )
                    db.add(version)

                else:
                    job.status = "failed"
                    job.error_message = result.get("error", "Unknown error")
                    job.completed_at = datetime.utcnow()

                db.commit()

            except Exception as modal_error:
                logger.error(f"Modal invocation failed: {modal_error}")
                job.status = "failed"
                job.error_message = f"Modal error: {str(modal_error)}"
                job.completed_at = datetime.utcnow()
                db.commit()

        except Exception as e:
            logger.error(f"Training failed for job {job_id}: {e}")
            job.status = "failed"
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
            db.commit()

    async def _subscribe_to_progress(self, db: Session, job_id: UUID) -> None:
        """
        Subscribe to training progress updates via Redis pub/sub.

        Args:
            db: Database session
            job_id: Training job ID
        """
        redis_client = await self._get_redis_client()
        pubsub = redis_client.pubsub()

        channel = f"training:{job_id}:progress"
        await pubsub.subscribe(channel)

        logger.info(f"Subscribed to progress channel: {channel}")

        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    data = json.loads(message["data"])

                    # Update job metrics
                    job = db.query(TrainingJob).filter(
                        TrainingJob.id == job_id
                    ).first()

                    if job:
                        job.metrics = data.get("metrics", {})
                        db.commit()

                    # Stop listening if training completed or failed
                    if data["status"] in ["completed", "failed"]:
                        break

        except Exception as e:
            logger.error(f"Progress subscription error: {e}")
        finally:
            await pubsub.unsubscribe(channel)

    @staticmethod
    def _build_s3_path(
        user_id: UUID,
        resource_type: str,
        resource_id: UUID,
        filename: str,
    ) -> str:
        """
        Build validated S3 path.

        Security: Prevents directory traversal by using UUID-based paths.

        Args:
            user_id: User ID
            resource_type: Resource type (datasets, models, adapters)
            resource_id: Resource ID
            filename: Filename

        Returns:
            S3 path in format: finetune-models/<user_id>/<type>/<resource_id>/<filename>
        """
        # Validate resource type
        allowed_types = ["datasets", "models", "adapters"]
        if resource_type not in allowed_types:
            raise ValueError(f"Invalid resource type: {resource_type}")

        # Sanitize filename (no directory traversal)
        filename = filename.replace("..", "").replace("/", "")

        return f"finetune-models/{user_id}/{resource_type}/{resource_id}/{filename}"


# Global service instance
training_service = TrainingService()
