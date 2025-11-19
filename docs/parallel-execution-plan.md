# Parallel Execution Plan - Fine-Tune Platform MVP

This document breaks down the MVP into independent work packages that can be executed in parallel by multiple agents/developers.

## Execution Strategy

### Phase 0: Foundation (Sequential - Must Complete First)
**Duration**: 2-4 hours
**Assignee**: Single agent
**Blockers**: None

This phase establishes contracts that all other work packages depend on.

### Phase 1: Parallel Development (Can Run Simultaneously)
**Duration**: 6-12 hours per package
**Assignees**: 6 agents working in parallel
**Blockers**: Phase 0 must complete first

### Phase 2: Integration & Testing (Sequential)
**Duration**: 2-4 hours
**Assignee**: Single agent
**Blockers**: Phase 1 must complete first

---

## Phase 0: Foundation Work

### WP-0: Contracts & Schemas
**Agent ID**: `foundation-agent`
**Estimated Time**: 2-4 hours
**Dependencies**: None
**Blocks**: All Phase 1 work packages

#### Deliverables

1. **Database Schema** (`backend/models/`)
   - SQLAlchemy models for all entities
   - Alembic migration scripts
   - Database creation script

2. **API Contracts** (`backend/schemas/`)
   - Pydantic request/response schemas for all endpoints
   - OpenAPI spec generation

3. **Type Definitions** (`frontend/src/types/`)
   - TypeScript interfaces matching API schemas
   - Shared constants and enums

4. **Mock Data** (`tests/fixtures/`)
   - Sample tasks, datasets, jobs for testing
   - Mock API responses

#### Acceptance Criteria
- [ ] All database models defined with proper relationships
- [ ] Migration creates all tables successfully
- [ ] Pydantic schemas validate correctly
- [ ] TypeScript types compile without errors
- [ ] Mock data available for all entities
- [ ] OpenAPI spec generated and accessible at `/docs`

#### Files to Create
```
backend/
├── models/
│   ├── __init__.py
│   ├── user.py
│   ├── task.py
│   ├── dataset.py
│   ├── training_job.py
│   ├── model_version.py
│   ├── feedback.py
│   └── deployment.py
├── schemas/
│   ├── __init__.py
│   ├── task.py
│   ├── dataset.py
│   ├── training.py
│   ├── evaluation.py
│   └── deployment.py
└── alembic/
    └── versions/
        └── 001_initial_schema.py

frontend/src/types/
├── index.ts
├── task.ts
├── dataset.ts
├── training.ts
└── api.ts

tests/fixtures/
├── tasks.json
├── datasets.json
└── training_jobs.json
```

#### Testing
```bash
# Backend
cd backend
pytest tests/test_models.py
pytest tests/test_schemas.py

# Frontend
cd frontend
npm run type-check
```

---

## Phase 1: Parallel Development

### WP-1: Frontend Shell & Components
**Agent ID**: `frontend-agent`
**Estimated Time**: 8-10 hours
**Dependencies**: WP-0
**Parallel With**: WP-2, WP-3, WP-4, WP-5, WP-6

#### Scope
Build all UI components and pages WITHOUT backend integration. Use mock data from WP-0.

#### Deliverables

1. **Project Setup**
   - Vite + React + TypeScript
   - Routing (React Router)
   - State management (React Query + Context)
   - Styling (Tailwind CSS)

2. **Shared Components** (`frontend/src/components/`)
   - Button, Input, TextArea
   - Table, Modal, Card
   - LoadingSpinner, ProgressBar
   - ErrorBoundary, Toast notifications

3. **Pages** (`frontend/src/pages/`)
   - TaskCreatePage
   - DataEditorPage
   - TrainingDashboardPage
   - EvaluationPage
   - DeploymentPage

4. **Mock API Client** (`frontend/src/api/mock.ts`)
   - Returns fixture data from WP-0
   - Simulates delays (setTimeout)
   - No actual HTTP calls

#### Acceptance Criteria
- [ ] All pages render without errors
- [ ] Navigation works between all pages
- [ ] Forms accept input and validate
- [ ] Table displays mock data
- [ ] Loading and error states work
- [ ] Responsive design (mobile + desktop)
- [ ] TypeScript compiles with no errors
- [ ] All components have basic tests

