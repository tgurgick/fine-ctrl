"""API schemas package."""
from backend.schemas.auth import (
    UserRegister,
    UserLogin,
    Token,
    TokenRefresh,
    AccessToken,
    TokenData,
)
from backend.schemas.user import (
    UserBase,
    UserCreate,
    UserUpdate,
    UserResponse,
    UserProfile,
)
from backend.schemas.task import (
    TaskBase,
    TaskCreate,
    TaskUpdate,
    TaskResponse,
    TaskDetail,
)
from backend.schemas.dataset import (
    TrainingExampleBase,
    TrainingExampleCreate,
    TrainingExampleResponse,
    DatasetBase,
    DatasetCreate,
    DatasetUpdate,
    DatasetResponse,
    DatasetDetail,
)
from backend.schemas.training import (
    TrainingJobBase,
    TrainingJobCreate,
    TrainingJobUpdate,
    TrainingJobResponse,
    ModelVersionBase,
    ModelVersionCreate,
    ModelVersionUpdate,
    ModelVersionResponse,
)
from backend.schemas.deployment import (
    DeploymentBase,
    DeploymentCreate,
    DeploymentUpdate,
    DeploymentResponse,
    InferenceRequest,
    InferenceResponse,
)
from backend.schemas.api_key import (
    APIKeyBase,
    APIKeyCreate,
    APIKeyUpdate,
    APIKeyResponse,
    APIKeyCreated,
)
from backend.schemas.evaluation import (
    EvaluationRequest,
    EvaluationMetrics,
    EvaluationResult,
    FeedbackCreate,
    FeedbackResponse,
    FeedbackSample,
    FeedbackAnalysis,
    SampleSelectionRequest,
    SampleSelectionResponse,
)

__all__ = [
    # Auth
    "UserRegister",
    "UserLogin",
    "Token",
    "TokenRefresh",
    "AccessToken",
    "TokenData",
    # User
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserProfile",
    # Task
    "TaskBase",
    "TaskCreate",
    "TaskUpdate",
    "TaskResponse",
    "TaskDetail",
    # Dataset
    "TrainingExampleBase",
    "TrainingExampleCreate",
    "TrainingExampleResponse",
    "DatasetBase",
    "DatasetCreate",
    "DatasetUpdate",
    "DatasetResponse",
    "DatasetDetail",
    # Training
    "TrainingJobBase",
    "TrainingJobCreate",
    "TrainingJobUpdate",
    "TrainingJobResponse",
    "ModelVersionBase",
    "ModelVersionCreate",
    "ModelVersionUpdate",
    "ModelVersionResponse",
    # Deployment
    "DeploymentBase",
    "DeploymentCreate",
    "DeploymentUpdate",
    "DeploymentResponse",
    "InferenceRequest",
    "InferenceResponse",
    # API Key
    "APIKeyBase",
    "APIKeyCreate",
    "APIKeyUpdate",
    "APIKeyResponse",
    "APIKeyCreated",
    # Evaluation
    "EvaluationRequest",
    "EvaluationMetrics",
    "EvaluationResult",
    "FeedbackCreate",
    "FeedbackResponse",
    "FeedbackSample",
    "FeedbackAnalysis",
    "SampleSelectionRequest",
    "SampleSelectionResponse",
]
