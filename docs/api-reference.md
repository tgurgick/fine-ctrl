# API Reference

Base URL: `https://api.finetune-platform.com/v1` (or `http://localhost:8000` for local development)

## Authentication

All API requests require authentication via Bearer token:

```bash
Authorization: Bearer <your_api_key>
```

Get your API key from the dashboard at `/settings/api-keys`.

## Core Endpoints

### Tasks

#### Create Task
```http
POST /api/tasks
```

Create a new fine-tuning task with agent analysis.

**Request Body**:
```json
{
  "name": "Support Ticket Classifier",
  "description": "Classify customer support tickets into categories: bug, feature_request, question, complaint"
}
```

**Response** (201 Created):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Support Ticket Classifier",
  "description": "Classify customer support tickets...",
  "task_type": "classification",
  "config": {
    "recommended_examples": 200,
    "examples_per_category": 50,
    "metrics": ["accuracy", "f1_score", "precision", "recall"],
    "show_confusion_matrix": true,
    "complexity": "simple"
  },
  "created_at": "2024-01-15T10:30:00Z"
}
```

#### Get Task
```http
GET /api/tasks/{task_id}
```

**Response** (200 OK):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Support Ticket Classifier",
  "description": "Classify customer support tickets...",
  "task_type": "classification",
  "config": { ... },
  "dataset_count": 2,
  "model_count": 3,
  "created_at": "2024-01-15T10:30:00Z"
}
```

#### List Tasks
```http
GET /api/tasks?limit=20&offset=0
```

**Query Parameters**:
- `limit` (optional): Number of results (default: 20, max: 100)
- `offset` (optional): Pagination offset (default: 0)
- `task_type` (optional): Filter by task type

**Response** (200 OK):
```json
{
  "items": [ ... ],
  "total": 42,
  "limit": 20,
  "offset": 0
}
```

### Training Examples

#### Add Examples (Bulk)
```http
POST /api/tasks/{task_id}/examples
```

**Request Body**:
```json
{
  "examples": [
    {
      "input": "My app keeps crashing when I click the submit button",
      "output": "bug"
    },
    {
      "input": "Can you add dark mode to the settings?",
      "output": "feature_request"
    }
  ]
}
```

**Response** (201 Created):
```json
{
  "dataset_id": "660e8400-e29b-41d4-a716-446655440000",
  "examples_added": 2,
  "total_examples": 150,
  "stats": {
    "diversity_score": 0.85,
    "category_distribution": {
      "bug": 45,
      "feature_request": 38,
      "question": 35,
      "complaint": 32
    },
    "avg_input_length": 42.5,
    "avg_output_length": 12.3
  }
}
```

#### Generate Examples with AI
```http
POST /api/tasks/{task_id}/generate-examples
```

**Request Body**:
```json
{
  "count": 20,
  "focus_area": "edge_cases_between_bug_and_complaint",
  "style": "realistic"
}
```

**Response** (200 OK):
```json
{
  "examples": [
    {
      "input": "The app is slow and I'm frustrated",
      "output": "complaint",
      "confidence": 0.92,
      "reasoning": "Expresses frustration without specific technical issue"
    },
    ...
  ],
  "total_generated": 20
}
```

#### Get Dataset
```http
GET /api/datasets/{dataset_id}
```

**Response** (200 OK):
```json
{
  "id": "660e8400-e29b-41d4-a716-446655440000",
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "version": 1,
  "examples": [ ... ],
  "stats": { ... },
  "created_at": "2024-01-15T11:00:00Z"
}
```

### Training Jobs

#### Start Training
```http
POST /api/training-jobs
```

