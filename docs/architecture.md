# Architecture Documentation

## System Overview

The Fine-Tune Platform is built as a distributed system with clear separation of concerns:

```
┌─────────────┐
│   Browser   │
└──────┬──────┘
       │
       │ HTTPS
       │
┌──────▼──────────────────────────────────────┐
│            Frontend (React)                 │
│  ┌──────────────┐  ┌────────────────────┐  │
│  │ Task Creator │  │ Data Editor        │  │
│  └──────────────┘  └────────────────────┘  │
│  ┌──────────────┐  ┌────────────────────┐  │
│  │ Eval UI      │  │ Deployment Manager │  │
│  └──────────────┘  └────────────────────┘  │
└──────────────┬──────────────────────────────┘
               │
               │ REST API
               │
┌──────────────▼──────────────────────────────┐
│          Backend (FastAPI)                  │
│  ┌──────────┐ ┌──────────┐ ┌────────────┐  │
│  │ API      │ │ Auth     │ │ Jobs       │  │
│  │ Routes   │ │ Service  │ │ Queue      │  │
│  └──────────┘ └──────────┘ └────────────┘  │
│  ┌──────────┐ ┌──────────┐ ┌────────────┐  │
│  │ Agent    │ │ Training │ │ Evaluation │  │
│  │ Service  │ │ Service  │ │ Service    │  │
│  └──────────┘ └──────────┘ └────────────┘  │
└─────┬────────────┬────────────┬─────────────┘
      │            │            │
      │            │            │
   ┌──▼──┐    ┌────▼─────┐  ┌──▼────┐
   │ DB  │    │  Redis   │  │  S3   │
   │(PG) │    │  Queue   │  │Storage│
   └─────┘    └────┬─────┘  └───────┘
                   │
                   │
          ┌────────▼────────┐
          │  Modal Workers  │
          ├─────────────────┤
          │  Training Jobs  │
          │  (GPU)          │
          ├─────────────────┤
          │  Inference      │
          │  (vLLM)         │
          └─────────────────┘
```

## Component Details

### Frontend Layer

**Technology**: React 18 + TypeScript + Vite

**Key Components**:

1. **Task Creator**
   - Form for task description
   - Real-time agent analysis feedback
   - Configuration preview

2. **Data Editor**
   - Table view for training examples
   - AI-assisted example generation
   - Import/export functionality
   - Quality metrics display

3. **Training Dashboard**
   - Progress tracking
   - Live metrics (loss, perplexity)
   - Error handling and retries

4. **Evaluation Playground**
   - Side-by-side comparison
   - Thumbs up/down feedback
   - Comment collection
   - Version selection

5. **Deployment Manager**
   - One-click deploy
   - API key management
   - Usage analytics
   - Public sharing controls

**State Management**: React Context + React Query for server state

**Routing**: React Router v6

### Backend Layer

**Technology**: Python 3.10+ FastAPI + SQLAlchemy + Alembic

**Core Services**:

1. **Agent Service** (`services/agent.py`)
   ```python
   class AgentService:
       async def analyze_task(self, description: str) -> TaskAnalysis
       async def generate_examples(self, task: Task, count: int) -> List[Example]
       async def analyze_failures(self, feedback: List[Feedback]) -> FailureAnalysis
       async def recommend_improvements(self, task: Task) -> Recommendations
   ```

2. **Training Service** (`services/training.py`)
   ```python
   class TrainingService:
       async def create_job(self, task_id: UUID, dataset_id: UUID) -> TrainingJob
       async def start_training(self, job_id: UUID) -> None
       async def get_status(self, job_id: UUID) -> JobStatus
       async def cancel_job(self, job_id: UUID) -> None
   ```

3. **Evaluation Service** (`services/evaluation.py`)
   ```python
   class EvaluationService:
       async def evaluate_model(self, model_id: UUID, test_set: Dataset) -> Metrics
       async def run_llm_judge(self, examples: List[Example]) -> List[JudgeScore]
       async def collect_feedback(self, model_id: UUID) -> FeedbackSummary
   ```