#### Files to Create
```
frontend/
├── src/
│   ├── components/
│   │   ├── Button/
│   │   ├── Input/
│   │   ├── Table/
│   │   ├── Modal/
│   │   ├── Card/
│   │   ├── ProgressBar/
│   │   └── Toast/
│   ├── pages/
│   │   ├── TaskCreatePage/
│   │   ├── DataEditorPage/
│   │   ├── TrainingDashboardPage/
│   │   ├── EvaluationPage/
│   │   └── DeploymentPage/
│   ├── hooks/
│   │   ├── useTask.ts
│   │   ├── useDataset.ts
│   │   └── useTraining.ts
│   ├── api/
│   │   └── mock.ts
│   └── App.tsx
├── package.json
└── vite.config.ts
```

#### Testing
```bash
npm test
npm run type-check
npm run lint
npm run build
```

#### Integration Points
- Will swap `mock.ts` for `client.ts` in Phase 2
- API contract from WP-0 ensures compatibility

---

### WP-2: Backend API Routes
**Agent ID**: `backend-api-agent`
**Estimated Time**: 6-8 hours
**Dependencies**: WP-0
**Parallel With**: WP-1, WP-3, WP-4, WP-5, WP-6

#### Scope
Implement all REST API endpoints WITHOUT business logic. Return mock/placeholder responses.

#### Deliverables

1. **FastAPI Application Setup**
   - App initialization with CORS
   - Database connection
   - Error handlers
   - Health check endpoint

2. **API Routes** (`backend/api/routes/`)
   - Tasks CRUD endpoints
   - Dataset management endpoints
   - Training job endpoints
   - Evaluation endpoints
   - Deployment endpoints

3. **Dependency Injection** (`backend/api/deps.py`)
   - Database session
   - Current user (placeholder auth)
   - Service instances

4. **Placeholder Responses**
   - Return fixture data from WP-0
   - Validate request schemas
   - No actual business logic yet

#### Acceptance Criteria
- [ ] All endpoints defined and documented
- [ ] Request validation works (Pydantic)
- [ ] Returns correct response schemas
- [ ] OpenAPI docs accessible at `/docs`
- [ ] Health check returns 200
- [ ] CORS configured correctly
- [ ] All endpoints have unit tests

#### Files to Create
```
backend/
├── main.py
├── config.py
├── api/
│   ├── __init__.py
│   ├── deps.py
│   └── routes/
│       ├── __init__.py
│       ├── tasks.py
│       ├── datasets.py
│       ├── training.py
│       ├── evaluation.py
│       └── deployments.py
└── tests/
    └── api/
        ├── test_tasks.py
        ├── test_datasets.py
        ├── test_training.py
        ├── test_evaluation.py
        └── test_deployments.py
```

#### Testing
```bash
pytest tests/api/
curl http://localhost:8000/health
curl http://localhost:8000/docs
```

#### Integration Points
- Service layer (WP-3, WP-4, WP-5, WP-6) will be injected in Phase 2
- Uses schemas from WP-0

---

### WP-3: Agent Service
**Agent ID**: `agent-service-agent`
**Estimated Time**: 6-8 hours
**Dependencies**: WP-0
**Parallel With**: WP-1, WP-2, WP-4, WP-5, WP-6

#### Scope
Implement Claude integration for task analysis, data generation, and failure analysis.

#### Deliverables

1. **Agent Service** (`backend/services/agent.py`)
   - Task analyzer
   - Example generator
   - Failure pattern analyzer
   - Recommendation engine

2. **Prompt Templates** (`backend/prompts/`)
   - Task analysis prompt
   - Data generation prompt
   - Failure analysis prompt
   - Structured output schemas

3. **Response Parsers**
   - JSON extraction from Claude responses
   - Validation of agent outputs
   - Error handling for API failures

4. **Configuration**
   - Anthropic API key management
   - Model selection (Sonnet/Haiku)
   - Retry logic with exponential backoff

#### Acceptance Criteria
- [ ] Task analysis returns valid TaskConfig
- [ ] Generated examples match expected format
- [ ] Failure analysis identifies patterns
- [ ] Handles API errors gracefully
- [ ] Respects rate limits
- [ ] All functions have unit tests with mocked API
- [ ] Integration test with real Anthropic API (optional)

#### Files to Create
```
backend/
├── services/
│   └── agent.py
├── prompts/
│   ├── task_analysis.txt
│   ├── generate_examples.txt
│   └── analyze_failures.txt
└── tests/
    └── services/
        └── test_agent.py
```

