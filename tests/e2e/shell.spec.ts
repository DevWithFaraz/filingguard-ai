import { expect, test } from '@playwright/test';

test('live health, disabled intake, navigation and responsive layout', async ({ page }, info) => {
  await page.goto('/');
  await expect(page.getByRole('heading', { name: 'New review' })).toBeVisible();
  await expect(page.getByText('API connected')).toBeVisible();
  await expect(page.getByRole('button', { name: 'Run review' })).toBeDisabled();
  await expect(page.getByRole('button', { name: 'Upload PDF' })).toBeDisabled();
  await page.keyboard.press('Tab');
  await expect(page.getByRole('link', { name: 'Skip to content' })).toBeFocused();
  await page.keyboard.press('Enter');
  await expect(page.getByRole('main')).toBeFocused();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await page.getByRole('heading', { name: 'New review' }).click();
  await page.screenshot({ path: `../../.runtime/shell-${info.project.name}.png`, fullPage: true });
  await page.getByRole('link', { name: 'Activity', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'No reviews yet' })).toBeVisible();
  await page.getByRole('link', { name: 'Settings', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Settings', exact: true })).toBeVisible();
});

test('connection failure is visible and can be retried', async ({ page }) => {
  await page.route('**/api/v1/health', route => route.fulfill({ status: 503, body: '{}' }));
  await page.goto('/');
  await expect(page.getByText('API unavailable')).toBeVisible();
  await page.unroute('**/api/v1/health');
  await page.getByRole('button', { name: 'Refresh API connection' }).click();
  await expect(page.getByText('API connected')).toBeVisible();
});