**Request Body**:
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "dataset_id": "660e8400-e29b-41d4-a716-446655440000",
  "config": {
    "num_epochs": 3,
    "learning_rate": 0.0002,
    "batch_size": 4
  }
}
```

**Response** (201 Created):
```json
{
  "id": "770e8400-e29b-41d4-a716-446655440000",
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "dataset_id": "660e8400-e29b-41d4-a716-446655440000",
  "status": "queued",
  "config": { ... },
  "created_at": "2024-01-15T12:00:00Z",
  "estimated_duration_minutes": 30
}
```

#### Get Training Job Status
```http
GET /api/training-jobs/{job_id}
```

**Response** (200 OK):
```json
{
  "id": "770e8400-e29b-41d4-a716-446655440000",
  "status": "training",
  "progress": 0.65,
  "current_epoch": 2,
  "total_epochs": 3,
  "metrics": {
    "loss": 0.234,
    "learning_rate": 0.0002,
    "tokens_per_second": 1250
  },
  "started_at": "2024-01-15T12:05:00Z",
  "estimated_completion": "2024-01-15T12:35:00Z"
}
```

**Status values**:
- `queued`: Waiting for GPU
- `training`: Currently training
- `evaluating`: Running post-training evaluation
- `completed`: Successfully finished
- `failed`: Error occurred

#### Cancel Training Job
```http
DELETE /api/training-jobs/{job_id}
```

**Response** (200 OK):
```json
{
  "id": "770e8400-e29b-41d4-a716-446655440000",
  "status": "cancelled"
}
```

### Evaluation

#### Run Evaluation
```http
POST /api/training-jobs/{job_id}/evaluate
```

**Request Body**:
```json
{
  "test_set_size": 100,
  "include_llm_judge": true
}
```

**Response** (200 OK):
```json
{
  "model_version_id": "880e8400-e29b-41d4-a716-446655440000",
  "metrics": {
    "accuracy": 0.94,
    "f1_score": 0.92,
    "precision": 0.93,
    "recall": 0.91,
    "confusion_matrix": {
      "bug": {"bug": 23, "feature_request": 1, "question": 1, "complaint": 0},
      "feature_request": {"bug": 0, "feature_request": 24, "question": 1, "complaint": 0},
      ...
    }
  },
  "llm_judge_scores": {
    "correctness": 4.2,
    "instruction_following": 4.5,
    "consistency": 4.1
  },
  "sample_predictions": [
    {
      "input": "The app won't load my data",
      "expected": "bug",
      "predicted": "bug",
      "confidence": 0.98
    },
    ...
  ]
}
```

#### Submit User Feedback
```http
POST /api/evaluation-feedback
```

**Request Body**:
```json
{
  "model_version_id": "880e8400-e29b-41d4-a716-446655440000",
  "example_input": "The app is really slow on my device",
  "model_output": "complaint",
  "user_rating": "perfect",
  "user_comment": "Correctly identified as complaint not bug"
}
```

**Response** (201 Created):
```json
{
  "id": "990e8400-e29b-41d4-a716-446655440000",
  "created_at": "2024-01-15T13:00:00Z"
}
```

#### Analyze Feedback & Get Recommendations
```http
POST /api/tasks/{task_id}/iterate
```

**Request Body**:
```json
{
  "model_version_id": "880e8400-e29b-41d4-a716-446655440000"
}
```

**Response** (200 OK):
```json
{
  "failure_patterns": [
    {
      "pattern": "Confusion between 'bug' and 'complaint' when user expresses frustration",
      "frequency": 6,
      "example_inputs": [ ... ]
    }
  ],
  "recommendations": [
    {
      "type": "targeted_data_generation",
      "description": "Add 20 examples distinguishing technical issues from complaints",
      "priority": "high"
    },
    {
      "type": "dpo_training",
      "description": "Run preference training on ambiguous cases",
      "priority": "medium"
    }
  ]
}
```

### Deployments

#### Deploy Model
```http
POST /api/deployments
```

**Request Body**:
```json
{
  "model_version_id": "880e8400-e29b-41d4-a716-446655440000",
  "name": "Ticket Classifier v2",
  "is_public": false,
  "keep_warm": true
}
```

**Response** (201 Created):
```json
{
  "id": "aa0e8400-e29b-41d4-a716-446655440000",
  "endpoint_url": "https://model-880e8400.inference.finetune.app",
  "api_key": "ft_sk_...",
  "status": "deploying",
  "is_public": false,
  "share_url": null
}
```

#### Get Deployment Status
```http
GET /api/deployments/{deployment_id}
```

**Response** (200 OK):
```json
{
  "id": "aa0e8400-e29b-41d4-a716-446655440000",
  "status": "active",
  "endpoint_url": "https://model-880e8400.inference.finetune.app",
  "inference_count": 1247,
  "avg_latency_ms": 120,
  "last_request_at": "2024-01-15T14:30:00Z"
}
```

#### Inference (on deployed model)
```http
POST https://model-880e8400.inference.finetune.app/predict
```

**Headers**:
```
Authorization: Bearer ft_sk_...
Content-Type: application/json
```

**Request Body**:
```json
{
  "input": "I want a refund for my subscription",
  "max_tokens": 100,
  "temperature": 0.1
}
```

**Response** (200 OK):
```json
{
  "output": "complaint",
  "confidence": 0.96,
  "latency_ms": 115
}
```

#### Update Deployment
```http
PATCH /api/deployments/{deployment_id}
```

**Request Body**:
```json
{
  "is_public": true,
  "keep_warm": false
}
```

**Response** (200 OK):
```json
{
  "id": "aa0e8400-e29b-41d4-a716-446655440000",
  "is_public": true,
  "share_url": "https://finetune.app/playground/aa0e8400",
  "keep_warm": false
}
```

## Webhooks

Configure webhooks to receive real-time updates.

### Events

- `training.started`
- `training.progress` (every 10%)
- `training.completed`
- `training.failed`
- `deployment.ready`
- `deployment.failed`

### Webhook Payload Example

```json
{
  "event": "training.completed",
  "timestamp": "2024-01-15T12:35:00Z",
  "data": {
    "job_id": "770e8400-e29b-41d4-a716-446655440000",
    "model_version_id": "880e8400-e29b-41d4-a716-446655440000",
    "metrics": { ... }
  }
}
```

## Rate Limits

| Plan       | Requests/minute | Training Jobs/day | Deployments |
|------------|-----------------|-------------------|-------------|
| Free       | 60              | 5                 | 1           |
| Pro        | 600             | 50                | 10          |
| Enterprise | Custom          | Unlimited         | Unlimited   |

Rate limit headers:
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 42
X-RateLimit-Reset: 1642251600
```

