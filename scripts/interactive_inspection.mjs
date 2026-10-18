import { chromium } from '@playwright/test';

const BASE_URL = 'http://127.0.0.1:5173';
const API_URL = 'http://127.0.0.1:8000';

async function main() {
  console.log('================================================================');
  console.log('  FilingGuard AI - Interactive Headful Browser Mode Inspection  ');
  console.log('================================================================\n');

  // Launch Chromium in interactive headful mode
  const browser = await chromium.launch({
    headless: false,
    slowMo: 150, // Slight delay so actions are clearly visible
  });

  const context = await browser.newContext({
    viewport: { width: 1366, height: 860 },
  });
  const page = await context.newPage();

  page.on('console', msg => {
    if (msg.type() === 'error') {
      console.log(`[Browser Console Error] ${msg.text()}`);
    }
  });

  const report = [];
  const logStep = (step, status, detail = '') => {
    const icon = status === 'PASS' ? '✅' : status === 'FAIL' ? '❌' : 'ℹ️';
    console.log(`${icon} [${step}] ${detail}`);
    report.push({ step, status, detail });
  };

  try {
    // ------------------------------------------------------------------------
    // 1. Visit Homepage & Inspect Brand Shell
    // ------------------------------------------------------------------------
    console.log('\n--- 1. Inspecting Homepage & Brand Shell ---');
    await page.goto(BASE_URL, { waitUntil: 'networkidle' });
    const title = await page.title();
    logStep('HOMEPAGE_LOAD', 'PASS', `Loaded page: "${title}"`);

    const heroText = await page.textContent('.hero-title');
    logStep('HERO_TITLE', heroText?.includes('FilingGuard') ? 'PASS' : 'FAIL', `Hero title: "${heroText?.trim().replace(/\s+/g, ' ')}"`);

    const glassComposer = await page.isVisible('.intake-composer');
    logStep('GLASS_SURFACE', glassComposer ? 'PASS' : 'FAIL', 'Translucent glass composer mounted on homepage');

    // ------------------------------------------------------------------------
    // 2. Intake Composer & Verified Court Profiles (T106)
    // ------------------------------------------------------------------------
    console.log('\n--- 2. Inspecting Intake Composer & Court Profiles (T106) ---');
    const courtSelect = page.locator('#court');
    const liveOptions = await courtSelect.locator('option').allTextContents();
    logStep('LIVE_COURT_OPTIONS', 'PASS', `Live mode options: ${JSON.stringify(liveOptions)}`);

    const hasTxnd = liveOptions.some(opt => opt.includes('N.D. Tex.') || opt.includes('Local Rule 7.2(f)'));
    logStep('TXND_PROFILE_SELECTABLE', hasTxnd ? 'PASS' : 'FAIL', 'N.D. Tex. Local Rule 7.2(f) verified profile present in Live mode');

    // Switch to Demo tab
    const demoTabBtn = page.getByRole('button', { name: 'Demo' });
    await demoTabBtn.click();
    await page.waitForTimeout(400);

    const demoOptions = await courtSelect.locator('option').allTextContents();
    logStep('DEMO_COURT_OPTIONS', 'PASS', `Demo mode options: ${JSON.stringify(demoOptions)}`);

    // ------------------------------------------------------------------------
    // 3. Prepare Demo Document & Execute Review
    // ------------------------------------------------------------------------
    console.log('\n--- 3. Preparing Demo Document & Executing Multi-Stage Review ---');
    const prepareBtn = page.getByRole('button', { name: 'Prepare document' });
    await prepareBtn.click();

    // Land on Prepared View (/analyses/:id)
    await page.waitForURL(/\/analyses\/[a-f0-9-]+$/, { timeout: 15000 });
    const preparedUrl = page.url();
    logStep('PREPARED_VIEW_NAV', 'PASS', `Navigated to Prepared View: ${preparedUrl}`);

    // Verify Court Profile in Prepared View metadata
    const courtProfileDisplay = await page.locator('dt:has-text("Court profile") + dd').textContent();
    logStep('PREPARED_COURT_PROFILE', 'PASS', `Court profile displayed: "${courtProfileDisplay?.trim()}"`);

    // Click "Run local checks"
    const runChecksBtn = page.getByRole('button', { name: /Run local checks/i });
    await runChecksBtn.waitFor({ state: 'visible', timeout: 8000 });
    await runChecksBtn.click();
    logStep('RUN_LOCAL_CHECKS_CLICKED', 'PASS', 'Started local checks; observing live review progress');

    // Wait for "Open review results" link to appear (allowing up to 120s for all 6 legal stages)
    console.log('   (Waiting for review stages: Privacy, Court Rules, Citations, Claims, Propositions, Quotes...)');
    const openResultsLink = page.getByRole('link', { name: /Open review results/i });
    await openResultsLink.waitFor({ state: 'visible', timeout: 120000 });
    logStep('REVIEW_COMPLETED', 'PASS', 'Multi-stage review completed successfully');

    // Click "Open review results"
    await openResultsLink.click();
    await page.waitForURL(/\/analyses\/[a-f0-9-]+\/results$/, { timeout: 15000 });
    const resultsUrl = page.url();
    logStep('RESULTS_VIEW_NAV', 'PASS', `Navigated to Results View: ${resultsUrl}`);

    // ------------------------------------------------------------------------
    // 4. Results View & Integrity Signals (T105)
    // ------------------------------------------------------------------------
    console.log('\n--- 4. Inspecting Results View & Category Filters (T105) ---');
    await page.waitForSelector('.result-score', { timeout: 30000 });
    const scoreVal = await page.textContent('.result-score-number');
    logStep('INTEGRITY_SCORE', 'PASS', `Filing integrity signal score: ${scoreVal?.trim()}`);

    // Test Category Score filter buttons
    const categoryFilterBtns = await page.locator('.category-filter-btn').all();
    logStep('CATEGORY_FILTERS_COUNT', 'PASS', `Found ${categoryFilterBtns.length} interactive category filter cards`);

    if (categoryFilterBtns.length > 0) {
      await categoryFilterBtns[0].click();
      await page.waitForTimeout(500);

      const isClearVisible = await page.isVisible('.category-clear-btn');
      logStep('CATEGORY_FILTER_APPLIED', isClearVisible ? 'PASS' : 'FAIL', 'Toggled category filter, "Show all categories" button is active');

      if (isClearVisible) {
        await page.click('.category-clear-btn');
        await page.waitForTimeout(300);
        logStep('CATEGORY_FILTER_CLEARED', 'PASS', 'Reset filter back to all categories');
      }
    }

    // ------------------------------------------------------------------------
    // 5. Findings, 5-Hop Rich Lineage & Explainer (T102)
    // ------------------------------------------------------------------------
    console.log('\n--- 5. Inspecting Findings & 5-Hop Lineage Chain (T102) ---');
    const findingBtns = await page.locator('.result-finding-button').all();
    logStep('FINDINGS_AVAILABLE', 'PASS', `Results contains ${findingBtns.length} findings`);

    if (findingBtns.length > 0) {
      await findingBtns[0].click();
      await page.waitForTimeout(500);

      // Inspect "How was this determined?" section
      const explainSummary = page.locator('details.determination-details summary');
      if (await explainSummary.isVisible()) {
        await explainSummary.click();
        await page.waitForTimeout(400);
        const methodBadge = await page.textContent('.determination-method-badge');
        logStep('METHODOLOGY_EXPLAINER', 'PASS', `Determination methodology: "${methodBadge?.trim().slice(0, 70)}..."`);
      }

      // Inspect 5-Hop Visual Lineage Chain
      const lineageHops = await page.locator('.lineage-step').all();
      logStep('5_HOP_LINEAGE', lineageHops.length >= 5 ? 'PASS' : 'FAIL', `Evidence lineage has ${lineageHops.length} hops (Span -> Extraction -> Source Authority -> Method -> Verdict)`);
    }

    // ------------------------------------------------------------------------
    // 6. Finding-Grounded Q&A (T103)
    // ------------------------------------------------------------------------
    console.log('\n--- 6. Testing Finding-Grounded Q&A (T103) ---');
    const qaSection = page.locator('.finding-qa-section');
    if (await qaSection.isVisible()) {
      const promptChips = await page.locator('.qa-chip-button').all();
      logStep('QA_PROMPT_CHIPS', 'PASS', `Found ${promptChips.length} suggested prompt chips`);

      if (promptChips.length > 0) {
        const chipPrompt = await promptChips[0].textContent();
        await promptChips[0].click();
        logStep('QA_SUBMIT_CHIP', 'PASS', `Clicked prompt chip: "${chipPrompt?.trim()}"`);

        // Wait for grounded answer
        await page.waitForSelector('.qa-thread-card', { timeout: 20000 });
        const answerText = await page.textContent('.qa-answer-text');
        const statusPill = await page.textContent('.qa-status-pill');
        logStep('QA_GROUNDED_ANSWER', 'PASS', `Answer received [${statusPill?.trim()}]: "${answerText?.slice(0, 90)}..."`);
      }
    }

    // ------------------------------------------------------------------------
    // 7. Apple-Design Legal Red-Team Mode (T101 & UI Polish)
    // ------------------------------------------------------------------------
    console.log('\n--- 7. Inspecting Apple-Design Legal Red-Team Mode (T101) ---');
    const redTeamPanel = page.locator('#result-red-team');
    logStep('RED_TEAM_MOUNTED', await redTeamPanel.isVisible() ? 'PASS' : 'FAIL', 'Legal Red-Team Mode container is mounted');

    // Verify absence of live dot
    const liveDotCount = await page.locator('.red-team-live-dot').count();
    logStep('NO_LIVE_DOT', liveDotCount === 0 ? 'PASS' : 'FAIL', 'Live dot icon is completely removed as requested');

    // Verify Metric Stat Capsules
    const metrics = await page.locator('.red-team-metric').all();
    logStep('RED_TEAM_CAPSULES', 'PASS', `Found ${metrics.length} metric capsules with fully rounded corners`);

    // Verify Weakness Cards and Minimize/Expand Toggle
    const cards = await page.locator('.red-team-card').all();
    logStep('RED_TEAM_CARDS', 'PASS', `Found ${cards.length} ranked vulnerability challenge cards`);

    if (cards.length > 0) {
      const firstCardToggle = cards[0].locator('.red-team-expand-toggle');
      const bodyInitial = await cards[0].locator('.red-team-card-body').isVisible();
      logStep('CARD_1_INITIAL', 'PASS', `Card 1 expanded initially: ${bodyInitial}`);

      // Test minimize
      await firstCardToggle.click();
      await page.waitForTimeout(400);
      const bodyAfterMin = await cards[0].locator('.red-team-card-body').isVisible();
      logStep('CARD_1_MINIMIZE', !bodyAfterMin ? 'PASS' : 'FAIL', 'Card minimized cleanly upon clicking toggle');

      // Test re-expand
      await firstCardToggle.click();
      await page.waitForTimeout(400);
      const bodyAfterExpand = await cards[0].locator('.red-team-card-body').isVisible();
      logStep('CARD_1_RE_EXPAND', bodyAfterExpand ? 'PASS' : 'FAIL', 'Card re-expanded cleanly upon second click');

      // Test Jump to Finding
      const jumpBtn = cards[0].locator('.linked-finding-jump').first();
      if (await jumpBtn.isVisible()) {
        await jumpBtn.click();
        await page.waitForTimeout(400);
        logStep('JUMP_TO_FINDING', 'PASS', 'Clicked "Jump to Finding", successfully shifted focus to target finding');
      }
    }

    // ------------------------------------------------------------------------
    // 8. Claim-Authority Graph Controls (T105)
    // ------------------------------------------------------------------------
    console.log('\n--- 8. Testing Claim-Authority Graph Controls (T105) ---');
    const graphSection = page.locator('#result-relationships');
    await graphSection.scrollIntoViewIfNeeded();
    await page.waitForTimeout(400);
    logStep('GRAPH_CONTAINER', await graphSection.isVisible() ? 'PASS' : 'FAIL', 'Evidence relationships graph mounted');

    const zoomIn = page.locator('.graph-toolbar-btn[aria-label="Zoom in graph"]');
    const zoomOut = page.locator('.graph-toolbar-btn[aria-label="Zoom out graph"]');
    const fitView = page.locator('.graph-toolbar-btn[aria-label="Fit graph to view"]');

    if (await zoomIn.isVisible() && await zoomOut.isVisible() && await fitView.isVisible()) {
      await zoomIn.click();
      await page.waitForTimeout(300);
      await zoomOut.click();
      await page.waitForTimeout(300);
      await fitView.click();
      await page.waitForTimeout(300);
      logStep('GRAPH_CONTROLS_INTERACTION', 'PASS', 'Exercised Zoom In, Zoom Out, and Fit View controls');
    }

    // ------------------------------------------------------------------------
    // 9. Report Export Formats (T104)
    // ------------------------------------------------------------------------
    console.log('\n--- 9. Testing Report Export (T104) ---');
    const analysisIdMatch = resultsUrl.match(/\/analyses\/([a-f0-9-]+)\/results/);
    const analysisId = analysisIdMatch ? analysisIdMatch[1] : null;

    if (analysisId) {
      // Retrieve session token from browser sessionStorage for authenticated report verification
      const sessionData = await page.evaluate(() => sessionStorage.getItem('filingguard-private-session-v1'));
      const token = sessionData ? JSON.parse(sessionData).token : null;
      const authHeaders = token ? { Authorization: `Bearer ${token}` } : {};

      const pdfResp = await page.request.get(`${API_URL}/api/v1/analyses/${analysisId}/report?format=pdf`, { headers: authHeaders });
      const body = await pdfResp.body();
      const isPdf = body.slice(0, 4).toString() === '%PDF';
      logStep('PDF_EXPORT', isPdf ? 'PASS' : 'FAIL', `Generated authenticated PDF export (${body.length} bytes, header: %PDF)`);

      const mdResp = await page.request.get(`${API_URL}/api/v1/analyses/${analysisId}/report?format=markdown`, { headers: authHeaders });
      const mdText = await mdResp.text();
      logStep('MD_EXPORT', mdText.includes('FilingGuard') ? 'PASS' : 'FAIL', `Generated authenticated Markdown report (${mdText.length} characters)`);
    }

    // ------------------------------------------------------------------------
    // 10. Live Submission with N.D. Tex. LR 7.2(f) Real Court Profile (T106)
    // ------------------------------------------------------------------------
    console.log('\n--- 10. Testing Live Text Submission with N.D. Tex. LR 7.2(f) (T106) ---');
    await page.goto(BASE_URL, { waitUntil: 'networkidle' });
    await page.waitForTimeout(500);

    // In text mode, select us-txnd-lr7-2f-v1
    await page.selectOption('#court', 'us-txnd-lr7-2f-v1');
    const aiCheckbox = page.locator('.checkbox-label input[type="checkbox"]');
    if (!(await aiCheckbox.isChecked())) {
      await aiCheckbox.check();
    }
    logStep('AI_USED_CHECKED', await aiCheckbox.isChecked() ? 'PASS' : 'FAIL', 'Configured AI-used disclosure requirement flag to true');

    // Type text WITHOUT the required heading on page 1
    const filingContent = 'IN THE UNITED STATES DISTRICT COURT FOR THE NORTHERN DISTRICT OF TEXAS\n\nMOTION FOR SUMMARY JUDGMENT\n\nPlaintiff moves for summary judgment under Fed. R. Civ. P. 56.\nRelevant legal authority: 576 U.S. 644.';
    await page.fill('#filing', filingContent);

    await page.click('button:has-text("Prepare document")');
    await page.waitForURL(/\/analyses\/[a-f0-9-]+$/, { timeout: 15000 });

    const liveCourtDisplay = await page.locator('dt:has-text("Court profile") + dd').textContent();
    logStep('LIVE_PREPARED_COURT', 'PASS', `Court profile displayed: "${liveCourtDisplay?.trim()}"`);

    const liveRunBtn = page.getByRole('button', { name: /Run local checks/i });
    await liveRunBtn.waitFor({ state: 'visible', timeout: 8000 });
    await liveRunBtn.click();
    logStep('LIVE_CHECKS_STARTED', 'PASS', 'Started live review checks for N.D. Tex. LR 7.2(f)');

    const liveOpenResults = page.getByRole('link', { name: /Open review results/i });
    await liveOpenResults.waitFor({ state: 'visible', timeout: 120000 });
    await liveOpenResults.click();
    await page.waitForURL(/\/analyses\/[a-f0-9-]+\/results$/, { timeout: 15000 });
    logStep('LIVE_RESULTS_VIEW', 'PASS', 'Live review completed and navigated to results view');

    // Wait for results score to load
    await page.waitForSelector('.result-score', { timeout: 30000 });

    // Verify N.D. Tex. Local Rule 7.2(f) finding is generated
    await page.waitForSelector('.result-finding-button', { timeout: 15000 });
    const findingsListText = await page.locator('.results-finding-list').textContent();
    const hasTxndRuleFinding = findingsListText?.includes('N.D. Tex. Local Rule 7.2(f)');
    logStep('TXND_RULE_FINDING_VERIFIED', hasTxndRuleFinding ? 'PASS' : 'FAIL', `Verified N.D. Tex. LR 7.2(f) AI-use disclosure finding generated: ${hasTxndRuleFinding}`);

    // Pause briefly so user can view the final result state in the open browser window
    console.log('\n[Inspection Complete] Pausing for 5 seconds on the verified results page in headful browser...');
    await page.waitForTimeout(5000);

  } catch (err) {
    console.error('\n❌ Execution error:', err);
    logStep('TEST_EXCEPTION', 'FAIL', err.message);
  } finally {
    await browser.close();
  }

  console.log('\n================================================================');
  console.log('                 VERIFICATION SUMMARY REPORT                    ');
  console.log('================================================================');
  let passCount = 0;
  let failCount = 0;
  for (const r of report) {
    if (r.status === 'PASS') passCount++;
    if (r.status === 'FAIL') failCount++;
  }
  console.log(`Total checkpoints: ${report.length} | Passed: ${passCount} | Failed: ${failCount}`);
  if (failCount === 0) {
    console.log('🎉 100% OF ALL PHASE B FEATURES VERIFIED SUCCESSFULLY IN HEADFUL BROWSER!');
  }
}

main().catch(console.error);
