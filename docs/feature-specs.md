# Feature Specifications

Detailed specifications for core features of the Fine-Tune Platform.

## Phase 1: MVP Features

### Feature 1: Task Creation & Agent Analysis

**User Story**: As a domain expert, I want to describe my task in plain English and have the system configure everything automatically, so I don't need ML expertise.

**Acceptance Criteria**:
- [ ] User can input task name and description in a form
- [ ] Agent analyzes task within 5 seconds
- [ ] System detects task type with >90% accuracy
- [ ] Recommendations are displayed clearly with reasoning
- [ ] User can accept or modify agent suggestions

**UI Components**:
1. **Task Description Form**
   - Text input for name (max 100 chars)
   - Textarea for description (max 2000 chars)
   - "Analyze Task" button
   - Loading state during analysis

2. **Analysis Results Panel**
   - Task type badge (classification, extraction, etc.)
   - Complexity indicator (simple/medium/complex)
   - Recommended metrics with explanations
   - Data requirements with justification
   - Training config preview (collapsible)

**Agent Prompt Template**:
```
You are analyzing a fine-tuning task. The user has provided:

Task Name: {name}
Description: {description}

Analyze this task and determine:

1. TASK TYPE - Choose one:
   - classification: Assign inputs to predefined categories
   - extraction: Pull specific information from text
   - generation_creative: Create original content
   - generation_factual: Generate based on facts
   - transformation: Convert format/style
   - conversation: Multi-turn dialogue

2. COMPLEXITY:
   - simple: Binary or few clear categories
   - medium: Multiple categories or moderate nuance
   - complex: High ambiguity or specialized domain

3. RECOMMENDED METRICS:
   List metrics appropriate for this task type with reasoning

4. DATA REQUIREMENTS:
   - Minimum examples needed
   - Recommended examples for good results
   - How many per category (if applicable)

5. TRAINING CONFIGURATION:
   Suggest epochs, batch size, learning rate with reasoning

6. SUCCESS CRITERIA:
   What metrics indicate the model is production-ready?

Output as JSON following this schema:
{
  "task_type": "...",
  "complexity": "...",
  "metrics": [...],
  "data_requirements": {...},
  "training_config": {...},
  "success_criteria": {...},
  "reasoning": "..."
}
```

**Edge Cases**:
- Ambiguous task description → Ask clarifying questions
- Multiple possible task types → Show confidence scores for each
- Agent API failure → Fallback to sensible defaults with warning

---

### Feature 2: Manual Data Input

**User Story**: As a user, I want to input training examples through a spreadsheet-like interface, so I can quickly add my existing data.

**Acceptance Criteria**:
- [ ] Table view with input/output columns
- [ ] Add row individually or bulk paste
- [ ] Real-time validation of format
- [ ] Diversity and balance metrics update live
- [ ] Can edit and delete examples
- [ ] Auto-save to prevent data loss

**UI Components**:
1. **Data Table**
   - Columns: Input | Output | Actions
   - Inline editing (click to edit)
   - Row numbers
   - Sortable by any column
   - Filterable (search inputs/outputs)

2. **Bulk Actions Toolbar**
   - "Add Row" button
   - "Bulk Paste" button (opens modal)
   - "Import CSV/JSON" button
   - "Export" dropdown (CSV, JSON, JSONL)
   - Delete selected (multi-select with checkboxes)

3. **Stats Sidebar** (updates in real-time)
   - Total examples: 142
   - Category distribution (if classification)
   - Diversity score (0-1)
   - Average lengths
   - Quality warnings (duplicates, imbalance)

**Bulk Paste Modal**:
```
┌─────────────────────────────────────┐
│ Paste Examples                      │
├─────────────────────────────────────┤
│ Format: INPUT [tab] OUTPUT          │
│                                     │
│ ┌─────────────────────────────────┐ │
│ │ What is your name? [tab] name   │ │
│ │ How old are you? [tab] age      │ │
│ │ ...                             │ │
│ └─────────────────────────────────┘ │
│                                     │
│ Detected: 25 examples               │
│                                     │
│ [Cancel]  [Add Examples]            │
└─────────────────────────────────────┘
```

**Validation Rules**:
- Input cannot be empty
- Output cannot be empty
- For classification: Output must match defined categories
- For extraction: Output must be valid JSON (if structured)
- Warn on duplicates
- Warn if category imbalance >2x

