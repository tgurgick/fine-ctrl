import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { Button, Card, ProgressBar, LoadingSpinner, Table, useToast } from '../components';
import { apiClient } from '../api/client';

interface TrainingJob {
  id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number;
  created_at: string;
  completed_at?: string;
  metrics?: {
    loss: number;
    accuracy?: number;
  };
}

export const TrainingDashboardPage: React.FC = () => {
  const { taskId } = useParams<{ taskId: string }>();
  const [jobs, setJobs] = useState<TrainingJob[]>([]);
  const [currentJob, setCurrentJob] = useState<TrainingJob | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const { showToast } = useToast();

  useEffect(() => {
    fetchJobs();
    const interval = setInterval(fetchJobs, 5000); // Poll every 5 seconds
    return () => clearInterval(interval);
  }, [taskId]);

  const fetchJobs = async () => {
    try {
      const data = await apiClient.get<TrainingJob[]>(`/api/tasks/${taskId}/training-jobs`);
      setJobs(Array.isArray(data) ? data : []);

      const running = (Array.isArray(data) ? data : []).find(
        (job: TrainingJob) => job.status === 'running'
      );
      setCurrentJob(running || null);
    } catch (error) {
      console.error('Failed to fetch training jobs:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleStartTraining = async () => {
    try {
      showToast('Starting training job...', 'info');
      await apiClient.post(`/api/tasks/${taskId}/training-jobs`);
      showToast('Training started successfully!', 'success');
      fetchJobs();
    } catch (error) {
      showToast('Failed to start training', 'error');
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'text-green-600 bg-green-100';
      case 'running':
        return 'text-blue-600 bg-blue-100';
      case 'failed':
        return 'text-red-600 bg-red-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  const columns = [
    { key: 'id', header: 'Job ID', render: (row: TrainingJob) => row.id.slice(0, 8) },
    {
      key: 'status',
      header: 'Status',
      render: (row: TrainingJob) => (
        <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(row.status)}`}>
          {row.status}
        </span>
      ),
    },
    { key: 'progress', header: 'Progress', render: (row: TrainingJob) => `${row.progress}%` },
    {
      key: 'created_at',
      header: 'Created',
      render: (row: TrainingJob) => new Date(row.created_at).toLocaleString(),
    },
  ];

  if (isLoading) {
    return <LoadingSpinner className="min-h-screen" />;
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Training Dashboard</h1>
        <Button onClick={handleStartTraining} disabled={!!currentJob}>
          Start Training
        </Button>
      </div>

      {currentJob && (
        <Card className="mb-6" title="Current Training Job">
          <div className="space-y-4">
            <ProgressBar progress={currentJob.progress} label="Training Progress" />
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-gray-600">Status:</span>{' '}
                <span className="font-medium">{currentJob.status}</span>
              </div>
              <div>
                <span className="text-gray-600">Job ID:</span>{' '}
                <span className="font-mono text-xs">{currentJob.id}</span>
              </div>
              {currentJob.metrics && (
                <>
                  <div>
                    <span className="text-gray-600">Loss:</span>{' '}
                    <span className="font-medium">{currentJob.metrics.loss.toFixed(4)}</span>
                  </div>
                  {currentJob.metrics.accuracy && (
                    <div>
                      <span className="text-gray-600">Accuracy:</span>{' '}
                      <span className="font-medium">{(currentJob.metrics.accuracy * 100).toFixed(2)}%</span>
                    </div>
                  )}
                </>
              )}
            </div>
          </div>
        </Card>
      )}

      <Card title="Training History">
        <Table data={jobs} columns={columns} />
      </Card>
    </div>
  );
};
