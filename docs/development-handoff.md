# Fine-Tune Platform - Development Handoff

## Project Overview

An open-source web application that makes fine-tuning open-source LLMs accessible to domain experts without ML expertise. The core innovation is focusing on **data generation as the primary UX**, with all training complexity abstracted away.

## Core Product Principles

1. **Data generation is the bottleneck** - Users should spend time creating quality examples, not configuring models
2. **Agent-driven configuration** - Claude analyzes the task and sets everything up automatically
3. **Iterative improvement loops** - Built-in feedback collection leads to targeted data generation or RLHF
4. **One-click everything** - Training, evaluation, deployment should require minimal user decisions

## Key Differentiators

- **Not** another training UI with exposed hyperparameters
- **Not** a model marketplace
- **IS** a data generation tool that happens to train models
- **IS** focused on the complete loop: describe → generate data → train → evaluate → iterate → deploy

## Technical Stack Decisions

### Training Infrastructure
- **Method**: QLoRA (4-bit quantization + LoRA adapters)
- **Why**: Best cost/quality tradeoff, runs on cheaper GPUs (~$0.50 per job)
- **Base Model**: Mistral 7B Instruct v0.3 (Apache 2.0 license)
- **Framework**: HuggingFace (transformers + PEFT + TRL)
- **Compute**: Modal for serverless GPU execution

### Cost Economics
- Training job (1K examples, 3 epochs): ~30 min on A10G = $0.55
- Charge users $2-5 per job = 3-8x margin
- 100 users × 10 jobs/month = $200-300 compute cost

### Architecture Components

**Frontend** (React + TypeScript)
- Task description interface
- Data generation/curation UI (the star of the show)
- Training progress dashboard
- Evaluation playground with thumbs up/down
- Model deployment and sharing

**Backend** (Python FastAPI)
- REST API for job management
- PostgreSQL for metadata (users, jobs, datasets, models)
- S3 for artifacts (datasets, model weights, logs)
- Redis for job queue and real-time updates

**Training Service** (Modal)
- Serverless functions that spin up on-demand
- QLoRA training script using TRL's SFTTrainer
- Automatic evaluation on holdout set
- Pushes weights to S3/HuggingFace Hub

**Agent Service** (Claude API)
- Task analysis and configuration
- Training data generation assistance
- Post-training failure analysis
- Recommendation engine for next steps

**Inference Service** (vLLM on Modal)
- Fast inference for deployed models
- Keep-warm instances for low latency
- Usage tracking and billing

## Critical User Flows

### Flow 1: Initial Training (Happy Path)

1. **User describes task**: "Classify support tickets into 4 categories"
2. **Agent analyzes**:
   - Detects classification task
   - Recommends 50 examples per category (200 total)
   - Suggests accuracy + F1 + confusion matrix
   - Sets up training config automatically
3. **User generates data**:
   - Can type examples manually
   - Can upload existing data (CSV, JSON)
   - Can use Claude to generate synthetic examples
   - System checks for diversity and balance
4. **Training kicks off**:
   - User clicks "Train" (no other decisions needed)
   - 30 min later, gets notification
5. **Evaluation**:
   - User shown 10 test examples
   - Side-by-side: Base model vs Fine-tuned
   - Thumbs up/down on each
6. **Decision point**:
   - If 8+/10 good → Deploy
   - If <8/10 → Iterate

### Flow 2: Iterative Improvement

After initial training with mediocre results:

1. **Agent analyzes feedback**:
   - "Your model struggles with ambiguous requests between 'complaint' and 'refund'"
   - "Recommend adding 20 examples of edge cases"
2. **User chooses path**:
   - **Option A**: Generate more targeted training data
   - **Option B**: Run RLHF/DPO preference session
3. **If Option A** (Targeted Data):
   - Agent generates 20 examples focusing on weak areas
   - User reviews/edits each
   - Retrain with original + new data
4. **If Option B** (RLHF):
   - Show user 10 preference pairs
   - "Which output is better?"
   - Run DPO training (simpler than full RLHF)
   - Creates v2 model
5. **Version comparison**:
   - A/B test on same 10 examples
   - Track improvement over versions

### Flow 3: Deployment & Sharing

1. **One-click deploy**:
   - Spins up vLLM inference endpoint on Modal
   - Returns API URL + key
2. **Sharing options**:
   - Public playground (anyone can test)
   - Team access (invite colleagues)
   - Export weights (self-host)
   - Embed widget (for websites)
3. **Analytics**:
   - Request volume
   - Latency metrics
   - User ratings on outputs

