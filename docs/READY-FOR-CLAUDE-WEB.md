# Ready for Claude Web - Implementation Guide

**Status**: ✅ Ready to Begin
**Plan Version**: 2.0 (Revised)
**Date**: 2024-01-15

---

## 🎯 Overview

All planning and security architecture complete. Ready to execute parallel development in Claude Web.

**Repository**: https://github.com/tgurgick/fine-ctrl

---

## 📋 Pre-Flight Checklist

Before starting in Claude Web, verify:

### Documentation Complete
- [x] Security architecture defined (`docs/security-architecture.md`)
- [x] Parallel execution plan v2 created (`docs/parallel-execution-plan-v2.md`)
- [x] Agent reviews completed (`docs/AGENT-REVIEW-SUMMARY.md`)
- [x] All critical vulnerabilities addressed in plan
- [x] Work packages updated with security requirements

### Setup Requirements
- [ ] AWS Secrets Manager configured (or plan to use env vars for dev)
- [ ] Modal account created and configured
- [ ] Anthropic API key available
- [ ] GitHub repository cloned in Claude Web

---

## 🚀 Execution Sequence

### Phase 0: Foundation + Security (6-8 hours)

**DO THIS SEQUENTIALLY** - Two agents, one after the other:

#### Step 1: Agent for WP-0 (Foundation)
**Time**: 2.5 hours

**Prompt for Claude Web**:
```
You are implementing WP-0: Foundation work for the Fine-Tune Platform.

Repository: https://github.com/tgurgick/fine-ctrl
Branch: foundation (create from main)

Read these files:
1. docs/parallel-execution-plan-v2.md#wp-0 (your work package)
2. docs/AGENT-REVIEW-SUMMARY.md (critical feedback)

Your tasks:
- Create SQLAlchemy database models (backend/models/)
- Create Pydantic API schemas (backend/schemas/)
- Create service interfaces/ABCs (backend/services/interfaces.py)
- Create FastAPI stub app (backend/main.py)
- Create Alembic migration

IMPORTANT - DO NOT CREATE:
❌ Mock data fixtures (removed as bloat)
❌ Manual TypeScript types (will auto-generate from OpenAPI)

MUST CREATE:
✅ Service ABCs (interfaces.py)
✅ FastAPI stub app with health endpoint
✅ All database models
✅ All Pydantic schemas

Acceptance:
- pytest tests/test_models.py passes
- pytest tests/test_schemas.py passes
- FastAPI starts: uvicorn backend.main:app
- OpenAPI at http://localhost:8000/docs

When complete: Push to 'foundation' branch and merge to main.
```

**Wait for completion** ⏸️ Do not proceed until WP-0 is merged to main.

---

#### Step 2: Agent for WP-0.5 (Security Foundation)
**Time**: 3-4 hours
**Dependencies**: WP-0 must be complete

**Prompt for Claude Web**:
```
You are implementing WP-0.5: Security Foundation for the Fine-Tune Platform.

Repository: https://github.com/tgurgick/fine-ctrl
Branch: security-foundation (create from main after WP-0 merged)

Read these files:
1. docs/security-architecture.md (COMPLETE implementation specs)
2. docs/parallel-execution-plan-v2.md#wp-05 (your work package)
3. docs/AGENT-REVIEW-SUMMARY.md (3 CRITICAL vulnerabilities to fix)

Your tasks:
Implement ALL security controls before any feature development:

1. Authentication Service (backend/services/auth.py)
   - JWT tokens (15min expiry)
   - Refresh tokens with rotation (30 day)
   - Token revocation (Redis blacklist)
   - Login/logout/refresh endpoints

2. Authorization Framework (backend/api/deps.py)
   - get_current_user() dependency
   - require_resource_ownership() helpers
   - require_scopes() decorator
   - PostgreSQL Row-Level Security

3. Secret Management (backend/services/secrets.py)
   - AWS Secrets Manager integration
   - SecretsManager class with caching
   - Log scrubber for secrets

4. API Key Security (backend/services/api_keys.py)
   - Bcrypt hashing (NEVER plain text)
   - Key generation/validation/revocation

5. Input Validation (backend/validators/)
   - XSS/SQL injection protection
   - Prompt injection detection

6. S3 Security (infrastructure/s3_setup.py)
   - Encryption, no public access
   - Bucket policies

7. Security Logging (backend/services/security_logger.py)
   - Auth failures, authz denials

8. Rate Limiting (backend/middleware/rate_limiter.py)
   - Redis-backed, per-endpoint limits

Acceptance:
- All security tests pass
- JWT auth working
- IDOR prevented (resource ownership enforced)
- Secrets from AWS Secrets Manager
- API keys hashed with bcrypt
- Input sanitization blocking attacks
- Rate limiting active

When complete: Push to 'security-foundation' branch and merge to main.

Reference: docs/security-architecture.md has COMPLETE code examples.
```

