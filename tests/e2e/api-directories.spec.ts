// File: tests/e2e/api-directories.spec.ts
// Description: Playwright API tests for Directories endpoints
// Author: Libor Ballaty <libor@arionetworks.com>
// Created: 2026-01-07

import { test, expect } from '@playwright/test';
import axios from 'axios';

const API_BASE_URL = 'http://localhost:3003';
const api = axios.create({ baseURL: API_BASE_URL });

test.describe('Directories API @api @directories', () => {
  let testDirectoryId: number;
  let testDirectoryPath: string = '/tmp/test_playwright_dir';

  test.beforeAll(async () => {
    // Create test directory on filesystem
    const { execSync } = require('child_process');
    try {
      execSync(`mkdir -p ${testDirectoryPath}`);
    } catch (e) {
      // Directory might already exist
    }
  });

  test.afterAll(async () => {
    // Clean up test directory from API
    if (testDirectoryId) {
      try {
        await api.delete(`/directories/${testDirectoryId}`);
      } catch (e) {
        // Might already be deleted
      }
    }
  });

  // SMOKE TESTS
  test('@smoke @fast: GET /directories returns list', async () => {
    const response = await api.get('/directories');

    expect(response.status).toBe(200);
    expect(Array.isArray(response.data)).toBeTruthy();

    if (response.data.length > 0) {
      const dir = response.data[0];
      expect(dir).toHaveProperty('id');
      expect(dir).toHaveProperty('path');
      expect(dir).toHaveProperty('name');
      expect(dir).toHaveProperty('enabled');
      expect(dir).toHaveProperty('priority');
    }
  });

  test('@smoke @fast: GET /directories?enabled_only=true filters correctly', async () => {
    const allResponse = await api.get('/directories');
    const enabledResponse = await api.get('/directories?enabled_only=true');

    expect(enabledResponse.status).toBe(200);
    expect(Array.isArray(enabledResponse.data)).toBeTruthy();

    // All enabled directories should have enabled=true
    enabledResponse.data.forEach((dir: any) => {
      expect(dir.enabled).toBe(true);
    });

    // Enabled count should be <= total count
    expect(enabledResponse.data.length).toBeLessThanOrEqual(allResponse.data.length);
  });

  // CREATE TESTS
  test('@fast @directories: POST /directories creates directory', async () => {
    const response = await api.post('/directories', {
      path: testDirectoryPath,
      name: 'Playwright Test Directory',
      enabled: true,
      priority: 100,
      notes: 'Created by Playwright test suite',
    });

    expect(response.status).toBe(200);
    expect(response.data).toHaveProperty('id');
    expect(response.data.path).toContain('test_playwright_dir');
    expect(response.data.name).toBe('Playwright Test Directory');
    expect(response.data.enabled).toBe(true);
    expect(response.data.priority).toBe(100);

    testDirectoryId = response.data.id;
  });

  test('@fast @directories: POST /directories with invalid path returns 400', async () => {
    try {
      await api.post('/directories', {
        path: '/nonexistent/path/does/not/exist/12345',
        name: 'Should Fail',
        enabled: true,
      });

      // Should not reach here
      expect(true).toBe(false);
    } catch (error: any) {
      expect(error.response.status).toBe(400);
      expect(error.response.data.detail).toContain('does not exist');
    }
  });

  test('@fast @directories: POST /directories with file path returns 400', async () => {
    try {
      // Create a test file
      const { execSync } = require('child_process');
      const testFile = '/tmp/playwright_test_file.txt';
      execSync(`touch ${testFile}`);

      await api.post('/directories', {
        path: testFile,
        name: 'Should Fail',
        enabled: true,
      });

      expect(true).toBe(false);
    } catch (error: any) {
      expect(error.response.status).toBe(400);
      expect(error.response.data.detail).toContain('not a directory');
    }
  });

  // READ TESTS
  test('@fast @directories: GET /directories/{id} retrieves specific directory', async () => {
    // First create a directory
    const createResponse = await api.post('/directories', {
      path: '/tmp/test_get_dir',
      name: 'Get Test Directory',
      enabled: true,
      priority: 50,
    });

    const dirId = createResponse.data.id;

    // Now retrieve it
    const getResponse = await api.get(`/directories/${dirId}`);

    expect(getResponse.status).toBe(200);
    expect(getResponse.data.id).toBe(dirId);
    expect(getResponse.data.name).toBe('Get Test Directory');
    expect(getResponse.data.priority).toBe(50);

    // Clean up
    await api.delete(`/directories/${dirId}`);
  });

  test('@fast @directories: GET /directories/{id} with invalid id returns 404', async () => {
    try {
      await api.get('/directories/999999');
      expect(true).toBe(false);
    } catch (error: any) {
      expect(error.response.status).toBe(404);
    }
  });

  // UPDATE TESTS
  test('@integration @directories: PATCH /directories/{id} updates directory', async () => {
    // Create initial directory
    const createResponse = await api.post('/directories', {
      path: '/tmp/test_patch_dir',
      name: 'Original Name',
      enabled: true,
      priority: 10,
      notes: 'Original notes',
    });

    const dirId = createResponse.data.id;

    // Update it
    const updateResponse = await api.patch(`/directories/${dirId}`, {
      path: '/tmp/test_patch_dir',
      name: 'Updated Name',
      enabled: false,
      priority: 20,
      notes: 'Updated notes',
    });

    expect(updateResponse.status).toBe(200);
    expect(updateResponse.data.name).toBe('Updated Name');
    expect(updateResponse.data.enabled).toBe(false);
    expect(updateResponse.data.priority).toBe(20);
    expect(updateResponse.data.notes).toBe('Updated notes');

    // Verify update persisted
    const getResponse = await api.get(`/directories/${dirId}`);
    expect(getResponse.data.name).toBe('Updated Name');

    // Clean up
    await api.delete(`/directories/${dirId}`);
  });

  test('@fast @directories: PATCH /directories/{id} requires path field', async () => {
    // Create directory
    const createResponse = await api.post('/directories', {
      path: '/tmp/test_patch_required_dir',
      name: 'Test',
      enabled: true,
    });

    const dirId = createResponse.data.id;

    try {
      // Try to update without path
      await api.patch(`/directories/${dirId}`, {
        name: 'Updated',
        // Missing path
      });

      expect(true).toBe(false);
    } catch (error: any) {
      expect(error.response.status).toBe(422);
      expect(error.response.data.detail).toBeTruthy();
    }

    // Clean up
    await api.delete(`/directories/${dirId}`);
  });

  // DELETE TESTS
  test('@integration @directories: DELETE /directories/{id} removes directory', async () => {
    // Create directory
    const createResponse = await api.post('/directories', {
      path: '/tmp/test_delete_dir',
      name: 'To Delete',
      enabled: true,
    });

    const dirId = createResponse.data.id;

    // Delete it
    const deleteResponse = await api.delete(`/directories/${dirId}`);

    expect(deleteResponse.status).toBe(200);
    expect(deleteResponse.data.status).toBe('success');

    // Verify deletion
    try {
      await api.get(`/directories/${dirId}`);
      expect(true).toBe(false);
    } catch (error: any) {
      expect(error.response.status).toBe(404);
    }
  });

  test('@fast @directories: DELETE /directories/{id} with invalid id returns 404', async () => {
    try {
      await api.delete('/directories/999999');
      expect(true).toBe(false);
    } catch (error: any) {
      expect(error.response.status).toBe(404);
    }
  });

  // REINDEX TESTS
  test('@fast @directories: POST /directories/{id}/reindex triggers reindex', async () => {
    // Create directory
    const createResponse = await api.post('/directories', {
      path: '/tmp/test_reindex_dir',
      name: 'Reindex Test',
      enabled: true,
    });

    const dirId = createResponse.data.id;

    // Trigger reindex
    const reindexResponse = await api.post(
      `/directories/${dirId}/reindex`,
      {
        index_keyword: true,
        index_vector: true,
        full_rebuild: false,
      }
    );

    expect(reindexResponse.status).toBe(200);
    expect(reindexResponse.data.status).toBe('started');
    expect(reindexResponse.data.directory_id).toBe(dirId);

    // Clean up
    await api.delete(`/directories/${dirId}`);
  });

  test('@fast @directories: POST /directories/{id}/reindex with invalid id returns 404', async () => {
    try {
      await api.post('/directories/999999/reindex', {
        index_keyword: true,
        index_vector: true,
      });

      expect(true).toBe(false);
    } catch (error: any) {
      expect(error.response.status).toBe(404);
    }
  });

  // DISCOVERY TESTS
  test('@fast @directories: GET /directories/{id}/discover returns tree structure', async () => {
    // Create directory with subdirectories
    const { execSync } = require('child_process');
    const testDir = '/tmp/test_discover_dir';
    execSync(`mkdir -p ${testDir}/subdir1/subdir2`);

    const createResponse = await api.post('/directories', {
      path: testDir,
      name: 'Discovery Test',
      enabled: true,
    });

    const dirId = createResponse.data.id;

    // Get discovery
    const discoverResponse = await api.get(
      `/directories/${dirId}/discover?max_depth=2`
    );

    expect(discoverResponse.status).toBe(200);
    expect(discoverResponse.data).toHaveProperty('id');
    expect(discoverResponse.data).toHaveProperty('name');
    expect(discoverResponse.data).toHaveProperty('path');
    expect(discoverResponse.data).toHaveProperty('subdirectories');
    expect(Array.isArray(discoverResponse.data.subdirectories)).toBeTruthy();

    // Clean up
    await api.delete(`/directories/${dirId}`);
  });

  // DUPLICATE DETECTION
  test('@fast @directories: POST /directories with duplicate path returns 409', async () => {
    // Create first directory
    const createResponse1 = await api.post('/directories', {
      path: '/tmp/test_duplicate_dir',
      name: 'First',
      enabled: true,
    });

    const dirId1 = createResponse1.data.id;

    try {
      // Try to create with same path
      await api.post('/directories', {
        path: '/tmp/test_duplicate_dir',
        name: 'Second',
        enabled: true,
      });

      expect(true).toBe(false);
    } catch (error: any) {
      expect(error.response.status).toBe(409);
      expect(error.response.data.detail).toContain('already registered');
    }

    // Clean up
    await api.delete(`/directories/${dirId1}`);
  });

  // SORTING TESTS
  test('@integration @directories: Directory list sorted by priority', async () => {
    const response = await api.get('/directories');

    if (response.data.length > 1) {
      // Check sorting by priority (descending)
      for (let i = 0; i < response.data.length - 1; i++) {
        const current = response.data[i];
        const next = response.data[i + 1];

        // Priority should be >= next priority
        expect(current.priority).toBeGreaterThanOrEqual(next.priority);
      }
    }
  });

  // FIELD VALIDATION TESTS
  test('@fast @directories: Directory fields are properly formatted', async () => {
    const response = await api.get('/directories');

    if (response.data.length > 0) {
      const dir = response.data[0];

      // Check field types
      expect(typeof dir.id).toBe('number');
      expect(typeof dir.path).toBe('string');
      expect(typeof dir.name).toBe('string');
      expect(typeof dir.enabled).toBe('boolean');
      expect(typeof dir.priority).toBe('number');
      expect(typeof dir.created_at).toBe('number');
      expect(typeof dir.updated_at).toBe('number');

      // Check timestamp validity
      expect(dir.created_at).toBeGreaterThan(0);
      expect(dir.updated_at).toBeGreaterThan(0);
      expect(dir.updated_at).toBeGreaterThanOrEqual(dir.created_at);
    }
  });
});
