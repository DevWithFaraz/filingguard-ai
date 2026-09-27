import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: '../../tests/e2e',
  outputDir: '../../.runtime/playwright-results',
  reporter: 'list',
  use: { baseURL: 'http://127.0.0.1:5173', trace: 'retain-on-failure',
    channel: process.env.PLAYWRIGHT_BROWSER_CHANNEL || undefined },
  projects: [
    { name: 'desktop', use: { ...devices['Desktop Chrome'] } },
    { name: 'mobile', use: { ...devices['iPhone 13'], defaultBrowserType: 'chromium' } },
  ],
  webServer: [
    { command: 'npm run dev:api', cwd: '../..', url: 'http://127.0.0.1:8000/api/v1/health',
      reuseExistingServer: !process.env.CI, timeout: 60000 },
    { command: 'npm run dev:web', cwd: '../..', url: 'http://127.0.0.1:5173',
      reuseExistingServer: !process.env.CI, timeout: 120000 },
  ],
});