**Wait for completion** ⏸️ Do not proceed until WP-0.5 is merged to main.

---

### Phase 1: Parallel Development (6-10 hours each)

**ONLY START AFTER** both WP-0 and WP-0.5 are complete and merged to main.

Launch **5 agents simultaneously** in separate Claude Web conversations:

#### Agent 1: Frontend (WP-1)
```
You are implementing WP-1: Frontend for the Fine-Tune Platform.

Repository: https://github.com/tgurgick/fine-ctrl
Branch: frontend (create from main)

Read: docs/parallel-execution-plan-v2.md#wp-1

Tasks:
- Setup Vite + React + TypeScript + Tailwind
- Create all UI components (Button, Table, Modal, etc.)
- Create all pages (Login, Task, Data Editor, Training, Eval, Deploy)
- AUTO-GENERATE TypeScript types from OpenAPI (not manual!)
  Command: npx openapi-typescript http://localhost:8000/openapi.json -o src/types/api.ts
- Integrate authentication (JWT tokens)
- Real API integration (not mocks - backend has stubs)

Acceptance:
- npm run build succeeds
- npm test passes
- All pages render
- Can call backend /health endpoint
- Auth flow working

Push to 'frontend' branch when done.
```

#### Agent 2: Backend Routes (WP-2)
```
You are implementing WP-2: Backend API Routes for the Fine-Tune Platform.

Repository: https://github.com/tgurgick/fine-ctrl
Branch: backend-routes (create from main)

Read: docs/parallel-execution-plan-v2.md#wp-2

Tasks:
- Implement all API endpoints with auth/authz
- Tasks, Datasets, Training, Evaluation, Deployment routes
- Apply authentication to all protected endpoints
- Apply authorization (resource ownership)
- Apply rate limiting
- Input validation with Pydantic
- Use service interfaces from WP-0

Acceptance:
- All endpoints defined
- Auth required on protected routes
- Authorization enforced (IDOR prevented)
- Rate limiting applied
- OpenAPI docs at /docs complete
- pytest tests/api/ passes

Push to 'backend-routes' branch when done.
```

#### Agent 3: Agent Service (WP-3)
```
You are implementing WP-3: Agent Service (Claude integration) for the Fine-Tune Platform.

Repository: https://github.com/tgurgick/fine-ctrl
Branch: agent-service (create from main)

Read: docs/parallel-execution-plan-v2.md#wp-3

Tasks:
- Implement AgentService (backend/services/agent.py)
- Task analysis using Claude API
- Example generation using Claude API
- Failure analysis
- Prompt injection protection (from WP-0.5)
- Cost monitoring and budgets

Acceptance:
- Task analysis returns valid config
- Generated examples match format
- Prompt injection blocked
- Cost tracking working
- pytest tests/services/test_agent.py passes

Push to 'agent-service' branch when done.
```

