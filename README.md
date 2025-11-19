# Fine-Tune Platform

> Democratizing domain expertise capture through simplified LLM fine-tuning

## Vision

Make fine-tuning open source models as easy as describing what you want and providing examples. No ML expertise required. Domain experts should be able to create production-quality specialized models through an intuitive interface that handles all the complexity.

## Core Philosophy

1. **Data generation is the bottleneck** - Focus UX on helping users create high-quality training data
2. **Abstract complexity** - Users shouldn't think about hyperparameters, model selection, or infrastructure
3. **Intelligent defaults** - Agent-driven configuration based on task type
4. **Iterative improvement** - Built-in feedback loops for continuous refinement
5. **Open ecosystem** - Contribute trained models back to the community

## Key Features

### 🤖 Agent-Driven Setup
- Describe your task in plain English
- Agent analyzes and configures everything automatically
- Task-specific metrics and evaluation strategies
- Smart recommendations for data requirements

### 📊 Intelligent Data Generation
- Assisted example creation with AI suggestions
- Templates for common use cases
- Quality checks and diversity analysis
- Active learning suggestions for weak areas

### 🔄 Iterative Refinement Loop
- Post-training evaluation on 10 representative examples
- User feedback collection (thumbs up/down)
- Pattern analysis of failures
- Targeted data generation or RLHF for improvement

### 🚀 Easy Deployment & Sharing
- One-click deployment to serverless infrastructure
- Public playground for testing
- Team collaboration features
- Export for self-hosting

## Technology Stack

- **Frontend**: React + TypeScript
- **Backend**: Python FastAPI
- **Training**: HuggingFace (transformers + PEFT + TRL)
- **Compute**: Modal (serverless GPU)
- **Storage**: PostgreSQL + S3
- **Agent**: Claude API

## Quick Start

```bash
# Clone the repository
git clone <repository-url>
cd fine-ctrl

# See full setup instructions
open docs/getting-started.md
```

**New to the project?** Start with the [Getting Started Guide](docs/getting-started.md)

## Documentation

Comprehensive documentation is available in the `/docs` directory:

- **[Getting Started](docs/getting-started.md)** - Setup instructions and quick start
- **[Development Handoff](docs/development-handoff.md)** - Complete technical specification
- **[Architecture](docs/architecture.md)** - System design and component details
- **[Feature Specifications](docs/feature-specs.md)** - Detailed feature requirements
- **[API Reference](docs/api-reference.md)** - Complete API documentation
- **[Contributing](CONTRIBUTING.md)** - How to contribute to the project

### For Parallel Development

Want to build the MVP faster with multiple agents working simultaneously?

- **[Parallel Execution Plan](docs/parallel-execution-plan.md)** - Detailed work package breakdown
- **[Quick Start for Agents](docs/quick-start-agents.md)** - Ready-to-use agent prompts

**Speedup**: Build MVP in ~20 hours instead of ~50 hours (2.5x faster)

## Project Structure

```
fine-ctrl/
├── docs/                    # Comprehensive documentation
│   ├── getting-started.md   # Setup guide
│   ├── development-handoff.md # Full technical spec
│   ├── architecture.md      # System design
│   ├── feature-specs.md     # Feature details
│   └── api-reference.md     # API documentation
├── backend/                 # Python FastAPI application
├── frontend/                # React + TypeScript application
├── training/                # Modal fine-tuning scripts
├── evaluation/              # Metrics and evaluation
└── deployment/              # Infrastructure configurations
```

## Key Concepts

### The Innovation

Unlike other fine-tuning platforms, we focus on **data generation as the primary UX**. Users spend time creating quality examples while an AI agent handles all the ML complexity automatically.

### User Journey

```
Describe Task → Agent Configures → Generate Data → Train (30min) → Evaluate → Deploy
```

No hyperparameters. No GPU management. No ML expertise required.

## Development

### Prerequisites

- Python 3.10+
- Node.js 18+
- Docker (for local database)
- Modal account (for GPU compute)
- Anthropic API key

### Quick Setup

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Frontend
cd frontend
npm install
npm run dev
```

See the [Getting Started Guide](docs/getting-started.md) for detailed setup instructions.

## Contributing

We welcome contributions! This project aims to democratize LLM fine-tuning and make AI more accessible.

- Read the [Contributing Guidelines](CONTRIBUTING.md)
- Check out [issues labeled "good first issue"](https://github.com/your-repo/fine-ctrl/issues?q=label%3A%22good+first+issue%22)
- Join discussions in [GitHub Discussions](https://github.com/your-repo/fine-ctrl/discussions)

## Support

- **Issues**: [Report bugs or request features](https://github.com/your-repo/fine-ctrl/issues)
- **Discussions**: [Ask questions and share ideas](https://github.com/your-repo/fine-ctrl/discussions)
- **Documentation**: Comprehensive guides in `/docs`

## License

MIT License - See [LICENSE](LICENSE) for details

---

**Built with**: React, FastAPI, Modal, HuggingFace, Claude