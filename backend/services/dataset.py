"""Dataset service for managing training datasets."""
import logging
from typing import List
from uuid import UUID, uuid4
from datetime import datetime

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from backend.services.interfaces import IDatasetService
from backend.services.agent import agent_service
from backend.models import Dataset, TrainingExample, Task
from backend.schemas.dataset import DatasetCreate, TrainingExampleCreate
from backend.utils.validation import sanitize_input

logger = logging.getLogger(__name__)


class DatasetService(IDatasetService):
    """Service for managing training datasets."""

    async def create_dataset(
        self,
        db: Session,
        user_id: UUID,
        dataset_data: DatasetCreate
    ) -> Dataset:
        """
        Create a new dataset with training examples.

        Args:
            db: Database session
            user_id: User creating the dataset
            dataset_data: Dataset creation data including examples

        Returns:
            Created dataset

        Raises:
            HTTPException: If task not found or user doesn't own it
        """
        # Verify task exists and user owns it
        task = db.query(Task).filter(Task.id == dataset_data.task_id).first()
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

        # Sanitize dataset name
        safe_name = sanitize_input(dataset_data.name)

        # Calculate dataset statistics
        example_count = len(dataset_data.examples) if dataset_data.examples else 0
        stats = {
            "example_count": example_count,
            "created_from": "manual",  # or "generated", "imported"
        }

        # Create dataset
        dataset = Dataset(
            id=uuid4(),
            user_id=user_id,
            task_id=dataset_data.task_id,
            name=safe_name,
            split=dataset_data.split,
            stats=stats,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        db.add(dataset)
        db.flush()  # Get dataset ID

        # Add training examples
        if dataset_data.examples:
            for example_data in dataset_data.examples:
                example = TrainingExample(
                    id=uuid4(),
                    dataset_id=dataset.id,
                    input_text=sanitize_input(example_data.input_text),
                    output_text=sanitize_input(example_data.output_text),
                    metadata=example_data.metadata or {},
                    created_at=datetime.utcnow()
                )
                db.add(example)

        db.commit()
        db.refresh(dataset)

        logger.info(f"Dataset {dataset.id} created with {example_count} examples")
        return dataset

    async def get_dataset(
        self,
        db: Session,
        dataset_id: UUID,
        user_id: UUID
    ) -> Dataset:
        """
        Get dataset by ID with ownership check.

        Args:
            db: Database session
            dataset_id: Dataset ID
            user_id: User requesting the dataset

        Returns:
            Dataset

        Raises:
            HTTPException: If not found or access denied
        """
        dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()

        if not dataset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dataset not found"
            )

        if dataset.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resource not found or access denied"
            )

        return dataset

    async def list_datasets(
        self,
        db: Session,
        task_id: UUID,
        user_id: UUID
    ) -> List[Dataset]:
        """
        List datasets for a task.

        Args:
            db: Database session
            task_id: Task ID
            user_id: User requesting the datasets

        Returns:
            List of datasets

        Raises:
            HTTPException: If task not found or access denied
        """
        # Verify task ownership
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

        return (
            db.query(Dataset)
            .filter(Dataset.task_id == task_id)
            .order_by(Dataset.created_at.desc())
            .all()
        )

    async def add_examples(
        self,
        db: Session,
        dataset_id: UUID,
        user_id: UUID,
        examples: List[TrainingExampleCreate]
    ) -> List[TrainingExample]:
        """
        Add training examples to a dataset.

        Args:
            db: Database session
            dataset_id: Dataset ID
            user_id: User adding examples
            examples: List of examples to add

        Returns:
            List of created training examples

        Raises:
            HTTPException: If dataset not found or access denied
        """
        # Verify dataset ownership
        dataset = await self.get_dataset(db, dataset_id, user_id)

        # Create training examples
        created_examples = []
        for example_data in examples:
            example = TrainingExample(
                id=uuid4(),
                dataset_id=dataset_id,
                input_text=sanitize_input(example_data.input_text),
                output_text=sanitize_input(example_data.output_text),
                metadata=example_data.metadata or {},
                created_at=datetime.utcnow()
            )
            db.add(example)
            created_examples.append(example)

        # Update dataset stats
        current_count = dataset.stats.get("example_count", 0)
        dataset.stats["example_count"] = current_count + len(examples)
        dataset.updated_at = datetime.utcnow()

        db.commit()

        # Refresh all examples
        for example in created_examples:
            db.refresh(example)

        logger.info(f"Added {len(examples)} examples to dataset {dataset_id}")
        return created_examples

    async def generate_examples(
        self,
        db: Session,
        task_id: UUID,
        user_id: UUID,
        count: int = 10,
        focus_areas: List[str] = None
    ) -> List[dict]:
        """
        Generate synthetic training examples using the agent service.

        Args:
            db: Database session
            task_id: Task ID
            user_id: User requesting generation
            count: Number of examples to generate
            focus_areas: Optional specific areas to focus on

        Returns:
            List of generated examples (not yet saved to database)

        Raises:
            HTTPException: If task not found or access denied
        """
        # Verify task ownership
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

        # Generate examples using agent service
        try:
            examples = await agent_service.generate_examples(
                db=db,
                task=task,
                count=count,
                focus_areas=focus_areas
            )
            logger.info(f"Generated {len(examples)} examples for task {task_id}")
            return examples
        except Exception as e:
            logger.error(f"Example generation failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Example generation failed: {str(e)}"
            )


# Global service instance
dataset_service = DatasetService()