#### Agent 4: Training Service (WP-4)
```
You are implementing WP-4: Training Service (Modal + QLoRA) for the Fine-Tune Platform.

Repository: https://github.com/tgurgick/fine-ctrl
Branch: training-service (create from main)

Read: docs/parallel-execution-plan-v2.md#wp-4

Tasks:
- Modal training function (training/train.py)
- QLoRA training with Mistral 7B
- TrainingService orchestration (backend/services/training.py)
- Progress tracking with Redis pub/sub
- S3 upload/download with path validation (security)
- Resource limits

Acceptance:
- modal deploy training/train.py succeeds
- Can train on small dataset
- Progress updates working
- Model uploaded to S3
- pytest tests/services/test_training.py passes

Push to 'training-service' branch when done.
```

#### Agent 5: Evaluation Service (WP-5)
```
You are implementing WP-5: Evaluation Service for the Fine-Tune Platform.

Repository: https://github.com/tgurgick/fine-ctrl
Branch: evaluation-service (create from main)

Read: docs/parallel-execution-plan-v2.md#wp-5

IMPORTANT: This is a SINGLE service combining evaluation + feedback.

Tasks:
- Metrics calculator (evaluation/metrics.py)
- EvaluationService (backend/services/evaluation.py)
  - evaluate_model()
  - select_feedback_samples()
  - submit_feedback() [merged from FeedbackService]
  - analyze_feedback() [merged from FeedbackService]
- Sample selection logic

Acceptance:
- Metrics calculated correctly
- Confusion matrix generated
- Feedback collection working
- Feedback analysis identifies patterns
- pytest tests/services/test_evaluation.py passes

Push to 'evaluation-service' branch when done.
```

---

### Phase 2: Integration + Security Testing (12-18 hours)

**ONLY START AFTER** all Phase 1 agents complete.

#### Agent 6: Integration (WP-7)
**Time**: 8-12 hours

```
You are implementing WP-7: Integration for the Fine-Tune Platform.

Repository: https://github.com/tgurgick/fine-ctrl
Branch: integration (create by merging all Phase 1 branches)

Read: docs/parallel-execution-plan-v2.md#wp-7

Tasks:
1. Merge all branches: frontend, backend-routes, agent-service, training-service, evaluation-service
2. Resolve any merge conflicts
3. Wire services into API routes (replace mocks)
4. Setup docker-compose for local dev
5. Test complete flow: task → data → train → eval → deploy
6. Verify all security controls working
7. Fix integration issues (budget 8-12 hours)

Acceptance:
- docker-compose up works
- Complete E2E flow works
- Security verified (auth, authz, secrets, rate limiting)
- Cannot access other users' resources
- E2E tests pass

Push to main when complete.
```

#### Agent 7: Security Testing (WP-8)
**Time**: 4-6 hours
**Dependencies**: WP-7 complete

```
You are implementing WP-8: Security Testing for the Fine-Tune Platform.

Repository: https://github.com/tgurgick/fine-ctrl
Branch: main (after WP-7 merged)

Read: docs/parallel-execution-plan-v2.md#wp-8

Tasks:
1. Run automated scans (OWASP ZAP, Bandit, Snyk, npm audit)
2. Manual security testing:
   - Test auth bypass attempts
   - Test IDOR (cross-user access)
   - Test XSS/SQL injection
   - Test prompt injection
   - Verify API keys hashed
   - Verify secrets not in logs
3. Complete security checklist (in WP-8 section)
4. Generate security report

Acceptance:
- All scans pass or findings addressed
- Security checklist 100% complete
- No CRITICAL or HIGH vulnerabilities
- Security sign-off approved

Create reports/security-sign-off.md when complete.
```

---

## 📊 Progress Tracking

### Simple Status Check
```bash
git branch -a | grep -E "(foundation|security|frontend|backend|agent|training|evaluation|integration)"
```

### Current Phase
- [ ] Phase 0: Foundation + Security (Sequential)
  - [ ] WP-0: Foundation (2.5h)
  - [ ] WP-0.5: Security (3-4h)