## Key Technical Implementations

### 1. Agent Task Analyzer
```python
# Prompt structure for Claude
analyze_task_prompt = f"""
Analyze this fine-tuning task:

Description: {user_description}
Sample data (if any): {sample_data}

Determine:
1. Task type: [classification, extraction, generation_creative, generation_factual, transformation, conversation]
2. Complexity: [simple, medium, complex]
3. Structured output: [yes/no]
4. Recommended metrics
5. Data requirements (min/recommended examples)
6. Training configuration
7. Success criteria

Output as JSON with reasoning for each decision.
"""
```

### 2. Task-Specific Metric Selection
```python
METRIC_PRESETS = {
    "classification": {
        "automatic": ["accuracy", "precision", "recall", "f1_score"],
        "requires_judge": False,
        "show_confusion_matrix": True
    },
    "extraction": {
        "automatic": ["exact_match", "partial_match", "parse_success_rate"],
        "requires_judge": True,
        "structured_validation": True
    },
    "generation_creative": {
        "automatic": ["perplexity", "length_distribution"],
        "requires_judge": True,
        "judge_criteria": ["creativity", "coherence", "instruction_following"]
    },
    # ... etc
}
```

### 3. QLoRA Training Configuration
```python
# Default config that works for most use cases
default_config = {
    "base_model": "mistralai/Mistral-7B-Instruct-v0.3",
    "load_in_4bit": True,  # QLoRA
    "lora_r": 16,  # Rank
    "lora_alpha": 32,
    "lora_dropout": 0.05,
    "target_modules": ["q_proj", "v_proj", "k_proj", "o_proj"],
    "num_train_epochs": 3,
    "per_device_train_batch_size": 4,
    "gradient_accumulation_steps": 4,
    "learning_rate": 2e-4,
    "bf16": True,
    "gradient_checkpointing": True,
}
```

### 4. LLM-as-Judge Evaluation
```python
# For non-classification tasks
judge_prompt = f"""
Evaluate this model output:

Input: {input_text}
Expected: {expected_output}
Model Output: {model_output}

Rate 1-5 on:
- Correctness: Does it answer correctly?
- Completeness: Is it thorough enough?
- Instruction Following: Does it follow the format/style requested?

Provide score and brief reasoning.
"""

# Cost: ~$0.001 per eval with Claude Haiku
# Run on 50-100 examples = $0.05-0.10 per training job
```

### 5. DPO for Preference Learning
```python
from trl import DPOTrainer

# After collecting user preferences on output pairs
def preference_training(model, preference_data):
    """
    Direct Preference Optimization - simpler than full RLHF
    No reward model needed
    """
    dpo_dataset = format_preferences(preference_data)
    # Format: [{input, chosen_output, rejected_output}, ...]

    trainer = DPOTrainer(
        model=model,
        train_dataset=dpo_dataset,
        beta=0.1,  # Regularization
        max_length=2048,
    )

    return trainer.train()
```

## Data Models

### Core Entities
```python
class User:
    id: UUID
    email: str
    plan: str  # free, pro, enterprise
    created_at: datetime

class Task:
    id: UUID
    user_id: UUID
    name: str
    description: str
    task_type: str  # classification, extraction, etc.
    config: dict  # Agent-generated config
    created_at: datetime

class Dataset:
    id: UUID
    task_id: UUID
    examples: List[TrainingExample]
    stats: dict  # Diversity, balance, etc.
    version: int

class TrainingExample:
    input: str
    output: str
    metadata: dict  # Source, quality score, etc.

class TrainingJob:
    id: UUID
    task_id: UUID
    dataset_id: UUID
    status: str  # queued, training, completed, failed
    config: dict  # Training hyperparameters
    metrics: dict  # Loss, perplexity, etc.
    started_at: datetime
    completed_at: datetime

class ModelVersion:
    id: UUID
    task_id: UUID
    training_job_id: UUID
    version: int
    weights_path: str  # S3/HF Hub
    eval_results: dict
    user_rating: float  # From feedback
    deployment_status: str

class EvaluationFeedback:
    id: UUID
    model_version_id: UUID
    example_input: str
    model_output: str
    user_rating: str  # perfect, okay, wrong
    user_comment: str
    created_at: datetime

class Deployment:
    id: UUID
    model_version_id: UUID
    endpoint_url: str
    status: str  # active, paused
    inference_count: int
    is_public: bool
    share_token: str
```

