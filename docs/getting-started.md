# Getting Started Guide

## Prerequisites

- Python 3.10+
- Node.js 18+
- Docker (for local database)
- Modal account (for GPU compute)
- Anthropic API key (for Claude agent)
- AWS account or MinIO (for storage)

## Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
cd fine-ctrl
```

### 2. Backend Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
cd backend
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your credentials
```

### 3. Database Setup

```bash
# Start PostgreSQL with Docker
docker run -d \
  --name finetune-db \
  -p 5432:5432 \
  -e POSTGRES_DB=finetune \
  -e POSTGRES_USER=finetune \
  -e POSTGRES_PASSWORD=your_password \
  postgres:15

# Run migrations
cd backend
alembic upgrade head
```

### 4. Modal Setup

```bash
# Install Modal CLI
pip install modal

# Authenticate
modal token new

# Deploy training function
cd training
modal deploy train.py
```

### 5. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

### 6. Start Backend Server

```bash
cd backend
uvicorn main:app --reload --port 8000
```

## Environment Variables

Create a `.env` file in the backend directory:

```bash
# Database
DATABASE_URL=postgresql://finetune:your_password@localhost:5432/finetune

# Storage
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
S3_BUCKET=finetune-models
AWS_REGION=us-east-1

# Anthropic
ANTHROPIC_API_KEY=sk-ant-...

# Modal
MODAL_TOKEN_ID=ak-...
MODAL_TOKEN_SECRET=as-...

# Application
SECRET_KEY=generate_random_secret_key
ENVIRONMENT=development
DEBUG=true

# Costs
COST_PER_TRAINING_JOB=2.00
MAX_FREE_TRAINING_JOBS=5
```

## Testing the Setup

### 1. Test Backend API

```bash
curl http://localhost:8000/health
# Expected: {"status": "healthy"}
```

### 2. Test Agent Integration

```bash
curl -X POST http://localhost:8000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Ticket Classifier",
    "description": "Classify support tickets into bug, feature, question"
  }'
```

### 3. Test Frontend

Open browser to `http://localhost:5173` (or whatever port Vite assigns)

## Development Workflow

### Creating a New Task

1. Open the web interface
2. Click "New Task"
3. Describe your task in plain English
4. Agent analyzes and suggests configuration
5. Add training examples (manual or AI-generated)
6. Click "Train Model"
7. Wait for training to complete (~30 min)
8. Evaluate results with 10 test examples
9. Deploy or iterate based on feedback

### Local Training (Optional)

For faster iteration during development, you can run training locally:

```bash
cd training
python local_train.py \
  --dataset path/to/dataset.json \
  --output_dir ./models/test-run
```

Note: Requires GPU with 24GB+ VRAM for 7B models.

## Common Issues

### Modal Authentication Fails
```bash
# Re-authenticate
modal token new
```

### Database Connection Error
```bash
# Check if PostgreSQL is running
docker ps | grep finetune-db

# Check connection
psql postgresql://finetune:password@localhost:5432/finetune
```

### Frontend Build Errors
```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

### Training Job Fails
- Check Modal logs: `modal app logs`
- Verify GPU quota in Modal dashboard
- Check dataset format in S3

## Project Structure

```
fine-ctrl/
├── backend/
│   ├── main.py              # FastAPI app
│   ├── api/                 # API routes
│   ├── models/              # SQLAlchemy models
│   ├── services/            # Business logic
│   │   ├── agent.py         # Claude integration
│   │   ├── training.py      # Training orchestration
│   │   └── evaluation.py    # Metrics and eval
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── pages/           # Page components
│   │   ├── hooks/           # Custom hooks
│   │   └── api/             # API client
│   └── package.json
├── training/
│   ├── train.py             # Modal training function
│   ├── config.py            # QLoRA configuration
│   └── utils.py             # Training utilities
├── evaluation/
│   ├── metrics.py           # Evaluation metrics
│   └── judge.py             # LLM-as-judge
└── docs/
    ├── development-handoff.md
    ├── getting-started.md
    └── architecture.md
```

## Next Steps

1. Read the [Development Handoff](./development-handoff.md) for full context
2. Review the [Architecture Documentation](./architecture.md)
3. Start with Phase 1 MVP features
4. Join the community discussions

## Getting Help

- GitHub Issues: Report bugs and request features
- Discussions: Ask questions and share ideas
- Documentation: Detailed guides in `/docs`

## Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines on:
- Code style
- Testing requirements
- Pull request process
- Community guidelines
