import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: '../../tests/e2e',
  // Private journeys each use fresh rate buckets in playwright.workflow.config.ts.
  testIgnore: ['curated-demo.spec.ts', 'intake.spec.ts', 'results.spec.ts',
    'workflow-design.spec.ts', 'accessibility.spec.ts', 'performance.spec.ts'],
  outputDir: '../../.runtime/playwright-results',
  reporter: 'list',
  workers: 1,
  use: { baseURL: 'http://127.0.0.1:5173', trace: 'retain-on-failure',
    channel: process.env.PLAYWRIGHT_BROWSER_CHANNEL || undefined },
  projects: [
    { name: 'desktop', use: { ...devices['Desktop Chrome'] } },
    { name: 'mobile', use: { ...devices['iPhone 13'], defaultBrowserType: 'chromium' } },
  ],
  webServer: [
    { command: 'node scripts/api.mjs run python scripts/run_intake_preview.py --port 8002', cwd: '../..',
      url: 'http://127.0.0.1:8002/api/v1/health', reuseExistingServer: false, timeout: 60000 },
    { command: 'npm run dev --workspace @filingguard/web -- --host 127.0.0.1 --port 5175 --strictPort',
      cwd: '../..', url: 'http://127.0.0.1:5175',
      env: { VITE_API_BASE_URL: 'http://127.0.0.1:8002' },
      reuseExistingServer: false, timeout: 120000 },
    { command: 'npm run dev:api', cwd: '../..', url: 'http://127.0.0.1:8000/api/v1/health',
      reuseExistingServer: false, timeout: 60000 },
    { command: 'npm run dev:web', cwd: '../..', url: 'http://127.0.0.1:5173',
      reuseExistingServer: false, timeout: 120000 },
  ],
});