## API Endpoints
```
POST /api/tasks
  → Create new task, trigger agent analysis

POST /api/tasks/{id}/examples
  → Add training examples

POST /api/tasks/{id}/generate-examples
  → Use Claude to generate synthetic examples

POST /api/training-jobs
  → Start training

GET /api/training-jobs/{id}
  → Get training progress/status

POST /api/training-jobs/{id}/evaluate
  → Run evaluation on test set

POST /api/evaluation-feedback
  → Submit user feedback on outputs

POST /api/tasks/{id}/iterate
  → Analyze feedback, recommend next steps

POST /api/deployments
  → Deploy model to inference endpoint

GET /api/models/{id}/playground
  → Public testing interface
```

## Environment Setup
```bash
# Backend dependencies
pip install \
  fastapi \
  uvicorn \
  sqlalchemy \
  psycopg2-binary \
  boto3 \
  anthropic \
  transformers \
  peft \
  trl \
  bitsandbytes \
  modal

# Modal setup
modal token set --token-id xxx --token-secret yyy

# Database
docker run -p 5432:5432 -e POSTGRES_PASSWORD=xxx postgres

# S3 (or use MinIO locally)
AWS_ACCESS_KEY_ID=xxx
AWS_SECRET_ACCESS_KEY=yyy
```

## Key Configuration
```python
# config.py
class Settings:
    # Model defaults
    DEFAULT_BASE_MODEL = "mistralai/Mistral-7B-Instruct-v0.3"
    LORA_RANK = 16
    LEARNING_RATE = 2e-4

    # Compute
    MODAL_GPU_TYPE = "A10G"  # 24GB, ~$1.10/hr
    TRAINING_TIMEOUT = 3600  # 1 hour max

    # Costs
    COST_PER_TRAINING_JOB = 2.00  # What to charge users

    # Agent
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    AGENT_MODEL = "claude-sonnet-4-20250514"

    # Storage
    DATABASE_URL = os.getenv("DATABASE_URL")
    S3_BUCKET = os.getenv("S3_BUCKET")

    # Features
    ENABLE_RLHF = True
    ENABLE_LLM_JUDGE = True
    MAX_FREE_TRAINING_JOBS = 5
```

## MVP Feature Priority

### Must Have (Phase 1)
1. Task description + agent analysis
2. Manual data input (paste examples)
3. QLoRA training on Mistral 7B
4. Basic evaluation (loss, perplexity)
5. 10-example feedback collection
6. Simple API deployment

### Should Have (Phase 2)
7. Synthetic data generation with Claude
8. LLM-as-judge evaluation
9. Failure pattern analysis
10. Targeted data generation recommendations
11. DPO preference training
12. Version comparison

### Nice to Have (Phase 3)
13. Public playground sharing
14. Team collaboration
15. Usage analytics
16. CSV/JSON data import
17. HuggingFace Hub integration
18. Custom evaluation metrics

## Open Questions to Resolve

1. **Pricing model**: Per-job? Subscription? Freemium tiers?
2. **Data privacy**: How to handle sensitive training data?
3. **Model limits**: Support 13B/70B models or stick to 7B?
4. **Inference pricing**: Charge for API calls or include in training cost?
5. **Template marketplace**: Should users be able to share task templates?
6. **Evaluation budget**: How many LLM-as-judge calls per job?

## Success Metrics

### Technical
- Training job success rate >95%
- Average job completion time <30 min
- Model quality improvement vs base >20% on user tasks

### Product
- Time from signup to first trained model <60 min
- User satisfaction rating >4/5 on feedback
- % of models that get deployed >50%
- Users who iterate (train v2+) >40%

### Business (if applicable)
- User retention (train 2+ models)
- Upgrade to paid plan conversion
- Community-contributed templates

## Risk Mitigation

1. **GPU availability**: Use Modal's auto-scaling, fallback to Lambda Labs
2. **Training failures**: Comprehensive error handling, automatic retries
3. **Bad training data**: Validation checks, diversity warnings
4. **Cost overruns**: Per-user quotas, job time limits
5. **Model quality**: Set baseline metrics before allowing deployment

## Next Steps

1. Set up basic FastAPI backend with task creation
2. Implement agent task analyzer
3. Build data input interface (React)
4. Create Modal training function
5. Test end-to-end: describe → data → train → evaluate
6. Iterate on UX based on testing

---

## Additional Context

- This is a **personal open-source project** aimed at democratizing fine-tuning
- Primary goal: Make domain expertise capturable without ML knowledge
- Inspiration: "Retool for LLM fine-tuning"
- Differentiator: Focus on data generation, not model configuration
