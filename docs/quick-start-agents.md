# Quick Start Guide for Parallel Agent Execution

Use this guide to quickly spin up multiple Claude agents to work on the Fine-Tune Platform MVP in parallel.

## Overview

**Total Time**: ~17-27 hours across 8 work packages
**Parallelization**: 6 agents working simultaneously after foundation
**Speedup**: 2-3x faster than sequential execution

## Execution Sequence

### Step 1: Foundation (1 agent, 2-4 hours)
Run **Agent 1** first to establish contracts.

### Step 2: Parallel Development (6 agents, 6-12 hours each)
Once Agent 1 completes, launch **Agents 2-7** simultaneously.

### Step 3: Integration (1 agent, 3-5 hours)
Once Agents 2-7 complete, run **Agent 8** to integrate everything.

---

## Agent Assignments

### 🔧 Agent 1: Foundation (WP-0)
**Status**: Start immediately
**Branch**: `foundation`
**Time**: 2-4 hours
**Blocks**: All other agents

**Prompt**:
```
You are Agent 1 responsible for WP-0: Foundation work.

Your task is to create the database schema, API contracts, and TypeScript types
that all other agents depend on.

Repository: fine-ctrl
Branch: foundation (create from main)

Read and execute all tasks in:
docs/parallel-execution-plan.md#wp-0-contracts--schemas

Deliverables:
1. Database models (SQLAlchemy) in backend/models/
2. API schemas (Pydantic) in backend/schemas/
3. TypeScript types in frontend/src/types/
4. Mock fixtures in tests/fixtures/
5. Alembic migration script

Acceptance criteria:
- pytest tests/test_models.py passes
- pytest tests/test_schemas.py passes
- npm run type-check passes
- Migration creates all tables successfully

When done, push to 'foundation' branch and merge to main.
```

---

### 🎨 Agent 2: Frontend (WP-1)
**Status**: Wait for Agent 1, then start
**Branch**: `frontend`
**Time**: 8-10 hours
**Dependencies**: WP-0

**Prompt**:
```
You are Agent 2 responsible for WP-1: Frontend Shell & Components.

Your task is to build all React UI components and pages using MOCK data.
Do NOT integrate with real backend yet.

Repository: fine-ctrl
Branch: frontend (create from main after WP-0 merges)

Read and execute all tasks in:
docs/parallel-execution-plan.md#wp-1-frontend-shell--components

Deliverables:
1. Vite + React + TypeScript setup
2. All shared components (Button, Table, Modal, etc.)
3. All pages (Task, Data Editor, Training, Evaluation, Deployment)
4. Mock API client using fixtures from WP-0
5. Routing and navigation

Acceptance criteria:
- npm run build succeeds
- npm test passes
- All pages render without errors
- Can navigate between all pages
- Forms validate input
- Responsive design works

When done, push to 'frontend' branch (do NOT merge yet).
```

---

### 🔌 Agent 3: Backend Routes (WP-2)
**Status**: Wait for Agent 1, then start
**Branch**: `backend-routes`
**Time**: 6-8 hours
**Dependencies**: WP-0

**Prompt**:
```
You are Agent 3 responsible for WP-2: Backend API Routes.

Your task is to implement all FastAPI endpoints with PLACEHOLDER responses.
Do NOT add real business logic yet.

Repository: fine-ctrl
Branch: backend-routes (create from main after WP-0 merges)

Read and execute all tasks in:
docs/parallel-execution-plan.md#wp-2-backend-api-routes

Deliverables:
1. FastAPI app setup with CORS
2. All API routes (tasks, datasets, training, eval, deployment)
3. Request validation with Pydantic
4. Dependency injection structure
5. Health check endpoint
6. Unit tests for all routes

Acceptance criteria:
- uvicorn main:app runs without errors
- All endpoints return 200 with fixture data
- OpenAPI docs at /docs work
- pytest tests/api/ passes

When done, push to 'backend-routes' branch (do NOT merge yet).
```

---

### 🤖 Agent 4: Agent Service (WP-3)
**Status**: Wait for Agent 1, then start
**Branch**: `agent-service`
**Time**: 6-8 hours
**Dependencies**: WP-0

