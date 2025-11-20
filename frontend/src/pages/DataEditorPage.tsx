import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { Button, Card, Table, Modal, TextArea, LoadingSpinner, useToast } from '../components';
import { apiClient } from '../api/client';

interface DataExample {
  id: string;
  input: string;
  output: string;
  created_at: string;
}

export const DataEditorPage: React.FC = () => {
  const { taskId } = useParams<{ taskId: string }>();
  const [examples, setExamples] = useState<DataExample[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [newInput, setNewInput] = useState('');
  const [newOutput, setNewOutput] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { showToast } = useToast();

  useEffect(() => {
    fetchExamples();
  }, [taskId]);

  const fetchExamples = async () => {
    try {
      const data = await apiClient.get<DataExample[]>(`/api/tasks/${taskId}/examples`);
      setExamples(Array.isArray(data) ? data : []);
    } catch (error) {
      showToast('Failed to load examples', 'error');
      setExamples([]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleAddExample = async () => {
    setIsSubmitting(true);
    try {
      await apiClient.post(`/api/tasks/${taskId}/examples`, {
        input: newInput,
        output: newOutput,
      });

      showToast('Example added successfully!', 'success');
      setIsModalOpen(false);
      setNewInput('');
      setNewOutput('');
      fetchExamples();
    } catch (error) {
      showToast('Failed to add example', 'error');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleGenerateExamples = async () => {
    try {
      showToast('Generating examples...', 'info');
      await apiClient.post(`/api/tasks/${taskId}/generate-examples`, { count: 10 });
      showToast('Examples generated successfully!', 'success');
      fetchExamples();
    } catch (error) {
      showToast('Failed to generate examples', 'error');
    }
  };

  const columns = [
    { key: 'input', header: 'Input' },
    { key: 'output', header: 'Output' },
    {
      key: 'created_at',
      header: 'Created',
      render: (row: DataExample) => new Date(row.created_at).toLocaleDateString(),
    },
  ];

  if (isLoading) {
    return <LoadingSpinner className="min-h-screen" />;
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Training Data</h1>
          <p className="text-gray-600 mt-2">{examples.length} examples</p>
        </div>
        <div className="flex gap-3">
          <Button variant="secondary" onClick={handleGenerateExamples}>
            Generate Examples
          </Button>
          <Button onClick={() => setIsModalOpen(true)}>Add Example</Button>
        </div>
      </div>

      <Card>
        <Table data={examples} columns={columns} />
      </Card>

      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="Add Training Example"
        footer={
          <>
            <Button variant="ghost" onClick={() => setIsModalOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleAddExample} isLoading={isSubmitting}>
              Add Example
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          <TextArea
            label="Input"
            value={newInput}
            onChange={(e) => setNewInput(e.target.value)}
            placeholder="Enter the input text..."
            rows={4}
          />
          <TextArea
            label="Output"
            value={newOutput}
            onChange={(e) => setNewOutput(e.target.value)}
            placeholder="Enter the expected output..."
            rows={4}
          />
        </div>
      </Modal>
    </div>
  );
};