#### Example Interface
```python
class AgentService:
    async def analyze_task(
        self,
        description: str,
        sample_data: Optional[List[dict]] = None
    ) -> TaskAnalysis:
        """Analyze task and return recommended config."""

    async def generate_examples(
        self,
        task_description: str,
        count: int,
        focus_area: Optional[str] = None
    ) -> List[TrainingExample]:
        """Generate synthetic training examples."""

    async def analyze_failures(
        self,
        feedback: List[EvaluationFeedback]
    ) -> FailureAnalysis:
        """Identify patterns in failed predictions."""
```

#### Testing
```bash
pytest tests/services/test_agent.py
pytest tests/services/test_agent.py -m integration  # Real API test
```

#### Integration Points
- Used by WP-2 API routes in Phase 2
- Independent of other services

---

### WP-4: Training Service (Modal)
**Agent ID**: `training-agent`
**Estimated Time**: 10-12 hours
**Dependencies**: WP-0
**Parallel With**: WP-1, WP-2, WP-3, WP-5, WP-6

#### Scope
Implement QLoRA training pipeline on Modal with progress tracking.

#### Deliverables

1. **Modal Setup**
   - Modal app configuration
   - Custom image with dependencies
   - GPU selection (A10G)
   - Secret management

2. **Training Function** (`training/train.py`)
   - Dataset loading from S3
   - Model initialization (Mistral 7B + QLoRA)
   - Training loop with TRL SFTTrainer
   - Progress callbacks
   - Model upload to S3

3. **Training Service** (`backend/services/training.py`)
   - Job creation and queuing
   - Modal function invocation
   - Progress tracking (Redis pub/sub)
   - Status updates to database
   - Error handling and retries

4. **Configuration** (`training/config.py`)
   - QLoRA hyperparameters
   - Training arguments
   - Model paths
   - S3 paths

#### Acceptance Criteria
- [ ] Modal function deploys successfully
- [ ] Can train on sample dataset (<100 examples)
- [ ] Progress updates published to Redis
- [ ] Model weights uploaded to S3
- [ ] Training completes in <10 min for small dataset
- [ ] Handles OOM errors gracefully
- [ ] All functions have unit tests
- [ ] End-to-end training test passes

#### Files to Create
```
training/
├── train.py          # Modal function
├── config.py         # Training config
├── utils.py          # Helper functions
└── requirements.txt

backend/services/
└── training.py       # Orchestration service

tests/
├── training/
│   └── test_train.py
└── services/
    └── test_training.py
```

#### Example Interface
```python
# training/train.py
@app.function(gpu="A10G", timeout=3600)
def train_model(
    dataset_s3_path: str,
    output_s3_path: str,
    config: dict,
    progress_channel: str
) -> dict:
    """Run QLoRA training on Modal."""

# backend/services/training.py
class TrainingService:
    async def create_job(
        self,
        task_id: UUID,
        dataset_id: UUID
    ) -> TrainingJob:
        """Create and queue training job."""

    async def start_training(
        self,
        job_id: UUID
    ) -> None:
        """Trigger Modal training function."""

    async def get_progress(
        self,
        job_id: UUID
    ) -> JobProgress:
        """Get real-time training progress."""
```

#### Testing
```bash
# Unit tests (mocked Modal)
pytest tests/services/test_training.py

# Integration test (real Modal)
pytest tests/training/test_train.py -m integration
```

#### Integration Points
- Called by WP-2 training endpoints
- Publishes progress for WP-1 frontend to consume
- Independent of other services

---

### WP-5: Evaluation Service
**Agent ID**: `evaluation-agent`
**Estimated Time**: 6-8 hours
**Dependencies**: WP-0
**Parallel With**: WP-1, WP-2, WP-3, WP-4, WP-6

#### Scope
Implement evaluation metrics, model comparison, and feedback collection.

#### Deliverables

1. **Metrics Calculator** (`evaluation/metrics.py`)
   - Classification metrics (accuracy, F1, precision, recall)
   - Confusion matrix
   - Per-category breakdown
   - Comparison vs base model

2. **Evaluation Service** (`backend/services/evaluation.py`)
   - Run inference on test set
   - Compute metrics
   - Select diverse sample examples
   - Store results in database

3. **Feedback Manager** (`backend/services/feedback.py`)
   - Collect user ratings
   - Aggregate feedback
   - Identify low-confidence predictions
   - Export for analysis

4. **Sample Selector**
   - Pick diverse evaluation examples
   - Balance by category
   - Include edge cases

