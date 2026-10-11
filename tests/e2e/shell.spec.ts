import { expect, test } from '@playwright/test';

test('live health, disabled intake, navigation and responsive layout', async ({ page }, info) => {
  await page.goto('/');
  await expect(page.getByRole('heading', { name: 'FilingGuard-AI' })).toBeVisible();
  await expect(page.getByText('API connected')).toBeVisible();
  await expect(page.getByRole('button', { name: 'Prepare document' })).toBeDisabled();
  await expect(page.getByRole('button', { name: 'Upload PDF' })).toBeDisabled();
  await page.keyboard.press('Tab');
  await expect(page.getByRole('link', { name: 'Skip to content' })).toBeFocused();
  await page.keyboard.press('Enter');
  await expect(page.getByRole('main')).toBeFocused();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await page.getByRole('heading', { name: 'FilingGuard-AI' }).click();
  await page.screenshot({ path: `../../.runtime/shell-${info.project.name}.png`, fullPage: true });
  const menu = page.getByRole('button', { name: 'Open navigation' });
  if (await menu.isVisible()) await menu.click();
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

test('reviewed sample labels provenance, exposes conditions and resets', async ({ page }, info) => {
  await page.goto('/');
  await page.getByRole('button', { name: 'Open reviewed sample' }).click();
  await expect(page.getByRole('heading', { name: 'Reviewed sample' })).toBeVisible();
  await expect(page.getByText('Codex (AI assistant)', { exact: false })).toBeVisible();
  await expect(page.getByText('Analysis not run', { exact: true })).toBeVisible();
  await expect(page.locator('.scenario-button')).toHaveCount(18);
  await page.getByRole('button', { name: 'quote altered Quotation / Conditional' }).click();
  const evidence = page.getByRole('region', { name: 'Selected scenario evidence' });
  await expect(evidence.getByText('Separate educational facilities are inherently equal.', { exact: true })).toBeVisible();
  await expect(evidence.getByText('Separate educational facilities are inherently unequal.', { exact: true })).toBeVisible();
  await expect(evidence.getByText(/Meaning is reversed despite high character similarity/)).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  expect(await page.getByRole('img', { name: 'FilingGuard AI', exact: true }).evaluate(
    (element: HTMLImageElement) => element.complete && element.naturalWidth > 0,
  )).toBe(true);
  await page.screenshot({ path: `../../.runtime/demo-${info.project.name}.png`, fullPage: true });
  await page.getByRole('button', { name: 'Reset sample' }).click();
  await expect(page.getByRole('heading', { name: 'FilingGuard-AI' })).toBeVisible();
  await expect(evidence).toHaveCount(0);
  await page.getByRole('button', { name: 'Open reviewed sample' }).click();
  await expect(page.locator('.scenario-button')).toHaveCount(18);
  await expect(evidence).toHaveCount(0);
});

test('sample request failure is explicit and retry restores only demo data', async ({ page }) => {
  await page.route('**/api/v1/demos/**', route => route.fulfill({ status: 503, body: '{}' }));
  await page.goto('/');
  await page.getByRole('button', { name: 'Open reviewed sample' }).click();
  await expect(page.getByRole('alert')).toContainText('Reviewed sample unavailable');
  await expect(page.locator('.scenario-button')).toHaveCount(0);
  await page.unroute('**/api/v1/demos/**');
  await page.getByRole('button', { name: 'Retry sample' }).click();
  await expect(page.locator('.scenario-button')).toHaveCount(18);
});
