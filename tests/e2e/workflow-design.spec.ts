import { expect, test } from '@playwright/test';

test.use({ baseURL: process.env.FILINGGUARD_E2E_BASE_URL || 'http://127.0.0.1:5174' });
test('shared pages: availability recovery, navigation, sample evidence and motion preferences', async ({ page }, info) => {
  test.setTimeout(60000);
  const errors: string[] = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.route('**/api/v1/capabilities', route => route.fulfill({ status: 503, body: '{}' }));
  await page.goto('/settings');
  await expect(page.getByRole('heading', { name: 'Settings', exact: true })).toBeVisible();
  await expect(page.getByRole('alert')).toContainText('Availability could not be confirmed');
  await expect(page.getByText('Availability unknown', { exact: true })).toHaveCount(2);
  await page.unroute('**/api/v1/capabilities');
  await page.getByRole('button', { name: 'Retry availability' }).click();
  await expect(page.getByText('Available · private sessions', { exact: true })).toBeVisible();
  await expect(page.getByRole('link', { name: 'Settings', exact: true })).toHaveAttribute('aria-current', 'page');
  await page.screenshot({ path: info.outputPath('settings.png'), fullPage: true, animations: 'disabled' });
  await page.getByRole('link', { name: 'Activity', exact: true }).click();
  await expect(page.getByRole('main')).toBeFocused();
  await expect(page.getByRole('heading', { name: 'No reviews yet' })).toBeVisible();
  await page.screenshot({ path: info.outputPath('activity-empty.png'), fullPage: true, animations: 'disabled' });
  await page.getByRole('link', { name: 'Privacy & limits', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Know the boundaries.' })).toBeVisible();
  await page.screenshot({ path: info.outputPath('privacy.png'), fullPage: true, animations: 'disabled' });
  await page.getByRole('link', { name: 'Sample', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Reviewed sample' })).toBeVisible();
  await expect(page.locator('.scenario-button')).toHaveCount(18);
  await page.getByRole('button', { name: 'quote altered Quotation / Conditional' }).focus();
  await page.keyboard.press('Enter');
  const evidence = page.getByRole('region', { name: 'Selected scenario evidence' });
  await expect(evidence).toBeFocused();
  await expect(evidence).toContainText('Meaning is reversed despite high character similarity');
  await page.locator('.demo-filing details summary').focus();
  await page.keyboard.press('Enter');
  await expect(page.locator('.demo-filing code')).toBeVisible();
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.screenshot({ path: info.outputPath('sample.png'), fullPage: true, animations: 'disabled' });
  await page.emulateMedia({ reducedMotion: 'no-preference' });
  expect(await page.locator('.workflow-route').evaluate(el => getComputedStyle(el).animationName)).toBe('workflow-reveal');
  await page.emulateMedia({ reducedMotion: 'reduce' });
  expect(await page.locator('.workflow-route').evaluate(el => getComputedStyle(el).animationName)).toBe('none');
  await page.emulateMedia({ reducedMotion: 'reduce', contrast: 'more' });
  for (const route of ['/settings', '/activity', '/privacy', '/not-a-page']) {
    await page.goto(route);
    await expect(page.locator('.workflow-hero')).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  }
  await expect(page.getByRole('heading', { name: 'Page not found' })).toBeVisible();
  await page.screenshot({ path: info.outputPath('not-found.png'), fullPage: true, animations: 'disabled' });
  for (const width of [320, 768, 1440]) {
    await page.setViewportSize({ width, height: 900 });
    for (const route of ['/settings', '/privacy', '/demo']) {
      await page.goto(route);
      await expect(page.locator('.workflow-hero')).toBeVisible();
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    }
  }
  await page.goto('/not-a-page');
  await page.getByRole('link', { name: 'Return to review' }).click();
  await expect(page.getByRole('heading', { name: 'FilingGuard-AI' })).toBeVisible();
  expect(errors).toEqual([]);
});