#### Acceptance Criteria
- [ ] Metrics calculated correctly for classification
- [ ] Confusion matrix generated
- [ ] Sample selection is diverse
- [ ] Feedback stored properly
- [ ] Handles missing ground truth
- [ ] All functions have unit tests
- [ ] Metric calculations verified against sklearn

#### Files to Create
```
evaluation/
├── metrics.py        # Metric calculations
└── selectors.py      # Sample selection

backend/services/
├── evaluation.py     # Evaluation orchestration
└── feedback.py       # Feedback management

tests/
├── evaluation/
│   └── test_metrics.py
└── services/
    ├── test_evaluation.py
    └── test_feedback.py
```

#### Example Interface
```python
# evaluation/metrics.py
def calculate_classification_metrics(
    predictions: List[str],
    ground_truth: List[str],
    categories: List[str]
) -> ClassificationMetrics:
    """Calculate accuracy, F1, precision, recall."""

def generate_confusion_matrix(
    predictions: List[str],
    ground_truth: List[str],
    categories: List[str]
) -> dict:
    """Generate confusion matrix."""

# backend/services/evaluation.py
class EvaluationService:
    async def evaluate_model(
        self,
        model_version_id: UUID,
        test_dataset_id: UUID
    ) -> EvaluationResults:
        """Run full evaluation."""

    async def select_feedback_samples(
        self,
        model_version_id: UUID,
        count: int = 10
    ) -> List[Example]:
        """Select diverse examples for user feedback."""
```

#### Testing
```bash
pytest tests/evaluation/
pytest tests/services/test_evaluation.py
```

#### Integration Points
- Called by WP-2 evaluation endpoints
- Used by WP-1 evaluation page
- Independent of other services

---

### WP-6: Deployment Service
**Agent ID**: `deployment-agent`
**Estimated Time**: 6-8 hours
**Dependencies**: WP-0
**Parallel With**: WP-1, WP-2, WP-3, WP-4, WP-5

#### Scope
Implement model deployment to Modal inference endpoints.

#### Deliverables

1. **Modal Inference Function** (`deployment/inference.py`)
   - Model loading with vLLM
   - Web endpoint
   - Request/response handling
   - Usage logging

2. **Deployment Service** (`backend/services/deployment.py`)
   - Deploy model to Modal
   - Generate API keys
   - Manage endpoint lifecycle
   - Track usage

3. **API Key Manager**
   - Generate secure API keys
   - Store hashed keys
   - Validate requests
   - Rate limiting

4. **Usage Tracker**
   - Log inference requests
   - Calculate latency metrics
   - Aggregate statistics

#### Acceptance Criteria
- [ ] Modal inference endpoint deploys
- [ ] Inference works with sample input
- [ ] API key authentication works
- [ ] Usage tracked correctly
- [ ] Latency <500ms for small models
- [ ] Handles concurrent requests
- [ ] All functions have unit tests
- [ ] End-to-end deployment test passes

#### Files to Create
```
deployment/
├── inference.py      # Modal inference function
└── requirements.txt

backend/services/
├── deployment.py     # Deployment orchestration
└── api_keys.py       # API key management

tests/
├── deployment/
│   └── test_inference.py
└── services/
    └── test_deployment.py
```

#### Example Interface
```python
# deployment/inference.py
@app.function(gpu="T4", keep_warm=1)
@modal.web_endpoint(method="POST")
async def inference(request: dict):
    """Inference endpoint."""

# backend/services/deployment.py
class DeploymentService:
    async def deploy_model(
        self,
        model_version_id: UUID,
        config: DeploymentConfig
    ) -> Deployment:
        """Deploy model to Modal."""

    async def generate_api_key(
        self,
        deployment_id: UUID
    ) -> str:
        """Generate API key for deployment."""

    async def track_usage(
        self,
        deployment_id: UUID,
        request_data: dict
    ) -> None:
        """Log inference request."""
```

#### Testing
```bash
# Unit tests
pytest tests/services/test_deployment.py

# Integration test (real Modal)
pytest tests/deployment/test_inference.py -m integration
```

#### Integration Points
- Called by WP-2 deployment endpoints
- Used by WP-1 deployment page
- Independent of other services

---

## Phase 2: Integration & Testing

### WP-7: Integration
**Agent ID**: `integration-agent`
**Estimated Time**: 3-5 hours
**Dependencies**: All Phase 1 packages
**Blocks**: None

