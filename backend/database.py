"""Database configuration and session management."""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from backend.config import settings

# Create database engine
# SQLite doesn't support pool_size and max_overflow
if settings.DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=settings.is_development,  # Log SQL in development
    )
else:
    engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
        pool_size=20,
        max_overflow=0,
        echo=settings.is_development,  # Log SQL in development
    )

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Create declarative base for models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Database session dependency for FastAPI.

    Yields:
        Database session

    Example:
        @app.get("/api/tasks")
        async def get_tasks(db: Session = Depends(get_db)):
            return db.query(Task).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def init_db() -> None:
    """Initialize database (create tables if they don't exist)."""
    # Import all models here to ensure they're registered
    from backend.models import (
        user,
        task,
        dataset,
        training_job,
        model_version,
        deployment,
        api_key,
        feedback,
    )

    Base.metadata.create_all(bind=engine)
