import { defineConfig, devices } from '@playwright/test';

const live = process.env.FILINGGUARD_LIVE_DEMO === '1';
export default defineConfig({
  testDir: '../../tests/e2e', testMatch: 'curated-demo.spec.ts',
  outputDir: '../../.runtime/playwright-curated',
  reporter: [['list'], ['json', { outputFile: '../../.runtime/curated-results.json' }]], workers: 1,
  use: { baseURL: 'http://127.0.0.1:5175', reducedMotion: 'reduce', trace: 'off',
    channel: process.env.PLAYWRIGHT_BROWSER_CHANNEL || undefined },
  projects: live ? [{ name: 'desktop-live-model', use: { ...devices['Desktop Chrome'] } }]
    : [{ name: 'desktop', use: { ...devices['Desktop Chrome'] } },
      { name: 'mobile', use: { ...devices['iPhone 13'], defaultBrowserType: 'chromium' } }],
  webServer: [
    { command: `node scripts/api.mjs run python scripts/run_intake_preview.py --port 8002${live ? ' --live-semantic' : ''}`,
      cwd: '../..', url: 'http://127.0.0.1:8002/api/v1/health', reuseExistingServer: false, timeout: 60000 },
    { command: 'npm run dev --workspace @filingguard/web -- --host 127.0.0.1 --port 5175 --strictPort',
      cwd: '../..', url: 'http://127.0.0.1:5175', reuseExistingServer: false,
      env: { VITE_API_BASE_URL: 'http://127.0.0.1:8002' }, timeout: 60000 },
  ],
});
