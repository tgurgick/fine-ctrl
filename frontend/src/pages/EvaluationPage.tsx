import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { Button, Card, Table, LoadingSpinner, useToast } from '../components';
import { apiClient } from '../api/client';

interface EvaluationResult {
  id: string;
  model_version_id: string;
  accuracy: number;
  precision: number;
  recall: number;
  f1_score: number;
  created_at: string;
}

interface FeedbackSample {
  id: string;
  input: string;
  model_output: string;
  user_rating?: 'good' | 'bad';
}

export const EvaluationPage: React.FC = () => {
  const { modelId } = useParams<{ modelId: string }>();
  const [results, setResults] = useState<EvaluationResult[]>([]);
  const [samples, setSamples] = useState<FeedbackSample[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const { showToast } = useToast();

  useEffect(() => {
    fetchEvaluationResults();
    fetchFeedbackSamples();
  }, [modelId]);

  const fetchEvaluationResults = async () => {
    try {
      const data = await apiClient.get<EvaluationResult[]>(`/api/models/${modelId}/evaluations`);
      setResults(Array.isArray(data) ? data : []);
    } catch (error) {
      showToast('Failed to load evaluation results', 'error');
      setResults([]);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchFeedbackSamples = async () => {
    try {
      const data = await apiClient.get<FeedbackSample[]>(`/api/models/${modelId}/feedback-samples`);
      setSamples(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Failed to load feedback samples:', error);
    }
  };

  const handleRunEvaluation = async () => {
    try {
      showToast('Running evaluation...', 'info');
      await apiClient.post(`/api/models/${modelId}/evaluate`);
      showToast('Evaluation completed!', 'success');
      fetchEvaluationResults();
    } catch (error) {
      showToast('Failed to run evaluation', 'error');
    }
  };

  const handleFeedback = async (sampleId: string, rating: 'good' | 'bad') => {
    try {
      await apiClient.post(`/api/models/${modelId}/feedback`, {
        sample_id: sampleId,
        rating,
      });
      showToast('Feedback submitted!', 'success');
      fetchFeedbackSamples();
    } catch (error) {
      showToast('Failed to submit feedback', 'error');
    }
  };

  const columns = [
    {
      key: 'created_at',
      header: 'Date',
      render: (row: EvaluationResult) => new Date(row.created_at).toLocaleDateString(),
    },
    { key: 'accuracy', header: 'Accuracy', render: (row: EvaluationResult) => `${(row.accuracy * 100).toFixed(2)}%` },
    { key: 'precision', header: 'Precision', render: (row: EvaluationResult) => `${(row.precision * 100).toFixed(2)}%` },
    { key: 'recall', header: 'Recall', render: (row: EvaluationResult) => `${(row.recall * 100).toFixed(2)}%` },
    { key: 'f1_score', header: 'F1 Score', render: (row: EvaluationResult) => row.f1_score.toFixed(4) },
  ];

  if (isLoading) {
    return <LoadingSpinner className="min-h-screen" />;
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Model Evaluation</h1>
        <Button onClick={handleRunEvaluation}>Run Evaluation</Button>
      </div>

      <Card title="Evaluation Results" className="mb-6">
        <Table data={results} columns={columns} />
      </Card>

      <Card title="Provide Feedback">
        <p className="text-sm text-gray-600 mb-4">
          Review sample predictions and provide feedback to improve the model
        </p>
        <div className="space-y-4">
          {samples.map((sample) => (
            <div key={sample.id} className="border border-gray-200 rounded-lg p-4">
              <div className="mb-3">
                <p className="text-sm font-medium text-gray-700">Input:</p>
                <p className="text-sm text-gray-900 mt-1">{sample.input}</p>
              </div>
              <div className="mb-3">
                <p className="text-sm font-medium text-gray-700">Model Output:</p>
                <p className="text-sm text-gray-900 mt-1">{sample.model_output}</p>
              </div>
              <div className="flex gap-2">
                <Button
                  size="sm"
                  variant={sample.user_rating === 'good' ? 'primary' : 'secondary'}
                  onClick={() => handleFeedback(sample.id, 'good')}
                >
                  👍 Good
                </Button>
                <Button
                  size="sm"
                  variant={sample.user_rating === 'bad' ? 'danger' : 'secondary'}
                  onClick={() => handleFeedback(sample.id, 'bad')}
                >
                  👎 Bad
                </Button>
              </div>
            </div>
          ))}
          {samples.length === 0 && (
            <p className="text-sm text-gray-500 text-center py-4">
              No feedback samples available. Run an evaluation first.
            </p>
          )}
        </div>
      </Card>
    </div>
  );
};
