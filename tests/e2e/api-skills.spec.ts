// File: tests/e2e/api-skills.spec.ts
// Description: Skill discovery API tests
// Author: Libor Ballaty <libor@arionetworks.com>
// Created: 2026-01-07

import { test, expect } from './fixtures';

test.describe('API Skill Endpoints - @api @discovery @fast', () => {
  test('should list all skills', async ({ apiClient }) => {
    const response = await apiClient.get('/api/v1/agent/skills');

    expect(response.status).toBe(200);
    expect(response.data).toHaveProperty('total');
    expect(response.data).toHaveProperty('skills');
    expect(Array.isArray(response.data.skills)).toBe(true);
    expect(response.data.total).toBeGreaterThanOrEqual(5);
  });

  test('should have required fields in skill list', async ({ apiClient }) => {
    const response = await apiClient.get('/api/v1/agent/skills');

    response.data.skills.forEach((skill: any) => {
      expect(skill).toHaveProperty('name');
      expect(skill).toHaveProperty('description');
      expect(skill).toHaveProperty('input_schema');
      expect(skill).toHaveProperty('output_schema');
      expect(skill).toHaveProperty('required_config');
    });
  });

  test('should include all core skills', async ({ apiClient }) => {
    const response = await apiClient.get('/api/v1/agent/skills');

    const skillNames = response.data.skills.map((s: any) => s.name);
    expect(skillNames).toContain('search');
    expect(skillNames).toContain('code_analysis');
    expect(skillNames).toContain('report');
    expect(skillNames).toContain('llm');
    expect(skillNames).toContain('sql');
  });

  test('should get search skill info', async ({ apiClient }) => {
    const response = await apiClient.get('/api/v1/agent/skills/search');

    expect(response.status).toBe(200);
    expect(response.data.name).toBe('search');
    expect(response.data).toHaveProperty('description');
    expect(response.data).toHaveProperty('input_schema');
    expect(response.data).toHaveProperty('output_schema');
  });

  test('should have query parameter in search skill', async ({ apiClient }) => {
    const response = await apiClient.get('/api/v1/agent/skills/search');

    expect(response.data.input_schema).toHaveProperty('query');
    expect(response.data.input_schema.query.required).toBe(true);
  });

  test('should have results in search skill output', async ({ apiClient }) => {
    const response = await apiClient.get('/api/v1/agent/skills/search');

    expect(response.data.output_schema).toHaveProperty('results');
  });

  test('should get code_analysis skill info', async ({ apiClient }) => {
    const response = await apiClient.get('/api/v1/agent/skills/code_analysis');

    expect(response.status).toBe(200);
    expect(response.data.name).toBe('code_analysis');
    expect(response.data.input_schema).toHaveProperty('code');
    expect(response.data.input_schema.code.required).toBe(true);
  });

  test('should have language parameter in code_analysis', async ({ apiClient }) => {
    const response = await apiClient.get('/api/v1/agent/skills/code_analysis');

    expect(response.data.input_schema).toHaveProperty('language');
  });

  test('should get report skill info', async ({ apiClient }) => {
    const response = await apiClient.get('/api/v1/agent/skills/report');

    expect(response.status).toBe(200);
    expect(response.data.name).toBe('report');
    expect(response.data.input_schema).toHaveProperty('title');
    expect(response.data.input_schema).toHaveProperty('content');
  });

  test('should get llm skill info', async ({ apiClient }) => {
    const response = await apiClient.get('/api/v1/agent/skills/llm');

    expect(response.status).toBe(200);
    expect(response.data.name).toBe('llm');
    expect(response.data.input_schema).toHaveProperty('prompt');
  });

  test('should return 404 for unknown skill', async ({ apiClient }) => {
    const response = await apiClient.get(
      '/api/v1/agent/skills/unknown_skill_xyz',
    );

    expect(response.status).toBe(404);
  });

  test('should have valid input schemas', async ({ apiClient }) => {
    const response = await apiClient.get('/api/v1/agent/skills');

    response.data.skills.forEach((skill: any) => {
      expect(typeof skill.input_schema).toBe('object');
      expect(skill.input_schema).not.toBeNull();
    });
  });

  test('should have valid output schemas', async ({ apiClient }) => {
    const response = await apiClient.get('/api/v1/agent/skills');

    response.data.skills.forEach((skill: any) => {
      expect(typeof skill.output_schema).toBe('object');
      expect(skill.output_schema).not.toBeNull();
    });
  });

  test('should have required_config array', async ({ apiClient }) => {
    const response = await apiClient.get('/api/v1/agent/skills');

    response.data.skills.forEach((skill: any) => {
      expect(Array.isArray(skill.required_config)).toBe(true);
    });
  });

  test('should have non-empty descriptions', async ({ apiClient }) => {
    const response = await apiClient.get('/api/v1/agent/skills');

    response.data.skills.forEach((skill: any) => {
      expect(skill.description).toBeDefined();
      expect(skill.description.length).toBeGreaterThan(0);
    });
  });
});
