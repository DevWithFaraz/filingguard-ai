import { expect, test } from '@playwright/test';
import { performance } from 'node:perf_hooks';

test.use({ baseURL: process.env.FILINGGUARD_E2E_BASE_URL || 'http://127.0.0.1:5174', reducedMotion: 'reduce' });

for (const maximum of [false, true]) test(maximum ? 'maximum text review timing' : 'normal cached demo timing', async ({ page }, info) => {
  test.skip(maximum && info.project.name !== 'desktop', 'Maximum input measured once on desktop');
  test.setTimeout(300000);
  const measurements: { input: string; initial_progress_ms: number; analysis_ms: number; dashboard_ms: number }[] = [];
  for (let trial = maximum ? 3 : 0; trial < (maximum ? 4 : 3); trial++) {
    await page.goto('/');
    await expect(page.getByRole('textbox', { name: 'Filing text' })).toBeEnabled();
    if (trial === 3) {
      // Exactly 100,000 Unicode characters and 2,000 paragraphs, both accepted maxima.
      const text = Array.from({ length: 2000 }, () => 'Synthetic maximum input. ' + 'x'.repeat(23)).join('\n\n') + 'xx';
      expect(text.length).toBe(100000);
      await page.getByRole('textbox', { name: 'Filing text' }).fill(text);
    } else {
      await page.getByRole('button', { name: 'Demo', exact: true }).click();
    }
    const prepareResponse = page.waitForResponse(r => r.request().method() === 'POST' && /\/analyses\/(text|demo)$/.test(r.url()));
    const prepareBegan = performance.now();
    await page.getByRole('button', { name: 'Prepare document' }).click();
    const prepared = await prepareResponse;
    await info.attach(`preparation-${trial + 1}`, { body: JSON.stringify({ status: prepared.status(), elapsed_ms: Math.round(performance.now() - prepareBegan) }), contentType: 'application/json' });
    expect(prepared.status()).toBe(201);
    await expect(page.getByRole('button', { name: 'Run local checks' })).toBeVisible({ timeout: 30000 });
    const documentURL = page.url();
    const began = performance.now();
    await page.getByRole('button', { name: 'Run local checks' }).click();
    await expect(page.locator('.local-review [role="status"]').first()).toContainText(/Review (in progress|completed|partial)/);
    const progress = performance.now() - began;
    await expect(page.getByRole('link', { name: 'Open review results' })).toBeVisible({ timeout: 100000 });
    const analysis = performance.now() - began;
    const dashboardBegan = performance.now();
    await page.getByRole('link', { name: 'Open review results' }).click();
    await expect(page.locator('.result-category-scores li')).toHaveCount(6);
    if (trial < 3) await expect(page.locator('.result-graph-list summary')).toBeVisible();
    else await expect(page.locator('#result-relationships')).toContainText('No persisted sections, claims or authorities');
    const dashboard = performance.now() - dashboardBegan;
    measurements.push({ input: trial === 3 ? '100000 characters / 2000 paragraphs' : `cached demo ${trial + 1}`, initial_progress_ms: Math.round(progress), analysis_ms: Math.round(analysis), dashboard_ms: Math.round(dashboard) });
    await info.attach(`timing-${trial + 1}`, { body: JSON.stringify(measurements.at(-1)), contentType: 'application/json' });
    expect(progress).toBeLessThanOrEqual(2000);
    if (trial < 3) expect(analysis).toBeLessThanOrEqual(60000);
    expect(dashboard).toBeLessThanOrEqual(3000);
    await page.goto(documentURL);
    if (trial === 3) {
      page.once('dialog', dialog => dialog.accept());
      await page.getByRole('button', { name: 'Delete document' }).click();
    } else await page.getByRole('button', { name: 'Reset demo' }).click();
    await expect(page.getByRole('textbox', { name: 'Filing text' })).toBeVisible();
  }
  await info.attach('timings', { body: JSON.stringify({ scope: 'Local Windows / Vite development server / cached public sources / model disabled / emulated mobile', measurements }, null, 2), contentType: 'application/json' });
});
