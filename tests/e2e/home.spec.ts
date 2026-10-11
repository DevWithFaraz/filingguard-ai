import { expect, test } from '@playwright/test';

test.use({ baseURL: process.env.FILINGGUARD_E2E_BASE_URL || 'http://127.0.0.1:5175' });

test('homepage assets, responsive composition, source modes and reduced motion', async ({ page }, info) => {
  const errors: string[] = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.goto('/');
  await expect(page.getByRole('textbox', { name: 'Filing text' })).toBeEnabled();
  await page.evaluate(() => document.fonts.ready);
  const background = page.locator('.hero-background');
  expect(await background.evaluate((element: HTMLImageElement) => ({ width: element.naturalWidth, height: element.naturalHeight, opacity: getComputedStyle(element).opacity, filter: getComputedStyle(element).filter }))).toEqual({ width: 3888, height: 2592, opacity: '1', filter: 'none' });
  await expect.poll(() => page.locator('.hero-title').evaluate(element => getComputedStyle(element).transform)).toBe('none');
  await expect.poll(() => page.locator('.title-piece').last().evaluate(element => getComputedStyle(element).transform)).toBe('none');
  expect(await page.evaluate(() => document.fonts.check('700 44px "GC Avalance"'))).toBe(true);
  expect(await page.locator('.home-brand img').evaluate(element => getComputedStyle(element).filter)).toBe('none');
  const footerLogo = page.locator('.footer-identity img');
  await expect(footerLogo).toHaveAttribute('src', (await page.locator('.home-brand img').getAttribute('src'))!);
  expect(await footerLogo.evaluate(element => getComputedStyle(element).filter)).toBe('none');
  for (const image of await page.locator('.hero-background, .home-brand img').all()) {
    expect(await image.evaluate((element: HTMLImageElement) => element.complete && element.naturalWidth > 0)).toBe(true);
  }
  for (const width of info.project.name === 'desktop' ? [768, 1024, 1440, 1920] : [360, 390]) {
    await page.setViewportSize({ width, height: info.project.name === 'desktop' ? 900 : 844 });
    const header = await page.locator('.home-header').boundingBox();
    expect(header!.x).toBeCloseTo(0, 2); expect(header!.width).toBeCloseTo(width, 2);
    expect(await page.locator('.home-header').evaluate(element => getComputedStyle(element).borderRadius)).toBe('0px');
    for (const selector of ['.limits-heading', '.evidence-intro', '.experience-heading']) {
      const block = page.locator(selector);
      await block.scrollIntoViewIfNeeded();
      await expect.poll(() => block.evaluate(element => getComputedStyle(element).transform)).toBe('none');
    }
    await page.locator('.evidence-stage').scrollIntoViewIfNeeded();
    await expect(page.locator('.evidence-experience')).toHaveAttribute('data-scene-status', 'ready');
    await expect(page.locator('.evidence-stage canvas')).toHaveAttribute('data-transitioning', 'false');
    await page.evaluate(() => window.scrollTo(0, 0));
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    const hero = await page.locator('.home-hero').boundingBox();
    expect(hero!.y + hero!.height).toBeLessThan(840);
    const title = page.getByRole('heading', { name: 'FilingGuard-AI' });
    expect(await title.evaluate(element => element.scrollWidth <= element.clientWidth)).toBe(true);
    await page.screenshot({ path: `../../.runtime/home-${width}.png`, fullPage: true });
  }
  await page.setViewportSize(info.project.name === 'desktop' ? { width: 1366, height: 768 } : { width: 320, height: 667 });
  await page.locator('.home-footer').screenshot({ path: `../../.runtime/footer-${info.project.name}.png` });
  await page.evaluate(() => window.scrollTo(0, 0));
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  const compactHero = await page.locator('.home-hero').boundingBox();
  expect(compactHero!.y + compactHero!.height).toBeLessThan((await page.evaluate(() => innerHeight)) - 20);
  await page.screenshot({ path: `../../.runtime/home-compact-${info.project.name}.png`, fullPage: true });
  await page.getByRole('textbox', { name: 'Filing text' }).fill('Synthetic draft retained between source modes.');
  const menuToggle = page.getByRole('button', { name: 'Open navigation' });
  if (await menuToggle.isVisible()) {
    await menuToggle.click();
    await page.getByRole('link', { name: 'Activity', exact: true }).focus();
    await page.keyboard.press('Escape');
    await expect(menuToggle).toBeFocused();
    await expect(page.getByRole('link', { name: 'Activity', exact: true })).not.toBeVisible();
  }
  await page.getByRole('button', { name: 'PDF', exact: true }).click();
  await expect(page.getByText('Drop your filing here')).toBeVisible();
  await page.getByRole('button', { name: 'Demo', exact: true }).click();
  await expect(page.getByText('A filing with something to find.')).toBeVisible();
  await page.getByRole('button', { name: 'Text', exact: true }).click();
  await expect(page.getByRole('textbox', { name: 'Filing text' })).toHaveValue('Synthetic draft retained between source modes.');
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await page.reload();
  await expect(page.getByRole('heading', { name: 'FilingGuard-AI' })).toBeVisible();
  expect(await page.locator('.hero-title').evaluate(element => getComputedStyle(element).transform)).toBe('none');
  expect(await page.locator('.mode-indicator').evaluate(element => getComputedStyle(element).transitionDuration)).toBe('0s');
  await page.getByRole('button', { name: 'PDF', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Upload PDF', exact: true })).toBeEnabled();
  expect(errors).toEqual([]);
});
