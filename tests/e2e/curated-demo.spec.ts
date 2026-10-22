import { expect, test } from '@playwright/test';
import { readFile } from 'node:fs/promises';
import { performance } from 'node:perf_hooks';
import { resolve } from 'node:path';
import type { components } from '../../apps/web/src/lib/api/schema';

const live = process.env.FILINGGUARD_LIVE_DEMO === '1';
test('curated source demo: sample, choices, execution, saved views, evidence, report and reset', async ({ page }, info) => {
  test.setTimeout(150000);
  const errors: string[] = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.goto('/');
  await page.getByRole('button', { name: 'Demo', exact: true }).click();
  await page.getByLabel('Court profile', { exact: true }).selectOption('unverified');
  await page.getByLabel('Court profile', { exact: true }).selectOption('synthetic-demo-v1');
  await page.getByLabel('Generative AI used in this filing').uncheck();
  await page.getByLabel('Generative AI used in this filing').check();
  await page.getByRole('button', { name: 'Prepare document' }).focus();
  await page.keyboard.press('Enter');
  await expect(page.getByRole('heading', { name: 'Curated synthetic filing' })).toBeVisible();
  await expect(page.getByText(/Cached public opinions for the exact curated sample/)).toBeVisible();
  const documentURL = page.url();
  await expect(page.getByRole('navigation', { name: 'Review steps' })).toBeVisible();
  await expect(page.getByRole('link', { name: /Explore results/ })).toHaveCount(0);
  await page.locator('.document-details summary').focus();
  await page.keyboard.press('Enter');
  await expect(page.getByText('Synthetic demo court', { exact: true })).toBeVisible();
  await page.keyboard.press('Enter');
  await expect(page.getByText('Synthetic demo court', { exact: true })).not.toBeVisible();
  await page.getByRole('link', { name: 'Activity', exact: true }).click();
  await page.getByRole('link', { name: 'Curated synthetic filing', exact: true }).click();
  await expect(page).toHaveURL(documentURL);
  await page.emulateMedia({ reducedMotion: 'no-preference' });
  expect(await page.locator('.prepared-hero').evaluate(el => getComputedStyle(el).animationName)).toBe('document-arrive');
  await page.screenshot({ path: info.outputPath('prepared-page.png'), fullPage: true, animations: 'disabled' });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.emulateMedia({ reducedMotion: 'reduce' });
  expect(await page.locator('.prepared-hero').evaluate(el => getComputedStyle(el).animationName)).toBe('none');
  await page.getByRole('button', { name: 'Run local checks' }).focus();
  const reviewBegan = performance.now();
  await page.keyboard.press('Enter');
  await expect(page.locator('.local-review [role="status"]')).toContainText(/Review (in progress|completed|partial)/);
  const initialProgressMs = Math.round(performance.now() - reviewBegan);
  await expect(page.getByRole('link', { name: 'Open review results' })).toBeVisible({ timeout: 100000 });
  const analysisMs = Math.round(performance.now() - reviewBegan);
  await expect(page.getByRole('link', { name: /Explore results/ })).toBeVisible();
  await page.locator('.document-findings summary').focus();
  await page.keyboard.press('Enter');
  await expect(page.locator('.finding-list')).toBeVisible();
  expect(await page.locator('.finding-list').innerText()).not.toContain('900-12-3456');
  await page.screenshot({ path: info.outputPath('prepared-completed.png'), fullPage: true });
  const savedResponse = page.waitForResponse(response => response.url().endsWith('/results'));
  await page.getByRole('link', { name: 'Open review results' }).focus();
  const dashboardBegan = performance.now();
  await page.keyboard.press('Enter');
  await expect(page.getByRole('heading', { name: 'Review results', exact: true })).toBeVisible();
  const saved = await savedResponse;
  const result = await saved.json() as components['schemas']['SavedResultsResponse'];
  await expect(page.locator('.result-category-scores li')).toHaveCount(6);
  const dashboardMs = Math.round(performance.now() - dashboardBegan);
  await info.attach('execution-receipt', { body: JSON.stringify({
    scope: live ? 'Cached public sources and genuine free-credit model' : 'Cached public sources; model disabled',
    initial_progress_ms: initialProgressMs, analysis_ms: analysisMs, dashboard_ms: dashboardMs,
    proposition_statuses: result.claims.flatMap(c => c.links.map(l => l.support_status)),
    claim_issue_states: result.findings.filter(f => f.type === 'claim_support').map(f => f.title),
  }, null, 2), contentType: 'application/json' });
  expect(result.score.value).not.toBeNull();
  await expect(page.locator('.result-category-scores li')).toHaveCount(6);
  expect(result.citations.filter(c => c.verification_status === 'verified').length).toBeGreaterThanOrEqual(4);
  expect(result.citations.some(c => c.verification_status !== 'verified')).toBe(true);
  expect(result.quotes.map(q => q.match_status)).toEqual(expect.arrayContaining(['exact', 'close']));
  expect(result.findings.map(f => f.type)).toEqual(expect.arrayContaining(['court_rule', 'privacy', 'quote']));
  const propositions = result.claims.flatMap(c => c.links.map(l => l.support_status));
  if (live) {
    const expectations = JSON.parse(await readFile(resolve(__dirname, '../../data/demo/curated-v1/expectations.json'), 'utf8')) as {
      cases: { id: string; category: string; expected_status: string; simulation?: string; filing_span: { start: number; end: number } }[];
    };
    // Forced outage scenarios are verified separately; they are not the normal demo.
    for (const control of expectations.cases.filter(c => c.category === 'proposition' && !c.simulation)) {
      const claim = result.claims.find(c => c.location.start <= control.filing_span.start && c.location.end >= control.filing_span.end);
      expect(claim, control.id).toBeDefined();
      expect.soft(claim!.links.map(l => l.support_status), control.id).toContain(control.expected_status);
    }
    expect.soft(initialProgressMs).toBeLessThanOrEqual(2000);
    expect.soft(analysisMs).toBeLessThanOrEqual(60000);
    expect.soft(dashboardMs).toBeLessThanOrEqual(3000);
  } else expect(propositions.every(status => status === 'not_run')).toBe(true);
  await page.getByText(`Citation occurrences (${result.citations.length})`, { exact: true }).click();
  await expect(page.locator('.results-checks')).toContainText('verified');
  await page.getByText(`Quotation checks (${result.quotes.length})`, { exact: true }).click();
  await expect(page.locator('.results-checks')).toContainText('close');
  await expect(page.locator('.result-graph-canvas .react-flow__node').first()).toBeVisible();
  await page.locator('.result-graph-list summary').focus();
  await page.keyboard.press('Enter');
  await expect(page.locator('.result-graph-list > ul > li > button').first()).toBeVisible();
  for (const category of ['privacy', 'quote']) {
    await page.getByLabel('Finding category').selectOption(category);
    await page.locator('.results-finding-list button').first().focus();
    await page.keyboard.press('Enter');
    await expect(page.locator('.result-detail .result-evidence').first()).toBeVisible();
    await expect(page.locator('.result-detail')).toContainText('Next review action');
  }
  if (live) {
    await page.getByLabel('Finding category').selectOption('claim_support');
    await page.getByRole('button', { name: /Potentially misrepresented source/ }).click();
    await expect(page.locator('.result-detail')).toContainText('proposition-source-review-v4-batch');
    await expect.poll(() => page.locator('.result-detail .result-evidence').count()).toBeGreaterThanOrEqual(2);
  }
  const downloadEvent = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Download Markdown' }).focus();
  await page.keyboard.press('Enter');
  const download = await downloadEvent;
  const target = info.outputPath('curated-report.md');
  await download.saveAs(target);
  const report = await readFile(target, 'utf8');
  expect(report).toContain('cached_public');
  expect(report).not.toContain('900-12-3456');
  expect(report).toContain('quote-forensics-v2');
  if (live) expect(report).toContain('misrepresented');
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.screenshot({ path: info.outputPath('curated-results.png'), fullPage: true });
  const resultURL = page.url();
  await page.goto(documentURL);
  await page.getByRole('button', { name: 'Reset demo' }).click();
  await expect(page.getByRole('heading', { name: 'FilingGuard-AI' })).toBeVisible();
  await page.goto(resultURL);
  await expect(page.getByRole('heading', { name: 'Results unavailable' })).toBeVisible();
  expect(errors).toEqual([]);
  await info.attach('acceptance-scope', { body: live
    ? 'Cached public sources + genuine model calls; twelve SRS 18.2 controls exercised. AI-reviewed synthetic fixture.'
    : 'Cached public sources + deterministic engines; semantic stage disabled. Eleven SRS 18.2 controls, step 7 pending.', contentType: 'text/plain' });
});
