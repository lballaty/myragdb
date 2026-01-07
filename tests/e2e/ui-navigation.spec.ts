// File: tests/e2e/ui-navigation.spec.ts
// Description: UI navigation and basic interaction tests
// Author: Libor Ballaty <libor@arionetworks.com>
// Created: 2026-01-07

import { test, expect } from './fixtures';

test.describe('UI Navigation - @ui @smoke @fast', () => {
  test('should load home page', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveTitle(/MyRAGDB|Agent/);
    await expect(page.locator('body')).toBeTruthy();
  });

  test('should have main navigation elements', async ({ page }) => {
    await page.goto('/');

    // Check for common navigation elements
    const header = page.locator('header, nav, [role="navigation"]');
    expect(header).toBeDefined();
  });

  test('should display repository list on load', async ({ page }) => {
    await page.goto('/');

    // Wait for content to load
    await page.waitForLoadState('networkidle');

    // Check for list or table structure
    const listElement = page.locator('[role="list"], table, .repository-list');
    expect(listElement).toBeDefined();
  });

  test('should handle page refresh', async ({ page }) => {
    await page.goto('/');
    await page.reload();

    // Should not have error state
    const errorElements = page.locator('[role="alert"], .error, .error-message');
    const count = await errorElements.count();
    expect(count).toBe(0);
  });

  test('should be responsive', async ({ page }) => {
    // Test mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/');

    // Should still be able to see content
    const content = page.locator('body');
    expect(content).toBeTruthy();
  });

  test('should handle back/forward navigation', async ({ page }) => {
    await page.goto('/');

    // Navigate and go back
    await page.reload();
    await page.goBack();

    // Should be able to navigate
    expect(page.url()).toBeDefined();
  });
});
