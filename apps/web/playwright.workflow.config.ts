import { defineConfig, devices } from '@playwright/test';

// Fresh storage/rate buckets per suite; preserve the user's review preview.
const suites: Record<string, string> = { public: 'workflow-design.spec.ts', intake: 'intake.spec.ts', results: 'results.spec.ts', accessibility: 'accessibility.spec.ts', performance: 'performance.spec.ts' };
const suite = process.env.FILINGGUARD_WORKFLOW_SUITE || 'public';
if (!suites[suite]) throw new Error('Unknown FILINGGUARD_WORKFLOW_SUITE');
process.env.FILINGGUARD_E2E_BASE_URL = 'http://127.0.0.1:5175';
export default defineConfig({
  testDir: '../../tests/e2e', testMatch: suites[suite],
  outputDir: `../../.runtime/playwright-workflow-${suite}`,
  reporter: [['list'], ['json', { outputFile: `../../.runtime/workflow-${suite}-results.json` }]], workers: 1,
  use: { baseURL: 'http://127.0.0.1:5175', reducedMotion: 'reduce', trace: 'off' },
  projects: [{ name: 'desktop', use: devices['Desktop Chrome'] },
    { name: 'mobile', use: { ...devices['iPhone 13'], defaultBrowserType: 'chromium' } }],
  webServer: [
    { command: 'node scripts/api.mjs run python scripts/run_intake_preview.py --port 8002', cwd: '../..',
      url: 'http://127.0.0.1:8002/api/v1/health', reuseExistingServer: false, timeout: 60000 },
    { command: 'npm run dev --workspace @filingguard/web -- --host 127.0.0.1 --port 5175 --strictPort', cwd: '../..',
      url: 'http://127.0.0.1:5175', env: { VITE_API_BASE_URL: 'http://127.0.0.1:8002' }, reuseExistingServer: false, timeout: 60000 },
  ],
});
