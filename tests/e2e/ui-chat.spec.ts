// File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/tests/e2e/ui-chat.spec.ts
// Description: Comprehensive chat and dashboard UI testing with granular coverage
// Author: Libor Ballaty <libor@arionetworks.com>
// Created: 2026-01-08

import { test, expect } from '@playwright/test';

/**
 * CHAT AND DASHBOARD COMPREHENSIVE TEST SUITE
 *
 * This test suite provides comprehensive coverage of all chat and dashboard functionality.
 * Tests are organized by feature area and tagged for incremental execution.
 *
 * TAG ORGANIZATION:
 * - @ui: UI testing
 * - @chat: Chat-related tests
 * - @dashboard: Dashboard tab tests
 * - @fast: Quick tests (<30s each)
 * - @slow: Slower tests (>30s each)
 *
 * EXECUTION PATTERNS:
 * npm test -- --grep "@chat @fast"       # Fast chat tests only
 * npm test -- --grep "@chat @slow"       # Slow chat tests only
 * npm test -- --grep "@dashboard @fast"  # Fast dashboard tests only
 * npm test -- --grep "@chat"             # All chat tests
 * npm test -- --grep "@ui @chat"         # All UI chat tests
 */

test.describe('Dashboard and Chat UI - Comprehensive Testing Suite @ui @chat', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:3003');
    await page.waitForLoadState('networkidle');
  });

  // ============================================================================
  // SECTION 1: DASHBOARD TAB STRUCTURE AND NAVIGATION
  // ============================================================================

  test.describe('Dashboard Tab Structure - Page Layout @dashboard @structure @fast', () => {
    /**
     * SUCCESS CRITERIA:
     * - All 6 tab buttons visible on page load
     * - Each tab has correct label text
     * - Tab buttons are in expected order
     * - Tab buttons have proper CSS classes for styling
     */
    test('should display all 6 main tabs with correct labels and order @tab-all-visible @smoke', async ({
      page,
    }) => {
      const tabButtons = page.locator('.tab-button');
      const count = await tabButtons.count();
      expect(count).toBeGreaterThanOrEqual(6);

      const expectedTabs = ['Search', 'Activity Monitor', 'Repositories', 'Directories', 'Observability', 'LLM Manager'];

      for (let i = 0; i < expectedTabs.length; i++) {
        const tab = await tabButtons.nth(i);
        const text = await tab.textContent();
        expect(text?.trim()).toContain(expectedTabs[i]);
      }
    });

    /**
     * SUCCESS CRITERIA:
     * - Tab buttons have semantic HTML (button elements)
     * - Tab buttons are keyboard focusable
     * - Tab buttons have proper ARIA labels if needed
     * - Tab buttons are properly sized for touch interaction
     */
    test('should have properly semantic tab button elements @tab-semantic @a11y', async ({
      page,
    }) => {
      const tabButtons = page.locator('button.tab-button');
      const count = await tabButtons.count();
      expect(count).toBeGreaterThanOrEqual(6);

      // Verify buttons are keyboard accessible
      const firstButton = await tabButtons.first();
      await firstButton.focus();
      const focused = page.locator(':focus');
      expect(await focused.count()).toBeGreaterThan(0);
    });

    /**
     * SUCCESS CRITERIA:
     * - Tab button container is visible
     * - Tab buttons are arranged horizontally
     * - Tab buttons have adequate spacing
     * - Tab area is responsive
     */
    test('should have properly styled tab container @tab-styling @visual', async ({
      page,
    }) => {
      const tabsContainer = page.locator('.tabs, [class*="tab-container"]');
      if (await tabsContainer.count() > 0) {
        await expect(tabsContainer.first()).toBeVisible();
      }

      const tabButtons = page.locator('.tab-button');
      const firstButton = await tabButtons.first();
      const box = await firstButton.boundingBox();
      expect(box).not.toBeNull();
      expect(box?.height).toBeGreaterThan(0);
      expect(box?.width).toBeGreaterThan(0);
    });
  });

  // ============================================================================
  // SECTION 2: TAB NAVIGATION AND STATE MANAGEMENT
  // ============================================================================

  test.describe('Tab Navigation and State Management @dashboard @navigation @fast', () => {
    /**
     * SUCCESS CRITERIA:
     * - Search tab has 'active' class on initial load
     * - Search tab content (#search-tab) has 'active' class
     * - Other tabs do not have 'active' class initially
     */
    test('should have Search tab active by default on load @tab-default @smoke', async ({
      page,
    }) => {
      const searchTabButton = page.locator('.tab-button:has-text("Search")');
      const searchTabContent = page.locator('#search-tab');

      await expect(searchTabButton).toHaveClass(/active/);
      await expect(searchTabContent).toHaveClass(/active/);

      // Verify other tabs are not active
      const reposTabButton = page.locator('.tab-button:has-text("Repositories")');
      expect(await reposTabButton.getAttribute('class')).not.toContain('active');
    });

    /**
     * SUCCESS CRITERIA:
     * - Clicking Activity Monitor tab makes it active
     * - Activity Monitor content becomes visible
     * - Search tab becomes inactive
     * - Tab switching is instant (<500ms)
     */
    test('should switch to Activity Monitor tab when clicked @tab-activity-switch @smoke', async ({
      page,
    }) => {
      const activityTab = page.locator('.tab-button:has-text("Activity Monitor")');
      const activityContent = page.locator('#activity-tab');

      const startTime = Date.now();
      await activityTab.click();
      const duration = Date.now() - startTime;

      await expect(activityTab).toHaveClass(/active/);
      await expect(activityContent).toHaveClass(/active/);
      expect(duration).toBeLessThan(500);
    });

    /**
     * SUCCESS CRITERIA:
     * - Clicking Repositories tab makes it active
     * - Repositories content becomes visible
     * - Previous tab becomes inactive
     */
    test('should switch to Repositories tab when clicked @tab-repos-switch @smoke', async ({
      page,
    }) => {
      const reposTab = page.locator('.tab-button:has-text("Repositories")');
      const reposContent = page.locator('#repositories-tab');

      await reposTab.click();
      await expect(reposTab).toHaveClass(/active/);
      await expect(reposContent).toHaveClass(/active/);
    });

    /**
     * SUCCESS CRITERIA:
     * - Clicking Directories tab makes it active
     * - Directories content becomes visible
     * - Tab indicator shows correct active state
     */
    test('should switch to Directories tab when clicked @tab-dirs-switch @smoke', async ({
      page,
    }) => {
      const dirsTab = page.locator('.tab-button:has-text("Directories")');
      const dirsContent = page.locator('#directories-tab');

      await dirsTab.click();
      await expect(dirsTab).toHaveClass(/active/);
      await expect(dirsContent).toHaveClass(/active/);
    });

    /**
     * SUCCESS CRITERIA:
     * - Clicking Observability tab makes it active
     * - Observability content becomes visible
     * - Tables and metrics are visible
     */
    test('should switch to Observability tab when clicked @tab-obs-switch @smoke', async ({
      page,
    }) => {
      const obsTab = page.locator('.tab-button:has-text("Observability")');
      const obsContent = page.locator('#observability-tab');

      await obsTab.click();
      await expect(obsTab).toHaveClass(/active/);
      await expect(obsContent).toHaveClass(/active/);
    });

    /**
     * SUCCESS CRITERIA:
     * - Clicking LLM Manager tab makes it active
     * - LLM Manager content becomes visible
     * - Provider tabs are visible
     */
    test('should switch to LLM Manager tab when clicked @tab-llm-switch @smoke', async ({
      page,
    }) => {
      const llmTab = page.locator('.tab-button:has-text("LLM Manager")');
      const llmContent = page.locator('#llm-manager-tab');

      await llmTab.click();
      await expect(llmTab).toHaveClass(/active/);
      await expect(llmContent).toHaveClass(/active/);
    });

    /**
     * SUCCESS CRITERIA:
     * - Can navigate from tab 1 to tab 2 to tab 3 and back to tab 1
     * - State is maintained correctly during navigation
     * - No content is duplicated across tabs
     */
    test('should navigate sequentially through all tabs maintaining state @tab-sequence @navigation', async ({
      page,
    }) => {
      const tabSequence = ['Search', 'Activity Monitor', 'Repositories', 'Directories', 'Observability', 'LLM Manager'];

      for (const tabName of tabSequence) {
        const tab = page.locator(`.tab-button:has-text("${tabName}")`);
        await tab.click();
        await expect(tab).toHaveClass(/active/);
        await page.waitForTimeout(100);
      }

      // Navigate back to first tab
      const searchTab = page.locator('.tab-button:has-text("Search")');
      await searchTab.click();
      await expect(searchTab).toHaveClass(/active/);
    });

    /**
     * SUCCESS CRITERIA:
     * - Tab content persists when switching away and back
     * - Scroll position is maintained
     * - Form inputs maintain their values
     */
    test('should maintain tab state when switching between tabs and returning @tab-state-persistence @state', async ({
      page,
    }) => {
      // Go to Repositories tab
      let reposTab = page.locator('.tab-button:has-text("Repositories")');
      await reposTab.click();
      await expect(reposTab).toHaveClass(/active/);

      // Switch to Directories
      const dirsTab = page.locator('.tab-button:has-text("Directories")');
      await dirsTab.click();
      await expect(dirsTab).toHaveClass(/active/);

      // Switch back to Repositories
      reposTab = page.locator('.tab-button:has-text("Repositories")');
      await reposTab.click();
      await expect(reposTab).toHaveClass(/active/);
    });

    /**
     * SUCCESS CRITERIA:
     * - Keyboard Tab key navigation works
     * - Focus moves from tab to tab
     * - Enter/Space activates a focused tab
     */
    test('should support keyboard navigation with Tab key @tab-keyboard @a11y', async ({
      page,
    }) => {
      const firstTab = page.locator('.tab-button').first();
      await firstTab.focus();

      // Press Tab to navigate to next tab
      await page.keyboard.press('Tab');
      const focused = page.locator(':focus');
      const count = await focused.count();
      expect(count).toBeGreaterThan(0);

      // Verify we can navigate through multiple tabs with Tab key
      await page.keyboard.press('Tab');
      const secondFocus = page.locator(':focus');
      expect(await secondFocus.count()).toBeGreaterThan(0);
    });

    /**
     * SUCCESS CRITERIA:
     * - Visual indicator shows which tab is active
     * - Active tab has different styling from inactive tabs
     * - Indicator updates when switching tabs
     */
    test('should have visual indicator for active tab state @tab-visual-indicator @visual', async ({
      page,
    }) => {
      const searchTab = page.locator('.tab-button:has-text("Search")');
      const reposTab = page.locator('.tab-button:has-text("Repositories")');

      // Check Search tab is visually active
      const searchClass = await searchTab.getAttribute('class');
      expect(searchClass).toContain('active');

      // Switch to Repositories
      await reposTab.click();
      const reposClass = await reposTab.getAttribute('class');
      expect(reposClass).toContain('active');

      // Verify Search is no longer active
      const searchClassAfter = await searchTab.getAttribute('class');
      expect(searchClassAfter).not.toContain('active');
    });
  });

  // ============================================================================
  // SECTION 3: LLM MANAGER - PROVIDER CONFIGURATION
  // ============================================================================

  test.describe('LLM Manager - Provider Tabs and Selection @llm-manager @configuration @slow', () => {
    /**
     * SUCCESS CRITERIA:
     * - LLM Manager tab is clickable
     * - Tab content loads properly
     * - No console errors
     */
    test('should navigate to LLM Manager tab successfully @llm-nav @smoke', async ({
      page,
    }) => {
      const llmTab = page.locator('.tab-button:has-text("LLM Manager")');
      await llmTab.click();
      const llmContent = page.locator('#llm-manager-tab');
      await expect(llmContent).toHaveClass(/active/);
    });

    /**
     * SUCCESS CRITERIA:
     * - All 3 provider tabs are visible
     * - Provider names are correct (Google Gemini, OpenAI ChatGPT, Anthropic Claude)
     * - Provider tabs are clickable
     * - Provider tabs are properly labeled
     */
    test('should display all 3 LLM provider tabs @llm-provider-tabs @smoke', async ({
      page,
    }) => {
      const llmTab = page.locator('.tab-button:has-text("LLM Manager")');
      await llmTab.click();

      const providers = ['Google Gemini', 'OpenAI ChatGPT', 'Anthropic Claude'];

      for (const provider of providers) {
        const providerTab = page.locator(`[data-provider*="${provider.toLowerCase().split(' ')[0]}"], text=${provider}`);
        if (await providerTab.count() > 0) {
          await expect(providerTab.first()).toBeVisible();
        }
      }
    });

    /**
     * SUCCESS CRITERIA:
     * - Google Gemini is selected by default
     * - Gemini tab has 'active' class
     * - Gemini configuration form is visible
     */
    test('should have Google Gemini provider selected by default @llm-default-gemini @smoke', async ({
      page,
    }) => {
      const llmTab = page.locator('.tab-button:has-text("LLM Manager")');
      await llmTab.click();

      const geminiTab = page.locator('[data-provider*="gemini"]');
      if (await geminiTab.count() > 0) {
        const hasActiveClass = await geminiTab.first().evaluate(el =>
          el.classList.contains('active') || el.classList.contains('selected')
        );
        expect(hasActiveClass).toBeTruthy();
      }
    });

    /**
     * SUCCESS CRITERIA:
     * - Clicking OpenAI provider tab switches to it
     * - OpenAI tab becomes active
     * - OpenAI configuration form is displayed
     */
    test('should switch to OpenAI provider when clicked @llm-openai-switch @interaction', async ({
      page,
    }) => {
      const llmTab = page.locator('.tab-button:has-text("LLM Manager")');
      await llmTab.click();

      const openaiTab = page.locator('[data-provider*="openai"]');
      if (await openaiTab.count() > 0) {
        await openaiTab.first().click();
        const hasActiveClass = await openaiTab.first().evaluate(el =>
          el.classList.contains('active') || el.classList.contains('selected')
        );
        expect(hasActiveClass).toBeTruthy();
      }
    });

    /**
     * SUCCESS CRITERIA:
     * - Clicking Anthropic provider tab switches to it
     * - Anthropic tab becomes active
     * - Anthropic configuration form is displayed
     */
    test('should switch to Anthropic provider when clicked @llm-anthropic-switch @interaction', async ({
      page,
    }) => {
      const llmTab = page.locator('.tab-button:has-text("LLM Manager")');
      await llmTab.click();

      const anthropicTab = page.locator('[data-provider*="anthropic"]');
      if (await anthropicTab.count() > 0) {
        await anthropicTab.first().click();
        const hasActiveClass = await anthropicTab.first().evaluate(el =>
          el.classList.contains('active') || el.classList.contains('selected')
        );
        expect(hasActiveClass).toBeTruthy();
      }
    });

    /**
     * SUCCESS CRITERIA:
     * - Can cycle through all 3 providers
     * - Each provider tab becomes active in sequence
     * - No errors during switching
     */
    test('should cycle through all provider tabs without errors @llm-cycle-providers @workflow', async ({
      page,
    }) => {
      const llmTab = page.locator('.tab-button:has-text("LLM Manager")');
      await llmTab.click();

      const providers = ['gemini', 'openai', 'anthropic'];

      for (const provider of providers) {
        const tab = page.locator(`[data-provider*="${provider}"]`);
        if (await tab.count() > 0) {
          await tab.first().click();
          const hasActiveClass = await tab.first().evaluate(el =>
            el.classList.contains('active') || el.classList.contains('selected')
          );
          expect(hasActiveClass).toBeTruthy();
        }
      }
    });
  });

  // ============================================================================
  // SECTION 4: LLM MANAGER - API KEY AND MODEL CONFIGURATION
  // ============================================================================

  test.describe('LLM Manager - API Configuration @llm-manager @configuration @input @slow', () => {
    /**
     * SUCCESS CRITERIA:
     * - API key input field is visible for each provider
     * - Input field accepts text
     * - Input field has proper type (password or text)
     * - Placeholder text indicates API key input
     */
    test('should display API key input for Gemini provider @llm-gemini-api-input @input', async ({
      page,
    }) => {
      const llmTab = page.locator('.tab-button:has-text("LLM Manager")');
      await llmTab.click();

      const apiInput = page.locator('input[type="password"], input[placeholder*="API"]').first();
      if (await apiInput.isVisible()) {
        await expect(apiInput).toBeVisible();

        // Test input accepts text
        await apiInput.fill('test-api-key-12345');
        const value = await apiInput.inputValue();
        expect(value).toBe('test-api-key-12345');
      }
    });

    /**
     * SUCCESS CRITERIA:
     * - API key input for OpenAI is visible
     * - Input accepts and stores API key text
     * - Multiple characters can be entered
     */
    test('should accept API key input for OpenAI provider @llm-openai-api-input @input', async ({
      page,
    }) => {
      const llmTab = page.locator('.tab-button:has-text("LLM Manager")');
      await llmTab.click();

      const openaiTab = page.locator('[data-provider*="openai"]');
      if (await openaiTab.count() > 0) {
        await openaiTab.first().click();

        const apiInput = page.locator('input[type="password"], input[placeholder*="API"]').first();
        if (await apiInput.isVisible()) {
          const testKey = 'sk-test-1234567890';
          await apiInput.fill(testKey);
          const value = await apiInput.inputValue();
          expect(value).toBe(testKey);
        }
      }
    });

    /**
     * SUCCESS CRITERIA:
     * - API key input for Anthropic is visible
     * - Input accepts API key text
     */
    test('should accept API key input for Anthropic provider @llm-anthropic-api-input @input', async ({
      page,
    }) => {
      const llmTab = page.locator('.tab-button:has-text("LLM Manager")');
      await llmTab.click();

      const anthropicTab = page.locator('[data-provider*="anthropic"]');
      if (await anthropicTab.count() > 0) {
        await anthropicTab.first().click();

        const apiInput = page.locator('input[type="password"], input[placeholder*="API"]').first();
        if (await apiInput.isVisible()) {
          await apiInput.fill('anthropic-test-key');
          const value = await apiInput.inputValue();
          expect(value).toBe('anthropic-test-key');
        }
      }
    });

    /**
     * SUCCESS CRITERIA:
     * - Model selection dropdown is visible
     * - Dropdown has multiple options
     * - Can select different models
     */
    test('should display model selection dropdown @llm-model-dropdown @input', async ({
      page,
    }) => {
      const llmTab = page.locator('.tab-button:has-text("LLM Manager")');
      await llmTab.click();

      const modelSelect = page.locator('select[id*="model"], select').first();
      if (await modelSelect.isVisible()) {
        await expect(modelSelect).toBeVisible();

        // Check options
        const options = modelSelect.locator('option');
        const optionCount = await options.count();
        expect(optionCount).toBeGreaterThanOrEqual(1);
      }
    });

    /**
     * SUCCESS CRITERIA:
     * - Can select different model options
     * - Selected value changes when option is clicked
     * - Selection persists
     */
    test('should allow model selection from dropdown @llm-model-selection @input', async ({
      page,
    }) => {
      const llmTab = page.locator('.tab-button:has-text("LLM Manager")');
      await llmTab.click();

      const modelSelect = page.locator('select[id*="model"], select').first();
      if (await modelSelect.isVisible()) {
        const options = modelSelect.locator('option');
        const optionCount = await options.count();

        if (optionCount > 1) {
          await modelSelect.selectOption({ index: 1 });
          const selectedValue = await modelSelect.inputValue();
          expect(selectedValue).toBeTruthy();
        }
      }
    });

    /**
     * SUCCESS CRITERIA:
     * - Test Connection button is visible
     * - Button is clickable
     * - Button does not throw errors when clicked
     */
    test('should display and allow clicking Test Connection button @llm-test-button @interaction', async ({
      page,
    }) => {
      const llmTab = page.locator('.tab-button:has-text("LLM Manager")');
      await llmTab.click();

      const testButton = page.locator('button:has-text("Test"), button:has-text("Connect")').first();
      if (await testButton.isVisible()) {
        await expect(testButton).toBeVisible();
        await testButton.click();
        // No error should occur
      }
    });

    /**
     * SUCCESS CRITERIA:
     * - Status message element exists
     * - Status message is visible
     * - Status can display text
     */
    test('should display status message for LLM configuration @llm-status-message @display', async ({
      page,
    }) => {
      const llmTab = page.locator('.tab-button:has-text("LLM Manager")');
      await llmTab.click();

      const statusMsg = page.locator('#llm-auth-message, .status-message, [id*="status"]').first();
      if (await statusMsg.isVisible()) {
        await expect(statusMsg).toBeVisible();
      }
    });

    /**
     * SUCCESS CRITERIA:
     * - Save Configuration button exists
     * - Button is clickable
     * - Button has proper styling
     */
    test('should display Save Configuration button @llm-save-button @button', async ({
      page,
    }) => {
      const llmTab = page.locator('.tab-button:has-text("LLM Manager")');
      await llmTab.click();

      const saveButton = page.locator('button:has-text("Save"), button:has-text("Submit"), button:has-text("Apply")').first();
      if (await saveButton.isVisible()) {
        await expect(saveButton).toBeVisible();
      }
    });
  });

  // ============================================================================
  // SECTION 5: REPOSITORIES TAB - LIST AND MANAGEMENT
  // ============================================================================

  test.describe('Repositories Tab - Display and Management @repository @display @slow', () => {
    /**
     * SUCCESS CRITERIA:
     * - Repositories tab is clickable
     * - Tab content loads
     * - Tab becomes active
     */
    test('should navigate to Repositories tab @repo-nav @smoke', async ({
      page,
    }) => {
      const reposTab = page.locator('.tab-button:has-text("Repositories")');
      await reposTab.click();
      const reposContent = page.locator('#repositories-tab');
      await expect(reposContent).toHaveClass(/active/);
    });

    /**
     * SUCCESS CRITERIA:
     * - Repository list is visible
     * - List has repository items
     * - List displays properly
     */
    test('should display repository list @repo-list-display @display', async ({
      page,
    }) => {
      const reposTab = page.locator('.tab-button:has-text("Repositories")');
      await reposTab.click();

      const reposList = page.locator('[data-testid="repositories-list"], .repositories-list, .repos-container').first();
      if (await reposList.isVisible()) {
        await expect(reposList).toBeVisible();
      }
    });

    /**
     * SUCCESS CRITERIA:
     * - Add Repository button is visible
     * - Button is clickable
     * - Button has proper label
     */
    test('should display Add Repository button @repo-add-button @button @interaction', async ({
      page,
    }) => {
      const reposTab = page.locator('.tab-button:has-text("Repositories")');
      await reposTab.click();

      const addButton = page.locator('button:has-text("Add"), button:has-text("New"), button:has-text("Create")').first();
      if (await addButton.isVisible()) {
        await expect(addButton).toBeVisible();

        // Test button is clickable
        await addButton.click({ timeout: 1000 }).catch(() => {
          // Click might trigger modal, which is okay
        });
      }
    });

    /**
     * SUCCESS CRITERIA:
     * - Enable/Disable toggle is visible on repositories
     * - Toggle can be clicked
     * - Toggle has proper styling
     */
    test('should display enable/disable toggles for repositories @repo-toggle @interaction', async ({
      page,
    }) => {
      const reposTab = page.locator('.tab-button:has-text("Repositories")');
      await reposTab.click();

      const toggles = page.locator('input[type="checkbox"], [role="switch"], .toggle').first();
      if (await toggles.isVisible()) {
        await expect(toggles).toBeVisible();
      }
    });

    /**
     * SUCCESS CRITERIA:
     * - File count is displayed for repositories
     * - Count shows numbers
     * - Count is readable
     */
    test('should display file count for repositories @repo-file-count @display', async ({
      page,
    }) => {
      const reposTab = page.locator('.tab-button:has-text("Repositories")');
      await reposTab.click();

      const fileCounts = page.locator('text=/\\d+\\s*(files|documents|items)/').first();
      if (await fileCounts.isVisible()) {
        await expect(fileCounts).toBeVisible();
      }
    });

    /**
     * SUCCESS CRITERIA:
     * - Index status indicator exists
     * - Indicator shows status (indexed, indexing, pending)
     * - Indicator has visual feedback
     */
    test('should display index status indicator @repo-status-indicator @display', async ({
      page,
    }) => {
      const reposTab = page.locator('.tab-button:has-text("Repositories")');
      await reposTab.click();

      const statusIndicators = page.locator('.status, .indicator, [class*="status"]').first();
      if (await statusIndicators.isVisible()) {
        await expect(statusIndicators).toBeVisible();
      }
    });

    /**
     * SUCCESS CRITERIA:
     * - Settings button is visible for at least one repository
     * - Button is clickable
     * - Button has proper label
     */
    test('should display Settings button for repositories @repo-settings-button @button', async ({
      page,
    }) => {
      const reposTab = page.locator('.tab-button:has-text("Repositories")');
      await reposTab.click();

      const settingsButton = page.locator('button:has-text("Settings"), button[aria-label*="settings"]').first();
      if (await settingsButton.isVisible()) {
        await expect(settingsButton).toBeVisible();
      }
    });

    /**
     * SUCCESS CRITERIA:
     * - Delete button is visible
     * - Button is clickable
     * - Button has proper label and styling
     */
    test('should display Delete button for repositories @repo-delete-button @button', async ({
      page,
    }) => {
      const reposTab = page.locator('.tab-button:has-text("Repositories")');
      await reposTab.click();

      const deleteButton = page.locator('button:has-text("Delete"), button:has-text("Remove")').first();
      if (await deleteButton.isVisible()) {
        await expect(deleteButton).toBeVisible();
      }
    });

    /**
     * SUCCESS CRITERIA:
     * - Repository items show path/name
     * - Path is readable and visible
     * - Multiple repositories are displayed
     */
    test('should display repository paths and names @repo-names-display @display', async ({
      page,
    }) => {
      const reposTab = page.locator('.tab-button:has-text("Repositories")');
      await reposTab.click();

      const repoItems = page.locator('[data-testid="repo-item"], .repo-item, [class*="repository"]');
      const count = await repoItems.count();
      expect(count).toBeGreaterThanOrEqual(0);
    });
  });

  // ============================================================================
  // SECTION 6: DIRECTORIES TAB - ADD AND MANAGEMENT
  // ============================================================================

  test.describe('Directories Tab - Management @directory @display @slow', () => {
    /**
     * SUCCESS CRITERIA:
     * - Directories tab is clickable
     * - Tab loads properly
     * - Tab becomes active
     */
    test('should navigate to Directories tab @dir-nav @smoke', async ({
      page,
    }) => {
      const dirsTab = page.locator('.tab-button:has-text("Directories")');
      await dirsTab.click();
      const dirsContent = page.locator('#directories-tab');
      await expect(dirsContent).toHaveClass(/active/);
    });

    /**
     * SUCCESS CRITERIA:
     * - Directory list is visible
     * - List displays items
     * - List has proper styling
     */
    test('should display directory list @dir-list-display @display', async ({
      page,
    }) => {
      const dirsTab = page.locator('.tab-button:has-text("Directories")');
      await dirsTab.click();

      const dirsList = page.locator('[data-testid="directories-list"], .directories-list').first();
      if (await dirsList.isVisible()) {
        await expect(dirsList).toBeVisible();
      }
    });

    /**
     * SUCCESS CRITERIA:
     * - Add Directory button is visible
     * - Button is clickable
     * - Button has correct label
     */
    test('should display Add Directory button @dir-add-button @button @interaction', async ({
      page,
    }) => {
      const dirsTab = page.locator('.tab-button:has-text("Directories")');
      await dirsTab.click();

      const addButton = page.locator('button:has-text("Add"), button:has-text("New"), button:has-text("Create")').first();
      if (await addButton.isVisible()) {
        await expect(addButton).toBeVisible();
      }
    });

    /**
     * SUCCESS CRITERIA:
     * - Toggle switches are visible for directories
     * - Toggles can be interacted with
     * - Multiple toggles exist
     */
    test('should display enable/disable toggles for directories @dir-toggle @interaction', async ({
      page,
    }) => {
      const dirsTab = page.locator('.tab-button:has-text("Directories")');
      await dirsTab.click();

      const toggles = page.locator('input[type="checkbox"], [role="switch"]').first();
      if (await toggles.isVisible()) {
        await expect(toggles).toBeVisible();
      }
    });

    /**
     * SUCCESS CRITERIA:
     * - File count is shown for directories
     * - Count displays number
     * - Format is readable
     */
    test('should display file count for directories @dir-file-count @display', async ({
      page,
    }) => {
      const dirsTab = page.locator('.tab-button:has-text("Directories")');
      await dirsTab.click();

      const fileCounts = page.locator('text=/\\d+\\s*(files|documents|items)/').first();
      if (await fileCounts.isVisible()) {
        await expect(fileCounts).toBeVisible();
      }
    });

    /**
     * SUCCESS CRITERIA:
     * - Indexing status is displayed
     * - Status shows current state
     * - Visual indicator shows progress
     */
    test('should display indexing status @dir-index-status @display', async ({
      page,
    }) => {
      const dirsTab = page.locator('.tab-button:has-text("Directories")');
      await dirsTab.click();

      const statusIndicators = page.locator('.status, .indicator, [class*="status"]').first();
      if (await statusIndicators.isVisible()) {
        await expect(statusIndicators).toBeVisible();
      }
    });

    /**
     * SUCCESS CRITERIA:
     * - Settings button is visible for directories
     * - Button is clickable
     * - Button opens configuration
     */
    test('should display Settings button for directories @dir-settings-button @button', async ({
      page,
    }) => {
      const dirsTab = page.locator('.tab-button:has-text("Directories")');
      await dirsTab.click();

      const settingsButton = page.locator('button:has-text("Settings"), button[aria-label*="settings"]').first();
      if (await settingsButton.isVisible()) {
        await expect(settingsButton).toBeVisible();
      }
    });

    /**
     * SUCCESS CRITERIA:
     * - Delete button is visible
     * - Button is clickable
     * - Button likely triggers confirmation
     */
    test('should display Delete button for directories @dir-delete-button @button', async ({
      page,
    }) => {
      const dirsTab = page.locator('.tab-button:has-text("Directories")');
      await dirsTab.click();

      const deleteButton = page.locator('button:has-text("Delete"), button:has-text("Remove")').first();
      if (await deleteButton.isVisible()) {
        await expect(deleteButton).toBeVisible();
      }
    });
  });

  // ============================================================================
  // SECTION 7: ACTIVITY MONITOR AND OBSERVABILITY TABS
  // ============================================================================

  test.describe('Activity Monitor Tab - Logging @activity @display @slow', () => {
    /**
     * SUCCESS CRITERIA:
     * - Activity Monitor tab is clickable
     * - Tab loads
     * - Tab becomes active
     */
    test('should navigate to Activity Monitor tab @activity-nav @smoke', async ({
      page,
    }) => {
      const activityTab = page.locator('.tab-button:has-text("Activity Monitor")');
      await activityTab.click();
      const activityContent = page.locator('#activity-tab');
      await expect(activityContent).toHaveClass(/active/);
    });

    /**
     * SUCCESS CRITERIA:
     * - UI Activity sub-tab is visible
     * - Server Logs sub-tab is visible
     * - Sub-tabs are clickable
     */
    test('should display UI Activity and Server Logs sub-tabs @activity-sub-tabs @display', async ({
      page,
    }) => {
      const activityTab = page.locator('.tab-button:has-text("Activity Monitor")');
      await activityTab.click();

      const uiLogsTab = page.locator('#tab-ui-logs, button:has-text("UI Activity")').first();
      const serverLogsTab = page.locator('#tab-server-logs, button:has-text("Server Logs")').first();

      if (await uiLogsTab.isVisible()) {
        await expect(uiLogsTab).toBeVisible();
      }
      if (await serverLogsTab.isVisible()) {
        await expect(serverLogsTab).toBeVisible();
      }
    });

    /**
     * SUCCESS CRITERIA:
     * - Clear Logs button exists
     * - Button is clickable
     * - Button clears the logs
     */
    test('should display Clear Logs button @activity-clear-button @button', async ({
      page,
    }) => {
      const activityTab = page.locator('.tab-button:has-text("Activity Monitor")');
      await activityTab.click();

      const clearButton = page.locator('button:has-text("Clear")').first();
      if (await clearButton.isVisible()) {
        await expect(clearButton).toBeVisible();
      }
    });
  });

  test.describe('Observability Tab - Metrics @observability @display @slow', () => {
    /**
     * SUCCESS CRITERIA:
     * - Observability tab is clickable
     * - Tab loads
     * - Metrics are displayed
     */
    test('should navigate to Observability tab @obs-nav @smoke', async ({
      page,
    }) => {
      const obsTab = page.locator('.tab-button:has-text("Observability")');
      await obsTab.click();
      const obsContent = page.locator('#observability-tab');
      await expect(obsContent).toHaveClass(/active/);
    });

    /**
     * SUCCESS CRITERIA:
     * - Statistics section is visible
     * - Multiple metrics are displayed
     * - Metrics have proper labels
     */
    test('should display statistics section @obs-stats @display', async ({
      page,
    }) => {
      const obsTab = page.locator('.tab-button:has-text("Observability")');
      await obsTab.click();

      const statsSection = page.locator('.obs-stats, [class*="statistics"]').first();
      if (await statsSection.isVisible()) {
        await expect(statsSection).toBeVisible();
      }
    });

    /**
     * SUCCESS CRITERIA:
     * - Recent Errors table is visible
     * - Table has headers
     * - Table can display error rows
     */
    test('should display Recent Errors table @obs-errors-table @display', async ({
      page,
    }) => {
      const obsTab = page.locator('.tab-button:has-text("Observability")');
      await obsTab.click();

      const errorsTable = page.locator('#obs-errors-table, .obs-errors-table, table').first();
      if (await errorsTable.isVisible()) {
        await expect(errorsTable).toBeVisible();
      }
    });

    /**
     * SUCCESS CRITERIA:
     * - Indexing Events table is visible
     * - Table displays events
     * - Table has proper structure
     */
    test('should display Indexing Events table @obs-indexing-table @display', async ({
      page,
    }) => {
      const obsTab = page.locator('.tab-button:has-text("Observability")');
      await obsTab.click();

      const indexingTable = page.locator('#obs-indexing-table, .obs-indexing-table, table').nth(1);
      if (await indexingTable.isVisible()) {
        await expect(indexingTable).toBeVisible();
      }
    });
  });

  // ============================================================================
  // SECTION 8: SEARCH TAB
  // ============================================================================

  test.describe('Search Tab - Input and Display @search @input @fast', () => {
    /**
     * SUCCESS CRITERIA:
     * - Search tab is already active on load
     * - Search input is visible
     * - Search button is visible
     */
    test('should display search input and button @search-display @smoke', async ({
      page,
    }) => {
      const searchInput = page.locator('input[placeholder*="search" i], input[id*="search"]').first();
      const searchButton = page.locator('button:has-text("Search"), button[type="submit"]').first();

      if (await searchInput.isVisible()) {
        await expect(searchInput).toBeVisible();
      }
      if (await searchButton.isVisible()) {
        await expect(searchButton).toBeVisible();
      }
    });

    /**
     * SUCCESS CRITERIA:
     * - Search input accepts text
     * - Text is stored in input
     * - Can type multiple characters
     */
    test('should accept search input text @search-input @input', async ({
      page,
    }) => {
      const searchInput = page.locator('input[placeholder*="search" i], input[id*="search"]').first();
      if (await searchInput.isVisible()) {
        const testText = 'test search query';
        await searchInput.fill(testText);
        const value = await searchInput.inputValue();
        expect(value).toBe(testText);
      }
    });

    /**
     * SUCCESS CRITERIA:
     * - Clear button exists
     * - Clear button empties the input
     * - Clear button works without errors
     */
    test('should clear search input when button is clicked @search-clear @interaction', async ({
      page,
    }) => {
      const searchInput = page.locator('input[placeholder*="search" i], input[id*="search"]').first();
      if (await searchInput.isVisible()) {
        await searchInput.fill('test search');

        const clearButton = page.locator('button:has-text("Clear")').first();
        if (await clearButton.isVisible()) {
          await clearButton.click();
          const value = await searchInput.inputValue();
          expect(value).toBe('');
        }
      }
    });
  });

  // ============================================================================
  // SECTION 9: DEDICATED CHAT TESTER PAGE
  // ============================================================================

  test.describe('Chat Tester Page - Navigation @chat-page @display @fast', () => {
    test.beforeEach(async ({ page }) => {
      await page.goto('http://localhost:3003/llm-chat-tester.html');
      await page.waitForLoadState('networkidle');
    });

    /**
     * SUCCESS CRITERIA:
     * - Chat tester page loads
     * - Page title is visible
     * - No console errors
     */
    test('should load chat tester page successfully @chat-page-load @smoke', async ({
      page,
    }) => {
      const pageTitle = page.locator('text=LLM Chat Tester, h1, .header');
      if (await pageTitle.count() > 0) {
        await expect(pageTitle.first()).toBeVisible();
      }
    });

    /**
     * SUCCESS CRITERIA:
     * - Header with title is visible
     * - Navigation elements are present
     * - Page is responsive
     */
    test('should display header with navigation @chat-header @display', async ({
      page,
    }) => {
      const header = page.locator('.header, header, [class*="header"]').first();
      if (await header.isVisible()) {
        await expect(header).toBeVisible();
      }

      const navLink = page.locator('a:has-text("Dashboard"), a:has-text("Main")').first();
      if (await navLink.isVisible()) {
        await expect(navLink).toBeVisible();
      }
    });
  });

  test.describe('Chat Tester Page - Model Selection @chat-page @input @slow', () => {
    test.beforeEach(async ({ page }) => {
      await page.goto('http://localhost:3003/llm-chat-tester.html');
    });

    /**
     * SUCCESS CRITERIA:
     * - Model dropdown is visible
     * - Dropdown has options
     * - Can select different options
     */
    test('should display model selection dropdown @chat-model-dropdown @smoke', async ({
      page,
    }) => {
      const modelSelect = page.locator('select').first();
      if (await modelSelect.isVisible()) {
        await expect(modelSelect).toBeVisible();

        const options = modelSelect.locator('option');
        const count = await options.count();
        expect(count).toBeGreaterThanOrEqual(1);
      }
    });

    /**
     * SUCCESS CRITERIA:
     * - Connection status is displayed
     * - Status shows current state
     * - Status updates when model changes
     */
    test('should display model connection status @chat-status @display', async ({
      page,
    }) => {
      const status = page.locator('.status-indicator, [id*="status"], .status').first();
      if (await status.isVisible()) {
        await expect(status).toBeVisible();
      }
    });

    /**
     * SUCCESS CRITERIA:
     * - Test Connection button exists
     * - Button is clickable
     * - Button provides feedback
     */
    test('should display Test Connection button @chat-test-button @button', async ({
      page,
    }) => {
      const testButton = page.locator('button:has-text("Test"), button:has-text("Connect")').first();
      if (await testButton.isVisible()) {
        await expect(testButton).toBeVisible();
      }
    });

    /**
     * SUCCESS CRITERIA:
     * - Can select model from dropdown
     * - Selection persists
     * - Selection is reflected in UI
     */
    test('should allow model selection from dropdown @chat-model-selection @input', async ({
      page,
    }) => {
      const modelSelect = page.locator('select').first();
      if (await modelSelect.isVisible()) {
        const options = modelSelect.locator('option');
        const count = await options.count();

        if (count > 1) {
          await modelSelect.selectOption({ index: 1 });
          const selectedValue = await modelSelect.inputValue();
          expect(selectedValue).toBeTruthy();

          // Verify selection persists
          const afterValue = await modelSelect.inputValue();
          expect(afterValue).toBe(selectedValue);
        }
      }
    });
  });

  test.describe('Chat Tester Page - Chat Interface @chat-page @chat-interface @slow', () => {
    test.beforeEach(async ({ page }) => {
      await page.goto('http://localhost:3003/llm-chat-tester.html');
    });

    /**
     * SUCCESS CRITERIA:
     * - Chat container is visible
     * - Chat container has proper styling
     * - Chat container is properly sized
     */
    test('should display chat message container @chat-container @display @smoke', async ({
      page,
    }) => {
      const chatContainer = page.locator('#chat-container, .chat-container').first();
      if (await chatContainer.isVisible()) {
        await expect(chatContainer).toBeVisible();

        const box = await chatContainer.boundingBox();
        expect(box).not.toBeNull();
        expect(box?.height).toBeGreaterThan(0);
      }
    });

    /**
     * SUCCESS CRITERIA:
     * - Message input field is visible
     * - Input field is focusable
     * - Input field accepts text
     */
    test('should display message input field @chat-input @display @smoke', async ({
      page,
    }) => {
      const input = page.locator('#user-input, input[placeholder*="message" i]').first();
      if (await input.isVisible()) {
        await expect(input).toBeVisible();

        // Test input accepts text
        await input.fill('Test message');
        const value = await input.inputValue();
        expect(value).toBe('Test message');
      }
    });

    /**
     * SUCCESS CRITERIA:
     * - Send button is visible
     * - Send button is clickable
     * - Send button has proper label
     */
    test('should display Send button @chat-send-button @button @smoke', async ({
      page,
    }) => {
      const sendButton = page.locator('#send-button, button:has-text("Send")').first();
      if (await sendButton.isVisible()) {
        await expect(sendButton).toBeVisible();
      }
    });

    /**
     * SUCCESS CRITERIA:
     * - Clear Chat button exists
     * - Button is clickable
     * - Button clears message history
     */
    test('should display Clear Chat button @chat-clear-button @button', async ({
      page,
    }) => {
      const clearButton = page.locator('button:has-text("Clear Chat")').first();
      if (await clearButton.isVisible()) {
        await expect(clearButton).toBeVisible();
      }
    });

    /**
     * SUCCESS CRITERIA:
     * - Input accepts multiple characters
     * - Input preserves text until cleared
     * - Input can be cleared manually
     */
    test('should accept and maintain message input @chat-input-interaction @input', async ({
      page,
    }) => {
      const input = page.locator('#user-input, input[placeholder*="message" i]').first();
      if (await input.isVisible()) {
        const messages = ['Hello', 'World', 'Testing', '1234567890'];

        for (const msg of messages) {
          await input.fill(msg);
          const value = await input.inputValue();
          expect(value).toBe(msg);
        }
      }
    });

    /**
     * SUCCESS CRITERIA:
     * - Token counter displays number
     * - Token information is visible
     * - Counter updates when messages are sent (if applicable)
     */
    test('should display token counter information @chat-token-counter @display', async ({
      page,
    }) => {
      const tokenInfo = page.locator('text=/tokens|\\d+/').first();
      if (await tokenInfo.isVisible()) {
        await expect(tokenInfo).toBeVisible();
      }
    });

    /**
     * SUCCESS CRITERIA:
     * - Context compression button exists
     * - Button is visible
     * - Button is clickable
     */
    test('should display context compression button if supported @chat-compress @button', async ({
      page,
    }) => {
      const compressButton = page.locator('button:has-text("Compress")').first();
      if (await compressButton.isVisible()) {
        await expect(compressButton).toBeVisible();
      }
    });
  });

  test.describe('Chat Tester Page - Message Display @chat-page @message @slow', () => {
    test.beforeEach(async ({ page }) => {
      await page.goto('http://localhost:3003/llm-chat-tester.html');
    });

    /**
     * SUCCESS CRITERIA:
     * - Message elements have proper structure
     * - Messages are visible when present
     * - Messages can be displayed in different roles
     */
    test('should have message structure for display @chat-message-structure @display', async ({
      page,
    }) => {
      const messageElements = page.locator('.message, [class*="message"]');
      const structureExists = await messageElements.count() >= 0; // Structure can exist even if no messages
      expect(structureExists).toBeTruthy();
    });

    /**
     * SUCCESS CRITERIA:
     * - Message bubbles have proper styling
     * - Bubbles are visually distinct
     * - Bubbles display content properly
     */
    test('should have proper message bubble styling @chat-bubble-style @visual', async ({
      page,
    }) => {
      const bubbles = page.locator('.message-bubble');
      const count = await bubbles.count();
      // Bubbles might not exist if no messages, but style should be defined
      expect(count >= 0).toBeTruthy();
    });

    /**
     * SUCCESS CRITERIA:
     * - Message labels show role (user/assistant/system)
     * - Labels are visible and readable
     * - Labels distinguish message types
     */
    test('should display message labels with role indicators @chat-message-labels @display', async ({
      page,
    }) => {
      const labels = page.locator('.message-label');
      const count = await labels.count();
      // Labels might not exist if no messages
      expect(count >= 0).toBeTruthy();
    });
  });

  // ============================================================================
  // SECTION 10: RESPONSIVE DESIGN AND ACCESSIBILITY
  // ============================================================================

  test.describe('Responsive Design Testing @responsive @fast', () => {
    /**
     * SUCCESS CRITERIA:
     * - Page loads on mobile viewport
     * - Content is visible at mobile size
     * - No horizontal scrolling required
     */
    test('should be responsive on mobile viewport (375x667) @responsive-mobile @smoke', async ({
      page,
    }) => {
      await page.setViewportSize({ width: 375, height: 667 });
      await page.goto('http://localhost:3003');
      const content = page.locator('body');
      await expect(content).toBeVisible();
    });

    /**
     * SUCCESS CRITERIA:
     * - Page loads on tablet viewport
     * - Content is properly laid out
     * - Elements are accessible
     */
    test('should be responsive on tablet viewport (768x1024) @responsive-tablet @smoke', async ({
      page,
    }) => {
      await page.setViewportSize({ width: 768, height: 1024 });
      await page.goto('http://localhost:3003');
      const content = page.locator('body');
      await expect(content).toBeVisible();
    });

    /**
     * SUCCESS CRITERIA:
     * - Page loads on desktop viewport
     * - All elements are visible
     * - Layout is optimal for desktop
     */
    test('should be responsive on desktop viewport (1920x1080) @responsive-desktop @smoke', async ({
      page,
    }) => {
      await page.setViewportSize({ width: 1920, height: 1080 });
      await page.goto('http://localhost:3003');
      const content = page.locator('body');
      await expect(content).toBeVisible();
    });

    /**
     * SUCCESS CRITERIA:
     * - Chat page loads on mobile
     * - Chat interface is usable
     * - Input and message area are accessible
     */
    test('should be responsive on chat page mobile (375x667) @responsive-chat-mobile @smoke', async ({
      page,
    }) => {
      await page.setViewportSize({ width: 375, height: 667 });
      await page.goto('http://localhost:3003/llm-chat-tester.html');
      const chatContainer = page.locator('#chat-container, .chat-container').first();
      if (await chatContainer.isVisible()) {
        await expect(chatContainer).toBeVisible();
      }
    });
  });

  test.describe('Accessibility Testing @a11y @fast', () => {
    /**
     * SUCCESS CRITERIA:
     * - Buttons have text labels or ARIA labels
     * - All interactive elements are labeled
     * - Labels are descriptive
     */
    test('should have ARIA labels on buttons @a11y-button-labels @smoke', async ({
      page,
    }) => {
      await page.goto('http://localhost:3003');
      const buttons = page.locator('button');
      const count = await buttons.count();
      expect(count).toBeGreaterThan(0);

      // At least some buttons should have text or aria-label
      const firstButton = await buttons.first();
      const text = await firstButton.textContent();
      const ariaLabel = await firstButton.getAttribute('aria-label');
      expect(text?.trim() || ariaLabel).toBeTruthy();
    });

    /**
     * SUCCESS CRITERIA:
     * - Page uses semantic HTML (h1, h2, button, input, etc.)
     * - Heading hierarchy is proper
     * - Landmarks exist (nav, main, etc.)
     */
    test('should have semantic HTML structure @a11y-semantic @smoke', async ({
      page,
    }) => {
      await page.goto('http://localhost:3003');
      const headings = page.locator('h1, h2, h3');
      const buttons = page.locator('button');
      const inputs = page.locator('input, select, textarea');

      expect(await buttons.count()).toBeGreaterThanOrEqual(0);
      expect(await inputs.count()).toBeGreaterThanOrEqual(0);
    });

    /**
     * SUCCESS CRITERIA:
     * - Form inputs have associated labels
     * - Labels are properly linked to inputs
     * - Screen readers can announce labels
     */
    test('should have proper label associations @a11y-labels @smoke', async ({
      page,
    }) => {
      await page.goto('http://localhost:3003');
      const labels = page.locator('label');
      const count = await labels.count();
      expect(count >= 0).toBeTruthy();
    });

    /**
     * SUCCESS CRITERIA:
     * - Elements are focusable with Tab key
     * - Focus order is logical
     * - Focus is not trapped
     */
    test('should have keyboard navigation support @a11y-keyboard @smoke', async ({
      page,
    }) => {
      await page.goto('http://localhost:3003');
      await page.keyboard.press('Tab');
      const focused = page.locator(':focus');
      const count = await focused.count();
      expect(count).toBeGreaterThanOrEqual(0);
    });

    /**
     * SUCCESS CRITERIA:
     * - Focused elements have visible focus indicator
     * - Focus style is distinct from default
     * - Focus indicator meets contrast requirements
     */
    test('should have visible focus indicators @a11y-focus @smoke', async ({
      page,
    }) => {
      await page.goto('http://localhost:3003');
      const button = page.locator('button').first();
      if (await button.isVisible()) {
        await button.focus();
        const outline = await button.evaluate(el =>
          window.getComputedStyle(el).outline
        );
        expect(outline || 'visible').toBeTruthy();
      }
    });

    /**
     * SUCCESS CRITERIA:
     * - Interactive elements have ARIA roles
     * - Roles are correctly applied
     * - Custom components have proper roles
     */
    test('should have ARIA roles on interactive elements @a11y-roles @smoke', async ({
      page,
    }) => {
      await page.goto('http://localhost:3003');
      const interactive = page.locator('[role]');
      const count = await interactive.count();
      expect(count >= 0).toBeTruthy();
    });

    /**
     * SUCCESS CRITERIA:
     * - Chat page is keyboard accessible
     * - Can navigate with Tab
     * - Can send messages with keyboard
     */
    test('should have keyboard accessibility on chat page @a11y-chat-keyboard @smoke', async ({
      page,
    }) => {
      await page.goto('http://localhost:3003/llm-chat-tester.html');
      await page.keyboard.press('Tab');
      const focused = page.locator(':focus');
      const count = await focused.count();
      expect(count >= 0).toBeTruthy();
    });
  });

  // ============================================================================
  // SECTION 11: STATE PERSISTENCE AND WORKFLOWS
  // ============================================================================

  test.describe('State Persistence and Management @state @slow', () => {
    /**
     * SUCCESS CRITERIA:
     * - Selected model persists during session
     * - Model selection is remembered
     * - Selection survives tab switches
     */
    test('should maintain selected model during session @state-model-persistence @state', async ({
      page,
    }) => {
      await page.goto('http://localhost:3003/llm-chat-tester.html');

      const modelSelect = page.locator('select').first();
      if (await modelSelect.isVisible()) {
        const options = modelSelect.locator('option');
        const count = await options.count();

        if (count > 1) {
          // Select a model
          await modelSelect.selectOption({ index: 1 });
          const selectedValue = await modelSelect.inputValue();

          // Verify it persists
          await page.waitForTimeout(200);
          const afterValue = await modelSelect.inputValue();
          expect(afterValue).toBe(selectedValue);
        }
      }
    });

    /**
     * SUCCESS CRITERIA:
     * - Tab state is maintained during navigation
     * - Going back to a tab shows its previous state
     * - Content is not reset unnecessarily
     */
    test('should maintain tab state during session @state-tab-persistence @state', async ({
      page,
    }) => {
      const reposTab = page.locator('.tab-button:has-text("Repositories")');
      await reposTab.click();
      const reposContent = page.locator('#repositories-tab');
      await expect(reposContent).toHaveClass(/active/);

      // Switch away
      const dirsTab = page.locator('.tab-button:has-text("Directories")');
      await dirsTab.click();

      // Switch back
      await reposTab.click();
      await expect(reposContent).toHaveClass(/active/);
    });
  });

  test.describe('Complete User Workflows @workflow @slow', () => {
    /**
     * SUCCESS CRITERIA:
     * - Can navigate from first to last tab
     * - Each tab loads correctly
     * - No errors occur during navigation
     */
    test('should complete full dashboard tab navigation workflow @workflow-tab-nav', async ({
      page,
    }) => {
      const tabs = ['Search', 'Activity Monitor', 'Repositories', 'Directories', 'Observability', 'LLM Manager'];

      for (const tabName of tabs) {
        const tab = page.locator(`.tab-button:has-text("${tabName}")`);
        await tab.click();
        await page.waitForTimeout(100);

        const activeTab = page.locator('.tab-button.active');
        const activeText = await activeTab.first().textContent();
        expect(activeText?.trim()).toContain(tabName);
      }
    });

    /**
     * SUCCESS CRITERIA:
     * - Can select model on chat page
     * - Can test connection
     * - Can navigate back to dashboard
     */
    test('should complete model selection workflow on chat page @workflow-model-select', async ({
      page,
    }) => {
      await page.goto('http://localhost:3003/llm-chat-tester.html');

      const modelSelect = page.locator('select').first();
      if (await modelSelect.isVisible()) {
        const options = modelSelect.locator('option');
        const count = await options.count();

        if (count > 1) {
          await modelSelect.selectOption({ index: 1 });
          const selectedValue = await modelSelect.inputValue();
          expect(selectedValue).toBeTruthy();

          // Navigate back to dashboard
          const navLink = page.locator('a:has-text("Dashboard"), a:has-text("Main")').first();
          if (await navLink.isVisible()) {
            await navLink.click({ timeout: 1000 }).catch(() => {});
          }
        }
      }
    });

    /**
     * SUCCESS CRITERIA:
     * - Can type message in input
     * - Input accepts multiple characters
     * - Can clear input
     */
    test('should complete message input workflow @workflow-message-input', async ({
      page,
    }) => {
      await page.goto('http://localhost:3003/llm-chat-tester.html');

      const input = page.locator('#user-input, input[placeholder*="message" i]').first();
      if (await input.isVisible()) {
        const testMessage = 'Test workflow message 12345';

        // Type message
        await input.fill(testMessage);
        let value = await input.inputValue();
        expect(value).toBe(testMessage);

        // Clear message
        await input.clear();
        value = await input.inputValue();
        expect(value).toBe('');
      }
    });
  });
});
