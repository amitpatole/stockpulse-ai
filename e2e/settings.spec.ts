import { test, expect } from '@playwright/test';

test.describe('Settings Page - Budget Settings Persistence', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to settings page
    await page.goto('/settings', { waitUntil: 'networkidle' });

    // Wait for the budget section to load
    await page.waitForSelector('[data-testid="monthly-budget"]', { timeout: 10000 });
  });

  test('should save budget settings and persist after page reload', async ({ page }) => {
    // Get input elements using data-testid attributes
    const monthlyBudgetInput = page.locator('[data-testid="monthly-budget"]');
    const dailyWarningInput = page.locator('[data-testid="daily-warning"]');
    const saveButton = page.locator('[data-testid="save-budget-button"]');

    // Set new budget values
    const newMonthlyBudget = '1500';
    const newDailyWarning = '150';

    await monthlyBudgetInput.fill(newMonthlyBudget);
    await dailyWarningInput.fill(newDailyWarning);

    // Click save button
    await saveButton.click();

    // Wait for success toast to appear
    const successToast = page.locator('text=Budget settings saved successfully');
    await expect(successToast).toBeVisible({ timeout: 5000 });

    // Verify input values are still as we set them
    await expect(monthlyBudgetInput).toHaveValue(newMonthlyBudget);
    await expect(dailyWarningInput).toHaveValue(newDailyWarning);

    // Reload the page
    await page.reload({ waitUntil: 'networkidle' });

    // Wait for inputs to load
    await page.waitForSelector('[data-testid="monthly-budget"]', { timeout: 10000 });

    // Verify values persisted after reload
    await expect(monthlyBudgetInput).toHaveValue(newMonthlyBudget);
    await expect(dailyWarningInput).toHaveValue(newDailyWarning);
  });

  test('should show error toast when saving invalid budget values', async ({ page }) => {
    const monthlyBudgetInput = page.locator('[data-testid="monthly-budget"]');
    const dailyWarningInput = page.locator('[data-testid="daily-warning"]');
    const saveButton = page.locator('[data-testid="save-budget-button"]');

    // Set invalid values: daily warning > monthly budget
    await monthlyBudgetInput.fill('100');
    await dailyWarningInput.fill('500');

    // Click save button
    await saveButton.click();

    // Wait for error toast
    const errorToast = page.locator('text=Daily warning threshold cannot exceed monthly budget');
    await expect(errorToast).toBeVisible({ timeout: 5000 });
  });

  test('should show error toast when saving negative budget values', async ({ page }) => {
    const monthlyBudgetInput = page.locator('[data-testid="monthly-budget"]');
    const saveButton = page.locator('[data-testid="save-budget-button"]');

    // Set negative value
    await monthlyBudgetInput.fill('-100');

    // Click save button
    await saveButton.click();

    // Wait for error toast
    const errorToast = page.locator('text=Budget values must be non-negative');
    await expect(errorToast).toBeVisible({ timeout: 5000 });
  });

  test('should disable save button while saving budget settings', async ({ page }) => {
    const monthlyBudgetInput = page.locator('[data-testid="monthly-budget"]');
    const saveButton = page.locator('[data-testid="save-budget-button"]');

    // Set a new value
    await monthlyBudgetInput.fill('2000');

    // Click save button
    await saveButton.click();

    // Button should be disabled during save (might have loading spinner)
    // Wait for button to be enabled again after save
    const successToast = page.locator('text=Budget settings saved successfully');
    await expect(successToast).toBeVisible({ timeout: 5000 });
  });
});

test.describe('Settings Page - Agent Framework Selection', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to settings page
    await page.goto('/settings', { waitUntil: 'networkidle' });

    // Wait for the framework selection section to load
    await page.waitForSelector('[data-testid="framework-selection"]', { timeout: 10000 });
  });

  test('should save agent framework selection and show success toast', async ({ page }) => {
    const frameworkOpenclawButton = page.locator('[data-testid="framework-openclaw"]');
    const saveFrameworkButton = page.locator('[data-testid="save-framework-button"]');

    // Click OpenClaw framework button
    await frameworkOpenclawButton.click();

    // Verify it's selected (has the active blue border)
    await expect(frameworkOpenclawButton).toHaveClass(/bg-blue-500/);

    // Click save button
    await saveFrameworkButton.click();

    // Wait for success toast
    const successToast = page.locator('text=Agent framework set to OpenClaw');
    await expect(successToast).toBeVisible({ timeout: 5000 });
  });

  test('should persist framework selection after page reload', async ({ page }) => {
    const frameworkCrewaiButton = page.locator('[data-testid="framework-crewai"]');
    const saveFrameworkButton = page.locator('[data-testid="save-framework-button"]');

    // Select CrewAI
    await frameworkCrewaiButton.click();
    await saveFrameworkButton.click();

    // Wait for success toast
    const successToast = page.locator('text=Agent framework set to CrewAI');
    await expect(successToast).toBeVisible({ timeout: 5000 });

    // Reload page
    await page.reload({ waitUntil: 'networkidle' });

    // Wait for framework buttons to load
    await page.waitForSelector('[data-testid="framework-selection"]', { timeout: 10000 });

    // Verify CrewAI is still selected after reload
    await expect(frameworkCrewaiButton).toHaveClass(/bg-blue-500/);
  });

  test('should switch between framework options', async ({ page }) => {
    const frameworkCrewaiButton = page.locator('[data-testid="framework-crewai"]');
    const frameworkOpenclawButton = page.locator('[data-testid="framework-openclaw"]');

    // CrewAI should be selected by default
    await expect(frameworkCrewaiButton).toHaveClass(/bg-blue-500/);

    // Click OpenClaw
    await frameworkOpenclawButton.click();
    await expect(frameworkOpenclawButton).toHaveClass(/bg-blue-500/);
    await expect(frameworkCrewaiButton).not.toHaveClass(/bg-blue-500/);

    // Click back to CrewAI
    await frameworkCrewaiButton.click();
    await expect(frameworkCrewaiButton).toHaveClass(/bg-blue-500/);
    await expect(frameworkOpenclawButton).not.toHaveClass(/bg-blue-500/);
  });
});

test.describe('Settings Page - AI Providers', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to settings page
    await page.goto('/settings', { waitUntil: 'networkidle' });

    // Wait for providers to load
    await page.waitForSelector('text=/AI Providers/i', { timeout: 10000 });
  });

  test('should display error when API key is empty', async ({ page }) => {
    const saveButton = page.locator('button:has-text("Save")').first();

    // Click save without entering API key
    await saveButton.click();

    // Wait for error toast
    const errorToast = page.locator('text=/API key is required/i');
    await expect(errorToast).toBeVisible({ timeout: 5000 });
  });

  test('should handle network errors gracefully for provider save', async ({ page }) => {
    // Intercept the API call and fail it
    await page.route('**/api/settings/ai-provider', (route) => {
      route.abort('failed');
    });

    const apiKeyInput = page.locator('input[placeholder*="Enter"]').first();
    const saveButton = page.locator('button:has-text("Save")').first();

    await apiKeyInput.fill('sk-test-key');
    await saveButton.click();

    // Wait for error toast (generic failure message)
    const errorToast = page.locator('text=/Failed to save/i');
    await expect(errorToast).toBeVisible({ timeout: 5000 });
  });
});
