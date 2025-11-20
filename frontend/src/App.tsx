import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from './contexts/AuthContext';
import { ErrorBoundary, ToastProvider, Layout, ProtectedRoute } from './components';
import {
  LoginPage,
  SignupPage,
  DashboardPage,
  TaskCreatePage,
  DataEditorPage,
  TrainingDashboardPage,
  EvaluationPage,
  DeploymentPage,
} from './pages';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

function App() {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <AuthProvider>
            <ToastProvider>
              <Layout>
                <Routes>
                  <Route path="/login" element={<LoginPage />} />
                  <Route path="/signup" element={<SignupPage />} />
                  <Route
                    path="/dashboard"
                    element={
                      <ProtectedRoute>
                        <DashboardPage />
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="/tasks/new"
                    element={
                      <ProtectedRoute>
                        <TaskCreatePage />
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="/tasks/:taskId/data"
                    element={
                      <ProtectedRoute>
                        <DataEditorPage />
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="/tasks/:taskId/training"
                    element={
                      <ProtectedRoute>
                        <TrainingDashboardPage />
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="/models/:modelId/evaluation"
                    element={
                      <ProtectedRoute>
                        <EvaluationPage />
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="/models/:modelId/deploy"
                    element={
                      <ProtectedRoute>
                        <DeploymentPage />
                      </ProtectedRoute>
                    }
                  />
                  <Route path="/" element={<Navigate to="/dashboard" replace />} />
                  <Route path="*" element={<Navigate to="/dashboard" replace />} />
                </Routes>
              </Layout>
            </ToastProvider>
          </AuthProvider>
        </BrowserRouter>
      </QueryClientProvider>
    </ErrorBoundary>
  );
}

export default App;