#### Tasks

1. **Backend Integration**
   - Wire services into API routes (replace placeholders)
   - Set up dependency injection
   - Configure database connection
   - Set up Redis for job queue

2. **Frontend Integration**
   - Replace mock API with real HTTP client
   - Set up API base URL configuration
   - Add authentication headers
   - Handle API errors properly

3. **End-to-End Testing**
   - Test complete user flow: create task → add data → train → evaluate → deploy
   - Test error scenarios
   - Test concurrent operations
   - Load testing (optional)

4. **Configuration**
   - Environment variables setup
   - Docker compose for local development
   - README for running locally

#### Acceptance Criteria
- [ ] All API endpoints work with real services
- [ ] Frontend successfully calls backend
- [ ] Can create task and get agent analysis
- [ ] Can add training data and see stats
- [ ] Can trigger training job (with small dataset)
- [ ] Can view evaluation results
- [ ] Can deploy model and call inference endpoint
- [ ] Error handling works across all layers
- [ ] E2E tests pass

#### Files to Create/Modify
```
backend/main.py              # Wire up services
frontend/src/api/client.ts   # Real HTTP client
docker-compose.yml           # Local development
.env.example                 # Environment template
```

#### Testing
```bash
# Start all services
docker-compose up

# Run E2E tests
pytest tests/e2e/
```

---

## Dependency Graph

```
Phase 0: Foundation
    WP-0: Contracts & Schemas
        ↓
        ↓ (blocks all Phase 1)
        ↓
    ┌───┴───┬───────┬────────┬─────────┬─────────┐
    ↓       ↓       ↓        ↓         ↓         ↓
WP-1:   WP-2:   WP-3:    WP-4:     WP-5:     WP-6:
Frontend Backend Agent   Training  Eval      Deploy
Shell   Routes  Service  Service   Service   Service
    │       │       │        │         │         │
    └───┬───┴───┬───┴────┬───┴─────┬───┴────┬────┘
        │       │        │         │        │
        └───────┴────────┴─────────┴────────┘
                    ↓
            Phase 2: Integration
                WP-7: Integration & E2E
```

## Execution Commands for Agents

### Agent 1: Foundation Agent (WP-0)
```bash
# Context
You are setting up the foundation for a fine-tuning platform.
Your job is to create database models, API schemas, and TypeScript types.

# Starting point
git checkout -b foundation
cd backend

# Tasks
1. Create all SQLAlchemy models in backend/models/
2. Create all Pydantic schemas in backend/schemas/
3. Create TypeScript types in frontend/src/types/
4. Create mock fixtures in tests/fixtures/
5. Generate Alembic migration
6. Test that migration runs successfully

# Acceptance
- pytest tests/test_models.py passes
- pytest tests/test_schemas.py passes
- npm run type-check passes (in frontend/)
- Migration creates all tables

# Deliverables
Commit to 'foundation' branch with all files listed in WP-0.
```

### Agent 2: Frontend Agent (WP-1)
**Wait for WP-0 to complete, then:**
```bash
# Context
You are building the frontend UI components and pages.
Use MOCK data - no real API calls yet.

# Starting point
git checkout foundation
git checkout -b frontend
cd frontend

# Tasks
1. Set up Vite + React + TypeScript + Tailwind
2. Create all shared components
3. Create all pages (use mock data from tests/fixtures/)
4. Set up routing
5. Add form validation
6. Make it responsive

# Acceptance
- npm run build succeeds
- npm test passes
- npm run type-check passes
- All pages render without errors
- Can navigate between pages

# Deliverables
Commit to 'frontend' branch with all files listed in WP-1.
```

### Agent 3: Backend Routes Agent (WP-2)
**Wait for WP-0 to complete, then:**
```bash
# Context
You are building the FastAPI backend routes.
Return PLACEHOLDER responses - no real business logic yet.

# Starting point
git checkout foundation
git checkout -b backend-routes
cd backend

# Tasks
1. Set up FastAPI app with CORS
2. Create all API routes (return fixture data)
3. Add request validation (Pydantic)
4. Set up dependency injection structure
5. Add health check endpoint
6. Write unit tests for each route

# Acceptance
- uvicorn main:app runs without errors
- All endpoints return 200 with fixture data
- OpenAPI docs accessible at /docs
- pytest tests/api/ passes

# Deliverables
Commit to 'backend-routes' branch with all files listed in WP-2.
```

