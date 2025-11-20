"""Deployment service for deploying models to Modal inference endpoints."""
import logging
from typing import List
from uuid import UUID, uuid4
from datetime import datetime

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from backend.services.interfaces import IDeploymentService
from backend.models import Deployment, ModelVersion, User
from backend.schemas.deployment import DeploymentCreate, DeploymentUpdate
from backend.config import settings

logger = logging.getLogger(__name__)


class DeploymentService(IDeploymentService):
    """Service for managing model deployments to Modal."""

    async def create_deployment(
        self,
        db: Session,
        user_id: UUID,
        deployment_data: DeploymentCreate
    ) -> Deployment:
        """
        Create and deploy a model version to Modal.

        Args:
            db: Database session
            user_id: User creating the deployment
            deployment_data: Deployment configuration

        Returns:
            Created deployment

        Raises:
            HTTPException: If model version not found or user doesn't own it
        """
        # Verify model version exists and user owns it
        model_version = db.query(ModelVersion).filter(
            ModelVersion.id == deployment_data.model_version_id
        ).first()

        if not model_version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Model version not found"
            )

        if model_version.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resource not found or access denied"
            )

        # Check if model version has weights
        if not model_version.weights_path:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Model version has no trained weights"
            )

        # Create deployment record
        deployment = Deployment(
            id=uuid4(),
            user_id=user_id,
            model_version_id=deployment_data.model_version_id,
            name=deployment_data.name,
            is_public=deployment_data.is_public,
            status="deploying",
            config=deployment_data.config or {},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        db.add(deployment)
        db.commit()
        db.refresh(deployment)

        try:
            # Deploy to Modal (async - this would trigger a background job)
            endpoint_url = await self._deploy_to_modal(
                deployment.id,
                model_version.weights_path,
                deployment_data.config or {}
            )

            # Update deployment with endpoint URL
            deployment.endpoint_url = endpoint_url
            deployment.status = "active"
            deployment.deployed_at = datetime.utcnow()
            deployment.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(deployment)

            logger.info(f"Deployment {deployment.id} created successfully")
            return deployment

        except Exception as e:
            logger.error(f"Deployment failed: {str(e)}")
            deployment.status = "failed"
            deployment.error_message = str(e)
            deployment.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(deployment)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Deployment failed: {str(e)}"
            )

    async def get_deployment(
        self,
        db: Session,
        deployment_id: UUID,
        user_id: UUID
    ) -> Deployment:
        """
        Get deployment by ID with ownership check.

        Args:
            db: Database session
            deployment_id: Deployment ID
            user_id: User requesting the deployment

        Returns:
            Deployment

        Raises:
            HTTPException: If not found or access denied
        """
        deployment = db.query(Deployment).filter(
            Deployment.id == deployment_id
        ).first()

        if not deployment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Deployment not found"
            )

        if deployment.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resource not found or access denied"
            )

        return deployment

    async def list_deployments(
        self,
        db: Session,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Deployment]:
        """
        List user's deployments.

        Args:
            db: Database session
            user_id: User ID
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of deployments
        """
        return (
            db.query(Deployment)
            .filter(Deployment.user_id == user_id)
            .order_by(Deployment.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    async def update_deployment(
        self,
        db: Session,
        deployment_id: UUID,
        user_id: UUID,
        update_data: DeploymentUpdate
    ) -> Deployment:
        """
        Update deployment configuration.

        Args:
            db: Database session
            deployment_id: Deployment ID
            user_id: User updating the deployment
            update_data: Update data

        Returns:
            Updated deployment

        Raises:
            HTTPException: If not found or access denied
        """
        deployment = await self.get_deployment(db, deployment_id, user_id)

        # Update fields
        if update_data.name is not None:
            deployment.name = update_data.name
        if update_data.is_public is not None:
            deployment.is_public = update_data.is_public
        if update_data.status is not None:
            deployment.status = update_data.status
        if update_data.config is not None:
            deployment.config = update_data.config

        deployment.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(deployment)

        logger.info(f"Deployment {deployment_id} updated")
        return deployment

    async def deactivate_deployment(
        self,
        db: Session,
        deployment_id: UUID,
        user_id: UUID
    ) -> Deployment:
        """
        Deactivate a deployment.

        Args:
            db: Database session
            deployment_id: Deployment ID
            user_id: User deactivating the deployment

        Returns:
            Deactivated deployment

        Raises:
            HTTPException: If not found or access denied
        """
        deployment = await self.get_deployment(db, deployment_id, user_id)

        # Update status
        deployment.status = "inactive"
        deployment.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(deployment)

        # TODO: Actually tear down the Modal deployment
        # await self._teardown_modal_deployment(deployment.id)

        logger.info(f"Deployment {deployment_id} deactivated")
        return deployment

    async def _deploy_to_modal(
        self,
        deployment_id: UUID,
        weights_path: str,
        config: dict
    ) -> str:
        """
        Deploy model to Modal inference endpoint.

        This is a simplified MVP implementation. In production, this would:
        1. Upload weights to Modal volume
        2. Create a Modal function with vLLM
        3. Deploy and get endpoint URL

        Args:
            deployment_id: Deployment ID
            weights_path: Path to model weights (S3 or HF Hub)
            config: Deployment configuration

        Returns:
            Endpoint URL

        Raises:
            Exception: If deployment fails
        """
        # TODO: Implement actual Modal deployment
        # For now, return a mock endpoint URL
        #
        # In production, this would:
        # 1. Use Modal SDK to create a function:
        #    @app.function(gpu="T4", keep_warm=1)
        #    @modal.web_endpoint(method="POST")
        #    async def inference(request: dict):
        #        # Load model with vLLM
        #        # Run inference
        #        # Return result
        #
        # 2. Deploy the function
        # 3. Get the URL from Modal API

        # Mock implementation for MVP
        base_url = settings.MODAL_INFERENCE_BASE_URL or "https://inference.modal.com"
        endpoint_url = f"{base_url}/deployments/{deployment_id}"

        logger.info(f"Deployed to Modal: {endpoint_url}")
        logger.info(f"Weights path: {weights_path}")
        logger.info(f"Config: {config}")

        return endpoint_url


# Global service instance
deployment_service = DeploymentService()