**Edge Cases**:
- Pasted data with wrong delimiter → Detect and auto-fix or prompt
- HTML/rich text pasted → Strip formatting
- Very long inputs (>10k chars) → Warn about truncation
- Special characters → Ensure proper escaping

---

### Feature 3: QLoRA Training

**User Story**: As a user, I want to click "Train" and have my model ready in 30 minutes, without thinking about GPUs or hyperparameters.

**Acceptance Criteria**:
- [ ] One-click training start
- [ ] Real-time progress updates (every 5-10 seconds)
- [ ] Live metrics display (loss, perplexity, tokens/sec)
- [ ] Training completes in <40 min for <1K examples
- [ ] Success rate >95%
- [ ] Clear error messages if failure

**Training Pipeline**:

1. **Pre-flight Checks** (5 seconds)
   - Validate dataset format
   - Check example count meets minimum
   - Verify user quota
   - Estimate cost and duration

2. **Dataset Preparation** (10 seconds)
   - Format as instruction tuning examples
   - Create train/test split (90/10)
   - Upload to S3
   - Generate dataset card

3. **Queue Job** (instant)
   - Create DB record
   - Push to Redis queue
   - Return job ID to client

4. **Modal Training** (20-35 min for 1K examples)
   - Spin up A10G GPU
   - Load Mistral 7B in 4-bit
   - Apply LoRA adapters
   - Train for 3 epochs
   - Publish progress every 10 steps
   - Save checkpoints every epoch

5. **Post-Training** (2-3 min)
   - Upload final model to S3
   - Run quick eval on test set
   - Generate sample predictions
   - Update DB with results

**Progress UI**:
```
┌────────────────────────────────────────────┐
│ Training: Ticket Classifier                │
├────────────────────────────────────────────┤
│ Status: Training Epoch 2/3                 │
│                                            │
│ Progress: [████████░░░] 65%               │
│                                            │
│ Time Elapsed: 18m 32s                      │
│ Estimated Remaining: 10m 15s               │
│                                            │
│ Metrics:                                   │
│   Loss: 0.234 ↓                           │
│   Learning Rate: 0.0002                    │
│   Tokens/sec: 1,250                        │
│                                            │
│ [View Logs] [Cancel Training]              │
└────────────────────────────────────────────┘
```

**Modal Function Signature**:
```python
@app.function(
    image=Image.from_registry("nvidia/cuda:12.1.0-base-ubuntu22.04")
        .pip_install("transformers", "peft", "trl", "bitsandbytes"),
    gpu="A10G",
    timeout=3600,
    secrets=[Secret.from_name("huggingface"), Secret.from_name("aws-s3")]
)
def train_model(
    dataset_s3_path: str,
    output_s3_path: str,
    config: TrainingConfig,
    progress_callback_url: str
) -> TrainingResult:
    """
    Run QLoRA fine-tuning on Mistral 7B.

    Posts progress updates to progress_callback_url every N steps.
    Returns final metrics and model path.
    """
    # Implementation in training/train.py
```

**Error Handling**:
- GPU unavailable → Retry 3 times with exponential backoff
- Out of memory → Reduce batch size and retry
- Dataset too large → Suggest sampling or contact support
- Training diverges (loss spikes) → Stop and notify user

---

### Feature 4: Basic Evaluation

**User Story**: As a user, I want to see how my model performs compared to the base model, so I can decide whether to deploy or iterate.

**Acceptance Criteria**:
- [ ] Automatic eval on 10% held-out test set
- [ ] Display accuracy, F1, precision, recall (for classification)
- [ ] Show confusion matrix (for classification)
- [ ] Display sample predictions (10 examples)
- [ ] Side-by-side comparison with base model
- [ ] Clear recommendation (deploy vs iterate)

**Evaluation Flow**:

1. **Automatic Metrics** (30 seconds)
   - Run inference on test set
   - Compute task-specific metrics
   - Compare to base model performance
   - Generate confusion matrix

2. **Sample Selection** (10 seconds)
   - Pick 10 diverse examples:
     - 3 from most confident correct
     - 3 from least confident correct
     - 3 from incorrect predictions
     - 1 random
   - Ensure category balance

