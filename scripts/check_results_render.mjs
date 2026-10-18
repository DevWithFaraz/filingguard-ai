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
        console.log('RESULTS BODY LENGTH:', text.length);
        console.log('RESULTS BODY SAMPLE:', text.slice(0, 300));
      }
    }
  });

  await page.goto('http://127.0.0.1:5173/analyses/62cc8517-7473-4c2e-a9c6-661fd486a529/results');

  for (let i = 0; i < 15; i++) {
    await page.waitForTimeout(1000);
    const scoreExists = await page.isVisible('.result-score');
    const notice = await page.locator('.workflow-notice').textContent().catch(() => '');
    console.log(`[t=${i}s] Score visible: ${scoreExists} | Notice: "${notice?.trim()}"`);
    if (scoreExists) {
      console.log('SUCCESS! .result-score is visible!');
      break;
    }
  }

  await browser.close();
}

test().catch(console.error);