- [ ] Phase 1: Parallel Development (6-10h each)
  - [ ] WP-1: Frontend
  - [ ] WP-2: Backend Routes
  - [ ] WP-3: Agent Service
  - [ ] WP-4: Training Service
  - [ ] WP-5: Evaluation Service
- [ ] Phase 2: Integration + Security (12-18h)
  - [ ] WP-7: Integration (8-12h)
  - [ ] WP-8: Security Testing (4-6h)

---

## ⚠️ Critical Reminders

### Before Phase 1
- ✅ WP-0 MUST complete first
- ✅ WP-0.5 MUST complete after WP-0
- ✅ Both MUST merge to main before Phase 1 starts
- ✅ All Phase 1 agents branch from main (with foundation + security)

### During Phase 1
- 👥 Run all 5 agents in parallel (separate conversations)
- ⏸️ Each agent works independently
- 🚫 Do NOT merge Phase 1 branches until ALL complete
- 🔒 Security controls already in place from WP-0.5

### Before Phase 2
- ✅ All Phase 1 agents must complete
- ✅ All Phase 1 branches pushed
- ✅ Ready to merge and integrate

### During Phase 2
- 🔨 Expect integration challenges (budget 8-12h)
- 🔍 Security testing mandatory before production
- ✅ Complete security checklist
- 📝 Generate security sign-off

---

## 📚 Key Reference Documents

| Document | Purpose | When to Read |
|----------|---------|--------------|
| [security-architecture.md](./security-architecture.md) | Complete security specs | WP-0.5 implementation |
| [parallel-execution-plan-v2.md](./parallel-execution-plan-v2.md) | Detailed work packages | All agents |
| [AGENT-REVIEW-SUMMARY.md](./AGENT-REVIEW-SUMMARY.md) | Critical issues & changes | Before starting |
| [development-handoff.md](./development-handoff.md) | Technical specification | Reference as needed |
| [api-reference.md](./api-reference.md) | API endpoints | WP-2 implementation |

---

## ✅ MVP Completion Criteria

You're done when:
- [ ] User can login/logout (auth working)
- [ ] User can create task → agent analyzes it
- [ ] User can add training examples manually
- [ ] User can train model (small dataset, end-to-end)
- [ ] User can evaluate model and give feedback
- [ ] User can deploy model (simplified MVP version)
- [ ] Security: Cannot access other users' resources
- [ ] Security: All 3 CRITICAL vulnerabilities fixed
- [ ] Security: No HIGH vulnerabilities remaining
- [ ] All tests passing (unit + integration + E2E + security)
- [ ] docker-compose up works locally

---

## 🎓 Timeline Summary

| Phase | Duration | Agents | Type |
|-------|----------|--------|------|
| Phase 0 | 6-8h | 2 | Sequential |
| Phase 1 | 6-10h | 5 | Parallel |
| Phase 2 | 12-18h | 2 | Sequential |
| **Total** | **28-40h** | | **1.75-2x faster** |

Compare to sequential: 70-80 hours (~2 weeks)

---

## 🚦 Ready to Start?

1. ✅ Read this document
2. ✅ Review [AGENT-REVIEW-SUMMARY.md](./AGENT-REVIEW-SUMMARY.md)
3. ✅ Ensure GitHub repo accessible in Claude Web
4. 🚀 Start with WP-0 (Foundation) agent
5. ⏸️ Wait for WP-0 to complete
6. 🚀 Continue with WP-0.5 (Security) agent
7. ⏸️ Wait for WP-0.5 to complete
8. 🚀🚀🚀🚀🚀 Launch all 5 Phase 1 agents in parallel
9. ⏸️ Wait for Phase 1 to complete
10. 🚀 Run WP-7 (Integration) agent
11. 🚀 Run WP-8 (Security Testing) agent
12. 🎉 MVP Complete!

---

**Last Updated**: 2024-01-15
**Status**: Ready for Claude Web Execution
**Next Action**: Begin with WP-0 in Claude Web
