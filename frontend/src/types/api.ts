// This file will be auto-generated from the OpenAPI spec
// Run: npm run generate-types
// For now, we use placeholder types

export interface User {
  id: string;
  email: string;
  name?: string;
}

export interface Task {
  id: string;
  user_id: string;
  name: string;
  description: string;
  config?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface Dataset {
  id: string;
  task_id: string;
  name: string;
  size: number;
  created_at: string;
}

export interface TrainingJob {
  id: string;
  task_id: string;
  dataset_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number;
  created_at: string;
  completed_at?: string;
}

export interface ModelVersion {
  id: string;
  task_id: string;
  training_job_id: string;
  version: string;
  metrics?: Record<string, any>;
  created_at: string;
}

export interface Deployment {
  id: string;
  model_version_id: string;
  user_id: string;
  name: string;
  endpoint_url: string;
  status: 'deploying' | 'active' | 'failed';
  is_public: boolean;
  created_at: string;
}