### Agent 4: Agent Service Agent (WP-3)
**Wait for WP-0 to complete, then:**
```bash
# Context
You are building the Claude AI agent integration service.
This service analyzes tasks, generates examples, and analyzes failures.

# Starting point
git checkout foundation
git checkout -b agent-service
cd backend

# Tasks
1. Create AgentService class in services/agent.py
2. Write prompt templates in prompts/
3. Implement task analysis with Claude API
4. Implement example generation
5. Implement failure analysis
6. Add error handling and retries
7. Write unit tests (mock Anthropic API)

# Acceptance
- pytest tests/services/test_agent.py passes
- Task analysis returns valid TaskAnalysis object
- Generated examples match expected format
- Handles API errors gracefully

# Deliverables
Commit to 'agent-service' branch with all files listed in WP-3.
```

### Agent 5: Training Service Agent (WP-4)
**Wait for WP-0 to complete, then:**
```bash
# Context
You are building the QLoRA training pipeline on Modal.
This includes the Modal function and the orchestration service.

# Starting point
git checkout foundation
git checkout -b training-service

# Tasks
1. Set up Modal app and custom image
2. Create QLoRA training function in training/train.py
3. Create TrainingService orchestration in backend/services/training.py
4. Implement progress tracking with Redis
5. Add S3 upload/download
6. Write tests (mock Modal for unit tests)

# Acceptance
- modal deploy training/train.py succeeds
- Can train on small dataset (<100 examples)
- Progress updates work
- Model uploaded to S3
- pytest tests/services/test_training.py passes

# Deliverables
Commit to 'training-service' branch with all files listed in WP-4.
```

### Agent 6: Evaluation Service Agent (WP-5)
**Wait for WP-0 to complete, then:**
```bash
# Context
You are building the evaluation and feedback services.
Calculate metrics, select samples, and manage user feedback.

# Starting point
git checkout foundation
git checkout -b evaluation-service

# Tasks
1. Create metrics calculator in evaluation/metrics.py
2. Create EvaluationService in backend/services/evaluation.py
3. Create FeedbackService in backend/services/feedback.py
4. Implement sample selection logic
5. Write unit tests

# Acceptance
- pytest tests/evaluation/test_metrics.py passes
- Metrics match sklearn calculations
- Sample selection is diverse
- pytest tests/services/test_evaluation.py passes

# Deliverables
Commit to 'evaluation-service' branch with all files listed in WP-5.
```

### Agent 7: Deployment Service Agent (WP-6)
**Wait for WP-0 to complete, then:**
```bash
# Context
You are building the model deployment service.
Deploy models to Modal inference endpoints with API key auth.

# Starting point
git checkout foundation
git checkout -b deployment-service

# Tasks
1. Create Modal inference function in deployment/inference.py
2. Create DeploymentService in backend/services/deployment.py
3. Implement API key generation and validation
4. Add usage tracking
5. Write tests (mock Modal for unit tests)

# Acceptance
- modal deploy deployment/inference.py succeeds
- Inference endpoint responds to requests
- API key authentication works
- Usage tracked correctly
- pytest tests/services/test_deployment.py passes

# Deliverables
Commit to 'deployment-service' branch with all files listed in WP-6.
```

### Agent 8: Integration Agent (WP-7)
**Wait for ALL Phase 1 agents to complete, then:**
```bash
# Context
You are integrating all the pieces together.
Wire up services to routes, connect frontend to backend, run E2E tests.

# Starting point
git checkout foundation
git merge frontend
git merge backend-routes
git merge agent-service
git merge training-service
git merge evaluation-service
git merge deployment-service
git checkout -b integration

# Tasks
1. Wire all services into API route dependencies
2. Replace frontend mock API with real HTTP client
3. Set up docker-compose for local development
4. Create .env.example
5. Write E2E tests
6. Update README with setup instructions
7. Test complete user flow

# Acceptance
- docker-compose up starts all services
- Frontend loads at http://localhost:5173
- Backend accessible at http://localhost:8000
- Can complete full flow: task → data → train → eval → deploy
- pytest tests/e2e/ passes

# Deliverables
Commit to 'integration' branch, then merge to main.
```

---

## Timeline Estimation

### Optimistic (All agents work simultaneously)
- **Phase 0**: 2 hours (sequential)
- **Phase 1**: 12 hours (parallel, limited by slowest package)
- **Phase 2**: 3 hours (sequential)
- **Total**: ~17 hours (~2 days)

