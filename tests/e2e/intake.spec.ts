import { expect, test, type Page } from '@playwright/test';
import path from 'node:path';

test.use({ baseURL: process.env.FILINGGUARD_E2E_BASE_URL || 'http://127.0.0.1:5174' });
// One API preparation slot is deliberate. Cross-project requests must not compete.
test.describe.configure({ mode: 'serial' });

test('text preparation, private reload, activity summary, ownership and deletion', async ({ page, browser }, info) => {
  test.setTimeout(60000);
  await page.goto('/');
  await expect(page.getByRole('textbox', { name: 'Filing text' })).toBeEnabled();
  const text = 'Synthetic claim with 😀 Unicode.\n\nSSN 123-45-6789. This is synthetic.';
  await page.getByRole('textbox', { name: 'Filing text' }).fill(text);
  await page.getByRole('textbox', { name: 'Document name' }).fill('Synthetic browser filing');
  await page.getByRole('checkbox', { name: 'Generative AI used in this filing' }).check();
  await page.getByRole('button', { name: 'Prepare document' }).click();
  await expect(page.getByRole('heading', { name: 'Synthetic browser filing' })).toBeVisible();
  await expect(page.getByText('Document prepared. Local checks have not run. No legal analysis or filing integrity score.')).toBeVisible();
  await page.getByRole('button', { name: 'Run local checks' }).click();
  await expect(page.getByText(/Review partial ·/)).toBeVisible({ timeout: 30000 });
  await page.locator('.document-findings summary').click();
  await expect(page.getByText('SSN-shaped identifier')).toBeVisible();
  expect(await page.locator('.finding-list').innerText()).not.toContain('123-45-6789');
  await expect(page.locator('.paragraph-list li')).toHaveCount(2);
  await expect(page.getByText(/Semantic review is disabled/)).toBeVisible();
  const resultURL = page.url();
  await page.reload();
  await expect(page.getByRole('heading', { name: 'Synthetic browser filing' })).toBeVisible();
  const outsiderContext = await browser.newContext();
  const outsider = await outsiderContext.newPage();
  await outsider.goto(resultURL);
  await expect(outsider.getByRole('heading', { name: 'Document unavailable' })).toBeVisible();
  await expect(outsider.locator('.paragraph-list')).toHaveCount(0);
  await outsiderContext.close();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await page.screenshot({ path: `../../.runtime/intake-text-${info.project.name}.png`, fullPage: true });
  const activityResponse = page.waitForResponse(response => response.url().endsWith('/api/v1/analyses'));
  await page.getByRole('link', { name: 'Activity', exact: true }).click();
  const activity = await activityResponse;
  expect(await activity.text()).not.toContain('123-45-6789');
  await page.getByRole('link', { name: 'Synthetic browser filing' }).click();
  page.once('dialog', dialog => dialog.accept());
  await page.getByRole('button', { name: 'Delete document' }).click();
  await expect(page.getByRole('heading', { name: 'FilingGuard-AI' })).toBeVisible();
  await page.goto(resultURL);
  await expect(page.getByRole('heading', { name: 'Document unavailable' })).toBeVisible();
  await pdfWorkflow(page, info.project.name);
});

async function pdfWorkflow(page: Page, project: string) {
  await page.goto('/');
  await page.getByRole('button', { name: 'PDF', exact: true }).click();
  await page.getByLabel('PDF file').setInputFiles(path.resolve('../../data/demo/curated-v1/filing.pdf'));
  await expect(page.getByRole('button', { name: 'Prepare document' })).toBeEnabled();
  await page.getByRole('button', { name: 'Prepare document' }).click();
  await expect(page.getByRole('heading', { name: 'filing.pdf' })).toBeVisible();
  await page.locator('.document-details summary').click();
  await expect(page.getByText('pypdf-bounded-v1')).toBeVisible();
  await expect(page.locator('.paragraph-list li').first()).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await page.screenshot({ path: `../../.runtime/intake-pdf-${project}.png`, fullPage: true });
  await page.getByRole('main').getByRole('link', { name: 'New document', exact: true }).click();
  await page.getByRole('button', { name: 'PDF', exact: true }).click();
  await page.getByLabel('PDF file').setInputFiles({ name: 'bad.pdf', mimeType: 'application/pdf', buffer: Buffer.from('%PDF-invalid') });
  await page.getByRole('button', { name: 'Prepare document' }).click();
  await expect(page.getByRole('alert')).toContainText('paste text instead');
  await page.getByRole('button', { name: 'Demo', exact: true }).click();
  await page.getByRole('button', { name: 'Prepare document' }).click();
  await expect(page.getByRole('heading', { name: 'Curated synthetic filing' })).toBeVisible();
  await expect(page.getByText('Demo', { exact: true })).toBeVisible();
  await expect(page.getByText('Document prepared. Local checks have not run. No legal analysis or filing integrity score.')).toBeVisible();
}
