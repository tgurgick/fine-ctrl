# Training Module - QLoRA Fine-tuning on Modal

This module implements QLoRA (Quantized Low-Rank Adaptation) fine-tuning for Mistral 7B on Modal's serverless GPU infrastructure.

## Architecture

### Components

1. **`train.py`** - Modal training function
   - Loads dataset from S3
   - Configures QLoRA with 4-bit quantization
   - Trains using TRL's SFTTrainer
   - Publishes progress to Redis
   - Uploads adapter weights to S3

2. **`config.py`** - Training configuration
   - QLoRA hyperparameters
   - Resource limits
   - Model settings

3. **`utils.py`** - Utility functions
   - S3Manager with path validation (security)
   - ProgressTracker for Redis pub/sub
   - Dataset loading and formatting

4. **`backend/services/training.py`** - Orchestration service
   - Creates and manages training jobs
   - Invokes Modal functions
   - Tracks progress
   - Updates database

## Security Features

### S3 Path Validation
All S3 paths are validated to prevent:
- Directory traversal attacks (`../`)
- Absolute path access
- Access to other users' data

Valid path format:
```
finetune-models/<user_id>/<resource_type>/<resource_id>/<filename>
```

Where:
- `user_id`: UUID v4
- `resource_type`: One of `datasets`, `models`, `adapters`
- `resource_id`: UUID v4
- `filename`: Sanitized filename (no `/` or `..`)

### Resource Limits
- Max training time: 1 hour
- Max dataset size: 500 MB
- Max examples: 10,000
- Max concurrent jobs per user: 5 (free) / 50 (pro)

### Progress Tracking
Real-time progress updates via Redis pub/sub:
- Training initialization
- Step-by-step progress
- Loss and metrics
- Completion or error status

## Deployment

### Prerequisites

1. **Modal account and credentials**:
   ```bash
   modal token set
   ```

2. **S3 credentials** (MinIO for dev, AWS for prod):
   ```bash
   export S3_ENDPOINT_URL=http://localhost:9000
   export AWS_ACCESS_KEY_ID=minioadmin
   export AWS_SECRET_ACCESS_KEY=minioadmin
   ```

3. **Redis** for progress tracking:
   ```bash
   export REDIS_URL=redis://localhost:6379
   ```

### Deploy to Modal

```bash
# Deploy the training function
modal deploy training/train.py

# Verify deployment
modal app list
```

### Test Deployment

```bash
# Run local test
modal run training/train.py

# Or invoke remotely
python -c "
from modal import Function
train = Function.lookup('finetune-training', 'train_model')
result = train.remote(
    job_id='test-123',
    dataset_s3_path='finetune-models/.../datasets/.../train.jsonl',
    output_s3_path='finetune-models/.../adapters/...',
    config_dict={},
    redis_url='redis://localhost:6379'
)
print(result)
"
```

## Usage

### From Backend Service

```python
from backend.services.training import TrainingService
from backend.schemas.training import TrainingJobCreate

service = TrainingService()

# Create training job
job_data = TrainingJobCreate(
    task_id=task_id,
    dataset_id=dataset_id,
    config={
        "num_train_epochs": 3,
        "learning_rate": 2e-4,
    }
)

job = await service.create_training_job(db, user_id, job_data)

# Monitor progress
# (Progress updates are automatically published to Redis)
```

### Subscribe to Progress

```python
import redis
import json

r = redis.from_url("redis://localhost:6379", decode_responses=True)
pubsub = r.pubsub()
pubsub.subscribe(f"training:{job_id}:progress")

for message in pubsub.listen():
    if message['type'] == 'message':
        update = json.loads(message['data'])
        print(f"Status: {update['status']}")
        print(f"Progress: {update['progress']}%")
        print(f"Metrics: {update['metrics']}")
```

## Configuration

### Default QLoRA Settings

```python
QLoRAConfig(
    # Model
    model_name="mistralai/Mistral-7B-v0.1",
    max_seq_length=2048,

    # LoRA
    lora_r=64,
    lora_alpha=16,
    lora_dropout=0.1,

    # Quantization
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",

    # Training
    num_train_epochs=3,
    per_device_train_batch_size=4,
    learning_rate=2e-4,
)
```

### Custom Configuration

```python
custom_config = {
    "num_train_epochs": 5,
    "per_device_train_batch_size": 2,
    "learning_rate": 1e-4,
    "lora_r": 128,
}

job_data = TrainingJobCreate(
    task_id=task_id,
    dataset_id=dataset_id,
    config=custom_config,
)
```

## Dataset Format

Training datasets must be in JSONL format with `input` and `output` fields:

```jsonl
{"input": "Classify: This movie was amazing!", "output": "positive"}
{"input": "Classify: Terrible experience.", "output": "negative"}
{"input": "Classify: It was okay, nothing special.", "output": "neutral"}
```

The trainer automatically formats examples as:
```
### Instruction:
{input}

### Response:
{output}
```

## Testing

### Unit Tests

```bash
# Test training service
pytest tests/services/test_training.py -v

# Test training utilities
pytest tests/training/test_utils.py -v

# Run all tests
pytest tests/ -v
```

### Integration Test

```bash
# Requires Modal deployment and real S3/Redis
pytest tests/training/test_train.py -m integration
```

## Monitoring

### Training Metrics

Metrics published during training:
- `loss`: Training loss
- `learning_rate`: Current learning rate
- `epoch`: Current epoch
- `step`: Training step
- `final_loss`: Final training loss
- `examples_trained`: Total examples used

### Error Handling

Errors are caught and published to Redis:
```json
{
  "status": "failed",
  "progress": 0,
  "message": "Training failed: CUDA out of memory"
}
```

Common errors:
- CUDA OOM: Reduce batch size or max_seq_length
- Dataset too large: Exceeds resource limits
- S3 access denied: Invalid credentials or path
- Model loading failed: Network issues or cache problems

## Performance

### Expected Training Times

| Dataset Size | GPU    | Time     |
|--------------|--------|----------|
| 100 examples | A10G   | ~5 min   |
| 500 examples | A10G   | ~15 min  |
| 1000 examples| A10G   | ~30 min  |
| 5000 examples| A10G   | ~2 hours |

### Resource Usage

- GPU Memory: ~14GB (A10G has 24GB)
- RAM: ~20GB
- Disk: ~15GB (model cache)

## Troubleshooting

### Modal Deployment Fails

```bash
# Check Modal status
modal app list

# View logs
modal app logs finetune-training

# Redeploy
modal deploy training/train.py --force
```

### Training Fails with OOM

Reduce memory usage:
```python
config = {
    "per_device_train_batch_size": 1,
    "gradient_accumulation_steps": 8,
    "max_seq_length": 1024,
}
```

### S3 Upload Fails

Check credentials and path:
```bash
aws s3 ls s3://finetune-models/ --endpoint-url=http://localhost:9000
```

### Redis Connection Issues

Verify Redis is running:
```bash
redis-cli ping
```

## Future Enhancements

- [ ] Multi-GPU training support
- [ ] Checkpoint saving and resuming
- [ ] Evaluation during training
- [ ] Wandb/TensorBoard integration
- [ ] Custom model support (beyond Mistral 7B)
- [ ] LoRA merging into base model
- [ ] Quantized model export for deployment
