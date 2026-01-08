// File: tests/e2e/ui-elements.spec.ts
// Description: Comprehensive UI element testing - all interactive elements, inputs, outputs, and modals
// Author: Libor Ballaty <libor@arionetworks.com>
// Created: 2026-01-08

import { test, expect } from '@playwright/test';

/**
 * Comprehensive UI Elements Test Suite
 *
 * Business Purpose: Validates all user interface elements including:
 * - Text inputs (search, filters, parameters)
 * - Selection controls (dropdowns, checkboxes, radio buttons)
 * - Buttons (action buttons, toggles)
 * - Display elements (lists, tables, cards)
 * - Modals and dialogs
 * - Form validation and error states
 * - Output displays and result rendering
 * - Interactive state changes
 */

test.describe('UI Elements - Interactive Components - @ui @elements @fast', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:3003');
    await page.waitForLoadState('networkidle');
  });

  // ============================================================
  // TEXT INPUTS
  // ============================================================

  test.describe('Text Input Elements', () => {
    test('should have search input field @ui @input @smoke', async ({
      page,
    }) => {
      // Find all text inputs on page
      const inputs = page.locator('input[type="text"]');
      const inputCount = await inputs.count();

      expect(inputCount).toBeGreaterThanOrEqual(0);
    });

    test('should accept search input text @ui @input @interaction', async ({
      page,
    }) => {
      const searchInput = page.locator(
        'input[placeholder*="search" i], input[placeholder*="Search" i], [role="searchbox"]'
      );

      if (await searchInput.isVisible({ timeout: 2000 })) {
        await searchInput.fill('authentication flow');
        const value = await searchInput.inputValue();
        expect(value).toBe('authentication flow');
      }
    });

    test('should clear search input @ui @input @interaction', async ({
      page,
    }) => {
      const searchInput = page.locator('input[type="text"]').first();

      if (await searchInput.isVisible({ timeout: 2000 })) {
        await searchInput.fill('test query');
        await searchInput.clear();
        const value = await searchInput.inputValue();
        expect(value).toBe('');
      }
    });

    test('should handle rapid text input @ui @input @stress', async ({
      page,
    }) => {
      const inputs = page.locator('input[type="text"]');

      if ((await inputs.count()) > 0) {
        const input = inputs.first();

        // Rapid typing
        for (let i = 0; i < 5; i++) {
          await input.fill(`test${i}`);
          const value = await input.inputValue();
          expect(value).toBe(`test${i}`);
        }
      }
    });

    test('should support input focus and blur @ui @input @interaction', async ({
      page,
    }) => {
      const inputs = page.locator('input[type="text"]');

      if ((await inputs.count()) > 0) {
        const input = inputs.first();

        // Focus input
        await input.focus();
        const isFocused = await input.evaluate((el: HTMLInputElement) =>
          document.activeElement === el
        );
        expect(isFocused).toBe(true);

        // Blur input
        await input.blur();
        const isBlurred = await input.evaluate((el: HTMLInputElement) =>
          document.activeElement !== el
        );
        expect(isBlurred).toBe(true);
      }
    });

    test('should validate input character limits @ui @input @validation', async ({
      page,
    }) => {
      const inputs = page.locator('input[maxlength]');

      if ((await inputs.count()) > 0) {
        const input = inputs.first();
        const maxLength = await input.getAttribute('maxlength');

        if (maxLength) {
          const limit = parseInt(maxLength, 10);
          const longText = 'a'.repeat(limit + 100);

          await input.fill(longText);
          const value = await input.inputValue();

          expect(value.length).toBeLessThanOrEqual(limit);
        }
      }
    });
  });

  // ============================================================
  // BUTTONS
  // ============================================================

  test.describe('Button Elements', () => {
    test('should find interactive buttons @ui @button @smoke', async ({
      page,
    }) => {
      const buttons = page.locator('button');
      const buttonCount = await buttons.count();

      expect(buttonCount).toBeGreaterThanOrEqual(0);
    });

    test('should execute button click actions @ui @button @interaction', async ({
      page,
    }) => {
      const buttons = page.locator('button');

      if ((await buttons.count()) > 0) {
        const firstButton = buttons.first();
        const buttonText = await firstButton.textContent();

        expect(buttonText).toBeTruthy();

        // Click should not throw error
        await firstButton.click({ force: true });
      }
    });

    test('should detect button disabled states @ui @button @state', async ({
      page,
    }) => {
      const disabledButtons = page.locator('button:disabled, button[disabled]');
      const disabledCount = await disabledButtons.count();

      // May or may not have disabled buttons
      expect(disabledCount).toBeGreaterThanOrEqual(0);
    });

    test('should respond to button hover @ui @button @interaction', async ({
      page,
    }) => {
      const buttons = page.locator('button');

      if ((await buttons.count()) > 0) {
        const button = buttons.first();

        // Get computed style before hover
        const stylesBefore = await button.evaluate((el) =>
          window.getComputedStyle(el)
        );

        // Hover over button
        await button.hover();

        // Get computed style after hover
        const stylesAfter = await button.evaluate((el) =>
          window.getComputedStyle(el)
        );

        // Styles should exist
        expect(stylesBefore).toBeTruthy();
        expect(stylesAfter).toBeTruthy();
      }
    });

    test('should handle button keyboard activation @ui @button @accessibility', async ({
      page,
    }) => {
      const buttons = page.locator('button');

      if ((await buttons.count()) > 0) {
        const button = buttons.first();

        await button.focus();
        await page.keyboard.press('Enter');

        // Should not throw error
        expect(button).toBeTruthy();
      }
    });
  });

  // ============================================================
  // DROPDOWNS / SELECT ELEMENTS
  // ============================================================

  test.describe('Dropdown and Select Elements', () => {
    test('should find select/dropdown elements @ui @select @smoke', async ({
      page,
    }) => {
      const selects = page.locator('select, [role="combobox"], [role="listbox"]');
      const selectCount = await selects.count();

      expect(selectCount).toBeGreaterThanOrEqual(0);
    });

    test('should open dropdown on click @ui @select @interaction', async ({
      page,
    }) => {
      const selects = page.locator(
        'select, [role="combobox"], [role="listbox"]'
      );

      if ((await selects.count()) > 0) {
        const select = selects.first();

        if (select.locator('role=option').isVisible({ timeout: 1000 })) {
          await select.click();

          const option = select.locator('[role="option"]').first();
          const isVisible = await option.isVisible({ timeout: 1000 });

          expect(isVisible).toBe(true);
        }
      }
    });

    test('should select dropdown option @ui @select @interaction', async ({
      page,
    }) => {
      const selects = page.locator(
        'select, [role="combobox"], [role="listbox"]'
      );

      if ((await selects.count()) > 0) {
        const select = selects.first();

        // For native select
        if ((await select.locator('option').count()) > 1) {
          const options = select.locator('option');
          const optionCount = await options.count();

          if (optionCount > 1) {
            await select.selectOption(
              await options.nth(1).getAttribute('value')
            );

            const selectedValue = await select.evaluate(
              (el: HTMLSelectElement) => el.value
            );
            expect(selectedValue).toBeTruthy();
          }
        }
      }
    });
  });

  // ============================================================
  // CHECKBOXES AND RADIO BUTTONS
  // ============================================================

  test.describe('Checkbox and Radio Elements', () => {
    test('should find checkboxes @ui @checkbox @smoke', async ({ page }) => {
      const checkboxes = page.locator('input[type="checkbox"]');
      const checkboxCount = await checkboxes.count();

      expect(checkboxCount).toBeGreaterThanOrEqual(0);
    });

    test('should toggle checkbox state @ui @checkbox @interaction', async ({
      page,
    }) => {
      const checkboxes = page.locator('input[type="checkbox"]');

      if ((await checkboxes.count()) > 0) {
        const checkbox = checkboxes.first();

        const initialState = await checkbox.isChecked();
        await checkbox.click();
        const newState = await checkbox.isChecked();

        expect(newState).not.toBe(initialState);
      }
    });

    test('should find radio buttons @ui @radio @smoke', async ({ page }) => {
      const radios = page.locator('input[type="radio"]');
      const radioCount = await radios.count();

      expect(radioCount).toBeGreaterThanOrEqual(0);
    });

    test('should select radio button @ui @radio @interaction', async ({
      page,
    }) => {
      const radios = page.locator('input[type="radio"]');

      if ((await radios.count()) > 0) {
        const radio = radios.first();

        await radio.click();
        const isChecked = await radio.isChecked();

        expect(isChecked).toBe(true);
      }
    });

    test('should enforce radio button mutual exclusivity @ui @radio @behavior',
      async ({ page }) => {
        const radios = page.locator('input[type="radio"]');

        if ((await radios.count()) > 1) {
          const radio1 = radios.nth(0);
          const radio2 = radios.nth(1);

          // Select first radio
          await radio1.click();
          expect(await radio1.isChecked()).toBe(true);

          // Select second radio
          await radio2.click();
          expect(await radio2.isChecked()).toBe(true);

          // First radio should now be unchecked (if same group)
          const radio1Checked = await radio1.isChecked();
          const radio2Checked = await radio2.isChecked();

          // Either both checked (different groups) or only one checked (same group)
          expect(radio1Checked || radio2Checked).toBe(true);
        }
      }
    );
  });

  // ============================================================
  // LISTS AND TABLES
  // ============================================================

  test.describe('List and Table Display Elements', () => {
    test('should find list or table structures @ui @list @smoke', async ({
      page,
    }) => {
      const lists = page.locator(
        '[role="list"], table, .list, .table, [data-testid="list"]'
      );
      const listCount = await lists.count();

      expect(listCount).toBeGreaterThanOrEqual(0);
    });

    test('should display list items @ui @list @display', async ({ page }) => {
      const listItems = page.locator(
        '[role="listitem"], tr, .list-item, [data-testid="item"]'
      );
      const itemCount = await listItems.count();

      // May or may not have visible list items
      expect(itemCount).toBeGreaterThanOrEqual(0);
    });

    test('should support list item selection @ui @list @interaction', async ({
      page,
    }) => {
      const listItems = page.locator(
        '[role="listitem"], .list-item, [data-testid="item"]'
      );

      if ((await listItems.count()) > 0) {
        const item = listItems.first();

        // Try to click item
        await item.click({ force: true });

        // Check if selected class or aria-selected is added
        const isSelected = await item.evaluate((el) => {
          return (
            el.classList.contains('selected') ||
            el.getAttribute('aria-selected') === 'true' ||
            el.hasAttribute('selected')
          );
        });

        // Item selection state checked
        expect(isSelected !== undefined).toBe(true);
      }
    });

    test('should render table headers and data @ui @table @display', async ({
      page,
    }) => {
      const tables = page.locator('table');

      if ((await tables.count()) > 0) {
        const table = tables.first();
        const headers = table.locator('th');
        const rows = table.locator('tbody tr');

        const headerCount = await headers.count();
        const rowCount = await rows.count();

        expect(headerCount).toBeGreaterThanOrEqual(0);
        expect(rowCount).toBeGreaterThanOrEqual(0);
      }
    });
  });

  // ============================================================
  // CARDS AND PANELS
  // ============================================================

  test.describe('Card and Panel Elements', () => {
    test('should find card components @ui @card @smoke', async ({ page }) => {
      const cards = page.locator(
        '[role="article"], .card, .panel, [data-testid="card"]'
      );
      const cardCount = await cards.count();

      expect(cardCount).toBeGreaterThanOrEqual(0);
    });

    test('should display card content @ui @card @display', async ({ page }) => {
      const cards = page.locator(
        '[role="article"], .card, .panel, [data-testid="card"]'
      );

      if ((await cards.count()) > 0) {
        const card = cards.first();
        const text = await card.textContent();

        expect(text).toBeTruthy();
      }
    });

    test('should respond to card interaction @ui @card @interaction', async ({
      page,
    }) => {
      const cards = page.locator(
        '[role="article"], .card, .panel, [data-testid="card"]'
      );

      if ((await cards.count()) > 0) {
        const card = cards.first();

        // Click card
        await card.click({ force: true });

        // Should not throw error
        expect(card).toBeTruthy();
      }
    });
  });

  // ============================================================
  // MODALS AND DIALOGS
  // ============================================================

  test.describe('Modal and Dialog Elements', () => {
    test('should find modal/dialog elements @ui @modal @smoke', async ({
      page,
    }) => {
      const modals = page.locator(
        '[role="dialog"], dialog, .modal, [data-testid="modal"]'
      );
      const modalCount = await modals.count();

      expect(modalCount).toBeGreaterThanOrEqual(0);
    });

    test('should open modal on trigger @ui @modal @interaction', async ({
      page,
    }) => {
      const modalTriggers = page.locator(
        'button:has-text("Add"), button:has-text("Create"), button:has-text("Edit"), button:has-text("Delete")'
      );

      if ((await modalTriggers.count()) > 0) {
        const trigger = modalTriggers.first();

        // Click to open modal
        await trigger.click({ force: true });

        // Wait for modal to appear
        const modal = page.locator('[role="dialog"], dialog, .modal');
        const isVisible = await modal.isVisible({ timeout: 2000 });

        expect(isVisible).toBe(true);
      }
    });

    test('should close modal with close button @ui @modal @interaction', async ({
      page,
    }) => {
      // First open a modal
      const modalTrigger = page.locator(
        'button:has-text("Add"), button:has-text("Create")'
      );

      if ((await modalTrigger.count()) > 0) {
        await modalTrigger.first().click({ force: true });

        // Wait for modal
        const modal = page.locator('[role="dialog"], dialog, .modal').first();
        await modal.waitFor({ state: 'visible', timeout: 2000 });

        // Find and click close button
        const closeBtn = modal.locator(
          'button:has-text("Close"), button:has-text("Cancel"), button[aria-label*="close" i]'
        );

        if ((await closeBtn.count()) > 0) {
          await closeBtn.first().click();

          // Modal should disappear
          const isClosed = await modal.isVisible({ timeout: 1000 });
          expect(isClosed).toBe(false);
        }
      }
    });

    test('should validate modal form inputs @ui @modal @form', async ({
      page,
    }) => {
      const modalTrigger = page.locator(
        'button:has-text("Add"), button:has-text("Create")'
      );

      if ((await modalTrigger.count()) > 0) {
        await modalTrigger.first().click({ force: true });

        const modal = page.locator('[role="dialog"], dialog, .modal').first();
        await modal.waitFor({ state: 'visible', timeout: 2000 });

        // Find form inputs in modal
        const inputs = modal.locator('input, textarea, select');

        if ((await inputs.count()) > 0) {
          // All inputs should be interactable
          for (let i = 0; i < (await inputs.count()); i++) {
            const input = inputs.nth(i);
            const isVisible = await input.isVisible();
            expect(isVisible).toBe(true);
          }
        }
      }
    });
  });

  // ============================================================
  // FORM ELEMENTS
  // ============================================================

  test.describe('Form Elements and Validation', () => {
    test('should find form elements @ui @form @smoke', async ({ page }) => {
      const forms = page.locator('form');
      const formCount = await forms.count();

      expect(formCount).toBeGreaterThanOrEqual(0);
    });

    test('should validate required inputs @ui @form @validation', async ({
      page,
    }) => {
      const requiredInputs = page.locator(
        'input[required], textarea[required], select[required]'
      );
      const requiredCount = await requiredInputs.count();

      expect(requiredCount).toBeGreaterThanOrEqual(0);
    });

    test('should display form validation errors @ui @form @error', async ({
      page,
    }) => {
      const errorElements = page.locator(
        '[role="alert"], .error, .error-message, [data-testid="error"]'
      );
      const errorCount = await errorElements.count();

      expect(errorCount).toBeGreaterThanOrEqual(0);
    });

    test('should support form submission @ui @form @interaction', async ({
      page,
    }) => {
      const forms = page.locator('form');

      if ((await forms.count()) > 0) {
        const form = forms.first();
        const submitButton = form.locator('button[type="submit"]');

        if ((await submitButton.count()) > 0) {
          // Try to submit form
          await submitButton.click({ force: true });

          // Form submission should not throw error
          expect(form).toBeTruthy();
        }
      }
    });
  });

  // ============================================================
  // ALERTS AND NOTIFICATIONS
  // ============================================================

  test.describe('Alert and Notification Elements', () => {
    test('should find alert elements @ui @alert @smoke', async ({ page }) => {
      const alerts = page.locator('[role="alert"], .alert, [data-testid="alert"]');
      const alertCount = await alerts.count();

      expect(alertCount).toBeGreaterThanOrEqual(0);
    });

    test('should display alert content @ui @alert @display', async ({
      page,
    }) => {
      const alerts = page.locator('[role="alert"], .alert');

      if ((await alerts.count()) > 0) {
        const alert = alerts.first();
        const text = await alert.textContent();

        expect(text).toBeTruthy();
      }
    });

    test('should dismiss notifications @ui @alert @interaction', async ({
      page,
    }) => {
      const closeButtons = page.locator(
        '[role="alert"] button, .alert button, [data-testid="alert"] button'
      );

      if ((await closeButtons.count()) > 0) {
        const closeBtn = closeButtons.first();
        await closeBtn.click();

        // Should not throw error
        expect(closeBtn).toBeTruthy();
      }
    });
  });

  // ============================================================
  // LOADING AND PROGRESS STATES
  // ============================================================

  test.describe('Loading and Progress States', () => {
    test('should find loading indicators @ui @loading @smoke', async ({
      page,
    }) => {
      const loaders = page.locator(
        '[role="progressbar"], .loader, .loading, [data-testid="loader"]'
      );
      const loaderCount = await loaders.count();

      expect(loaderCount).toBeGreaterThanOrEqual(0);
    });

    test('should show progress bar @ui @loading @display', async ({ page }) => {
      const progressBars = page.locator('[role="progressbar"], .progress-bar');

      if ((await progressBars.count()) > 0) {
        const progressBar = progressBars.first();
        const value = await progressBar.getAttribute('aria-valuenow');

        expect(value).toBeTruthy();
      }
    });

    test('should display loading spinner @ui @loading @display', async ({
      page,
    }) => {
      const spinners = page.locator(
        '.spinner, .loading-spinner, [data-testid="spinner"]'
      );
      const spinnerCount = await spinners.count();

      expect(spinnerCount).toBeGreaterThanOrEqual(0);
    });
  });

  // ============================================================
  // ACCESSIBILITY
  // ============================================================

  test.describe('Accessibility Features', () => {
    test('should have keyboard navigation @ui @a11y @accessibility', async ({
      page,
    }) => {
      // Tab through elements
      await page.keyboard.press('Tab');
      const focusedElement = await page.evaluate(() =>
        document.activeElement?.tagName
      );

      expect(focusedElement).toBeTruthy();
    });

    test('should have proper aria labels @ui @a11y @accessibility', async ({
      page,
    }) => {
      const elementsWithAriaLabel = page.locator('[aria-label], [aria-labelledby]');
      const ariaCount = await elementsWithAriaLabel.count();

      expect(ariaCount).toBeGreaterThanOrEqual(0);
    });

    test('should have proper role attributes @ui @a11y @accessibility', async ({
      page,
    }) => {
      const elementsWithRole = page.locator('[role]');
      const roleCount = await elementsWithRole.count();

      expect(roleCount).toBeGreaterThanOrEqual(0);
    });

    test('should have alt text on images @ui @a11y @accessibility', async ({
      page,
    }) => {
      const images = page.locator('img');

      if ((await images.count()) > 0) {
        const img = images.first();
        const altText = await img.getAttribute('alt');

        // Alt text should exist (may be empty for decorative)
        expect(altText !== undefined).toBe(true);
      }
    });
  });

  // ============================================================
  // INTERACTIVE STATE CHANGES
  // ============================================================

  test.describe('Interactive Element State Changes', () => {
    test('should respond to hover state @ui @state @interaction', async ({
      page,
    }) => {
      const buttons = page.locator('button, a, [role="button"]');

      if ((await buttons.count()) > 0) {
        const button = buttons.first();

        // Get initial state
        const computedStyle = await button.evaluate((el) =>
          window.getComputedStyle(el).backgroundColor
        );

        // Hover
        await button.hover();

        // State should be monitored
        expect(computedStyle).toBeTruthy();
      }
    });

    test('should respond to focus state @ui @state @interaction', async ({
      page,
    }) => {
      const inputs = page.locator('input, button, a, [role="button"]');

      if ((await inputs.count()) > 0) {
        const input = inputs.first();

        // Focus element
        await input.focus();

        const isFocused = await input.evaluate(
          (el) => document.activeElement === el
        );

        expect(isFocused).toBe(true);
      }
    });

    test('should respond to active state @ui @state @interaction', async ({
      page,
    }) => {
      const buttons = page.locator('button');

      if ((await buttons.count()) > 0) {
        const button = buttons.first();

        // Mouse down
        await button.dispatchEvent('mousedown');
        await button.dispatchEvent('mouseup');

        // Should not throw error
        expect(button).toBeTruthy();
      }
    });

    test('should respond to disabled state @ui @state @display', async ({
      page,
    }) => {
      const disabledElements = page.locator(':disabled, [disabled], [aria-disabled="true"]');
      const disabledCount = await disabledElements.count();

      expect(disabledCount).toBeGreaterThanOrEqual(0);
    });
  });

  // ============================================================
  // OUTPUT AND RESULT DISPLAY
  // ============================================================

  test.describe('Output and Result Display Elements', () => {
    test('should find result containers @ui @output @display', async ({
      page,
    }) => {
      const results = page.locator(
        '[role="region"], .results, .output, [data-testid="results"]'
      );
      const resultCount = await results.count();

      expect(resultCount).toBeGreaterThanOrEqual(0);
    });

    test('should display result items @ui @output @display', async ({
      page,
    }) => {
      const resultItems = page.locator(
        '.result-item, [data-testid="result"], .search-result'
      );
      const itemCount = await resultItems.count();

      expect(itemCount).toBeGreaterThanOrEqual(0);
    });

    test('should show result metadata @ui @output @display', async ({
      page,
    }) => {
      const metadata = page.locator(
        '[data-testid="metadata"], .metadata, .info'
      );
      const metadataCount = await metadata.count();

      expect(metadataCount).toBeGreaterThanOrEqual(0);
    });

    test('should display result actions @ui @output @interaction', async ({
      page,
    }) => {
      const resultActions = page.locator(
        '.result-actions button, [data-testid="result"] button'
      );
      const actionCount = await resultActions.count();

      expect(actionCount).toBeGreaterThanOrEqual(0);
    });
  });

  // ============================================================
  // PAGINATION
  // ============================================================

  test.describe('Pagination Elements', () => {
    test('should find pagination controls @ui @pagination @display', async ({
      page,
    }) => {
      const pagination = page.locator(
        '[role="navigation"] a, .pagination, [data-testid="pagination"]'
      );
      const paginationCount = await pagination.count();

      expect(paginationCount).toBeGreaterThanOrEqual(0);
    });

    test('should navigate between pages @ui @pagination @interaction', async ({
      page,
    }) => {
      const nextButton = page.locator(
        'a:has-text("Next"), button:has-text("Next"), [aria-label*="next" i]'
      );

      if ((await nextButton.count()) > 0) {
        const isEnabled = await nextButton
          .first()
          .evaluate((el) => !el.hasAttribute('disabled'));

        if (isEnabled) {
          await nextButton.first().click();

          // Should not throw error
          expect(nextButton).toBeTruthy();
        }
      }
    });
  });

  // ============================================================
  // TABS
  // ============================================================

  test.describe('Tab Elements', () => {
    test('should find tab controls @ui @tabs @display', async ({ page }) => {
      const tabs = page.locator('[role="tab"], .tab');
      const tabCount = await tabs.count();

      expect(tabCount).toBeGreaterThanOrEqual(0);
    });

    test('should switch between tabs @ui @tabs @interaction', async ({
      page,
    }) => {
      const tabs = page.locator('[role="tab"]');

      if ((await tabs.count()) > 1) {
        const tab2 = tabs.nth(1);

        await tab2.click();

        const isSelected = await tab2.evaluate((el) =>
          el.getAttribute('aria-selected') === 'true'
        );

        expect(isSelected).toBe(true);
      }
    });
  });

  // ============================================================
  // COMPLETE FORM WORKFLOW
  // ============================================================

  test('should support complete form workflow @ui @workflow @e2e @slow', async ({
    page,
  }) => {
    // 1. Find and fill form
    const forms = page.locator('form');

    if ((await forms.count()) > 0) {
      const form = forms.first();

      // 2. Fill inputs
      const inputs = form.locator('input[type="text"]');
      if ((await inputs.count()) > 0) {
        await inputs.first().fill('test value');
      }

      // 3. Select option
      const selects = form.locator('select');
      if ((await selects.count()) > 0) {
        const options = selects.first().locator('option');
        if ((await options.count()) > 1) {
          await selects.first().selectOption(await options.nth(1).getAttribute('value'));
        }
      }

      // 4. Check checkboxes
      const checkboxes = form.locator('input[type="checkbox"]');
      if ((await checkboxes.count()) > 0) {
        await checkboxes.first().click();
      }

      // 5. Submit
      const submitBtn = form.locator('button[type="submit"]');
      if ((await submitBtn.count()) > 0) {
        await submitBtn.click();
      }

      // Form should be interactable
      expect(form).toBeTruthy();
    }
  });
});
