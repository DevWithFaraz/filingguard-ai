import { chromium } from '@playwright/test';

async function test() {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  page.on('console', msg => console.log('CONSOLE:', msg.type(), msg.text()));
  page.on('pageerror', err => console.log('PAGE ERROR:', err.message));
  page.on('request', req => {
    if (req.url().includes('/api/')) console.log('>> REQ:', req.method(), req.url());
  });
  page.on('response', async resp => {
    if (resp.url().includes('/api/')) {
      console.log('<< RESP:', resp.status(), resp.url());
      if (resp.url().includes('/results')) {
        const text = await resp.text();
        console.log('RESULTS BODY (first 200 chars):', text.slice(0, 200));
      }
    }
  });

  await page.goto('http://127.0.0.1:5173');
  await page.getByRole('button', { name: 'Demo' }).click();
  await page.getByRole('button', { name: 'Prepare document' }).click();
  await page.waitForURL(/\/analyses\/[a-f0-9-]+$/);
  console.log('Prepared URL:', page.url());

  const runBtn = page.getByRole('button', { name: /Run local checks/i });
  await runBtn.waitFor({ state: 'visible' });
  await runBtn.click();
  console.log('Clicked Run local checks, waiting for Open review results link...');

  const openLink = page.getByRole('link', { name: /Open review results/i });
  await openLink.waitFor({ state: 'visible', timeout: 120000 });
  console.log('Review finished! Clicking Open review results...');

  await openLink.click();
  await page.waitForURL(/\/analyses\/[a-f0-9-]+\/results$/);
  console.log('On results page, waiting for .result-score...');

  const scoreLocator = page.locator('.result-score');
  await scoreLocator.waitFor({ state: 'visible', timeout: 30000 });
  console.log('SUCCESS! .result-score is visible!');

  const scoreText = await page.textContent('.result-score-number');
  console.log('Score text:', scoreText);

  await browser.close();
}

test().catch(console.error);
