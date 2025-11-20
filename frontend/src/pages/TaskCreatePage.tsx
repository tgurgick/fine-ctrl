import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Input, TextArea, Button, Card, useToast } from '../components';
import { apiClient } from '../api/client';

export const TaskCreatePage: React.FC = () => {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();
  const { showToast } = useToast();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      const response = await apiClient.post<{ id: string }>('/api/tasks', {
        name,
        description,
      });

      showToast('Task created successfully!', 'success');
      navigate(`/tasks/${response.id}`);
    } catch (error: any) {
      showToast(error.response?.data?.message || 'Failed to create task', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Create New Task</h1>
        <p className="text-gray-600 mt-2">
          Describe your fine-tuning task and let our AI analyze it
        </p>
      </div>

      <Card>
        <form onSubmit={handleSubmit} className="space-y-6">
          <Input
            label="Task Name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g., Customer Support Classifier"
            helperText="A short, descriptive name for your task"
            required
          />

          <TextArea
            label="Task Description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Describe what you want the model to do..."
            rows={8}
            helperText="Be specific about the input format, expected output, and any special requirements"
            required
          />

          <div className="flex gap-3">
            <Button type="submit" isLoading={isLoading}>
              Create Task
            </Button>
            <Button type="button" variant="ghost" onClick={() => navigate('/tasks')}>
              Cancel
            </Button>
          </div>
        </form>
      </Card>

      <Card className="mt-6" title="Tips for writing a good task description">
        <ul className="list-disc list-inside space-y-2 text-sm text-gray-600">
          <li>Clearly define the input format (e.g., "customer emails", "product descriptions")</li>
          <li>Specify the expected output (e.g., "category label", "sentiment score")</li>
          <li>Include any domain-specific context or constraints</li>
          <li>Provide examples if possible</li>
        </ul>
      </Card>
    </div>
  );
};
