import { apiClient } from '../api/client';

/**
 * Test if the backend /health endpoint is accessible
 */
export async function testHealthEndpoint(): Promise<boolean> {
  try {
    const response = await apiClient.health();
    console.log('Health check response:', response.data);
    return response.status === 200;
  } catch (error) {
    console.error('Health check failed:', error);
    return false;
  }
}

// If running this file directly
if (import.meta.url === `file://${process.argv[1]}`) {
  testHealthEndpoint().then((healthy) => {
    if (healthy) {
      console.log('✅ Backend is healthy!');
      process.exit(0);
    } else {
      console.log('❌ Backend is not responding');
      process.exit(1);
    }
  });
}