3. **Results Display**
   ```
   ┌──────────────────────────────────────────────────┐
   │ Evaluation Results                               │
   ├──────────────────────────────────────────────────┤
   │                                                  │
   │ Overall Performance:                             │
   │   Accuracy:  94.2% (Base: 72.1%) +22.1% ✓       │
   │   F1 Score:  0.92  (Base: 0.68)  +0.24  ✓       │
   │                                                  │
   │ Per-Category:                                    │
   │   Bug:              96% (48/50)                  │
   │   Feature Request:  94% (47/50)                  │
   │   Question:         92% (46/50)                  │
   │   Complaint:        95% (47/50)                  │
   │                                                  │
   │ Confusion Matrix:                                │
   │                 Predicted                        │
   │           Bug  Feature Question Complaint        │
   │   Bug      48    1       1        0             │
   │   Feature   1   47       2        0             │
   │   Question  2    1      46        1             │
   │   Complaint 0    0       1       47             │
   │                                                  │
   │ Recommendation: ✅ Ready to deploy!              │
   │ Your model significantly outperforms the base.   │
   │                                                  │
   │ [Deploy Model] [Review Examples] [Iterate]       │
   └──────────────────────────────────────────────────┘
   ```

4. **Sample Predictions View**
   ```
   Example 1/10                        [Prev] [Next]

   Input:
   "The app crashes every time I try to export"

   Expected Output: bug

   ┌─────────────────┬─────────────────────┐
   │ Base Model      │ Fine-Tuned Model    │
   ├─────────────────┼─────────────────────┤
   │ question        │ bug                 │
   │ Confidence: 62% │ Confidence: 98%     │
   │ ❌ Incorrect    │ ✅ Correct          │
   └─────────────────┴─────────────────────┘

   Your feedback:
   👍 Perfect  😐 Okay  👎 Wrong

   Comment (optional):
   [                                        ]

   [Submit Feedback]
   ```

**Decision Logic**:
```python
def recommend_action(metrics: dict, task_complexity: str) -> str:
    accuracy = metrics['accuracy']
    improvement = metrics['accuracy'] - metrics['base_accuracy']

    thresholds = {
        'simple': (0.95, 0.15),    # 95% accuracy, +15% improvement
        'medium': (0.90, 0.20),    # 90% accuracy, +20% improvement
        'complex': (0.85, 0.25)    # 85% accuracy, +25% improvement
    }

    target_acc, target_improvement = thresholds[task_complexity]

    if accuracy >= target_acc and improvement >= target_improvement:
        return "deploy"  # Green light
    elif improvement >= target_improvement * 0.5:
        return "iterate"  # Promising but needs work
    else:
        return "reevaluate_data"  # Fundamental issue
```

---

### Feature 5: User Feedback Collection

**User Story**: As a user, I want to rate model outputs so the system can identify failure patterns and suggest improvements.

**Acceptance Criteria**:
- [ ] Thumbs up/down rating on 10 examples
- [ ] Optional comment per example
- [ ] Feedback stored in DB
- [ ] Can provide feedback anytime (not just post-training)
- [ ] Feedback influences iteration recommendations

**Feedback Interface**:

Rating Options:
- 👍 **Perfect**: Output is exactly right
- 😐 **Okay**: Mostly right but could be better
- 👎 **Wrong**: Incorrect output

Comments encourage users to explain WHY, especially for "Okay" and "Wrong".

**Data Storage**:
```python
class EvaluationFeedback(Base):
    id: UUID
    model_version_id: UUID
    example_input: str
    expected_output: str
    model_output: str
    user_rating: str  # perfect, okay, wrong
    user_comment: Optional[str]
    created_at: datetime

    # Computed fields for analysis
    is_correct: bool  # Does model_output match expected?
    confidence_score: float  # From model
    failure_category: Optional[str]  # Set by agent analysis
```

**Feedback Analysis** (happens after 10+ ratings):
1. Group by rating (perfect/okay/wrong)
2. For "okay" and "wrong", use Claude to analyze patterns:
   ```
   Analyze these feedback instances where users rated the model as "okay" or "wrong":

   [List of examples with input, expected, model output, user comment]

   Identify:
   1. Common failure patterns (what types of inputs are problematic?)
   2. Recurring themes in errors
   3. Specific categories/edge cases that need work

   Output structured analysis with examples.
   ```

3. Generate recommendations:
   - **Targeted data generation**: "Add 20 examples of X"
   - **DPO training**: "Collect preferences on ambiguous cases"
   - **Prompt engineering**: "Adjust system prompt to emphasize Y"
   - **Category refinement**: "Consider splitting category Z"

---

### Feature 6: Simple API Deployment

**User Story**: As a user, I want to deploy my model with one click and get an API endpoint I can call from my application.