## Error Responses

All errors follow this format:

```json
{
  "error": {
    "code": "invalid_request",
    "message": "Missing required field: task_id",
    "details": {
      "field": "task_id",
      "location": "body"
    }
  }
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `invalid_request` | 400 | Malformed request |
| `authentication_failed` | 401 | Invalid API key |
| `forbidden` | 403 | Insufficient permissions |
| `not_found` | 404 | Resource not found |
| `rate_limit_exceeded` | 429 | Too many requests |
| `server_error` | 500 | Internal server error |
| `training_failed` | 500 | Training job failed |

## SDKs

### Python
```python
from finetune import Client

client = Client(api_key="your_api_key")

# Create task
task = client.tasks.create(
    name="Email Classifier",
    description="Classify emails as spam or ham"
)

# Add examples
client.tasks.add_examples(
    task_id=task.id,
    examples=[
        {"input": "Win a free iPhone!", "output": "spam"},
        {"input": "Meeting tomorrow at 2pm", "output": "ham"}
    ]
)

# Train
job = client.training.start(task_id=task.id)

# Wait for completion
model = client.training.wait(job.id)

# Deploy
deployment = client.deployments.create(model_version_id=model.id)

# Inference
result = deployment.predict("Click here to claim your prize")
print(result.output)  # "spam"
```

### TypeScript
```typescript
import { FinetuneClient } from '@finetune/sdk';

const client = new FinetuneClient({ apiKey: 'your_api_key' });

// Create task
const task = await client.tasks.create({
  name: 'Email Classifier',
  description: 'Classify emails as spam or ham'
});

// Add examples
await client.tasks.addExamples(task.id, {
  examples: [
    { input: 'Win a free iPhone!', output: 'spam' },
    { input: 'Meeting tomorrow at 2pm', output: 'ham' }
  ]
});

// Train
const job = await client.training.start({ taskId: task.id });

// Wait for completion
const model = await client.training.wait(job.id);

// Deploy
const deployment = await client.deployments.create({
  modelVersionId: model.id
});

// Inference
const result = await deployment.predict('Click here to claim your prize');
console.log(result.output); // "spam"
```

## Support

- API Status: https://status.finetune-platform.com
- Documentation: https://docs.finetune-platform.com
- Support: support@finetune-platform.com
