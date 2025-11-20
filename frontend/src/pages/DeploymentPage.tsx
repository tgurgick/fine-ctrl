import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { Button, Card, Input, Table, LoadingSpinner, useToast } from '../components';
import { apiClient } from '../api/client';

interface Deployment {
  id: string;
  name: string;
  endpoint_url: string;
  status: 'deploying' | 'active' | 'failed';
  is_public: boolean;
  created_at: string;
}

export const DeploymentPage: React.FC = () => {
  const { modelId } = useParams<{ modelId: string }>();
  const [deployments, setDeployments] = useState<Deployment[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [deploymentName, setDeploymentName] = useState('');
  const [isPublic, setIsPublic] = useState(false);
  const [isDeploying, setIsDeploying] = useState(false);
  const [testInput, setTestInput] = useState('');
  const [testOutput, setTestOutput] = useState('');
  const [isTesting, setIsTesting] = useState(false);
  const { showToast } = useToast();

  useEffect(() => {
    fetchDeployments();
  }, [modelId]);

  const fetchDeployments = async () => {
    try {
      const data = await apiClient.get<Deployment[]>(`/api/models/${modelId}/deployments`);
      setDeployments(Array.isArray(data) ? data : []);
    } catch (error) {
      showToast('Failed to load deployments', 'error');
      setDeployments([]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeploy = async () => {
    if (!deploymentName) {
      showToast('Please enter a deployment name', 'warning');
      return;
    }

    setIsDeploying(true);
    try {
      showToast('Deploying model...', 'info');
      await apiClient.post(`/api/models/${modelId}/deploy`, {
        name: deploymentName,
        is_public: isPublic,
      });
      showToast('Model deployed successfully!', 'success');
      setDeploymentName('');
      fetchDeployments();
    } catch (error) {
      showToast('Failed to deploy model', 'error');
    } finally {
      setIsDeploying(false);
    }
  };

  const handleTest = async (endpointUrl: string) => {
    if (!testInput) {
      showToast('Please enter test input', 'warning');
      return;
    }

    setIsTesting(true);
    try {
      const response = await apiClient.post<{ output?: string }>(endpointUrl, { input: testInput });
      setTestOutput(response.output || JSON.stringify(response));
      showToast('Test successful!', 'success');
    } catch (error) {
      showToast('Test failed', 'error');
      setTestOutput('Error: Failed to get response');
    } finally {
      setIsTesting(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'text-green-600 bg-green-100';
      case 'deploying':
        return 'text-blue-600 bg-blue-100';
      case 'failed':
        return 'text-red-600 bg-red-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  const columns = [
    { key: 'name', header: 'Name' },
    {
      key: 'status',
      header: 'Status',
      render: (row: Deployment) => (
        <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(row.status)}`}>
          {row.status}
        </span>
      ),
    },
    {
      key: 'is_public',
      header: 'Visibility',
      render: (row: Deployment) => (row.is_public ? 'Public' : 'Private'),
    },
    {
      key: 'endpoint_url',
      header: 'Endpoint',
      render: (row: Deployment) => (
        <code className="text-xs bg-gray-100 px-2 py-1 rounded">{row.endpoint_url}</code>
      ),
    },
    {
      key: 'created_at',
      header: 'Created',
      render: (row: Deployment) => new Date(row.created_at).toLocaleDateString(),
    },
  ];

  if (isLoading) {
    return <LoadingSpinner className="min-h-screen" />;
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold text-gray-900 mb-6">Model Deployment</h1>

      <Card title="Deploy New Version" className="mb-6">
        <div className="space-y-4">
          <Input
            label="Deployment Name"
            value={deploymentName}
            onChange={(e) => setDeploymentName(e.target.value)}
            placeholder="e.g., production-v1"
          />

          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="isPublic"
              checked={isPublic}
              onChange={(e) => setIsPublic(e.target.checked)}
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <label htmlFor="isPublic" className="text-sm text-gray-700">
              Make this deployment public
            </label>
          </div>

          <Button onClick={handleDeploy} isLoading={isDeploying}>
            Deploy Model
          </Button>
        </div>
      </Card>

      <Card title="Active Deployments" className="mb-6">
        <Table data={deployments} columns={columns} />
      </Card>

      {deployments.length > 0 && (
        <Card title="Test Deployment">
          <div className="space-y-4">
            <Input
              label="Test Input"
              value={testInput}
              onChange={(e) => setTestInput(e.target.value)}
              placeholder="Enter test input..."
            />

            <Button
              onClick={() => handleTest(deployments[0].endpoint_url)}
              isLoading={isTesting}
            >
              Test Endpoint
            </Button>

            {testOutput && (
              <div className="mt-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Output:
                </label>
                <pre className="bg-gray-50 border border-gray-200 rounded-lg p-4 text-sm">
                  {testOutput}
                </pre>
              </div>
            )}
          </div>
        </Card>
      )}
    </div>
  );
};