**Acceptance Criteria**:
- [ ] One-click deploy from evaluation screen
- [ ] Deployment completes in <5 minutes
- [ ] Returns API endpoint URL and key
- [ ] Includes usage instructions and code examples
- [ ] Can test in playground before production use

**Deployment Flow**:

1. **User Clicks Deploy**
   ```
   ┌─────────────────────────────────────┐
   │ Deploy Model                        │
   ├─────────────────────────────────────┤
   │ Model: Ticket Classifier v1         │
   │ Version: 1                          │
   │                                     │
   │ Deployment Name:                    │
   │ [Ticket Classifier API          ]   │
   │                                     │
   │ Visibility:                         │
   │ ◉ Private  ○ Public                 │
   │                                     │
   │ Performance:                        │
   │ ○ Cost-optimized (cold start)       │
   │ ◉ Balanced (1 warm instance)        │
   │ ○ Low-latency (3 warm instances)    │
   │                                     │
   │ Estimated cost: $0.20/day           │
   │                                     │
   │ [Cancel]  [Deploy]                  │
   └─────────────────────────────────────┘
   ```

2. **Modal Deploys vLLM Endpoint** (3-5 min)
   - Spin up Modal web endpoint
   - Load model with vLLM (optimized inference)
   - Configure keep-warm based on user selection
   - Generate API key
   - Return endpoint URL

3. **Deployment Success Screen**
   ```
   ┌─────────────────────────────────────────────────┐
   │ ✅ Deployment Successful                        │
   ├─────────────────────────────────────────────────┤
   │ Your model is live!                             │
   │                                                 │
   │ API Endpoint:                                   │
   │ https://model-abc123.inference.finetune.app     │
   │                                                 │
   │ API Key:                                        │
   │ ft_sk_xyz789... [Copy] [Show Full]             │
   │                                                 │
   │ Quick Start:                                    │
   │                                                 │
   │ curl -X POST \                                  │
   │   https://model-abc123.inference.finetune.app \│
   │   -H "Authorization: Bearer ft_sk_xyz789..." \ │
   │   -d '{"input": "example text"}'                │
   │                                                 │
   │ [Test in Playground] [View Documentation]       │
   │ [Share] [Settings]                              │
   └─────────────────────────────────────────────────┘
   ```

4. **Playground Testing**
   - Web UI to test the API
   - Input box
   - Response display with latency
   - Example requests
   - cURL, Python, JavaScript code snippets

**Inference Endpoint Implementation**:
```python
@app.function(
    image=inference_image,
    gpu="T4",
    keep_warm=1,  # Configurable
    allow_concurrent_inputs=10
)
@modal.web_endpoint(method="POST")
async def inference(request: dict):
    """
    Inference endpoint for deployed model.

    Request format:
    {
        "input": "text to classify",
        "max_tokens": 100,  # optional
        "temperature": 0.1  # optional
    }
    """
    # Load model (cached after first call)
    model = load_model_cached()

    # Run inference
    output = model.generate(
        request["input"],
        max_tokens=request.get("max_tokens", 100),
        temperature=request.get("temperature", 0.1)
    )

    # Log usage
    log_inference_request(model_id, request)

    return {
        "output": output,
        "model_version": model.version,
        "latency_ms": elapsed_time
    }
```

---

## Phase 2: Advanced Features

### Feature 7: AI-Assisted Data Generation

**User Story**: As a user, I want Claude to generate realistic training examples based on my task description, so I can quickly build a diverse dataset.

**Key Innovation**: Agent generates examples, but user MUST review and edit each one. No blindly accepting AI-generated data.

**Workflow**:
1. User clicks "Generate Examples"
2. Specifies:
   - How many (10-100)
   - Focus area (general, specific category, edge cases)
   - Style (realistic, diverse, edge cases)
3. Agent generates batch
4. User reviews in table view:
   - ✅ Accept as-is
   - ✏️ Edit before accepting
   - ❌ Reject
5. Only accepted examples added to dataset

**Generation Prompt**:
```
Generate {count} realistic training examples for this task:

Task: {task_description}
Type: {task_type}
Existing examples: {sample_existing_examples}

Focus: {focus_area}
Style: {style}

Requirements:
1. Examples should be DIVERSE (different scenarios, phrasings, edge cases)
2. Outputs should match this format: {output_format}
3. Maintain consistent quality across all examples
4. {additional_constraints}

Output as JSON array:
[
  {
    "input": "...",
    "output": "...",
    "reasoning": "Why this example is useful"
  },
  ...
]
```

