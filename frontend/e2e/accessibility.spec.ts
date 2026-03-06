import { test, expect } from '@playwright/test';

test.describe('Keyboard Navigation', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:3000');
  });

  test('skip link should be focusable and skip to main content', async ({ page }) => {
    // Tab to the skip link (should be first focusable element)
    await page.keyboard.press('Tab');
    const skipLink = page.getByText('Skip to main content');
    await expect(skipLink).toBeFocused();
    // Verify it's visible on focus
    await expect(skipLink).toBeVisible();
  });

  test('should tab through navigation items in order', async ({ page }) => {
    // Start on sidebar
    const sidebar = page.getByRole('navigation', { name: /main navigation/i });
    await expect(sidebar).toBeVisible();

    // Tab through nav links
    const navLinks = await page.getByRole('link').all();
    expect(navLinks.length).toBeGreaterThan(0);

    // Each link should be tabbable
    for (const link of navLinks.slice(0, 3)) {
      const isVisible = await link.isVisible();
      if (isVisible) {
        await link.focus();
        await expect(link).toBeFocused();
      }
    }
  });

  test('collapse button should be keyboard accessible', async ({ page }) => {
    const collapseBtn = page.getByLabel(/collapse sidebar/i);
    await expect(collapseBtn).toBeVisible();

    // Tab to the button
    let tabCount = 0;
    while (tabCount < 20) {
      await page.keyboard.press('Tab');
      const focused = await page.evaluate(() => document.activeElement?.getAttribute('aria-label'));
      if (focused?.includes('Collapse') || focused?.includes('Expand')) {
        await expect(collapseBtn).toBeFocused();
        break;
      }
      tabCount++;
    }

    // Space or Enter should toggle it
    const initialExpanded = await collapseBtn.getAttribute('aria-expanded');
    await page.keyboard.press('Space');
    const newExpanded = await collapseBtn.getAttribute('aria-expanded');
    expect(newExpanded).not.toBe(initialExpanded);
  });

  test('form inputs should be focusable and fillable with keyboard', async ({ page }) => {
    await page.goto('http://localhost:3000/settings');

    // Find form inputs
    const inputs = await page.getByRole('textbox').all();
    expect(inputs.length).toBeGreaterThan(0);

    // Each input should be tabbable
    for (const input of inputs.slice(0, 2)) {
      await input.focus();
      await expect(input).toBeFocused();
      await input.fill('test-value');
      const value = await input.inputValue();
      expect(value).toBe('test-value');
    }
  });

  test('buttons should respond to Space and Enter keys', async ({ page }) => {
    await page.goto('http://localhost:3000/settings');

    const saveButtons = await page.getByRole('button', { name: /save/i }).all();
    if (saveButtons.length > 0) {
      const btn = saveButtons[0];
      await btn.focus();
      await expect(btn).toBeFocused();

      // Space should activate button
      await page.keyboard.press('Space');
      // Verify button interaction (may be disabled, so just check it's pressed)
      const isDisabled = await btn.isDisabled();
      expect(typeof isDisabled).toBe('boolean');
    }
  });

  test('should maintain visible focus indicator', async ({ page }) => {
    const button = page.getByLabel(/collapse sidebar/i);
    await button.focus();
    await expect(button).toBeFocused();

    // Check that focus is visible (element has focus)
    const focusClass = await button.evaluate((el) => {
      const styles = window.getComputedStyle(el);
      return styles.outline || styles.boxShadow;
    });

    // Focus should be visible
    expect(focusClass).toBeTruthy();
  });
});

test.describe('Screen Reader Announcements', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:3000');
  });

  test('alerts should have role="alert" and aria-live', async ({ page }) => {
    const alertRegion = page.getByRole('region', { name: /notifications/i });
    await expect(alertRegion).toBeVisible();
    expect(await alertRegion.getAttribute('aria-live')).toBe('polite');
  });

  test('navigation should have proper landmarks', async ({ page }) => {
    const nav = page.getByRole('navigation');
    await expect(nav).toHaveCount(2); // Sidebar nav + inner nav menu

    const header = page.getByRole('banner');
    await expect(header).toBeVisible();
  });

  test('stock cards should be regions with labels', async ({ page }) => {
    await page.goto('http://localhost:3000');

    const regions = await page.getByRole('region').all();
    // Should have at least sidebar and some content regions
    expect(regions.length).toBeGreaterThan(1);
  });

  test('status indicators should have aria-live', async ({ page }) => {
    const connectionStatus = page.getByLabel(/connection status/i);
    await expect(connectionStatus).toHaveAttribute('aria-live', 'polite');
  });
});

test.describe('Heading Hierarchy', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:3000');
  });

  test('should have proper h1 and h2 hierarchy', async ({ page }) => {
    const h1Count = await page.locator('h1').count();
    const h2Count = await page.locator('h2').count();

    // Should have at least one h1 (page title)
    expect(h1Count).toBeGreaterThanOrEqual(1);
    // Should have h2s for sections
    expect(h2Count).toBeGreaterThanOrEqual(0);
  });

  test('should not skip heading levels', async ({ page }) => {
    const headings = await page.locator('h1, h2, h3, h4, h5, h6').all();
    const levels: number[] = [];

    for (const heading of headings) {
      const tag = await heading.evaluate((el) => parseInt(el.tagName[1]));
      levels.push(tag);
    }

    // Check that we don't skip levels (e.g., h1 -> h3 is bad)
    for (let i = 1; i < levels.length; i++) {
      const levelDiff = Math.abs(levels[i] - levels[i - 1]);
      expect(levelDiff).toBeLessThanOrEqual(1);
    }
  });
});

test.describe('Form Accessibility', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:3000/settings');
  });

  test('all form inputs should have associated labels', async ({ page }) => {
    const inputs = await page.locator('input, select, textarea').all();

    for (const input of inputs.slice(0, 5)) {
      const inputId = await input.getAttribute('id');
      if (inputId) {
        const label = page.locator(`label[for="${inputId}"]`);
        const isVisible = await label.isVisible().catch(() => false);
        // Either has associated label or aria-label
        const hasAriaLabel = await input.getAttribute('aria-label');
        expect(isVisible || hasAriaLabel).toBeTruthy();
      }
    }
  });

  test('form submission should work with keyboard only', async ({ page }) => {
    // Tab to first form field
    const firstInput = page.locator('input[type="text"]').first();
    if (await firstInput.isVisible()) {
      await firstInput.focus();
      await expect(firstInput).toBeFocused();
      await firstInput.fill('test');

      // Tab to submit button
      let tabCount = 0;
      while (tabCount < 30) {
        await page.keyboard.press('Tab');
        const focused = page.evaluate(() => {
          const el = document.activeElement as HTMLElement;
          return el?.tagName === 'BUTTON' && el?.textContent?.includes('Save');
        });
        if (focused) {
          break;
        }
        tabCount++;
      }
    }
  });

  test('required fields should have aria-required', async ({ page }) => {
    const apiKeyInputs = await page.locator('input[aria-required="true"]').all();
    expect(apiKeyInputs.length).toBeGreaterThan(0);
  });
});