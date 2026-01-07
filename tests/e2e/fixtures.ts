// File: tests/e2e/fixtures.ts
// Description: Shared fixtures for E2E and API tests
// Author: Libor Ballaty <libor@arionetworks.com>
// Created: 2026-01-07

import { test as base, Page } from '@playwright/test';
import axios, { AxiosInstance } from 'axios';

export type TestFixtures = {
  apiClient: AxiosInstance;
  apiBaseURL: string;
  uiBaseURL: string;
};

export const test = base.extend<TestFixtures>({
  apiBaseURL: 'http://localhost:3002',
  uiBaseURL: 'http://localhost:3003',

  apiClient: async ({ apiBaseURL }, use) => {
    const client = axios.create({
      baseURL: apiBaseURL,
      validateStatus: () => true, // Don't throw on any status
    });

    await use(client);
  },
});

export { expect } from '@playwright/test';
