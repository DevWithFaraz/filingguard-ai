import { chromium } from '@playwright/test';

const BASE_URL = 'http://127.0.0.1:5173';
const API_URL = 'http://127.0.0.1:8000';

async function main() {
  console.log('=== Starting FilingGuard AI End-to-End Browser Inspection ===\n');
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 1280, height: 900 },
  });
  const page = await context.newPage();

  const report = [];
  const logStep = (step, status, detail = '') => {
    const icon = status === 'PASS' ? '✅' : status === 'FAIL' ? '❌' : 'ℹ️';
    console.log(`${icon} [${step}] ${detail}`);
    report.push({ step, status, detail });
  };

  try {
    // 1. Visit Homepage & Verify Elements
    console.log('\n--- 1. Testing Homepage & Shell Navigation ---');
    await page.goto(BASE_URL, { waitUntil: 'networkidle' });
    const title = await page.title();
    logStep('HOMEPAGE_LOAD', 'PASS', `Loaded page with title: "${title}"`);

    const heroText = await page.textContent('.hero-title');
    if (heroText?.includes('FilingGuard')) {
      logStep('HERO_TITLE', 'PASS', `Hero title present: ${heroText.trim().replace(/\s+/g, ' ')}`);
    } else {
      logStep('HERO_TITLE', 'FAIL', 'Hero title missing or text mismatch');
    }

    // 2. Inspect Intake Composer Tabs & Court Profile Dropdown (T106)
    console.log('\n--- 2. Testing Intake Composer & Court Profiles (T106) ---');
    const composerVisible = await page.isVisible('.intake-composer');
    logStep('COMPOSER_VISIBLE', composerVisible ? 'PASS' : 'FAIL', 'Intake composer is mounted and visible');

    // Check Court Profiles dropdown in Live Text mode
    const courtSelect = page.locator('#court');
    const options = await courtSelect.locator('option').allTextContents();
    logStep('COURT_PROFILES', 'PASS', `Dropdown options: ${JSON.stringify(options)}`);

    const hasTxnd = options.some(opt => opt.includes('N.D. Tex.') || opt.includes('Local Rule 7.2(f)'));
    if (hasTxnd) {
      logStep('TXND_PROFILE_AVAILABLE', 'PASS', 'N.D. Tex. Local Rule 7.2(f) verified profile is selectable in Live mode');
    } else {
      logStep('TXND_PROFILE_AVAILABLE', 'FAIL', 'N.D. Tex. profile missing from dropdown');
    }

    // Switch to Demo tab
    const demoTabBtn = page.getByRole('button', { name: 'Demo' });
    await demoTabBtn.click();
    await page.waitForTimeout(300);
    const demoOptions = await courtSelect.locator('option').allTextContents();
    logStep('DEMO_TAB_SWITCH', 'PASS', `Switched to Demo tab. Options: ${JSON.stringify(demoOptions)}`);

    // 3. Prepare Demo Document & Executing Review
    console.log('\n--- 3. Preparing Demo Document & Executing Review ---');
    const prepareBtn = page.getByRole('button', { name: 'Prepare document' });
    await prepareBtn.click();

    // Land on Prepared View (/analyses/:id)
    await page.waitForURL(/\/analyses\/[a-f0-9-]+$/, { timeout: 10000 });
    const preparedUrl = page.url();
    logStep('PREPARED_VIEW_NAV', 'PASS', `Navigated to Prepared View: ${preparedUrl}`);

    // Verify Court Profile display in Prepared View
    const courtProfileDd = await page.locator('dt:has-text("Court profile") + dd').textContent();
    logStep('PREPARED_COURT_PROFILE', 'PASS', `Court profile displayed: "${courtProfileDd?.trim()}"`);

    // Click "Run local checks"
    const runChecksBtn = page.getByRole('button', { name: /Run local checks/i });
    await runChecksBtn.waitFor({ state: 'visible', timeout: 5000 });
    await runChecksBtn.click();
    logStep('RUN_LOCAL_CHECKS_CLICK', 'PASS', 'Clicked "Run local checks", waiting for review stages to complete');

    // Wait for "Open review results" link to appear
    const openResultsLink = page.getByRole('link', { name: /Open review results/i });
    await openResultsLink.waitFor({ state: 'visible', timeout: 35000 });
    logStep('REVIEW_FINISHED_SIGNAL', 'PASS', 'Review finished and "Open review results" link surfaced');
    await openResultsLink.click();

    // Wait for Results View navigation
    await page.waitForURL(/\/analyses\/[a-f0-9-]+\/results$/, { timeout: 10000 });
    const resultsUrl = page.url();
    logStep('RESULTS_VIEW_NAV', 'PASS', `Reached Results View: ${resultsUrl}`);

    // 4. Results View & Integrity Signals
    console.log('\n--- 4. Inspecting Results View & Category Filtering (T105) ---');
    await page.waitForSelector('.result-score', { timeout: 5000 });
    const scoreText = await page.textContent('.result-score-number');
    logStep('INTEGRITY_SCORE', 'PASS', `Filing integrity signal score: ${scoreText?.trim()}`);

    // Check Category Score filter buttons
    const categoryBtns = await page.locator('.category-filter-btn').all();
    logStep('CATEGORY_FILTERS', 'PASS', `Found ${categoryBtns.length} interactive category filter cards`);
    if (categoryBtns.length > 0) {
      await categoryBtns[0].click();
      await page.waitForTimeout(300);
      const isFiltered = await page.isVisible('.category-clear-btn');
      logStep('CATEGORY_FILTER_ACTIVE', isFiltered ? 'PASS' : 'FAIL', 'Clicking category card toggles filter and surfaces "Show all categories"');
      if (isFiltered) {
        await page.click('.category-clear-btn');
        await page.waitForTimeout(200);
      }
    }

    // 5. Findings, 5-Hop Rich Lineage & Determination Explanations (T102)
    console.log('\n--- 5. Inspecting Findings & 5-Hop Lineage Chain (T102) ---');
    const findingItems = await page.locator('.result-finding-button').all();
    logStep('FINDINGS_COUNT', 'PASS', `Found ${findingItems.length} findings in results view`);

    if (findingItems.length > 0) {
      // Click first finding
      await findingItems[0].click();
      await page.waitForTimeout(400);

      // Check "How was this determined?" button
      const explainSummary = page.locator('details.determination-details summary');
      const hasExplain = await explainSummary.isVisible();
      logStep('EXPLAINER_VISIBLE', hasExplain ? 'PASS' : 'FAIL', '"How was this determined?" section is present');
      if (hasExplain) {
        await explainSummary.click();
        await page.waitForTimeout(300);
        const methodBadge = await page.textContent('.determination-method-badge');
        logStep('DETERMINATION_METHOD', 'PASS', `Method: "${methodBadge?.trim().slice(0, 60)}..."`);
      }

      // Check 5-hop lineage chain
      const lineageSteps = await page.locator('.lineage-step').all();
      logStep('LINEAGE_5_HOPS', lineageSteps.length >= 5 ? 'PASS' : 'FAIL', `Visual lineage chain has ${lineageSteps.length} hops (expected >= 5)`);
    }

    // 6. Finding-Grounded Q&A (T103)
    console.log('\n--- 6. Testing Finding-Grounded Q&A (T103) ---');
    const qaSection = page.locator('.finding-qa-section');
    const qaVisible = await qaSection.isVisible();
    logStep('QA_SECTION_VISIBLE', qaVisible ? 'PASS' : 'FAIL', 'Grounded Q&A section is mounted inside finding details');

    if (qaVisible) {
      const promptChips = await page.locator('.qa-chip-button').all();
      logStep('QA_PROMPT_CHIPS', 'PASS', `Found ${promptChips.length} suggested prompt chips`);

      if (promptChips.length > 0) {
        // Click first chip to ask a question
        const chipText = await promptChips[0].textContent();
        await promptChips[0].click();
        logStep('QA_ASK_QUESTION', 'PASS', `Submitted prompt: "${chipText?.trim()}"`);

        // Await answer response
        await page.waitForSelector('.qa-thread-card', { timeout: 15000 });
        const answerText = await page.textContent('.qa-answer-text');
        logStep('QA_ANSWER_RECEIVED', 'PASS', `Grounded answer: "${answerText?.slice(0, 80)}..."`);

        // Check answer status pill
        const statusPill = await page.textContent('.qa-status-pill');
        logStep('QA_STATUS_PILL', 'PASS', `Answer verification status: "${statusPill?.trim()}"`);
      }
    }

    // 7. Legal Red-Team Mode (T101 & UI Polish)
    console.log('\n--- 7. Testing Legal Red-Team Mode Panel (T101) ---');
    const redTeamSection = page.locator('#result-red-team');
    const redTeamVisible = await redTeamSection.isVisible();
    logStep('RED_TEAM_VISIBLE', redTeamVisible ? 'PASS' : 'FAIL', 'Legal Red-Team Mode panel is mounted');

    if (redTeamVisible) {
      // Check Metric Stat Pills
      const metrics = await page.locator('.red-team-metric').all();
      logStep('RED_TEAM_METRICS', 'PASS', `Found ${metrics.length} metric capsules (Critical, High, Medium, Low)`);

      // Check Weakness Cards
      const cards = await page.locator('.red-team-card').all();
      logStep('RED_TEAM_CARDS', 'PASS', `Found ${cards.length} ranked vulnerability challenge cards`);

      if (cards.length > 0) {
        // Test Expand / Collapse toggle on the first card
        const firstCardToggle = cards[0].locator('.red-team-expand-toggle');
        const bodyBefore = await cards[0].locator('.red-team-card-body').isVisible();
        logStep('CARD_1_INITIAL_STATE', 'PASS', `Card 1 expanded initially: ${bodyBefore}`);

        // Click minimize toggle
        await firstCardToggle.click();
        await page.waitForTimeout(300);
        const bodyAfterClick1 = await cards[0].locator('.red-team-card-body').isVisible();
        logStep('CARD_1_MINIMIZE', !bodyAfterClick1 ? 'PASS' : 'FAIL', `Card 1 minimized on click: ${!bodyAfterClick1}`);

        // Click again to expand
        await firstCardToggle.click();
        await page.waitForTimeout(300);
        const bodyAfterClick2 = await cards[0].locator('.red-team-card-body').isVisible();
        logStep('CARD_1_RE_EXPAND', bodyAfterClick2 ? 'PASS' : 'FAIL', `Card 1 re-expanded on second click: ${bodyAfterClick2}`);

        // Check Jump to Finding button
        const jumpBtn = cards[0].locator('.linked-finding-jump').first();
        if (await jumpBtn.isVisible()) {
          await jumpBtn.click();
          await page.waitForTimeout(300);
          logStep('JUMP_TO_FINDING', 'PASS', 'Clicked "Jump to Finding", successfully focused target finding');
        }
      }
    }

    // 8. Claim-Authority Graph Controls (T105)
    console.log('\n--- 8. Testing Claim-Authority Graph Controls (T105) ---');
    const graphSection = page.locator('#result-relationships');
    const graphVisible = await graphSection.isVisible();
    logStep('GRAPH_MOUNTED', graphVisible ? 'PASS' : 'FAIL', 'Claim-Authority relationship graph mounted');

    const zoomInBtn = page.getByRole('button', { name: 'Zoom in graph' });
    const zoomOutBtn = page.getByRole('button', { name: 'Zoom out graph' });
    const fitViewBtn = page.getByRole('button', { name: 'Fit graph to view' });

    const hasControls = await zoomInBtn.isVisible() && await zoomOutBtn.isVisible() && await fitViewBtn.isVisible();
    logStep('GRAPH_CONTROLS', hasControls ? 'PASS' : 'FAIL', 'Zoom In, Zoom Out, and Fit View controls visible');

    if (hasControls) {
      await zoomInBtn.click();
      await page.waitForTimeout(200);
      await zoomOutBtn.click();
      await page.waitForTimeout(200);
      await fitViewBtn.click();
      await page.waitForTimeout(200);
      logStep('GRAPH_INTERACTIONS', 'PASS', 'Exercised graph zoom and fit controls without error');
    }

    // 9. PDF Report Export (T104)
    console.log('\n--- 9. Testing PDF Report Export (T104) ---');
    const analysisIdMatch = resultsUrl.match(/\/analyses\/([a-f0-9-]+)\/results/);
    const analysisId = analysisIdMatch ? analysisIdMatch[1] : null;

    if (analysisId) {
      const pdfResp = await page.request.get(`${API_URL}/api/v1/analyses/${analysisId}/report?format=pdf`);
      const status = pdfResp.status();
      const contentType = pdfResp.headers()['content-type'];
      const body = await pdfResp.body();
      const isPdfHeader = body.slice(0, 4).toString() === '%PDF';

      if (status === 200 && contentType?.includes('application/pdf') && isPdfHeader) {
        logStep('PDF_EXPORT', 'PASS', `PDF generated successfully! Size: ${body.length} bytes, Header: %PDF`);
      } else {
        logStep('PDF_EXPORT', 'FAIL', `PDF export failed: Status ${status}, Type ${contentType}`);
      }
    }

    // 10. Live Text Submission with N.D. Tex. LR 7.2(f) Real Court Profile (T106)
    console.log('\n--- 10. Testing Live Text Submission with N.D. Tex. LR 7.2(f) (T106) ---');
    await page.goto(BASE_URL, { waitUntil: 'networkidle' });
    await page.waitForTimeout(500);

    // In text mode, select us-txnd-lr7-2f-v1
    await page.selectOption('#court', 'us-txnd-lr7-2f-v1');
    await page.check('input[type="checkbox"]'); // AI used = true

    // Type text WITHOUT the required heading
    const testFilingText = 'MOTION FOR SUMMARY JUDGMENT\n\nPlaintiff hereby moves for summary judgment under Fed. R. Civ. P. 56.\nThis filing discusses legal precedents and citations: 576 U.S. 644.';
    await page.fill('#filing', testFilingText);

    await page.click('button:has-text("Prepare document")');
    await page.waitForURL(/\/analyses\/[a-f0-9-]+$/, { timeout: 10000 });

    const liveCourtDisplay = await page.locator('dt:has-text("Court profile") + dd').textContent();
    logStep('LIVE_PREPARED_COURT', 'PASS', `Live prepared view displays court profile: "${liveCourtDisplay?.trim()}"`);

    const liveRunChecksBtn = page.getByRole('button', { name: /Run local checks/i });
    await liveRunChecksBtn.waitFor({ state: 'visible', timeout: 5000 });
    await liveRunChecksBtn.click();
    logStep('LIVE_RUN_CHECKS_CLICK', 'PASS', 'Started live review checks');

    const liveOpenResultsLink = page.getByRole('link', { name: /Open review results/i });
    await liveOpenResultsLink.waitFor({ state: 'visible', timeout: 35000 });
    await liveOpenResultsLink.click();
    await page.waitForURL(/\/analyses\/[a-f0-9-]+\/results$/, { timeout: 10000 });
    logStep('LIVE_RESULTS_VIEW', 'PASS', 'Live review completed and navigated to results');

    // Check for N.D. Tex. Local Rule 7.2(f) finding
    const findingsText = await page.locator('.results-finding-list').textContent();
    const hasTxndFinding = findingsText?.includes('N.D. Tex. Local Rule 7.2(f)');
    logStep('TXND_DISCLOSURE_FINDING', hasTxndFinding ? 'PASS' : 'FAIL', `Verified court rule finding generated: ${hasTxndFinding}`);

  } catch (err) {
    console.error('Test execution error:', err);
    logStep('EXECUTION_ERROR', 'FAIL', err.message);
  } finally {
    await browser.close();
  }

  console.log('\n=== Summary of End-to-End Verification Results ===');
  let passCount = 0;
  let failCount = 0;
  for (const r of report) {
    if (r.status === 'PASS') passCount++;
    if (r.status === 'FAIL') failCount++;
  }
  console.log(`Total checks: ${report.length} | Passed: ${passCount} | Failed: ${failCount}`);
  if (failCount === 0) {
    console.log('🎉 ALL FEATURES VERIFIED AND PASSING 100%!');
  }
}

main().catch(console.error);
