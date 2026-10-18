import { chromium } from '@playwright/test';

async function test() {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  page.on('console', msg => console.log('PAGE LOG:', msg.text()));
  page.on('pageerror', err => console.log('PAGE ERROR:', err.message));
  page.on('response', resp => {
    if (resp.url().includes('/status') || resp.url().includes('/run')) {
      console.log('HTTP RESP:', resp.status(), resp.url());
    }
  });

  await page.goto('http://127.0.0.1:5173');
  await page.getByRole('button', { name: 'Demo' }).click();
  await page.getByRole('button', { name: 'Prepare document' }).click();
  await page.waitForURL(/\/analyses\/[a-f0-9-]+$/);
  console.log('On Prepared page:', page.url());

  const runBtn = page.getByRole('button', { name: /Run local checks/i });
  await runBtn.waitFor({ state: 'visible' });
  await runBtn.click();
  console.log('Clicked Run local checks');

  for (let i = 0; i < 20; i++) {
    await page.waitForTimeout(1000);
    const linkCount = await page.getByRole('link', { name: /Open review results/i }).count();
    const heroText = await page.locator('.prepared-hero h1').textContent().catch(() => '');
    const nextActionH2 = await page.locator('.next-action-card h2').textContent().catch(() => '');
    const demoNotice = await page.locator('.demo-notice').textContent().catch(() => '');
    console.log(`[t=${i}s] Links: ${linkCount} | Hero: "${heroText?.trim().replace(/\n/g, ' ')}" | Card: "${nextActionH2?.trim()}" | Notice: "${demoNotice?.trim().slice(0, 40)}"`);
    if (linkCount > 0) {
      console.log('FOUND Open review results link!');
      break;
    }
  }

  await browser.close();
}

test().catch(console.error);
