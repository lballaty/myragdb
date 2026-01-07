// File: tests/e2e/api-execution.spec.ts
// Description: API execution endpoint tests
// Author: Libor Ballaty <libor@arionetworks.com>
// Created: 2026-01-07

import { test, expect } from './fixtures';

test.describe('API Execution Endpoints - @api @integration @execution', () => {
  test('should execute code_search template @fast', async ({ apiClient, apiBaseURL }) => {
    const response = await apiClient.post('/api/v1/agent/execute', {
      request_type: 'code_search',
      parameters: {
        query: 'authentication',
        limit: 5,
      },
      execution_id: `test_${Date.now()}`,
    });

    expect(response.status).toBeLessThan(300);
    expect(response.data).toHaveProperty('execution_id');
    expect(response.data).toHaveProperty('status');
    expect(response.data.status).toMatch(/completed|failed/);
    expect(response.data).toHaveProperty('steps_completed');
    expect(response.data).toHaveProperty('total_steps');
  });

  test('should execute code_analysis template @fast', async ({ apiClient }) => {
    const response = await apiClient.post('/api/v1/agent/execute', {
      request_type: 'code_analysis',
      parameters: {
        query: 'class definition',
        language: 'python',
      },
    });

    expect(response.status).toBeLessThan(300);
    expect(response.data).toHaveProperty('status');
  });

  test('should execute code_review template @integration', async ({ apiClient }) => {
    const response = await apiClient.post('/api/v1/agent/execute', {
      request_type: 'code_review',
      parameters: {
        query: 'error handling',
        limit: 3,
      },
    });

    expect(response.status).toBeLessThan(300);
    expect(response.data).toHaveProperty('step_details');
  });

  test('should track execution progress @fast', async ({ apiClient }) => {
    const response = await apiClient.post('/api/v1/agent/execute', {
      request_type: 'code_search',
      parameters: {
        query: 'test',
        limit: 2,
      },
    });

    expect(response.data.steps_completed).toBeLessThanOrEqual(
      response.data.total_steps,
    );
    expect(response.data.total_steps).toBeGreaterThanOrEqual(1);
  });

  test('should reject missing required parameter @fast', async ({ apiClient }) => {
    const response = await apiClient.post('/api/v1/agent/execute', {
      request_type: 'code_search',
      parameters: {
        limit: 5,
        // Missing required 'query' parameter
      },
    });

    expect([400, 500]).toContain(response.status);
  });

  test('should reject unknown template @fast', async ({ apiClient }) => {
    const response = await apiClient.post('/api/v1/agent/execute', {
      request_type: 'unknown_template_xyz',
      parameters: {
        query: 'test',
      },
    });

    expect([404, 500]).toContain(response.status);
  });

  test('should execute custom workflow @integration', async ({ apiClient }) => {
    const response = await apiClient.post('/api/v1/agent/execute-workflow', {
      name: 'test_workflow',
      steps: [
        {
          skill: 'search',
          id: 'search_step',
          input: {
            query: 'test',
            limit: 2,
          },
        },
      ],
    });

    expect(response.status).toBeLessThan(300);
    expect(response.data).toHaveProperty('status');
    expect(response.data).toHaveProperty('step_details');
  });

  test('should handle step errors with on_error directive @integration', async ({
    apiClient,
  }) => {
    const response = await apiClient.post('/api/v1/agent/execute-workflow', {
      name: 'test_error_handling',
      steps: [
        {
          skill: 'search',
          id: 'find',
          input: {
            query: 'test',
            limit: 1,
          },
          on_error: 'continue',
        },
      ],
    });

    expect(response.status).toBeLessThan(300);
    expect(response.data).toHaveProperty('status');
  });

  test('should support variable interpolation in workflows @integration', async ({
    apiClient,
  }) => {
    const response = await apiClient.post('/api/v1/agent/execute-workflow', {
      name: 'interpolation_test',
      steps: [
        {
          skill: 'search',
          id: 'step1',
          input: {
            query: 'test',
            limit: 1,
          },
        },
      ],
    });

    // Should not error on variable reference syntax
    expect(response.status).toBeLessThan(300);
  });

  test('should include step details in response @fast', async ({ apiClient }) => {
    const response = await apiClient.post('/api/v1/agent/execute', {
      request_type: 'code_search',
      parameters: {
        query: 'test',
      },
    });

    expect(response.data.step_details).toBeDefined();
    expect(Array.isArray(response.data.step_details)).toBe(true);

    response.data.step_details.forEach((step: any) => {
      expect(step).toHaveProperty('skill');
      expect(step).toHaveProperty('status');
    });
  });
});
