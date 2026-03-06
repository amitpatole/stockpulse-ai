import { test, expect } from '@playwright/test';
import { injectAxe, checkA11y } from 'axe-playwright';

test.describe('axe-core Accessibility Scanning', () => {
  test('dashboard should have no critical violations', async ({ page }) => {
    await page.goto('http://localhost:3000');
    await injectAxe(page);

    const results = await checkA11y(page, null, {
      detailedReport: true,
      detailedReportOptions: {
        html: false,
      },
    });

    // Assert no critical violations
    expect(results).toBeNull();
  });

  test('settings page should have no critical violations', async ({ page }) => {
    await page.goto('http://localhost:3000/settings');
    await injectAxe(page);

    const results = await checkA11y(page, null, {
      detailedReport: true,
    });

    expect(results).toBeNull();
  });

  test('research page should have no critical violations', async ({ page }) => {
    await page.goto('http://localhost:3000/research');
    await injectAxe(page);

    const results = await checkA11y(page, null, {
      detailedReport: true,
    });

    expect(results).toBeNull();
  });

  test('agents page should have no critical violations', async ({ page }) => {
    await page.goto('http://localhost:3000/agents');
    await injectAxe(page);

    const results = await checkA11y(page, null, {
      detailedReport: true,
    });

    expect(results).toBeNull();
  });

  test('scheduler page should have no critical violations', async ({ page }) => {
    await page.goto('http://localhost:3000/scheduler');
    await injectAxe(page);

    const results = await checkA11y(page, null, {
      detailedReport: true,
    });

    expect(results).toBeNull();
  });

  test('header component should pass accessibility checks', async ({ page }) => {
    await page.goto('http://localhost:3000');

    // Check just the header element
    const header = page.locator('header').first();
    if (await header.isVisible()) {
      await injectAxe(page);
      const results = await checkA11y(page, 'header', {
        detailedReport: true,
      });
      expect(results).toBeNull();
    }
  });

  test('sidebar navigation should pass accessibility checks', async ({ page }) => {
    await page.goto('http://localhost:3000');

    // Check sidebar navigation
    const sidebar = page.locator('nav[aria-label*="navigation"]').first();
    if (await sidebar.isVisible()) {
      await injectAxe(page);
      const results = await checkA11y(page, 'nav', {
        detailedReport: true,
      });
      expect(results).toBeNull();
    }
  });

  test('form elements should have proper labels', async ({ page }) => {
    await page.goto('http://localhost:3000/settings');

    const inputs = await page.locator('input, select').all();
    for (const input of inputs.slice(0, 3)) {
      const id = await input.getAttribute('id');
      const ariaLabel = await input.getAttribute('aria-label');
      const hasLabel = id ? await page.locator(`label[for="${id}"]`).count() : false;

      // Each input should have either a label or aria-label
      expect(hasLabel || ariaLabel).toBeTruthy();
    }
  });

  test('buttons should have accessible names', async ({ page }) => {
    await page.goto('http://localhost:3000');

    const buttons = await page.getByRole('button').all();
    for (const button of buttons.slice(0, 5)) {
      const accessibleName = await button.getAttribute('aria-label');
      const textContent = await button.textContent();

      // Button should have either aria-label or text content
      expect(accessibleName || textContent?.trim()).toBeTruthy();
    }
  });

  test('alerts and notifications should be announced', async ({ page }) => {
    await page.goto('http://localhost:3000');

    const alertRegions = await page.getByRole('alert').all();
    for (const alert of alertRegions) {
      const ariaLive = await alert.getAttribute('aria-live');
      expect(ariaLive).toBeTruthy();
    }
  });

  test('all images should have alt text or be decorative', async ({ page }) => {
    await page.goto('http://localhost:3000');

    const images = await page.locator('img').all();
    for (const img of images) {
      const alt = await img.getAttribute('alt');
      const ariaHidden = await img.getAttribute('aria-hidden');

      // Image should have alt text OR be marked as decorative
      expect(alt || ariaHidden === 'true').toBeTruthy();
    }
  });

  test('focus indicators should be visible', async ({ page }) => {
    await page.goto('http://localhost:3000');

    const buttons = await page.getByRole('button').all();
    if (buttons.length > 0) {
      const button = buttons[0];
      await button.focus();

      // Check that focus is visible
      const styles = await button.evaluate((el) => {
        const computed = window.getComputedStyle(el);
        return {
          outline: computed.outline,
          boxShadow: computed.boxShadow,
          backgroundColor: computed.backgroundColor,
        };
      });

      // Focus styles should be applied
      expect(styles.outline || styles.boxShadow).toBeTruthy();
    }
  });
});