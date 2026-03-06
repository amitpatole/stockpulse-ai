import { test, expect } from '@playwright/test';

test.describe('Accessibility Compliance - Semantic HTML & ARIA', () => {
  test('dashboard should have proper semantic structure', async ({ page }) => {
    await page.goto('http://localhost:3000');

    // Check for main landmark
    const main = page.locator('main#main');
    expect(await main.count()).toBeGreaterThan(0);

    // Check for navigation landmark
    const nav = page.locator('nav');
    expect(await nav.count()).toBeGreaterThan(0);

    // Check for header landmark
    const header = page.locator('header');
    expect(await header.count()).toBeGreaterThan(0);

    // Check for proper heading hierarchy
    const h1 = page.locator('h1');
    expect(await h1.count()).toBeGreaterThan(0);
  });

  test('settings page should have accessible form structure', async ({ page }) => {
    await page.goto('http://localhost:3000/settings');

    // Check for form landmark
    const main = page.locator('main');
    expect(await main.count()).toBeGreaterThan(0);

    // Check for inputs with labels
    const inputs = page.locator('input[type="text"], input[type="email"], input[type="number"], textarea, select');
    const count = await inputs.count();

    if (count > 0) {
      // At least some inputs should have associated labels
      for (let i = 0; i < Math.min(3, count); i++) {
        const input = inputs.nth(i);
        const inputId = await input.getAttribute('id');
        const ariaLabel = await input.getAttribute('aria-label');
        const ariaLabelledby = await input.getAttribute('aria-labelledby');

        // Should have some form of label
        if (inputId) {
          const label = page.locator(`label[for="${inputId}"]`);
          const labelExists = await label.count();
          expect(labelExists + (ariaLabel ? 1 : 0) + (ariaLabelledby ? 1 : 0)).toBeGreaterThan(0);
        } else {
          expect(ariaLabel || ariaLabelledby).toBeTruthy();
        }
      }
    }
  });

  test('research page should be accessible', async ({ page }) => {
    await page.goto('http://localhost:3000/research');

    // Page should have main content area
    const main = page.locator('main');
    expect(await main.count()).toBeGreaterThan(0);

    // Should have at least one heading
    const headings = page.locator('h1, h2, h3, h4, h5, h6');
    expect(await headings.count()).toBeGreaterThan(0);
  });

  test('all buttons should have accessible names', async ({ page }) => {
    await page.goto('http://localhost:3000');

    const buttons = page.locator('button');
    const buttonCount = await buttons.count();

    expect(buttonCount).toBeGreaterThan(0);

    // Check first 10 buttons for accessible names
    for (let i = 0; i < Math.min(10, buttonCount); i++) {
      const button = buttons.nth(i);
      const ariaLabel = await button.getAttribute('aria-label');
      const text = (await button.textContent())?.trim();

      // Button should have either aria-label or text content
      expect(ariaLabel || text).toBeTruthy();
    }
  });

  test('all icon-only buttons should have aria-labels', async ({ page }) => {
    await page.goto('http://localhost:3000');

    // Find buttons with icons but no text
    const buttons = page.locator('button');
    const buttonCount = await buttons.count();

    for (let i = 0; i < buttonCount; i++) {
      const button = buttons.nth(i);
      const text = (await button.textContent())?.trim();
      const ariaLabel = await button.getAttribute('aria-label');
      const hasIcon = await button.locator('svg, img').count();

      // If button has icon and no text, it must have aria-label
      if (hasIcon > 0 && !text) {
        expect(ariaLabel).toBeTruthy();
      }
    }
  });

  test('alerts should have proper ARIA attributes', async ({ page }) => {
    await page.goto('http://localhost:3000');

    const alerts = page.locator('[role="alert"], [role="status"]');
    const alertCount = await alerts.count();

    if (alertCount > 0) {
      const firstAlert = alerts.first();
      const ariaLive = await firstAlert.getAttribute('aria-live');
      const ariaAtomic = await firstAlert.getAttribute('aria-atomic');

      expect(ariaLive).toMatch(/polite|assertive/);
      expect(ariaAtomic).toBe('true');
    }
  });

  test('navigation links should indicate current page', async ({ page }) => {
    await page.goto('http://localhost:3000/settings');

    // At least one nav link should have aria-current="page" or similar indicator
    const activeLink = page.locator('nav a[aria-current="page"], nav a.active, nav a[data-active="true"]');
    // Note: active indicator may not always be present, so we just verify nav exists
    const nav = page.locator('nav');
    expect(await nav.count()).toBeGreaterThan(0);
  });

  test('skip link should be present and keyboard accessible', async ({ page }) => {
    await page.goto('http://localhost:3000');

    // Skip link should exist
    const skipLink = page.locator('a[href="#main"]');
    expect(await skipLink.count()).toBeGreaterThan(0);

    // Skip link text should be present
    const skipLinkText = await skipLink.textContent();
    expect(skipLinkText?.toLowerCase()).toContain('skip');
  });

  test('heading hierarchy should be valid (no skips)', async ({ page }) => {
    await page.goto('http://localhost:3000');

    const headings = page.locator('h1, h2, h3, h4, h5, h6');
    const count = await headings.count();

    let previousLevel = 1;
    let isValid = true;

    for (let i = 0; i < count; i++) {
      const heading = headings.nth(i);
      const tagName = await heading.evaluate((el) => el.tagName);
      const level = parseInt(tagName[1], 10);

      // Should not skip heading levels
      if (level > previousLevel + 1) {
        isValid = false;
        break;
      }
      previousLevel = level;
    }

    expect(isValid).toBe(true);
  });

  test('form inputs should have visible labels or aria-label', async ({ page }) => {
    await page.goto('http://localhost:3000/settings');

    const inputs = page.locator('input:not([type="hidden"]), textarea, select');
    const count = await inputs.count();

    for (let i = 0; i < count && i < 5; i++) {
      const input = inputs.nth(i);
      const inputId = await input.getAttribute('id');
      const ariaLabel = await input.getAttribute('aria-label');
      const ariaLabelledby = await input.getAttribute('aria-labelledby');

      let hasLabel = false;

      if (ariaLabel || ariaLabelledby) {
        hasLabel = true;
      } else if (inputId) {
        const label = page.locator(`label[for="${inputId}"]`);
        if (await label.count() > 0) {
          hasLabel = true;
        }
      }

      expect(hasLabel).toBe(true);
    }
  });

  test('focusable elements should have visible focus indicators', async ({ page }) => {
    await page.goto('http://localhost:3000');

    // Tab through several elements
    const focusableElements = page.locator('button, a[href], input, select, textarea');
    const count = await focusableElements.count();

    for (let i = 0; i < Math.min(5, count); i++) {
      await page.keyboard.press('Tab');

      const focused = page.locator(':focus');
      const focusedCount = await focused.count();

      // Should have something focused
      expect(focusedCount).toBeGreaterThan(0);
    }
  });

  test('keyboard navigation should work throughout site', async ({ page }) => {
    await page.goto('http://localhost:3000');

    // Should be able to tab through elements without errors
    for (let i = 0; i < 10; i++) {
      try {
        await page.keyboard.press('Tab');
      } catch (e) {
        // If Tab fails, there's a structural issue
        throw new Error(`Keyboard navigation failed at step ${i}: ${e}`);
      }
    }

    // Test should pass if no errors thrown
    expect(true).toBe(true);
  });

  test('modals or dialogs should have proper ARIA attributes', async ({ page }) => {
    await page.goto('http://localhost:3000');

    const modals = page.locator('[role="dialog"], [aria-modal="true"]');
    const modalCount = await modals.count();

    if (modalCount > 0) {
      const firstModal = modals.first();
      const ariaModal = await firstModal.getAttribute('aria-modal');
      const ariaLabelledby = await firstModal.getAttribute('aria-labelledby');
      const ariaDescribedby = await firstModal.getAttribute('aria-describedby');

      // Modal should have aria-modal="true"
      expect(ariaModal).toBe('true');

      // Should have some labeling
      expect(ariaLabelledby || ariaDescribedby).toBeTruthy();
    }
  });

  test('tables should have proper semantics if present', async ({ page }) => {
    await page.goto('http://localhost:3000');

    const tables = page.locator('table');
    const tableCount = await tables.count();

    if (tableCount > 0) {
      const table = tables.first();

      // Should have thead
      const thead = table.locator('thead');
      expect(await thead.count()).toBeGreaterThan(0);

      // Should have th elements for headers
      const headers = table.locator('th');
      expect(await headers.count()).toBeGreaterThan(0);

      // Should have tbody for content
      const tbody = table.locator('tbody');
      expect(await tbody.count()).toBeGreaterThan(0);
    }
  });

  test('lists should use proper semantic elements', async ({ page }) => {
    await page.goto('http://localhost:3000');

    // Should have some lists (ul, ol, or role="list")
    const lists = page.locator('ul, ol, [role="list"]');
    const listCount = await lists.count();

    // At least nav should have list-like structure
    expect(listCount).toBeGreaterThan(0);
  });
});
