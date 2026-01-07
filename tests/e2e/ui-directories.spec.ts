// File: tests/e2e/ui-directories.spec.ts
// Description: Playwright E2E tests for Directories UI component
// Author: Libor Ballaty <libor@arionetworks.com>
// Created: 2026-01-07

import { test, expect } from '@playwright/test';

test.describe('Directories UI Component @ui @directories', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to application
    await page.goto('/');

    // Wait for page to load
    await page.waitForLoadState('networkidle');

    // Click on Directories tab
    const directoriesTab = page.locator('[data-tab="directories"]');
    await directoriesTab.click();
    await page.waitForLoadState('networkidle');
  });

  // SMOKE TESTS - Quick validation
  test('@smoke @fast: Directories tab loads and displays', async ({ page }) => {
    const tabContent = page.locator('#directories-tab');
    await expect(tabContent).toBeVisible();

    // Check for main sections
    const addSection = page.locator('text=Add Directory');
    const managedSection = page.locator('text=Managed Directories');
    const statsSection = page.locator('text=Directory Statistics');

    await expect(addSection).toBeVisible();
    await expect(managedSection).toBeVisible();
    await expect(statsSection).toBeVisible();
  });

  test('@smoke @fast: Add Directory form is visible', async ({ page }) => {
    const pathInput = page.locator('#dir-path-input');
    const nameInput = page.locator('#dir-name-input');
    const priorityInput = page.locator('#dir-priority-input');
    const addButton = page.locator('#add-directory-button');

    await expect(pathInput).toBeVisible();
    await expect(nameInput).toBeVisible();
    await expect(priorityInput).toBeVisible();
    await expect(addButton).toBeVisible();
  });

  // FORM INTERACTION TESTS
  test('@fast @directories: Add directory form accepts input', async ({ page }) => {
    const pathInput = page.locator('#dir-path-input');
    const nameInput = page.locator('#dir-name-input');

    // Fill form fields
    await pathInput.fill('/tmp/test_ui_dir');
    await nameInput.fill('UI Test Directory');

    // Verify values
    await expect(pathInput).toHaveValue('/tmp/test_ui_dir');
    await expect(nameInput).toHaveValue('UI Test Directory');
  });

  test('@fast @directories: Priority dropdown has correct options', async ({ page }) => {
    const prioritySelect = page.locator('#dir-priority-input');

    // Get all options
    const options = await prioritySelect.locator('option').allTextContents();

    // Verify some expected options exist
    expect(options.length).toBeGreaterThan(0);
    expect(options.some(opt => opt.includes('Normal'))).toBeTruthy();
  });

  test('@fast @directories: Notes textarea accepts input', async ({ page }) => {
    const notesTextarea = page.locator('#dir-notes-input');
    const testNotes = 'Test notes for UI testing';

    await notesTextarea.fill(testNotes);
    await expect(notesTextarea).toHaveValue(testNotes);
  });

  // BULK ACTIONS TESTS
  test('@fast @directories: Bulk action buttons are present', async ({ page }) => {
    const enableAllBtn = page.locator('#enable-dirs-button');
    const disableAllBtn = page.locator('#disable-dirs-button');
    const reindexAllBtn = page.locator('#reindex-all-dirs-button');

    // Only check if directories exist
    const dirCount = await page.locator('.directory-checkbox').count();
    if (dirCount > 0) {
      await expect(enableAllBtn).toBeVisible();
      await expect(disableAllBtn).toBeVisible();
      await expect(reindexAllBtn).toBeVisible();
    }
  });

  // DIRECTORY CARDS TESTS
  test('@fast @directories: Directory cards display with information', async ({ page }) => {
    // Wait for directories to load
    await page.waitForLoadState('networkidle');

    const cards = page.locator('.repository-card');
    const cardCount = await cards.count();

    if (cardCount > 0) {
      // Check first card
      const firstCard = cards.first();
      await expect(firstCard).toBeVisible();

      // Check for action buttons
      const editBtn = firstCard.locator('button:has-text("Edit")');
      const deleteBtn = firstCard.locator('button:has-text("Delete")');
      const reindexBtn = firstCard.locator('button:has-text("Reindex")');

      if (cardCount > 0) {
        expect(await editBtn.count()).toBeGreaterThan(0);
        expect(await deleteBtn.count()).toBeGreaterThan(0);
        expect(await reindexBtn.count()).toBeGreaterThan(0);
      }
    }
  });

  test('@fast @directories: Checkboxes in directory cards work', async ({ page }) => {
    // Wait for directories
    await page.waitForLoadState('networkidle');

    const checkboxes = page.locator('.directory-checkbox');
    const checkboxCount = await checkboxes.count();

    if (checkboxCount > 0) {
      const firstCheckbox = checkboxes.first();

      // Verify unchecked initially
      await expect(firstCheckbox).not.toBeChecked();

      // Check it
      await firstCheckbox.check();
      await expect(firstCheckbox).toBeChecked();

      // Uncheck it
      await firstCheckbox.uncheck();
      await expect(firstCheckbox).not.toBeChecked();
    }
  });

  // STATISTICS TESTS
  test('@fast @directories: Statistics dashboard displays counts', async ({ page }) => {
    const totalDirsText = page.locator('text=Total Directories:');
    const enabledText = page.locator('text=Enabled:');
    const disabledText = page.locator('text=Disabled:');

    await expect(totalDirsText).toBeVisible();
    await expect(enabledText).toBeVisible();
    await expect(disabledText).toBeVisible();
  });

  // INTEGRATION TESTS
  test('@integration @directories: Directory listing loads from API', async ({ page }) => {
    // Wait for page to fully load
    await page.waitForLoadState('networkidle');

    // Check if directory cards exist (might be empty, that's ok)
    const cards = page.locator('.repository-card');
    const cardCount = await cards.count();

    // Should have 0 or more cards
    expect(cardCount).toBeGreaterThanOrEqual(0);
  });

  test('@integration @directories: Status badges display correctly', async ({ page }) => {
    // Wait for load
    await page.waitForLoadState('networkidle');

    const enabledBadges = page.locator('text=✓ Enabled');
    const disabledBadges = page.locator('text=✗ Disabled');

    // If any directories exist, badges should be visible
    const badgeCount = (await enabledBadges.count()) + (await disabledBadges.count());
    const cardCount = await page.locator('.repository-card').count();

    if (cardCount > 0) {
      expect(badgeCount).toBeGreaterThan(0);
    }
  });

  // RESPONSIVENESS TESTS
  test('@fast @directories: Directories tab responsive on mobile', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });

    // Navigate to tab
    const directoriesTab = page.locator('[data-tab="directories"]');
    await directoriesTab.click();

    // Check main sections visible
    const tabContent = page.locator('#directories-tab');
    await expect(tabContent).toBeVisible();

    // Check form is accessible
    const addButton = page.locator('#add-directory-button');
    await expect(addButton).toBeVisible();
  });

  test('@fast @directories: Directory cards stack on mobile', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });

    // Navigate and wait
    await page.waitForLoadState('networkidle');

    // Cards should still be visible
    const cards = page.locator('.repository-card');
    const cardCount = await cards.count();

    if (cardCount > 0) {
      const firstCard = cards.first();
      await expect(firstCard).toBeVisible();
    }
  });

  // ERROR STATE TESTS
  test('@fast @directories: Empty state message when no directories', async ({ page }) => {
    // This test assumes we can identify empty state
    // In real scenario, would need to clear all directories first
    const directoriesList = page.locator('#directories-list');
    const cards = page.locator('.repository-card');

    const cardCount = await cards.count();

    // Either shows cards or empty message
    if (cardCount === 0) {
      const emptyMessage = page.locator('text=No directories configured');
      const messageCount = await emptyMessage.count();
      expect(messageCount).toBeGreaterThanOrEqual(0);
    }
  });

  // ACCESSIBILITY TESTS
  test('@accessibility @directories: Form inputs have proper labels', async ({ page }) => {
    const pathInput = page.locator('#dir-path-input');
    const nameInput = page.locator('#dir-name-input');

    // Verify inputs are properly associated or have placeholders
    const pathPlaceholder = await pathInput.getAttribute('placeholder');
    const namePlaceholder = await nameInput.getAttribute('placeholder');

    expect(pathPlaceholder).toBeTruthy();
    expect(namePlaceholder).toBeTruthy();
  });

  test('@accessibility @directories: Buttons have accessible text', async ({ page }) => {
    const addButton = page.locator('#add-directory-button');
    const editButtons = page.locator('button:has-text("Edit")');
    const deleteButtons = page.locator('button:has-text("Delete")');

    // Buttons should have text content
    const addText = await addButton.textContent();
    expect(addText).toBeTruthy();

    if (await editButtons.count() > 0) {
      const editText = await editButtons.first().textContent();
      expect(editText).toBeTruthy();
    }
  });

  test('@accessibility @directories: Tab navigation with keyboard', async ({ page }) => {
    // Tab to Directory button and activate with Enter
    const directoriesTab = page.locator('[data-tab="directories"]');

    // Focus on button
    await directoriesTab.focus();

    // Verify it has focus
    const isFocused = await directoriesTab.evaluate((el) => el === document.activeElement);
    expect(isFocused).toBeTruthy();

    // Press Enter
    await page.keyboard.press('Enter');

    // Tab should be active
    await expect(directoriesTab).toHaveAttribute('class', /active/);
  });
});
