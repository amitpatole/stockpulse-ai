/**
 * E2E tests for Onboarding Tour feature.
 * Tests user interactions with the guided tour on first visit.
 *
 * To run: npx playwright test frontend/src/components/onboarding/__tests__/OnboardingTour.e2e.ts
 */

import { test, expect } from '@playwright/test';

test.describe('Onboarding Tour', () => {
  test.beforeEach(async ({ page, context }) => {
    await context.addInitScript(() => {
      localStorage.clear();
    });
  });

  test('should auto-start tour on first visit', async ({ page }) => {
    await page.goto('http://localhost:3000');

    const overlay = page.locator('[style*="z-[9999]"]');
    await expect(overlay).toBeVisible();

    await expect(page.getByText('Welcome to TickerPulse!')).toBeVisible();
  });

  test('should navigate through tour steps', async ({ page }) => {
    await page.goto('http://localhost:3000');

    await expect(page.getByText('Welcome to TickerPulse!')).toBeVisible();

    await page.getByLabel('Next step').click();

    await expect(page.getByText('Your Stock Watchlist')).toBeVisible();
    await expect(page.getByText('Step 2 of 8')).toBeVisible();
  });

  test('should go back to previous step', async ({ page }) => {
    await page.goto('http://localhost:3000');

    await page.getByLabel('Next step').click();

    await page.getByLabel('Previous step').click();

    await expect(page.getByText('Welcome to TickerPulse!')).toBeVisible();
    await expect(page.getByText('Step 1 of 8')).toBeVisible();
  });

  test('should skip tour and persist in localStorage', async ({ page }) => {
    await page.goto('http://localhost:3000');

    await page.getByLabel('Skip tour').click();

    const overlay = page.locator('[style*="z-[9999]"]');
    await expect(overlay).not.toBeVisible();

    const storageData = await page.evaluate(() => {
      return localStorage.getItem('tickerpulse_tour_state');
    });
    expect(storageData).toBeTruthy();
    const parsed = JSON.parse(storageData || '{}');
    expect(parsed.completed).toBe(true);
    expect(parsed.skipped).toBe(true);
  });

  test('should complete tour and mark as done', async ({ page }) => {
    await page.goto('http://localhost:3000');

    for (let i = 0; i < 7; i++) {
      await page.getByLabel('Next step').click();
    }

    const doneButton = page.getByLabel('Complete tour');
    await expect(doneButton).toBeVisible();

    await doneButton.click();

    const overlay = page.locator('[style*="z-[9999]"]');
    await expect(overlay).not.toBeVisible();

    const storageData = await page.evaluate(() => {
      return localStorage.getItem('tickerpulse_tour_state');
    });
    const parsed = JSON.parse(storageData || '{}');
    expect(parsed.completed).toBe(true);
    expect(parsed.skipped).toBe(false);
  });

  test('should not show tour on subsequent visits after completion', async ({ page }) => {
    await page.goto('http://localhost:3000');
    await page.getByLabel('Skip tour').click();

    await page.reload();
    const overlay = page.locator('[style*="z-[9999]"]');
    await expect(overlay).not.toBeVisible();
  });

  test('should handle keyboard navigation', async ({ page }) => {
    await page.goto('http://localhost:3000');

    await page.keyboard.press('ArrowRight');
    await expect(page.getByText('Your Stock Watchlist')).toBeVisible();

    await page.keyboard.press('ArrowLeft');
    await expect(page.getByText('Welcome to TickerPulse!')).toBeVisible();

    await page.keyboard.press('Escape');
    const overlay = page.locator('[style*="z-[9999]"]');
    await expect(overlay).not.toBeVisible();
  });

  test('should display step indicators correctly', async ({ page }) => {
    await page.goto('http://localhost:3000');

    for (let i = 1; i <= 8; i++) {
      await expect(page.getByText(`Step ${i} of 8`)).toBeVisible();
      if (i < 8) {
        await page.getByLabel('Next step').click();
      }
    }
  });
});
