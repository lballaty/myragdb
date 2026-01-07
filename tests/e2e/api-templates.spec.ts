// File: tests/e2e/api-templates.spec.ts
// Description: Template discovery and management API tests
// Author: Libor Ballaty <libor@arionetworks.com>
// Created: 2026-01-07

import { test, expect } from './fixtures';

test.describe('API Template Endpoints - @api @discovery @fast', () => {
  test('should list all templates', async ({ apiClient }) => {
    const response = await apiClient.get('/api/v1/agent/templates');

    expect(response.status).toBe(200);
    expect(response.data).toHaveProperty('total');
    expect(response.data).toHaveProperty('templates');
    expect(Array.isArray(response.data.templates)).toBe(true);
    expect(response.data.total).toBeGreaterThanOrEqual(3);
  });

  test('should have required fields in template list', async ({ apiClient }) => {
    const response = await apiClient.get('/api/v1/agent/templates');

    response.data.templates.forEach((template: any) => {
      expect(template).toHaveProperty('id');
      expect(template).toHaveProperty('name');
      expect(template).toHaveProperty('description');
      expect(template).toHaveProperty('category');
      expect(template).toHaveProperty('parameters');
      expect(template).toHaveProperty('step_count');
    });
  });

  test('should include built-in templates', async ({ apiClient }) => {
    const response = await apiClient.get('/api/v1/agent/templates');

    const templateIds = response.data.templates.map((t: any) => t.id);
    expect(templateIds).toContain('code_search');
    expect(templateIds).toContain('code_analysis');
    expect(templateIds).toContain('code_review');
  });

  test('should get specific template info @fast', async ({ apiClient }) => {
    const response = await apiClient.get('/api/v1/agent/templates/code_search');

    expect(response.status).toBe(200);
    expect(response.data.id).toBe('code_search');
    expect(response.data).toHaveProperty('name');
    expect(response.data).toHaveProperty('description');
    expect(response.data).toHaveProperty('parameters');
    expect(response.data).toHaveProperty('step_count');
  });

  test('should have query parameter in code_search template', async ({ apiClient }) => {
    const response = await apiClient.get('/api/v1/agent/templates/code_search');

    expect(response.data.parameters).toHaveProperty('query');
    expect(response.data.parameters.query.required).toBe(true);
    expect(response.data.parameters.query.type).toBe('string');
  });

  test('should have optional parameters with defaults', async ({ apiClient }) => {
    const response = await apiClient.get('/api/v1/agent/templates/code_search');

    if (response.data.parameters.limit) {
      expect(response.data.parameters.limit.required).toBe(false);
      expect(response.data.parameters.limit).toHaveProperty('default');
    }
  });

  test('should return 404 for unknown template', async ({ apiClient }) => {
    const response = await apiClient.get(
      '/api/v1/agent/templates/unknown_template_xyz',
    );

    expect(response.status).toBe(404);
  });

  test('should register custom template @integration', async ({ apiClient }) => {
    const templateId = `test_template_${Date.now()}`;

    const response = await apiClient.post('/api/v1/agent/templates', {
      template_id: templateId,
      name: 'Test Template',
      description: 'Custom template for testing',
      steps: [
        {
          skill: 'search',
          input: {
            query: '{{ query }}',
          },
        },
      ],
      parameters: {
        query: {
          type: 'string',
          required: true,
          description: 'Search query',
        },
      },
    });

    expect(response.status).toBeLessThan(300);
    expect(response.data.status).toBe('success');
    expect(response.data.template_id).toBe(templateId);
  });

  test('should retrieve registered custom template @integration', async ({ apiClient }) => {
    const templateId = `test_retrieve_${Date.now()}`;

    // Register template
    await apiClient.post('/api/v1/agent/templates', {
      template_id: templateId,
      name: 'Retrievable Template',
      description: 'For retrieval testing',
      steps: [{ skill: 'search', input: { query: 'test' } }],
      parameters: { query: { type: 'string', required: true } },
    });

    // Retrieve it
    const getResponse = await apiClient.get(`/api/v1/agent/templates/${templateId}`);

    expect(getResponse.status).toBe(200);
    expect(getResponse.data.id).toBe(templateId);
    expect(getResponse.data.name).toBe('Retrievable Template');
  });

  test('should have category for each template', async ({ apiClient }) => {
    const response = await apiClient.get('/api/v1/agent/templates');

    response.data.templates.forEach((template: any) => {
      expect(template.category).toBeDefined();
      expect(['search', 'analysis', 'reporting', 'custom']).toContain(
        template.category,
      );
    });
  });

  test('should have step_count greater than 0', async ({ apiClient }) => {
    const response = await apiClient.get('/api/v1/agent/templates');

    response.data.templates.forEach((template: any) => {
      expect(template.step_count).toBeGreaterThan(0);
    });
  });
});
