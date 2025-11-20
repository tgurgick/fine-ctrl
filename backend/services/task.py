"""Task service for managing fine-tuning tasks."""
import logging
from typing import List
from uuid import UUID, uuid4
from datetime import datetime

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from backend.services.interfaces import ITaskService
from backend.services.agent import agent_service
from backend.models import Task
from backend.schemas.task import TaskCreate, TaskUpdate
from backend.utils.validation import sanitize_input

logger = logging.getLogger(__name__)


class TaskService(ITaskService):
    """Service for managing fine-tuning tasks with agent integration."""

    async def create_task(
        self,
        db: Session,
        user_id: UUID,
        task_data: TaskCreate
    ) -> Task:
        """
        Create a new task with agent-driven analysis.

        Args:
            db: Database session
            user_id: User creating the task
            task_data: Task creation data

        Returns:
            Created task with agent-analyzed configuration

        Raises:
            HTTPException: If validation fails
        """
        # Sanitize inputs
        safe_name = sanitize_input(task_data.name)
        safe_description = sanitize_input(task_data.description)

        # Use agent to analyze task and generate configuration
        try:
            config = await agent_service.analyze_task(
                description=safe_description,
                sample_data=None  # Could pass sample data if provided
            )
        except Exception as e:
            logger.error(f"Agent analysis failed: {str(e)}")
            # Fall back to basic config if agent fails
            config = {
                "task_type": task_data.task_type or "classification",
                "complexity": "medium",
                "recommended_metrics": ["accuracy"],
                "data_requirements": {"minimum": 50, "recommended": 200}
            }

        # Merge user config with agent config
        final_config = {**config, **(task_data.config or {})}

        # Create task
        task = Task(
            id=uuid4(),
            user_id=user_id,
            name=safe_name,
            description=safe_description,
            task_type=final_config.get("task_type", "classification"),
            config=final_config,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        db.add(task)
        db.commit()
        db.refresh(task)

        logger.info(f"Task {task.id} created for user {user_id}")
        return task

    async def get_task(
        self,
        db: Session,
        task_id: UUID,
        user_id: UUID
    ) -> Task:
        """
        Get task by ID with ownership check.

        Args:
            db: Database session
            task_id: Task ID
            user_id: User requesting the task

        Returns:
            Task

        Raises:
            HTTPException: If not found or access denied
        """
        task = db.query(Task).filter(Task.id == task_id).first()

        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )

        if task.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resource not found or access denied"
            )

        return task

    async def list_tasks(
        self,
        db: Session,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Task]:
        """
        List user's tasks.

        Args:
            db: Database session
            user_id: User ID
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of tasks
        """
        return (
            db.query(Task)
            .filter(Task.user_id == user_id)
            .order_by(Task.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    async def update_task(
        self,
        db: Session,
        task_id: UUID,
        user_id: UUID,
        task_data: TaskUpdate
    ) -> Task:
        """
        Update task.

        Args:
            db: Database session
            task_id: Task ID
            user_id: User updating the task
            task_data: Update data

        Returns:
            Updated task

        Raises:
            HTTPException: If not found or access denied
        """
        task = await self.get_task(db, task_id, user_id)

        # Update only provided fields
        if task_data.name is not None:
            task.name = sanitize_input(task_data.name)
        if task_data.description is not None:
            task.description = sanitize_input(task_data.description)
        if task_data.task_type is not None:
            task.task_type = task_data.task_type
        if task_data.config is not None:
            # Merge with existing config
            task.config = {**task.config, **task_data.config}

        task.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(task)

        logger.info(f"Task {task_id} updated")
        return task

    async def delete_task(
        self,
        db: Session,
        task_id: UUID,
        user_id: UUID
    ) -> None:
        """
        Delete task and all related data (cascade).

        Args:
            db: Database session
            task_id: Task ID
            user_id: User deleting the task

        Raises:
            HTTPException: If not found or access denied
        """
        task = await self.get_task(db, task_id, user_id)

        # SQLAlchemy cascade will handle related entities
        db.delete(task)
        db.commit()

        logger.info(f"Task {task_id} deleted")


# Global service instance
task_service = TaskService()