---

### Feature 8: LLM-as-Judge Evaluation

**User Story**: For tasks without clear right/wrong answers (like creative writing), I want an AI judge to evaluate quality.

**When to Use**:
- Creative generation tasks
- Summarization
- Rewriting/transformation
- Conversation

**Evaluation Criteria** (task-dependent):
- Correctness
- Completeness
- Instruction following
- Creativity (for creative tasks)
- Coherence
- Tone/style match

**Implementation**:
```python
async def llm_judge_evaluate(
    model_output: str,
    expected_output: str,
    input_text: str,
    task_type: str
) -> JudgeScore:
    criteria = JUDGE_CRITERIA[task_type]

    prompt = f"""
    Evaluate this model output:

    Task: {task_type}
    Input: {input_text}
    Expected: {expected_output}
    Model Output: {model_output}

    Rate 1-5 on each:
    {'\n'.join(f'- {c}' for c in criteria)}

    Provide:
    1. Score for each criterion (1-5)
    2. Overall score (average)
    3. Brief reasoning (2-3 sentences)

    Output as JSON.
    """

    response = await anthropic.messages.create(
        model="claude-haiku-20250514",  # Fast + cheap
        messages=[{"role": "user", "content": prompt}]
    )

    return parse_judge_response(response)
```

**Cost Management**:
- Use Haiku (~$0.001 per eval)
- Limit to 50-100 evals per training job
- Cache results
- Allow users to set budget

---

### Feature 9: DPO Preference Training

**User Story**: When my model produces multiple plausible outputs, I want to train it to prefer the better ones through direct feedback.

**Use Case**: User has a working model but wants to refine it based on preferences.

**Workflow**:
1. User selects "Run Preference Training"
2. System generates 10-20 preference pairs:
   - Same input
   - Two different outputs (either from different model versions or temperature variations)
3. User picks which output is better (or "both bad", "both good")
4. System runs DPO training to align model with preferences
5. Creates new model version (e.g., v1 → v1.1)

**Preference Pair UI**:
```
Preference Training: Example 3/15

Input:
"Write a friendly email declining a meeting request"

┌─────────────────────────┬─────────────────────────┐
│ Output A                │ Output B                │
├─────────────────────────┼─────────────────────────┤
│ Thanks for the invite!  │ Thank you for thinking  │
│ Unfortunately I'm fully │ of me. I appreciate the │
│ booked that day. Let's  │ invitation but my       │
│ find another time?      │ calendar is full. Happy │
│                         │ to reschedule.          │
├─────────────────────────┼─────────────────────────┤
│ ◉ Prefer this           │ ○ Prefer this           │
│ ○ Both good             │ ○ Both bad              │
└─────────────────────────┴─────────────────────────┘

[Previous] [Skip] [Next]
```

**DPO Training** (faster than full training):
- Uses existing fine-tuned model as base
- Trains only on preference pairs (no dataset needed)
- Runs 1 epoch (~5-10 minutes)
- Creates minor version bump (v1 → v1.1)

---

## Cross-Cutting Concerns

### Data Validation

All training examples must pass:
1. **Format validation**: Input and output are strings
2. **Length validation**: Not empty, not >10K characters
3. **Category validation** (classification): Output matches defined categories
4. **JSON validation** (extraction): Output is valid JSON if structured
5. **Diversity check**: Not duplicates of existing examples
6. **Balance check**: Categories within 2x of each other

### Cost Tracking

Every operation logs cost:
```python
class CostLog(Base):
    id: UUID
    user_id: UUID
    operation: str  # training, inference, llm_judge, data_generation
    cost: Decimal
    metadata: dict  # tokens, duration, model, etc.
    created_at: datetime
```

Display to user:
- Cost per training job
- Cost per 1K inferences
- Total spend this month
- Budget alerts

### Error Recovery

All long-running operations support:
1. **Automatic retry** (3 attempts with exponential backoff)
2. **Partial progress saving** (checkpoints)
3. **Clear error messages** (user-actionable)
4. **Rollback** (if critical failure)

### Security

- API keys: bcrypt hashed
- S3 presigned URLs: 1-hour expiry
- Rate limiting: 60 req/min for free tier
- Input sanitization: All user inputs validated
- CORS: Whitelist frontend domains
- SQL injection: Use parameterized queries (SQLAlchemy)

---

This completes the detailed feature specifications for Phase 1 (MVP) and Phase 2 (Advanced) features.