**Prompt**:
```
You are Agent 4 responsible for WP-3: Agent Service (Claude Integration).

Your task is to build the AI agent service that analyzes tasks, generates examples,
and analyzes failures using the Anthropic Claude API.

Repository: fine-ctrl
Branch: agent-service (create from main after WP-0 merges)

Read and execute all tasks in:
docs/parallel-execution-plan.md#wp-3-agent-service

Deliverables:
1. AgentService class in backend/services/agent.py
2. Prompt templates in backend/prompts/
3. Task analysis using Claude API
4. Example generation using Claude API
5. Failure pattern analysis
6. Error handling and retry logic
7. Unit tests with mocked Anthropic API

Acceptance criteria:
- pytest tests/services/test_agent.py passes
- Task analysis returns valid TaskAnalysis
- Generated examples match expected format
- Handles API errors gracefully

When done, push to 'agent-service' branch (do NOT merge yet).
```

---

### 🏋️ Agent 5: Training Service (WP-4)
**Status**: Wait for Agent 1, then start
**Branch**: `training-service`
**Time**: 10-12 hours
**Dependencies**: WP-0

**Prompt**:
```
You are Agent 5 responsible for WP-4: Training Service (Modal + QLoRA).

Your task is to build the QLoRA training pipeline on Modal including the
training function and orchestration service.

Repository: fine-ctrl
Branch: training-service (create from main after WP-0 merges)

Read and execute all tasks in:
docs/parallel-execution-plan.md#wp-4-training-service-modal

Deliverables:
1. Modal app setup and custom image
2. QLoRA training function in training/train.py
3. TrainingService orchestration in backend/services/training.py
4. Progress tracking with Redis pub/sub
5. S3 upload/download for datasets and models
6. Unit tests (mock Modal calls)

Acceptance criteria:
- modal deploy training/train.py succeeds
- Can train on small dataset (<100 examples)
- Progress updates published to Redis
- Model weights uploaded to S3
- pytest tests/services/test_training.py passes

When done, push to 'training-service' branch (do NOT merge yet).
```

---

### 📊 Agent 6: Evaluation Service (WP-5)
**Status**: Wait for Agent 1, then start
**Branch**: `evaluation-service`
**Time**: 6-8 hours
**Dependencies**: WP-0

**Prompt**:
```
You are Agent 6 responsible for WP-5: Evaluation Service.

Your task is to build evaluation metrics, sample selection, and feedback management.

Repository: fine-ctrl
Branch: evaluation-service (create from main after WP-0 merges)

Read and execute all tasks in:
docs/parallel-execution-plan.md#wp-5-evaluation-service

Deliverables:
1. Metrics calculator in evaluation/metrics.py
   (accuracy, F1, precision, recall, confusion matrix)
2. EvaluationService in backend/services/evaluation.py
3. FeedbackService in backend/services/feedback.py
4. Sample selection logic (diverse examples)
5. Unit tests

Acceptance criteria:
- pytest tests/evaluation/test_metrics.py passes
- Metrics match sklearn calculations
- Sample selection is diverse and balanced
- pytest tests/services/test_evaluation.py passes

When done, push to 'evaluation-service' branch (do NOT merge yet).
```

---

### 🚀 Agent 7: Deployment Service (WP-6)
**Status**: Wait for Agent 1, then start
**Branch**: `deployment-service`
**Time**: 6-8 hours
**Dependencies**: WP-0

**Prompt**:
```
You are Agent 7 responsible for WP-6: Deployment Service.

Your task is to build model deployment to Modal inference endpoints with
API key authentication and usage tracking.

Repository: fine-ctrl
Branch: deployment-service (create from main after WP-0 merges)

Read and execute all tasks in:
docs/parallel-execution-plan.md#wp-6-deployment-service

Deliverables:
1. Modal inference function in deployment/inference.py
2. DeploymentService in backend/services/deployment.py
3. API key generation and validation
4. Usage tracking and metrics
5. Unit tests (mock Modal calls)

Acceptance criteria:
- modal deploy deployment/inference.py succeeds
- Inference endpoint responds to requests
- API key authentication works
- Usage tracked correctly
- pytest tests/services/test_deployment.py passes

When done, push to 'deployment-service' branch (do NOT merge yet).
```

---

### 🔗 Agent 8: Integration (WP-7)
**Status**: Wait for Agents 2-7, then start
**Branch**: `integration`
**Time**: 3-5 hours
**Dependencies**: WP-1 through WP-6