### Realistic (Accounting for coordination overhead)
- **Phase 0**: 4 hours
- **Phase 1**: 18 hours (debugging, iterations)
- **Phase 2**: 5 hours (integration issues)
- **Total**: ~27 hours (~3-4 days)

### Conservative (Serial execution for comparison)
- Sum of all packages: 50+ hours (~1-2 weeks)

**Speedup from parallelization**: ~2-3x faster

---

## Communication Protocol

### Branch Naming
- `foundation` - WP-0
- `frontend` - WP-1
- `backend-routes` - WP-2
- `agent-service` - WP-3
- `training-service` - WP-4
- `evaluation-service` - WP-5
- `deployment-service` - WP-6
- `integration` - WP-7

### Merge Strategy
1. WP-0 merges to `main` first
2. Phase 1 agents all branch from `main` (after WP-0)
3. Phase 1 agents work independently (no cross-branch dependencies)
4. WP-7 merges all Phase 1 branches together
5. WP-7 resolves any conflicts and integrates
6. WP-7 merges to `main`

### Status Updates
Each agent should update a shared status file:

```json
{
  "wp-0": { "status": "completed", "branch": "foundation" },
  "wp-1": { "status": "in_progress", "branch": "frontend", "progress": 0.6 },
  "wp-2": { "status": "in_progress", "branch": "backend-routes", "progress": 0.4 },
  "wp-3": { "status": "completed", "branch": "agent-service" },
  "wp-4": { "status": "in_progress", "branch": "training-service", "progress": 0.8 },
  "wp-5": { "status": "not_started", "branch": null },
  "wp-6": { "status": "blocked", "reason": "waiting for WP-0" },
  "wp-7": { "status": "not_started", "branch": null }
}
```

---

## Success Criteria

### Phase 0 Complete When:
- [ ] All schemas compile
- [ ] Migration creates all tables
- [ ] Mock data available

### Phase 1 Complete When:
- [ ] All 6 agents have merged their branches
- [ ] All unit tests pass in each branch
- [ ] No merge conflicts between branches

### Phase 2 Complete When:
- [ ] E2E test passes: create task → train → evaluate → deploy
- [ ] All services integrated
- [ ] docker-compose up works

### MVP Complete When:
- [ ] User can describe a task and get agent analysis
- [ ] User can add training examples manually
- [ ] User can train a model (end-to-end on small dataset)
- [ ] User can evaluate results and provide feedback
- [ ] User can deploy model and call inference API
- [ ] All critical paths tested

---

## Risk Mitigation

### Risk: Agent conflicts on shared files
**Mitigation**: WP-0 creates all shared files first. Phase 1 agents only create new files in isolated directories.

### Risk: API contract changes during Phase 1
**Mitigation**: Lock API contracts in WP-0. No changes allowed during Phase 1.

### Risk: Integration failures in Phase 2
**Mitigation**: Clear interfaces defined. Each service testable in isolation.

### Risk: One agent blocks others
**Mitigation**: All Phase 1 work packages are truly independent. Can proceed even if one fails.

### Risk: Merge conflicts
**Mitigation**: Strict directory isolation. Each agent owns specific directories.

---

## Monitoring Parallel Execution

Create a simple dashboard to track progress:

```bash
# scripts/monitor.sh
while true; do
  clear
  echo "=== Parallel Execution Dashboard ==="
  echo ""
  echo "WP-0 (Foundation):    $(git branch | grep foundation && echo '✅' || echo '⏳')"
  echo "WP-1 (Frontend):      $(git branch | grep frontend && echo '✅' || echo '⏳')"
  echo "WP-2 (Backend):       $(git branch | grep backend-routes && echo '✅' || echo '⏳')"
  echo "WP-3 (Agent):         $(git branch | grep agent-service && echo '✅' || echo '⏳')"
  echo "WP-4 (Training):      $(git branch | grep training-service && echo '✅' || echo '⏳')"
  echo "WP-5 (Evaluation):    $(git branch | grep evaluation-service && echo '✅' || echo '⏳')"
  echo "WP-6 (Deployment):    $(git branch | grep deployment-service && echo '✅' || echo '⏳')"
  echo "WP-7 (Integration):   $(git branch | grep integration && echo '✅' || echo '⏳')"
  sleep 5
done
```

This plan enables maximum parallelization while minimizing dependencies and coordination overhead.
