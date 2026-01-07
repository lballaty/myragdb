// File: tests/e2e/api-orchestrator.spec.ts
// Description: Orchestrator info and health check tests
// Author: Libor Ballaty <libor@arionetworks.com>
// Created: 2026-01-07

import { test, expect } from './fixtures';

test.describe('API Orchestrator Endpoints - @api @orchestrator @fast', () => {
  test('should return health status', async ({ apiClient }) => {
    const response = await apiClient.get('/api/v1/agent/health');

    expect(response.status).toBe(200);
    expect(response.data.status).toBe('healthy');
    expect(response.data).toHaveProperty('message');
  });

  test('should have operational message in health check', async ({ apiClient }) => {
    const response = await apiClient.get('/api/v1/agent/health');

    expect(response.data.message).toContain('operational');
  });

  test('should return orchestrator info', async ({ apiClient }) => {
    const response = await apiClient.get('/api/v1/agent/info');

    expect(response.status).toBe(200);
    expect(response.data).toHaveProperty('total_skills');
    expect(response.data).toHaveProperty('total_templates');
    expect(response.data).toHaveProperty('available_skills');
    expect(response.data).toHaveProperty('available_templates');
  });

  test('should have correct skill count', async ({ apiClient }) => {
    const response = await apiClient.get('/api/v1/agent/info');

    expect(response.data.total_skills).toBeGreaterThanOrEqual(5);
    expect(response.data.available_skills.length).toBe(response.data.total_skills);
  });

  test('should have correct template count', async ({ apiClient }) => {
    const response = await apiClient.get('/api/v1/agent/info');

    expect(response.data.total_templates).toBeGreaterThanOrEqual(3);
    expect(response.data.available_templates.length).toBe(
      response.data.total_templates,
    );
  });

  test('should list core skills in available_skills', async ({ apiClient }) => {
    const response = await apiClient.get('/api/v1/agent/info');

    expect(response.data.available_skills).toContain('search');
    expect(response.data.available_skills).toContain('code_analysis');
    expect(response.data.available_skills).toContain('report');
    expect(response.data.available_skills).toContain('llm');
    expect(response.data.available_skills).toContain('sql');
  });

  test('should list core templates in available_templates', async ({ apiClient }) => {
    const response = await apiClient.get('/api/v1/agent/info');

    expect(response.data.available_templates).toContain('code_search');
    expect(response.data.available_templates).toContain('code_analysis');
    expect(response.data.available_templates).toContain('code_review');
  });

  test('should indicate session manager availability', async ({ apiClient }) => {
    const response = await apiClient.get('/api/v1/agent/info');

    expect(response.data).toHaveProperty('has_session_manager');
    expect(typeof response.data.has_session_manager).toBe('boolean');
  });

  test('should indicate search engine availability', async ({ apiClient }) => {
    const response = await apiClient.get('/api/v1/agent/info');

    expect(response.data).toHaveProperty('has_search_engine');
    expect(typeof response.data.has_search_engine).toBe('boolean');
  });

  test('should have consistent skill counts', async ({ apiClient }) => {
    const response = await apiClient.get('/api/v1/agent/info');

    const expectedCount = response.data.total_skills;
    expect(response.data.available_skills.length).toBe(expectedCount);
  });

  test('should have consistent template counts', async ({ apiClient }) => {
    const response = await apiClient.get('/api/v1/agent/info');

    const expectedCount = response.data.total_templates;
    expect(response.data.available_templates.length).toBe(expectedCount);
  });

  test('should match skill list with available skills', async ({ apiClient }) => {
    const infoResponse = await apiClient.get('/api/v1/agent/info');
    const skillsResponse = await apiClient.get('/api/v1/agent/skills');

    const infoSkillNames = infoResponse.data.available_skills.sort();
    const listSkillNames = skillsResponse.data.skills
      .map((s: any) => s.name)
      .sort();

    expect(infoSkillNames).toEqual(listSkillNames);
  });

  test('should match template list with available templates', async ({ apiClient }) => {
    const infoResponse = await apiClient.get('/api/v1/agent/info');
    const templatesResponse = await apiClient.get('/api/v1/agent/templates');

    const infoTemplateIds = infoResponse.data.available_templates.sort();
    const listTemplateIds = templatesResponse.data.templates
      .map((t: any) => t.id)
      .sort();

    expect(infoTemplateIds).toEqual(listTemplateIds);
  });
});
