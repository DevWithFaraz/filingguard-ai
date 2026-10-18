import { expect, test } from '@playwright/test';
import { readFile } from 'node:fs/promises';

test.use({ baseURL: process.env.FILINGGUARD_E2E_BASE_URL || 'http://127.0.0.1:5174', reducedMotion: 'reduce' });
test.describe.configure({ mode: 'serial' });

test('local review to masked evidence, graph list and authenticated saved reports', async ({ page, browser }, info) => {
  test.setTimeout(180000);
  const errors: string[] = [];
  page.on('pageerror', error => errors.push(error.message));
  const name = 'Synthetic <b>browser</b> review';
  const identifier = '123-45-6789';
  await page.goto('/');
  await expect(page.getByRole('textbox', { name: 'Filing text' })).toBeEnabled();
  await page.getByRole('textbox', { name: 'Filing text' }).fill(
    `SSN ${identifier}. This identifier is synthetic.\n\n` +
    'The court explained “Equal access is a fundamental public right.” Brown v. Board, 347 U.S. 483 (1954).',
  );
  await page.getByRole('textbox', { name: 'Document name' }).fill(name);
  await page.getByRole('button', { name: 'Prepare document' }).focus();
  await page.keyboard.press('Enter');
  await expect(page.getByRole('heading', { name })).toBeVisible();
  const documentURL = page.url();
  await page.getByRole('button', { name: 'Run local checks' }).focus();
  await page.keyboard.press('Enter');
  await expect(page.getByRole('link', { name: 'Open review results' })).toBeVisible({ timeout: 100000 });
  const graphResponse = page.waitForResponse(response => response.url().endsWith('/graph'));
  const savedResponse = page.waitForResponse(response => response.url().endsWith('/results'));
  await page.getByRole('link', { name: 'Open review results' }).focus();
  await page.keyboard.press('Enter');
  await expect(page.getByRole('heading', { name: 'Review results', exact: true })).toBeVisible();
  await expect(page.getByText('Incomplete review · partial')).toBeVisible();
  await expect(page.locator('.result-score-number')).toHaveText('Unknown');
  expect(await page.locator('.results-view').innerText()).not.toContain(identifier);
  const resultURL = page.url();
  await page.getByRole('navigation', { name: 'Results sections' }).getByRole('link', { name: 'Report' }).click();
  await expect(page.locator('#result-report')).toBeInViewport();
  await page.getByRole('navigation', { name: 'Results sections' }).getByRole('link', { name: 'Overview' }).click();
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.screenshot({ path: info.outputPath('results-top.png'), animations: 'disabled' });
  const savedResults = await (await savedResponse).json() as {
    score: { categories: { type: string; eligible: number; evaluated: number; value: number | null; deducted_points: number }[] };
  };
  const categories = page.locator('.result-category-scores li');
  await expect(categories).toHaveCount(savedResults.score.categories.length);
  for (const [index, category] of savedResults.score.categories.entries()) {
    await expect(categories.nth(index)).toContainText(category.type.replaceAll('_', ' '));
    await expect(categories.nth(index)).toContainText(category.value === null ? 'Unknown' : `${category.value}/100`);
    await expect(categories.nth(index)).toContainText(`${category.evaluated}/${category.eligible} evaluated`);
  }
  const savedGraph = await (await graphResponse).json() as {
    nodes: { id: string; label: string; kind: string; status: string; finding_ids: string[] }[];
    edges: { id: string; source: string; target: string; label: string }[];
  };

  await page.getByLabel('Finding category').selectOption('privacy');
  const finding = page.locator('.results-finding-list').getByRole('button', { name: /SSN-shaped identifier/ });
  await finding.focus();
  const evidenceResponse = page.waitForResponse(response => response.url().includes('/findings/') && response.url().endsWith('/evidence'));
  await page.keyboard.press('Enter');
  const evidence = await evidenceResponse;
  expect(evidence.ok()).toBe(true);
  expect(evidence.request().headers().authorization).toMatch(/^Bearer [A-Za-z0-9_-]{43}$/);
  await expect(page.locator('.result-detail .result-evidence')).toBeVisible();
  expect(await page.locator('.result-detail').innerText()).not.toContain(identifier);
  await expect(page.locator('.result-detail .result-hash')).toHaveText(/^[a-f0-9]{64}$/);
  await expect(page.locator('.result-detail')).toContainText('Unicode code points');
  await expect(page.locator('.result-detail')).toContainText('Next review action');

  await page.getByLabel('Finding category').selectOption('quote');
  await page.locator('.results-finding-list').getByRole('button', { name: /Quotation source comparison unavailable/ }).focus();
  await page.keyboard.press('Enter');
  await expect(page.locator('.result-detail h2')).toHaveText('Quotation source comparison unavailable');
  await expect(page.locator('.result-detail')).toContainText('legal support');
  await expect(page.locator('.result-detail .result-evidence')).toBeVisible();
  await page.getByText('Quotation checks (1)', { exact: true }).click();
  await expect(page.locator('.results-checks')).toContainText('source unavailable');
  await expect(page.locator('.results-checks')).toContainText('does not establish equivalent meaning');

  await page.locator('.result-graph-list summary').focus();
  await page.keyboard.press('Enter');
  const graphButtons = page.locator('.result-graph-list > ul > li > button');
  await expect(graphButtons).toHaveCount(savedGraph.nodes.length);
  for (const [index, node] of savedGraph.nodes.entries()) {
    await expect(graphButtons.nth(index)).toContainText(node.label);
    await expect(graphButtons.nth(index)).toContainText(node.status.replaceAll('_', ' '));
  }
  await expect(page.locator('.result-graph-list > ul > li > ul > li')).toHaveCount(savedGraph.edges.length);
  await expect(graphButtons.first()).toBeVisible();
  await graphButtons.first().focus();
  await page.keyboard.press('Enter');
  await expect(graphButtons.first()).toHaveAttribute('aria-pressed', 'true');
  await expect(page.locator('.result-detail .result-evidence')).toBeVisible();
  await expect(page.locator('.result-graph-canvas .react-flow__node').first()).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.screenshot({ path: info.outputPath(`results-${info.project.name}.png`), fullPage: true });
  await page.locator('.result-graph-canvas').screenshot({ path: info.outputPath(`graph-${info.project.name}.png`) });

  for (const format of ['markdown', 'html'] as const) {
    const reportResponse = page.waitForResponse(response => response.url().endsWith(`/report?format=${format}`));
    const downloadEvent = page.waitForEvent('download');
    await page.getByRole('button', { name: `Download ${format === 'html' ? 'HTML' : 'Markdown'}` }).focus();
    await page.keyboard.press('Enter');
    const response = await reportResponse;
    expect(response.ok()).toBe(true);
    expect(response.request().headers().authorization).toMatch(/^Bearer [A-Za-z0-9_-]{43}$/);
    const download = await downloadEvent;
    expect(download.suggestedFilename()).toBe(`filingguard-${resultURL.split('/').at(-2)}.${format === 'html' ? 'html' : 'md'}`);
    const target = info.outputPath(`saved-report.${format === 'html' ? 'html' : 'md'}`);
    await download.saveAs(target);
    const report = await readFile(target, 'utf8');
    expect(report).not.toContain(identifier);
    expect(report).toContain('partial');
    expect(report).toContain('Quotation source comparison unavailable');
    if (format === 'html') {
      expect(report).toContain('&lt;b&gt;browser&lt;/b&gt;');
      expect(report).not.toContain('<b>browser</b>');
    }
  }
  expect(errors).toEqual([]);
  const outsiderContext = await browser.newContext();
  const outsider = await outsiderContext.newPage();
  await outsider.goto(resultURL);
  await expect(outsider.getByRole('heading', { name: 'Results unavailable' })).toBeVisible();
  await expect(outsider.locator('.results-finding-list')).toHaveCount(0);
  await outsiderContext.close();

  await page.getByRole('link', { name: 'Activity', exact: true }).click();
  await expect(page.locator('.activity-list')).toContainText('partial');
  await expect(page.locator('.activity-list')).not.toContainText('Legal analysis not run');
  await page.screenshot({ path: info.outputPath('activity-saved.png'), fullPage: true, animations: 'disabled' });

  await page.goto(documentURL);
  await expect(page.getByRole('heading', { name })).toBeVisible();
  page.once('dialog', dialog => dialog.accept());
  await page.getByRole('button', { name: 'Delete document' }).click();
  await expect(page.getByRole('heading', { name: 'FilingGuard-AI' })).toBeVisible();
  await page.goto(resultURL);
  await expect(page.getByRole('heading', { name: 'Results unavailable' })).toBeVisible();
});
