import { test, expect } from '@playwright/test';

test.describe('Settings Persistence - Verify Data Survives Page Reload', () => {
  test('should persist budget settings after page reload', async ({ page }) => {
    // Navigate to settings page
    await page.goto('/settings');

    // Wait for page to load
    await page.waitForSelector('text=/Cost Budget/i', { timeout: 5000 });

    // Scroll to budget section
    await page.locator('text=/Cost Budget/i').scrollIntoViewIfNeeded();

    // Find budget inputs
    const monthlyBudgetInput = page.locator('input[type="number"]').nth(0);
    const dailyWarningInput = page.locator('input[type="number"]').nth(1);
    const saveBudgetButton = page.locator('button:has-text("Save Budget Settings")');

    // Set new values
    await monthlyBudgetInput.clear();
    await monthlyBudgetInput.fill('150');

    await dailyWarningInput.clear();
    await dailyWarningInput.fill('15');

    // Save settings
    await saveBudgetButton.click();

    // Wait for success toast
    const successToast = page.locator('text=/saved successfully/i');
    await expect(successToast).toBeVisible({ timeout: 5000 });

    // Reload the page
    await page.reload();

    // Wait for page to reload and providers to load
    await page.waitForSelector('text=/Cost Budget/i', { timeout: 5000 });

    // Scroll to budget section again
    await page.locator('text=/Cost Budget/i').scrollIntoViewIfNeeded();

    // Verify the values persisted
    const monthlyBudgetInputAfter = page.locator('input[type="number"]').nth(0);
    const dailyWarningInputAfter = page.locator('input[type="number"]').nth(1);

    await expect(monthlyBudgetInputAfter).toHaveValue('150');
    await expect(dailyWarningInputAfter).toHaveValue('15');
  });

  test('should persist agent framework selection after page reload', async ({ page }) => {
    // Navigate to settings page
    await page.goto('/settings');

    // Wait for page to load
    await page.waitForSelector('text=/Agent Framework/i', { timeout: 5000 });

    // Scroll to Agent Framework section
    await page.locator('text=/Agent Framework/i').scrollIntoViewIfNeeded();

    // Find and click OpenClaw button
    const openclawButton = page.locator('button:has-text("OpenClaw")');
    await openclawButton.click();

    // Find the save button for framework
    const saveFrameworkButton = page.locator('button:has-text("Save Framework Selection")');
    await saveFrameworkButton.click();

    // Wait for success toast
    const successToast = page.locator('text=/Agent framework set/i');
    await expect(successToast).toBeVisible({ timeout: 5000 });

    // Reload the page
    await page.reload();

    // Wait for page to reload
    await page.waitForSelector('text=/Agent Framework/i', { timeout: 5000 });

    // Scroll to Agent Framework section again
    await page.locator('text=/Agent Framework/i').scrollIntoViewIfNeeded();

    // Verify OpenClaw is still selected (has blue highlight)
    const selectedOpenclawButton = page.locator('button:has-text("OpenClaw")');
    await expect(selectedOpenclawButton).toHaveClass(/border-blue-500/);
  });

  test('should handle concurrent saves without losing data', async ({ page }) => {
    // Navigate to settings page
    await page.goto('/settings');

    // Wait for page to load
    await page.waitForSelector('text=/Cost Budget/i', { timeout: 5000 });

    // Scroll to budget section
    await page.locator('text=/Cost Budget/i').scrollIntoViewIfNeeded();

    // Set budget values
    const monthlyBudgetInput = page.locator('input[type="number"]').nth(0);
    const dailyWarningInput = page.locator('input[type="number"]').nth(1);
    const saveBudgetButton = page.locator('button:has-text("Save Budget Settings")');

    await monthlyBudgetInput.clear();
    await monthlyBudgetInput.fill('200');

    await dailyWarningInput.clear();
    await dailyWarningInput.fill('20');

    // Save and immediately reload
    await saveBudgetButton.click();

    // Wait a moment for the request to start
    await page.waitForTimeout(500);

    // Reload while save is in progress
    await page.reload();

    // Wait for page to reload and settle
    await page.waitForSelector('text=/Cost Budget/i', { timeout: 5000 });

    // Scroll and check values
    await page.locator('text=/Cost Budget/i').scrollIntoViewIfNeeded();

    const monthlyBudgetInputAfter = page.locator('input[type="number"]').nth(0);
    const dailyWarningInputAfter = page.locator('input[type="number"]').nth(1);

    // Values should either be persisted or reset to defaults, but not corrupted
    const monthlyValue = await monthlyBudgetInputAfter.inputValue();
    const dailyValue = await dailyWarningInputAfter.inputValue();

    // Should be a valid number
    expect(parseFloat(monthlyValue)).toBeGreaterThanOrEqual(0);
    expect(parseFloat(dailyValue)).toBeGreaterThanOrEqual(0);
  });

  test('should validate budget values on save', async ({ page }) => {
    // Navigate to settings page
    await page.goto('/settings');

    // Wait for page to load
    await page.waitForSelector('text=/Cost Budget/i', { timeout: 5000 });

    // Scroll to budget section
    await page.locator('text=/Cost Budget/i').scrollIntoViewIfNeeded();

    const monthlyBudgetInput = page.locator('input[type="number"]').nth(0);
    const dailyWarningInput = page.locator('input[type="number"]').nth(1);
    const saveBudgetButton = page.locator('button:has-text("Save Budget Settings")');

    // Try to set daily warning > monthly budget
    await monthlyBudgetInput.clear();
    await monthlyBudgetInput.fill('10');

    await dailyWarningInput.clear();
    await dailyWarningInput.fill('50');

    // Click save
    await saveBudgetButton.click();

    // Should show error toast about validation
    const errorToast = page.locator('text=/cannot exceed|invalid|error/i');
    await expect(errorToast).toBeVisible({ timeout: 5000 });

    // Values should not have been saved, so reload and verify
    await page.reload();

    await page.waitForSelector('text=/Cost Budget/i', { timeout: 5000 });
    await page.locator('text=/Cost Budget/i').scrollIntoViewIfNeeded();

    const monthlyAfter = page.locator('input[type="number"]').nth(0);
    const dailyAfter = page.locator('input[type="number"]').nth(1);

    // Should not be the invalid values we tried to set
    const monthlyVal = await monthlyAfter.inputValue();
    const dailyVal = await dailyAfter.inputValue();

    // Either defaults or previously saved values, but not the invalid ones
    expect(parseFloat(monthlyVal)).not.toBe(10);
    expect(parseFloat(dailyVal)).not.toBe(50);
  });
});
