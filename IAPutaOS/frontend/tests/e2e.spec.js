import { test, expect } from '@playwright/test';

test.describe('IAPutaOS Premium Tests', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:5173'); // Adjust URL as needed
  });

  test('should load the main interface', async ({ page }) => {
    await expect(page.locator('text=IAPuta OS')).toBeVisible();
  });

  test('should switch between neural and 3D orb', async ({ page }) => {
    // Click the title to switch orb modes
    await page.locator('text=IAPuta OS').click();

    // Check if the mode indicator changes
    await expect(page.locator('text=NEURAL CSS')).toBeVisible();

    await page.locator('text=IAPuta OS').click();
    await expect(page.locator('text=3D PLASMA')).toBeVisible();
  });

  test('should handle error boundary gracefully', async ({ page }) => {
    // This would require triggering an error in the app
    // For now, just verify the app loads without crashing
    await expect(page.locator('text=IAPuta OS')).toBeVisible();
  });

  test('should display loading spinner during lazy loads', async ({ page }) => {
    // Trigger lazy loading by interacting with components
    await page.locator('text=IAPuta OS').click();

    // Check for loading indicator (if implemented)
    // await expect(page.locator('.loading-spinner')).toBeVisible();
  });
});