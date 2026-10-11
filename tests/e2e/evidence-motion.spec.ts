import { expect, test, type Locator } from '@playwright/test';

test.use({ baseURL: process.env.FILINGGUARD_E2E_BASE_URL || 'http://127.0.0.1:5175' });

test('hero depth renders around an unobstructed composer', async ({ page }, info) => {
  await page.goto('/');
  const hero = page.locator('.hero-scene');
  await expect(hero).toHaveAttribute('data-scene-status', 'ready');
  const canvas = hero.locator('canvas');
  const before = await pixels(canvas);
  expect(before.coverage).toBeGreaterThan(.002);
  expect(before.coverage).toBeLessThan(.35);
  expect(await canvas.evaluate((element: HTMLCanvasElement) => {
    const copy = document.createElement('canvas'); copy.width = element.width; copy.height = element.height;
    const ctx = copy.getContext('2d')!; ctx.drawImage(element, 0, 0);
    return ctx.getImageData(Math.floor(copy.width / 2), Math.floor(copy.height / 2), 1, 1).data[3];
  })).toBe(0);
  if (info.project.name === 'desktop') {
    await page.mouse.move(30, 350);
    await expect.poll(async () => (await pixels(canvas)).hash).not.toBe(before.hash);
  }
  await page.getByRole('textbox', { name: 'Filing text' }).fill('Synthetic document: scene does not block intake.');
  await expect(page.getByRole('textbox', { name: 'Filing text' })).toHaveValue('Synthetic document: scene does not block intake.');
  await expect.poll(() => page.locator('.title-piece').last().evaluate(element => getComputedStyle(element).transform)).toBe('none');
  await page.getByRole('textbox', { name: 'Filing text' }).fill('');
  await page.getByRole('heading', { name: 'FilingGuard-AI' }).click();
  await page.screenshot({ path: `../../.runtime/glass-hero-${info.project.name}.png` });
});

async function pixels(canvas: Locator) {
  return canvas.evaluate((element: HTMLCanvasElement) => {
    const copy = document.createElement('canvas');
    copy.width = element.width; copy.height = element.height;
    const context = copy.getContext('2d')!;
    context.drawImage(element, 0, 0);
    const { data } = context.getImageData(0, 0, copy.width, copy.height);
    let count = 0; let hash = 0; let minX = copy.width; let maxX = 0; let minY = copy.height; let maxY = 0;
    for (let i = 0; i < data.length; i += 4) {
      hash = (hash + data[i] * ((i % 97) + 1)) % 1000000007;
      if (data[i + 3] > 200 && data[i] > 180 && data[i + 1] > 180 && data[i + 2] > 180) {
        count++; const x = (i / 4) % copy.width; const y = Math.floor(i / 4 / copy.width);
        minX = Math.min(x, minX); maxX = Math.max(x, maxX); minY = Math.min(y, minY); maxY = Math.max(y, maxY);
      }
    }
    return { coverage: count / (copy.width * copy.height), hash, minX, maxX, minY, maxY, width: copy.width, height: copy.height };
  });
}

test('real WebGL evidence is framed, interactive and survives navigation', async ({ page }, info) => {
  const errors: string[] = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.goto('/');
  const experience = page.locator('.evidence-experience');
  await experience.scrollIntoViewIfNeeded();
  await expect(experience).toHaveAttribute('data-scene-status', 'ready');
  const canvas = experience.locator('canvas');
  await expect(canvas).toHaveAttribute('data-transitioning', 'false');
  const before = await pixels(canvas);
  expect(before.coverage).toBeGreaterThan(.03);
  expect(before.minY).toBeGreaterThan(3); expect(before.maxY).toBeLessThan(before.height - 3);
  expect(before.minX).toBeGreaterThan(3); expect(before.maxX).toBeLessThan(before.width - 3);
  await page.getByRole('button', { name: /The authority/ }).click();
  await expect(canvas).toHaveAttribute('data-stage', '1');
  await expect(canvas).toHaveAttribute('data-transitioning', 'false');
  const after = await pixels(canvas);
  expect(after.hash).not.toBe(before.hash);
  expect(after.coverage).toBeGreaterThan(.03);
  expect(after.coverage).toBeLessThan(.8);
  expect(after.minX).toBeGreaterThan(3); expect(after.maxX).toBeLessThan(after.width - 3);
  expect(after.minY).toBeGreaterThan(3); expect(after.maxY).toBeLessThan(after.height - 3);
  await experience.screenshot({ path: `../../.runtime/evidence-${info.project.name}.png` });
  await page.getByRole('button', { name: /The difference/ }).focus();
  await page.keyboard.press('Enter');
  await expect(canvas).toHaveAttribute('data-stage', '2');
  await expect(canvas).toHaveAttribute('data-transitioning', 'false');
  const difference = await pixels(canvas);
  expect(difference.hash).not.toBe(after.hash);
  expect(difference.minY).toBeGreaterThan(3); expect(difference.maxY).toBeLessThan(difference.height - 3);
  expect(difference.minX).toBeGreaterThan(3); expect(difference.maxX).toBeLessThan(difference.width - 3);
  await expect(page.locator('.scene-caption')).toContainText('missing prefix');
  await page.getByRole('button', { name: 'Focus difference' }).click();
  await expect(page.getByRole('button', { name: 'Focus difference' })).toHaveAttribute('aria-pressed', 'true');
  await page.getByRole('button', { name: 'Open reviewed sample' }).click();
  await expect(page.locator('.evidence-stage canvas')).toHaveCount(0);
  await page.goBack();
  await page.locator('.evidence-experience').scrollIntoViewIfNeeded();
  await expect(page.locator('.evidence-experience')).toHaveAttribute('data-scene-status', 'ready');
  await expect(page.locator('.evidence-stage canvas')).toHaveCount(1);
  expect(errors).toEqual([]);
});

test('reduced motion keeps evidence selectable without animated travel', async ({ page }) => {
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await page.goto('/');
  await page.locator('.evidence-experience').scrollIntoViewIfNeeded();
  await expect(page.locator('.evidence-experience')).toHaveAttribute('data-scene-status', 'ready');
  await page.getByRole('button', { name: /The difference/ }).click();
  const canvas = page.locator('.evidence-stage canvas');
  await expect(canvas).toHaveAttribute('data-stage', '2');
  await expect(canvas).toHaveAttribute('data-transitioning', 'false');
  expect((await pixels(canvas)).coverage).toBeGreaterThan(.03);
  expect(await page.locator('.title-piece').first().evaluate(element => getComputedStyle(element).transform)).toBe('none');
});

test('WebGL unavailable retains the evidence and usable stage controls', async ({ page }) => {
  await page.addInitScript(() => {
    const getContext = HTMLCanvasElement.prototype.getContext;
    HTMLCanvasElement.prototype.getContext = function (kind: string, ...args: unknown[]) {
      if (kind.includes('webgl')) return null;
      return Reflect.apply(getContext, this, [kind, ...args]);
    } as typeof getContext;
  });
  await page.goto('/');
  await page.locator('.evidence-experience').scrollIntoViewIfNeeded();
  await expect(page.locator('.evidence-experience')).toHaveAttribute('data-scene-status', 'fallback');
  await expect(page.locator('.hero-scene')).toHaveAttribute('data-scene-status', 'fallback');
  await expect(page.getByText('Evidence study: static view')).toBeVisible();
  await page.getByRole('button', { name: /The difference/ }).click();
  await expect(page.locator('.scene-caption')).toContainText('missing prefix');
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
});
