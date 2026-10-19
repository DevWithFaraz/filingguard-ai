/**
 * FilingGuard AI - Microsoft Word Add-in Controller
 * Integrates Office.js with FilingGuard REST API for pre-filing compliance checks.
 */

let apiBaseUrl = 'http://localhost:8000';
let authToken = '';
let currentAnalysisId = null;
let paragraphMap = [];

Office.onReady((info) => {
  if (info.host === Office.HostType.Word) {
    document.getElementById('connect-btn').addEventListener('click', handleConnect);
    document.getElementById('run-review-btn').addEventListener('click', handleRunReview);
  }
});

async function handleConnect() {
  const urlInput = document.getElementById('api-url').value.trim().replace(/\/$/, '');
  const tokenInput = document.getElementById('session-token').value.trim();
  const statusEl = document.getElementById('auth-status');

  apiBaseUrl = urlInput || 'http://localhost:8000';
  authToken = tokenInput;

  statusEl.textContent = 'Verifying connection...';
  statusEl.className = 'addin-status-text';

  try {
    const res = await fetch(`${apiBaseUrl}/api/v1/health`);
    if (!res.ok) throw new Error(`API returned HTTP ${res.status}`);

    statusEl.textContent = 'Connected to FilingGuard API.';
    statusEl.className = 'addin-status-text success';
    document.getElementById('review-section').style.display = 'block';
  } catch (err) {
    statusEl.textContent = `Connection failed: ${err.message}`;
    statusEl.className = 'addin-status-text error';
  }
}

async function handleRunReview() {
  const runBtn = document.getElementById('run-review-btn');
  const progressContainer = document.getElementById('progress-bar-container');
  const progressText = document.getElementById('progress-text');
  const courtProfile = document.getElementById('court-profile').value;

  runBtn.disabled = true;
  progressContainer.style.display = 'block';
  progressText.textContent = 'Extracting document text from Word...';

  try {
    // 1. Extract paragraphs from active Word document
    const extractedText = await Word.run(async (context) => {
      const paragraphs = context.document.body.paragraphs;
      paragraphs.load('text');
      await context.sync();

      paragraphMap = [];
      let fullText = '';
      let currentOffset = 0;

      for (let i = 0; i < paragraphs.items.length; i++) {
        const pText = paragraphs.items[i].text.trim();
        if (pText.length > 0) {
          const start = currentOffset;
          const end = start + pText.length;
          paragraphMap.push({
            index: i,
            start,
            end,
            text: pText,
          });
          fullText += pText + '\n\n';
          currentOffset = fullText.length;
        }
      }
      return fullText;
    });

    if (!extractedText.trim()) {
      throw new Error('Word document contains no readable text.');
    }

    // 2. Prepare text analysis
    progressText.textContent = 'Submitting document to FilingGuard...';
    const prepHeaders = {
      'Content-Type': 'application/json',
      'Origin': window.location.origin || 'https://filingguard.ai',
    };
    if (authToken) {
      prepHeaders['Authorization'] = `Bearer ${authToken}`;
    }

    const prepRes = await fetch(`${apiBaseUrl}/api/v1/analyses/text`, {
      method: 'POST',
      headers: prepHeaders,
      body: JSON.stringify({
        document_name: 'Word Active Document',
        text: extractedText,
        court_profile_id: courtProfile,
        ai_used: true,
      }),
    });

    if (!prepRes.ok) {
      throw new Error(`Document preparation failed (HTTP ${prepRes.status})`);
    }

    const prepData = await prepRes.json();
    currentAnalysisId = prepData.analysis_id;

    // 3. Trigger review execution
    progressText.textContent = 'Running legal integrity checks...';
    await fetch(`${apiBaseUrl}/api/v1/analyses/${currentAnalysisId}/run`, {
      method: 'POST',
      headers: prepHeaders,
    });

    // 4. Poll until completion
    let status = 'queued';
    const deadline = Date.now() + 60000;
    while (status === 'queued' || status === 'running') {
      if (Date.now() > deadline) throw new Error('Review timed out.');
      await new Promise((r) => setTimeout(r, 1500));

      const statusRes = await fetch(`${apiBaseUrl}/api/v1/analyses/${currentAnalysisId}/status`, {
        headers: prepHeaders,
      });
      if (statusRes.ok) {
        const sData = await statusRes.json();
        status = sData.status;
        progressText.textContent = `Review in progress (${status})...`;
      }
    }

    // 5. Fetch and render findings
    const resultsRes = await fetch(`${apiBaseUrl}/api/v1/analyses/${currentAnalysisId}/results`, {
      headers: prepHeaders,
    });
    if (!resultsRes.ok) throw new Error('Could not load review results.');

    const results = await resultsRes.json();
    renderFindings(results);
    progressContainer.style.display = 'none';
  } catch (err) {
    progressText.textContent = `Error: ${err.message}`;
  } finally {
    runBtn.disabled = false;
  }
}

function renderFindings(results) {
  const section = document.getElementById('findings-section');
  const countEl = document.getElementById('findings-count');
  const scoreEl = document.getElementById('integrity-score');
  const listEl = document.getElementById('findings-list');

  section.style.display = 'block';
  countEl.textContent = results.findings.length;
  scoreEl.textContent = results.score && results.score.value !== null
    ? `Score: ${results.score.value}/100`
    : 'Score: Unrated';

  listEl.innerHTML = '';

  if (results.findings.length === 0) {
    listEl.innerHTML = '<li class="no-findings">No issues detected in document scope.</li>';
    return;
  }

  results.findings.forEach((finding) => {
    const li = document.createElement('li');
    li.className = `finding-item severity-${finding.severity}`;
    li.innerHTML = `
      <div class="finding-top">
        <span class="finding-sev-pill">${finding.severity}</span>
        <strong class="finding-title">${finding.title}</strong>
      </div>
      <p class="finding-desc">${finding.description}</p>
      ${finding.masked_excerpt ? `<blockquote class="finding-excerpt">${finding.masked_excerpt}</blockquote>` : ''}
    `;

    li.addEventListener('click', () => navigateToFindingInWord(finding));
    listEl.appendChild(li);
  });
}

/**
 * Document Synchronization:
 * Navigates to the relevant text/paragraph in Microsoft Word when a finding is clicked.
 */
async function navigateToFindingInWord(finding) {
  await Word.run(async (context) => {
    const searchTarget = finding.masked_excerpt || finding.title;
    if (!searchTarget) return;

    // Search for the matching text excerpt in the document
    const searchResults = context.document.body.search(searchTarget.slice(0, 50), {
      matchCase: false,
      matchWholeWord: false,
    });
    searchResults.load('items');
    await context.sync();

    if (searchResults.items.length > 0) {
      // Select the found text range in the Word document
      searchResults.items[0].select('Select');
      await context.sync();
    } else {
      // Fallback: select by paragraph index if mapped
      const paragraphs = context.document.body.paragraphs;
      paragraphs.load('items');
      await context.sync();
      if (paragraphs.items.length > 0) {
        paragraphs.items[0].select('Select');
      }
    }
  }).catch((err) => {
    console.error('Word selection synchronization error:', err);
  });
}
