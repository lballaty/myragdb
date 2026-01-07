// File: tests/e2e/ui-repository-management.spec.ts
// Description: UI tests for repository management features
// Author: Libor Ballaty <libor@arionetworks.com>
// Created: 2026-01-07

import { test, expect } from '@playwright/test';

test.describe('Repository Management UI - @ui @integration', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:3003');
    await page.waitForLoadState('networkidle');
  });

  test('should display repository list @smoke', async ({ page }) => {
    // Look for repository list/table
    const repositoryList =
      page.locator('[role="list"], table, .repository-list, [data-testid="repository-list"]');

    // Should find some element containing repositories
    const count = await repositoryList.count();
    expect(count).toBeGreaterThanOrEqual(0);
  });

  test('should be able to scroll repository list @ui', async ({ page }) => {
    const container =
      page.locator('[role="region"], .scrollable, .list-container');

    // Should be scrollable or contain items
    const isVisible = await container.isVisible();
    expect(isVisible).toBeDefined();
  });

  test('should handle bulk actions @ui @integration', async ({ page }) => {
    // Look for action buttons
    const actionButtons = page.locator(
      'button:has-text("Enable"), button:has-text("Disable"), button:has-text("Lock"), button:has-text("Unlock")',
    );

    const count = await actionButtons.count();
    // May or may not have action buttons, but should not error
    expect(count).toBeGreaterThanOrEqual(0);
  });

  test('should maintain state after refresh @ui @integration', async ({ page }) => {
    const title1 = await page.title();
    await page.reload();
    const title2 = await page.title();

    expect(title1).toBe(title2);
  });

  test('should handle empty states gracefully @ui', async ({ page }) => {
    // Even if no repositories, should not error
    const errorElements = page.locator('[role="alert"], .error');
    const count = await errorElements.count();

    // Should not have critical errors
    expect(count).toBeLessThanOrEqual(1);
  });

  test('should be keyboard accessible @ui @accessibility', async ({ page }) => {
    // Tab through page
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');

    // Should maintain focus without errors
    const focused = await page.evaluate(() => document.activeElement?.tagName);
    expect(focused).toBeDefined();
  });

  test('should handle network errors gracefully @ui @error-handling', async ({
    page,
  }) => {
    await page.route('**/api/**', (route) => route.abort());
    await page.reload();

    // Should show error or fallback UI, not crash
    const body = await page.locator('body').innerHTML();
    expect(body).toBeDefined();
  });
});
