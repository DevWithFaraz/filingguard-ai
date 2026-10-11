import AxeBuilder from '@axe-core/playwright';
import { expect, test, type Locator, type Page, type TestInfo } from '@playwright/test';

test.use({ baseURL: process.env.FILINGGUARD_E2E_BASE_URL || 'http://127.0.0.1:5174', reducedMotion: 'reduce' });

async function audit(page: Page, info: TestInfo, state: string) {
  const result = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa']).analyze();
  await info.attach(`axe-${state}`, { body: JSON.stringify(result), contentType: 'application/json' });
  expect(result.violations.map(v => ({ id: v.id, impact: v.impact, nodes: v.nodes.map(n => ({ target: n.target, summary: n.failureSummary })) })), state).toEqual([]);
}

async function tabTo(page: Page, target: Locator) {
  for (let i = 0; i < 150; i++) {
    if (await target.evaluate(el => el === document.activeElement)) return;
    await page.keyboard.press('Tab');
  }
  throw new Error('Control cannot be reached by sequential keyboard navigation');
}

test('P0 keyboard flow and accessibility semantics across real private states', async ({ page }, info) => {
  test.setTimeout(180000);
  await page.goto('/');
  await expect(page.getByRole('textbox', { name: 'Filing text' })).toBeEnabled();
  await audit(page, info, 'home');
  await page.keyboard.press('Tab');
  await expect(page.getByRole('link', { name: 'Skip to content' })).toBeFocused();
  await page.keyboard.press('Enter');
  await expect(page.getByRole('main')).toBeFocused();
  await tabTo(page, page.getByRole('button', { name: 'Demo', exact: true }));
  await page.keyboard.press('Enter');
  await tabTo(page, page.getByLabel('Court profile', { exact: true }));
  await page.keyboard.press('End');
  await expect(page.getByLabel('Court profile', { exact: true })).toHaveValue('synthetic-demo-v1');
  await tabTo(page, page.getByLabel('Generative AI used in this filing'));
  if (!(await page.getByLabel('Generative AI used in this filing').isChecked())) await page.keyboard.press('Space');
  await tabTo(page, page.getByRole('button', { name: 'Prepare document' }));
  await page.keyboard.press('Enter');
  await expect(page.getByRole('heading', { name: 'Curated synthetic filing' })).toBeVisible();
  await audit(page, info, 'prepared');
  await tabTo(page, page.getByRole('button', { name: 'Run local checks' }));
  await page.keyboard.press('Enter');
  await expect(page.getByRole('link', { name: 'Open review results' })).toBeVisible({ timeout: 100000 });
  await expect(page.locator('.local-review [role="status"]')).toHaveAttribute('aria-live', 'polite');
  await audit(page, info, 'review-terminal');
  await tabTo(page, page.getByRole('link', { name: 'Open review results' }));
  await page.keyboard.press('Enter');
  await expect(page.getByRole('heading', { name: 'Review results', exact: true })).toBeVisible();
  await audit(page, info, 'results');
  await tabTo(page, page.getByLabel('Finding category'));
  await page.keyboard.press('Home');
  await page.keyboard.press('p');
  // Native select keyboard behavior is browser/platform-specific; choose via arrows.
  for (let i = 0; i < 8 && (await page.getByLabel('Finding category').inputValue()) !== 'privacy'; i++) await page.keyboard.press('ArrowDown');
  await expect(page.getByLabel('Finding category')).toHaveValue('privacy');
  await tabTo(page, page.locator('.results-finding-list button').first());
  await page.keyboard.press('Enter');
  await expect(page.locator('.result-detail')).toBeFocused();
  await expect(page.locator('.result-detail .result-evidence').first()).toBeVisible();
  await audit(page, info, 'finding-evidence');
  await tabTo(page, page.locator('.result-graph-list summary'));
  await page.keyboard.press('Enter');
  await tabTo(page, page.locator('.result-graph-list > ul > li > button').first());
  await page.keyboard.press('Enter');
  await expect(page.locator('.result-graph-list > ul > li > button').first()).toHaveAttribute('aria-pressed', 'true');
  const download = page.waitForEvent('download');
  await tabTo(page, page.getByRole('button', { name: 'Download Markdown' }));
  await page.keyboard.press('Enter');
  await download;
  await tabTo(page, page.getByRole('link', { name: 'Activity', exact: true }));
  await page.keyboard.press('Enter');
  await expect(page.locator('.activity-list')).toContainText('partial');
  await audit(page, info, 'activity');
  await tabTo(page, page.getByRole('link', { name: 'Curated synthetic filing', exact: true }));
  await page.keyboard.press('Enter');
  await tabTo(page, page.getByRole('button', { name: 'Reset demo' }));
  await page.keyboard.press('Enter');
  await expect(page.getByRole('heading', { name: 'FilingGuard-AI' })).toBeVisible();
  for (const route of ['/settings', '/privacy', '/activity', '/demo', '/not-a-page']) {
    await page.goto(route);
    await expect(page.locator('.workflow-hero')).toBeVisible();
    await audit(page, info, route.slice(1));
  }
  await page.route('**/api/v1/demos/**', route => route.fulfill({ status: 503, body: '{}' }));
  await page.goto('/demo');
  await expect(page.getByRole('alert')).toBeVisible();
  await audit(page, info, 'sample-unavailable');
});