**Prompt**:
```
You are Agent 8 responsible for WP-7: Integration & E2E Testing.

Your task is to integrate all the components built by Agents 2-7 and ensure
the entire system works end-to-end.

Repository: fine-ctrl
Branch: integration (merge all Phase 1 branches)

Read and execute all tasks in:
docs/parallel-execution-plan.md#wp-7-integration

Steps:
1. Merge all Phase 1 branches (frontend, backend-routes, agent-service,
   training-service, evaluation-service, deployment-service)
2. Resolve any merge conflicts
3. Wire services into API routes
4. Replace frontend mock API with real HTTP client
5. Set up docker-compose for local development
6. Create .env.example
7. Write E2E tests
8. Update README with setup instructions

Acceptance criteria:
- docker-compose up starts all services
- Frontend loads at http://localhost:5173
- Backend accessible at http://localhost:8000
- Complete flow works: task → data → train → eval → deploy
- pytest tests/e2e/ passes

When done, merge 'integration' branch to main.
```

---

## Monitoring Progress

### Quick Status Check
```bash
# Run this to see which agents have completed
git branch -a | grep -E "(foundation|frontend|backend-routes|agent-service|training-service|evaluation-service|deployment-service|integration)"
```

### Detailed Status
```bash
# Check test status for each branch
for branch in foundation frontend backend-routes agent-service training-service evaluation-service deployment-service; do
  echo "=== $branch ==="
  git checkout $branch 2>/dev/null
  if [ $? -eq 0 ]; then
    pytest --collect-only 2>/dev/null | grep "test session starts"
  fi
done
```

---

## Coordination Checklist

### Before Starting
- [ ] Clone repository
- [ ] Read docs/parallel-execution-plan.md
- [ ] Verify dependencies (Python, Node, Docker, Modal)

### Phase 0
- [ ] Agent 1 starts on foundation branch
- [ ] Agent 1 completes and merges to main
- [ ] All agents sync with updated main

### Phase 1
- [ ] Launch Agents 2-7 simultaneously
- [ ] Each agent works on isolated branch
- [ ] Agents do NOT merge to main yet
- [ ] Each agent pushes to their branch when done

### Phase 2
- [ ] Verify all Agents 2-7 have pushed their branches
- [ ] Agent 8 starts integration work
- [ ] Agent 8 resolves conflicts and integrates
- [ ] Agent 8 runs E2E tests
- [ ] Agent 8 merges to main

### Final
- [ ] MVP is complete and functional
- [ ] All tests pass
- [ ] docker-compose up works
- [ ] README updated with instructions

---

## Troubleshooting

### Agent 1 blocked
**Problem**: Can't create database models
**Solution**: Reference docs/development-handoff.md for data model specifications

### Agents 2-7 start before Agent 1 done
**Problem**: Missing types/schemas
**Solution**: STOP and wait for foundation branch to merge to main

### Merge conflicts in Phase 2
**Problem**: Multiple agents modified same file
**Solution**: Each agent should own isolated directories per plan

### E2E tests fail
**Problem**: Services not wired together correctly
**Solution**: Check dependency injection in backend/main.py

### Modal deployment fails
**Problem**: API keys not configured
**Solution**: Set up Modal secrets as documented

---

## Success Metrics

### Phase 0 Success
- `git branch` shows `foundation` merged to `main`
- `pytest backend/tests/test_models.py` passes
- `npm run type-check` in frontend/ passes

### Phase 1 Success
- 6 branches pushed: frontend, backend-routes, agent-service, training-service, evaluation-service, deployment-service
- Each branch has passing tests in isolation
- No blocking merge conflicts

### Phase 2 Success
- `docker-compose up` starts without errors
- Frontend accessible at http://localhost:5173
- Backend accessible at http://localhost:8000
- `pytest tests/e2e/` passes

### MVP Complete
- User can create task and see agent analysis
- User can add training examples
- User can trigger training (tested with small dataset)
- User can evaluate model and give feedback
- User can deploy model and call inference API

---

## Timeline

| Phase | Duration | Agents | Can Parallelize? |
|-------|----------|--------|------------------|
| Phase 0 | 2-4h | 1 | No (foundation) |
| Phase 1 | 6-12h | 6 | Yes (fully parallel) |
| Phase 2 | 3-5h | 1 | No (integration) |
| **Total** | **11-21h** | **8** | **Partially** |

**Comparison to sequential**: ~50h → ~20h = **2.5x speedup**

---

## Next Steps After MVP

Once MVP is complete and merged to main:

1. **Deploy to staging**: Set up production environment
2. **User testing**: Get feedback from domain experts
3. **Phase 2 features**: AI data generation, LLM-as-judge, DPO
4. **Performance optimization**: Caching, query optimization
5. **Documentation**: User guides, video tutorials
6. **Community**: Open source release, contributor onboarding

See docs/development-handoff.md for Phase 2 and 3 roadmap.