4. **Deployment Service** (`services/deployment.py`)
   ```python
   class DeploymentService:
       async def deploy_model(self, model_id: UUID) -> Deployment
       async def get_endpoint_url(self, deployment_id: UUID) -> str
       async def scale_inference(self, deployment_id: UUID, instances: int) -> None
   ```

### Database Schema

**PostgreSQL 15+** with the following main tables:

```sql
-- Users
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    plan VARCHAR(50) DEFAULT 'free',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Tasks
CREATE TABLE tasks (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    name VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    task_type VARCHAR(50),
    config JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Datasets
CREATE TABLE datasets (
    id UUID PRIMARY KEY,
    task_id UUID REFERENCES tasks(id),
    version INT DEFAULT 1,
    stats JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Training Examples
CREATE TABLE training_examples (
    id UUID PRIMARY KEY,
    dataset_id UUID REFERENCES datasets(id),
    input TEXT NOT NULL,
    output TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Training Jobs
CREATE TABLE training_jobs (
    id UUID PRIMARY KEY,
    task_id UUID REFERENCES tasks(id),
    dataset_id UUID REFERENCES datasets(id),
    status VARCHAR(50) DEFAULT 'queued',
    config JSONB,
    metrics JSONB,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT
);

-- Model Versions
CREATE TABLE model_versions (
    id UUID PRIMARY KEY,
    task_id UUID REFERENCES tasks(id),
    training_job_id UUID REFERENCES training_jobs(id),
    version INT NOT NULL,
    weights_path VARCHAR(512),
    eval_results JSONB,
    user_rating FLOAT,
    deployment_status VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Evaluation Feedback
CREATE TABLE evaluation_feedback (
    id UUID PRIMARY KEY,
    model_version_id UUID REFERENCES model_versions(id),
    example_input TEXT NOT NULL,
    model_output TEXT NOT NULL,
    user_rating VARCHAR(50),
    user_comment TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Deployments
CREATE TABLE deployments (
    id UUID PRIMARY KEY,
    model_version_id UUID REFERENCES model_versions(id),
    endpoint_url VARCHAR(512),
    status VARCHAR(50) DEFAULT 'pending',
    inference_count INT DEFAULT 0,
    is_public BOOLEAN DEFAULT false,
    share_token VARCHAR(255) UNIQUE,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Storage Layer

**S3 (or compatible)**:

```
s3://finetune-models/
├── datasets/
│   └── {dataset_id}.json
├── models/
│   └── {model_version_id}/
│       ├── adapter_model.bin
│       ├── adapter_config.json
│       └── training_args.bin
├── logs/
│   └── {job_id}/
│       ├── train.log
│       └── tensorboard/
└── evaluations/
    └── {model_version_id}/
        └── results.json
```

### Queue System

**Redis** for job queue and pub/sub:

```python
# Job Queue
QUEUE_TRAINING = "training_jobs"
QUEUE_EVALUATION = "evaluation_jobs"
QUEUE_DEPLOYMENT = "deployment_jobs"

# Pub/Sub Channels
CHANNEL_JOB_UPDATES = "job_updates:{job_id}"
CHANNEL_TRAINING_METRICS = "training_metrics:{job_id}"
```

### Training Infrastructure (Modal)

**Modal Functions**:

1. **Training Function** (`training/train.py`)
   ```python
   @app.function(
       gpu="A10G",
       timeout=3600,
       secrets=[modal.Secret.from_name("huggingface")]
   )
   def train_model(
       dataset_path: str,
       config: dict,
       output_path: str
   ) -> dict:
       # Load dataset from S3
       # Initialize QLoRA model
       # Run training
       # Save to S3
       # Return metrics
   ```

2. **Evaluation Function** (`training/evaluate.py`)
   ```python
   @app.function(gpu="T4", timeout=600)
   def evaluate_model(
       model_path: str,
       test_set_path: str
   ) -> dict:
       # Load model from S3
       # Run inference on test set
       # Compute metrics
       # Return results
   ```

3. **Inference Function** (`deployment/inference.py`)
   ```python
   @app.function(
       gpu="T4",
       keep_warm=1,
       allow_concurrent_inputs=10
   )
   @modal.web_endpoint(method="POST")
   def inference(request: dict) -> dict:
       # Load model (cached)
       # Run inference with vLLM
       # Return predictions
   ```

## Data Flow

### Training Flow

```
1. User creates task
   → POST /api/tasks
   → Agent analyzes task
   → Returns recommended config

