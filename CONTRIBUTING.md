# Contributing to Fine-Tune Platform

Thank you for your interest in contributing! This project aims to democratize LLM fine-tuning, and we welcome contributions from the community.

## Code of Conduct

Be respectful, inclusive, and constructive. We're building tools to make AI more accessible to everyone.

## How to Contribute

### Reporting Bugs

1. Check if the bug has already been reported in [Issues](https://github.com/your-repo/fine-ctrl/issues)
2. If not, create a new issue with:
   - Clear description of the bug
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details (OS, Python version, etc.)
   - Relevant logs or screenshots

### Suggesting Features

1. Check [Discussions](https://github.com/your-repo/fine-ctrl/discussions) for similar ideas
2. Create a new discussion with:
   - Problem you're trying to solve
   - Proposed solution
   - Alternative approaches considered
   - Impact on existing features

### Submitting Pull Requests

1. **Fork the repository** and create a new branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**:
   - Follow the code style guidelines below
   - Add tests for new functionality
   - Update documentation as needed

3. **Test your changes**:
   ```bash
   # Backend tests
   cd backend
   pytest

   # Frontend tests
   cd frontend
   npm test

   # Integration tests
   ./scripts/test-integration.sh
   ```

4. **Commit with clear messages**:
   ```bash
   git commit -m "Add: User preference collection for DPO training"
   ```

5. **Push and create PR**:
   ```bash
   git push origin feature/your-feature-name
   ```
   Then open a PR on GitHub with:
   - Description of changes
   - Related issue numbers
   - Screenshots (if UI changes)
   - Testing notes

## Development Setup

See [Getting Started Guide](docs/getting-started.md) for detailed setup instructions.

Quick start:
```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Development dependencies

# Frontend
cd frontend
npm install
```

## Code Style Guidelines

### Python (Backend)

- **Formatter**: Black (line length 100)
- **Linter**: Ruff
- **Type hints**: Required for all functions
- **Docstrings**: Google style

```python
# Good
async def analyze_task(
    self, description: str, sample_data: Optional[List[dict]] = None
) -> TaskAnalysis:
    """Analyze a fine-tuning task using Claude.

    Args:
        description: Natural language description of the task
        sample_data: Optional sample training examples

    Returns:
        TaskAnalysis with recommended configuration

    Raises:
        AnthropicAPIError: If Claude API call fails
    """
    ...
```

Run before committing:
```bash
black .
ruff check .
mypy .
```

### TypeScript (Frontend)

- **Formatter**: Prettier
- **Linter**: ESLint
- **Style**: Functional components with hooks

```typescript
// Good
interface TaskCreatorProps {
  onTaskCreated: (task: Task) => void;
}

export const TaskCreator: React.FC<TaskCreatorProps> = ({ onTaskCreated }) => {
  const [description, setDescription] = useState('');
  const { mutate: createTask } = useCreateTask();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    createTask({ description }, { onSuccess: onTaskCreated });
  };

  return (
    <form onSubmit={handleSubmit}>
      {/* ... */}
    </form>
  );
};
```

Run before committing:
```bash
npm run lint
npm run format
npm run type-check
```

## Testing Guidelines

### Backend Tests

```python
# Use pytest with fixtures
@pytest.fixture
async def task_service(db_session):
    return TaskService(db_session)

async def test_create_task_with_agent_analysis(task_service, mock_anthropic):
    # Arrange
    description = "Classify emails as spam or not spam"
    mock_anthropic.analyze.return_value = TaskAnalysis(...)

    # Act
    task = await task_service.create_task(description)

    # Assert
    assert task.task_type == "classification"
    assert task.config["recommended_examples"] == 200
```

### Frontend Tests

```typescript
// Use Vitest + React Testing Library
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

describe('TaskCreator', () => {
  it('analyzes task on description change', async () => {
    const onTaskCreated = vi.fn();
    render(<TaskCreator onTaskCreated={onTaskCreated} />);

    const input = screen.getByLabelText('Task Description');
    await userEvent.type(input, 'Classify support tickets');

    await waitFor(() => {
      expect(screen.getByText(/Detected: classification/i)).toBeInTheDocument();
    });
  });
});
```

## Project Structure Conventions

### Backend
```
backend/
├── api/
│   ├── routes/          # FastAPI route handlers
│   │   ├── tasks.py
│   │   └── training.py
│   └── deps.py          # Dependency injection
├── models/              # SQLAlchemy models
│   └── task.py
├── schemas/             # Pydantic schemas
│   └── task.py
├── services/            # Business logic
│   └── agent.py
└── tests/
    ├── unit/
    └── integration/
```

### Frontend
```
frontend/src/
├── components/          # Reusable UI components
│   └── Button/
│       ├── Button.tsx
│       ├── Button.test.tsx
│       └── index.ts
├── pages/               # Route-level components
│   └── TaskPage/
├── hooks/               # Custom React hooks
│   └── useTaskAnalysis.ts
├── api/                 # API client
│   └── tasks.ts
└── types/               # TypeScript types
    └── task.ts
```

## Documentation

- Update relevant docs in `/docs` when adding features
- Add JSDoc/docstrings for all public APIs
- Include examples in documentation

## Commit Message Format

```
<type>: <subject>

<body>

<footer>
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance tasks

**Examples**:
```
feat: Add DPO preference training support

- Implement DPOTrainer integration
- Add preference pair UI for data collection
- Update model versioning for DPO runs

Closes #42
```

## Review Process

1. **Automated checks** must pass (tests, linting, type checking)
2. **One approving review** required from maintainer
3. **Documentation** updated if needed
4. **Changelog** entry for user-facing changes

## Feature Development Workflow

### For Major Features

1. **Discussion first**: Open a GitHub Discussion to validate approach
2. **Design doc**: Create a spec document in `/docs/specs/`
3. **Implementation**: Break into smaller PRs when possible
4. **Testing**: Include unit, integration, and E2E tests
5. **Documentation**: Update user-facing docs

### For Bug Fixes

1. **Create issue** with reproduction steps
2. **Write failing test** that demonstrates the bug
3. **Fix the bug** and ensure test passes
4. **Submit PR** with issue reference

## Areas Needing Help

Check out issues labeled:
- `good-first-issue`: Great for newcomers
- `help-wanted`: Community contributions welcome
- `documentation`: Improve docs
- `performance`: Optimization opportunities

## Questions?

- GitHub Discussions: Ask questions and discuss ideas
- Discord: [Join our community](https://discord.gg/...)
- Email: maintainer@example.com

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
