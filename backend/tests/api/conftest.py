"""Shared test fixtures for API tests."""
import pytest
from uuid import uuid4
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.main import app
from backend.database import Base, get_db
from backend.models import User, Task, Dataset, TrainingExample, TrainingJob, ModelVersion, Deployment
from backend.services.auth import auth_service


# Create in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="function")
def db():
    """Create a fresh database for each test."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def test_user(db):
    """Create a test user."""
    user = User(
        id=uuid4(),
        email="test@example.com",
        hashed_password=auth_service.hash_password("testpassword"),
        full_name="Test User",
        is_active="1",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def auth_headers(client, test_user):
    """Get authentication headers for test user."""
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "test@example.com",
            "password": "testpassword",
        },
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def test_task(db, test_user):
    """Create a test task."""
    task = Task(
        id=uuid4(),
        user_id=test_user.id,
        name="Test Task",
        description="Test task description",
        task_type="classification",
        config={"key": "value"},
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@pytest.fixture
def test_dataset(db, test_user, test_task):
    """Create a test dataset with examples."""
    dataset = Dataset(
        id=uuid4(),
        task_id=test_task.id,
        version=1,
        stats={"count": 2},
    )
    db.add(dataset)
    db.flush()

    # Add training examples
    example1 = TrainingExample(
        id=uuid4(),
        dataset_id=dataset.id,
        input="Test input 1",
        output="Test output 1",
        example_metadata={},
    )
    example2 = TrainingExample(
        id=uuid4(),
        dataset_id=dataset.id,
        input="Test input 2",
        output="Test output 2",
        example_metadata={},
    )
    db.add_all([example1, example2])
    db.commit()
    db.refresh(dataset)
    return dataset


@pytest.fixture
def test_training_job(db, test_user, test_task, test_dataset):
    """Create a test training job."""
    job = TrainingJob(
        id=uuid4(),
        user_id=test_user.id,
        task_id=test_task.id,
        dataset_id=test_dataset.id,
        status="queued",
        config={},
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


@pytest.fixture
def test_model_version(db, test_user, test_task, test_training_job):
    """Create a test model version."""
    model = ModelVersion(
        id=uuid4(),
        user_id=test_user.id,
        task_id=test_task.id,
        training_job_id=test_training_job.id,
        version="v1.0",
        status="ready",
        s3_weights_path="s3://bucket/weights.bin",
        s3_adapter_path="s3://bucket/adapter.bin",
        eval_results={"accuracy": 0.95},
        inference_config={},
    )
    db.add(model)
    db.commit()
    db.refresh(model)
    return model


@pytest.fixture
def test_deployment(db, test_user, test_model_version):
    """Create a test deployment."""
    deployment = Deployment(
        id=uuid4(),
        user_id=test_user.id,
        model_version_id=test_model_version.id,
        name="Test Deployment",
        is_public=False,
        status="active",
        endpoint_url="https://mock-endpoint.modal.run/test",
    )
    db.add(deployment)
    db.commit()
    db.refresh(deployment)
    return deployment