2. User adds examples
   → POST /api/tasks/{id}/examples (bulk)
   → Validates format
   → Stores in DB
   → Calculates diversity metrics

3. User starts training
   → POST /api/training-jobs
   → Creates job in DB (status: queued)
   → Uploads dataset to S3
   → Pushes to Redis queue
   → Returns job_id

4. Modal worker picks up job
   → Polls Redis queue
   → Downloads dataset from S3
   → Runs QLoRA training
   → Publishes metrics to Redis (real-time)
   → Uploads model to S3
   → Updates job status in DB

5. Backend triggers evaluation
   → Calls Modal evaluate function
   → Stores results in S3
   → Updates model_versions table
   → Notifies user (email/websocket)
```

### Evaluation Flow

```
1. User opens evaluation UI
   → GET /api/training-jobs/{id}/evaluate
   → Returns 10 random test examples
   → Loads base model + fine-tuned model

2. User rates each output
   → POST /api/evaluation-feedback (per example)
   → Stores in DB

3. Agent analyzes feedback
   → Detects patterns in failures
   → Generates recommendations
   → Returns to UI

4. User chooses next step
   → Deploy (if good)
   → Generate more data (if specific failures)
   → Run DPO (if preference issues)
```

### Deployment Flow

```
1. User clicks "Deploy"
   → POST /api/deployments
   → Creates deployment record
   → Triggers Modal deploy

2. Modal spins up vLLM
   → Loads model from S3
   → Starts inference server
   → Returns endpoint URL

3. Deployment ready
   → Updates deployment status
   → Returns API key to user
   → User can test in playground

4. Usage tracking
   → Each inference request logged
   → Metrics aggregated hourly
   → Billing calculated
```

## Security Considerations

1. **Authentication**: JWT tokens with refresh mechanism
2. **Authorization**: Row-level security in PostgreSQL
3. **API Rate Limiting**: Redis-backed rate limiter
4. **Data Encryption**:
   - At rest: S3 server-side encryption
   - In transit: TLS 1.3
5. **Secrets Management**: Environment variables + Modal secrets
6. **Input Validation**: Pydantic models for all API inputs

## Scalability

### Current Limits (MVP)
- 1000 concurrent users
- 100 training jobs/hour
- 10,000 inference requests/day

### Scaling Strategy
1. **Horizontal scaling**:
   - Frontend: CDN + multiple app servers
   - Backend: Load balanced FastAPI instances
   - Database: Read replicas for queries

2. **Vertical scaling**:
   - Modal auto-scales GPU workers
   - Redis cluster for job queue

3. **Caching**:
   - Model weights cached on Modal
   - API responses cached with Redis
   - Frontend assets on CDN

## Monitoring

1. **Application Metrics**:
   - Training job success rate
   - Average training time
   - Inference latency (p50, p95, p99)

2. **Infrastructure**:
   - Modal GPU utilization
   - Database connection pool
   - Redis queue depth

3. **Business Metrics**:
   - User signups
   - Training jobs per user
   - Deployment rate
   - User retention

## Cost Optimization

1. **Training**:
   - Use spot instances on Modal (30% cheaper)
   - Automatic job timeout (prevent runaway costs)
   - Smart batching of small jobs

2. **Inference**:
   - Cold start for low-traffic models
   - Keep-warm only for popular models
   - Request batching with vLLM

3. **Storage**:
   - S3 lifecycle policies (archive old models)
   - Compress training logs
   - Delete unused datasets

## Development vs Production

### Development
- SQLite for database (optional)
- MinIO for S3 (local)
- Mock Modal functions (fast iteration)

### Production
- RDS PostgreSQL (managed)
- S3 (with CloudFront CDN)
- Modal production environment
- Monitoring with Datadog/Sentry

## Next Steps

1. Implement core backend API
2. Set up Modal training functions
3. Build React frontend
4. Integrate Claude agent
5. End-to-end testing
6. Deploy to staging environment
