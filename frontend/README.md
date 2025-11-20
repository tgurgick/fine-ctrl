# Fine-Tune Platform Frontend

React + TypeScript + Vite frontend for the Fine-Tune Platform.

## Features

- ✅ Vite + React + TypeScript
- ✅ Tailwind CSS for styling
- ✅ React Router for navigation
- ✅ TanStack Query (React Query) for state management
- ✅ Axios for API calls
- ✅ JWT authentication with token refresh
- ✅ Comprehensive UI component library
- ✅ All pages implemented (Login, Task Create, Data Editor, Training, Evaluation, Deployment)
- ✅ Type-safe API client
- ✅ Component tests with Vitest
- ✅ Responsive design

## Getting Started

### Prerequisites

- Node.js 18+
- npm 9+
- Backend API running on http://localhost:8000

### Installation

```bash
npm install
```

### Development

```bash
npm run dev
```

The app will be available at http://localhost:5173

### Build

```bash
npm run build
```

### Test

```bash
# Run tests once
npm test

# Run tests in watch mode
npm run test:watch
```

### Type Checking

```bash
npm run type-check
```

### Generate API Types

Once the backend is running, generate TypeScript types from the OpenAPI spec:

```bash
npm run generate-types
```

This will create `src/types/api.ts` with type-safe interfaces for all API endpoints.

## Project Structure

```
frontend/
├── src/
│   ├── api/
│   │   └── client.ts          # API client with auth
│   ├── components/            # Shared UI components
│   │   ├── Button.tsx
│   │   ├── Input.tsx
│   │   ├── TextArea.tsx
│   │   ├── Card.tsx
│   │   ├── Table.tsx
│   │   ├── Modal.tsx
│   │   ├── LoadingSpinner.tsx
│   │   ├── ProgressBar.tsx
│   │   ├── ErrorBoundary.tsx
│   │   ├── Toast.tsx
│   │   ├── Layout.tsx
│   │   ├── ProtectedRoute.tsx
│   │   └── __tests__/        # Component tests
│   ├── contexts/
│   │   └── AuthContext.tsx   # Authentication state
│   ├── pages/                # Application pages
│   │   ├── LoginPage.tsx
│   │   ├── TaskCreatePage.tsx
│   │   ├── DataEditorPage.tsx
│   │   ├── TrainingDashboardPage.tsx
│   │   ├── EvaluationPage.tsx
│   │   └── DeploymentPage.tsx
│   ├── types/
│   │   └── api.ts            # Auto-generated API types
│   ├── test/
│   │   └── setup.ts          # Test setup
│   ├── App.tsx               # Main app component
│   ├── main.tsx              # App entry point
│   └── index.css             # Global styles
├── .env                       # Environment variables
├── .env.example              # Environment variables template
├── tailwind.config.js        # Tailwind configuration
├── postcss.config.js         # PostCSS configuration
├── vitest.config.ts          # Vitest configuration
└── package.json
```

## Environment Variables

Create a `.env` file:

```
VITE_API_URL=http://localhost:8000
```

## Pages

### Login Page
- Email/password authentication
- JWT token management
- Redirects to tasks page on success

### Task Create Page
- Create new fine-tuning tasks
- Describe task requirements
- AI analysis integration

### Data Editor Page
- Add training examples manually
- Generate examples with AI
- View and manage dataset

### Training Dashboard
- Start training jobs
- Monitor progress in real-time
- View training metrics

### Evaluation Page
- Run model evaluations
- View metrics (accuracy, F1, etc.)
- Provide feedback on predictions

### Deployment Page
- Deploy models to inference endpoints
- Manage deployments
- Test deployed models

## Authentication

The app uses JWT authentication with:
- Access tokens (15 minutes)
- Refresh tokens (auto-refresh)
- Token revocation support
- Protected routes

## API Integration

All API calls go through the centralized `apiClient`:

```typescript
import { apiClient } from './api/client';

// Example usage
const tasks = await apiClient.get('/api/tasks');
const newTask = await apiClient.post('/api/tasks', { name: 'My Task' });
```

The client automatically:
- Adds authentication headers
- Refreshes expired tokens
- Handles errors
- Types responses

## Testing

Tests are written with:
- Vitest (test runner)
- React Testing Library (component testing)
- @testing-library/jest-dom (matchers)

Run tests:
```bash
npm test
```

## Build for Production

```bash
npm run build
```

Output will be in the `dist/` directory.

## License

MIT
