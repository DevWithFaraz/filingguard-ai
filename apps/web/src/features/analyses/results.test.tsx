import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router';
import { beforeEach, expect, it, vi } from 'vitest';
import { downloadReport, getEvidence, getGraph, getRedTeam, getResults, runRedTeam, safeSourceURL, validateResults,
  type FindingEvidence, type RedTeamResponse, type ReviewGraph, type ReviewResults } from '../../lib/api/results';
import { ResultsView } from './ResultsView';

vi.mock('../../lib/api/results', async importOriginal => ({
  ...await importOriginal<typeof import('../../lib/api/results')>(),
  getResults: vi.fn(), getGraph: vi.fn(), getEvidence: vi.fn(), downloadReport: vi.fn(),
  getRedTeam: vi.fn(), runRedTeam: vi.fn(),
}));
export const mockZoomIn = vi.fn();
export const mockZoomOut = vi.fn();
export const mockFitView = vi.fn();

vi.mock('@xyflow/react', () => ({
  Background: () => null,
  Controls: () => null,
  Panel: ({ children }: { children: React.ReactNode }) => <div data-testid="flow-panel">{children}</div>,
  ReactFlowProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  useReactFlow: () => ({
    zoomIn: mockZoomIn,
    zoomOut: mockZoomOut,
    fitView: mockFitView,
  }),
  ReactFlow: ({
    nodes,
    children,
    onNodeClick,
  }: {
    nodes: { id: string; data: { label: string } }[];
    children?: React.ReactNode;
    onNodeClick: (event: unknown, node: { id: string }) => void;
  }) => (
    <div data-testid="flow">
      {children}
      {nodes.map(node => (
        <button key={node.id} onClick={() => onNodeClick(null, node)}>
          {node.data.label}
        </button>
      ))}
    </div>
  ),
}));
const id = 'b9127518-6920-45c2-915b-18ce3fa7d876';
const coverage = { eligible: 3, evaluated: 2, unavailable: 1, pending: 0, truncated: false, limitation: null };
const location = { start: 10, end: 30, page_number: null, segment_id: 'segment-1' };
function fixture(): ReviewResults {
  return { analysis_id: id, document_name: 'Synthetic control', created_at: '2026-10-08T08:00:00Z',
    court_profile_id: 'synthetic-demo-v1', mode: 'live', status: 'partial', coverage,
    stages: [{ name: 'quotes', status: 'partial', coverage, reason: 'One source was unavailable.', applicable: true }],
    score: { value: null, risk_level: null, provisional: true, version: 'integrity-v1', deductions: [],
      limitation: 'A score needs meaningful legal evaluation.' },
    findings: [{ id: 'quote-finding', type: 'quote', severity: 'medium', title: 'Quotation differs from source',
      description: 'The source omits the inserted negation. Similarity does not establish meaning.',
      masked_excerpt: 'Equal access is not a fundamental public right.', start: 10, end: 30,
      evidence_count: 2, ai_assisted: false },
    { id: 'critical-finding', type: 'privacy', severity: 'critical', title: 'Private identifier detected',
      description: 'Review the masked identifier before filing.', masked_excerpt: '[REDACTED]',
      start: 1, end: 8, evidence_count: 1, ai_assisted: false }],
    citations: [{ id: 'citation-1', masked_raw_text: '123 U.S. 456', verification_status: 'verified',
      authority_id: 'authority-1', location }],
    claims: [{ id: 'claim-1', text: 'Equal access is not a fundamental public right.', location,
      extraction_method: 'heuristic', links: [{ id: 'link-1', citation_id: 'citation-1',
        authority_id: 'authority-1', support_status: 'unclear', explanation: 'Limited passage coverage.', confidence: null }],
      corrected_text: null, correction_history: [], propositions_stale: false }],
    quotes: [{ id: 'quote-1', text: 'Equal access is not a fundamental public right.', location,
      citation_id: 'citation-1', match_status: 'close', similarity: .93,
      closest_passage: 'Equal access is a fundamental public right.' }],
    limitation: 'Missing provider checks remain unavailable. Human review is required.' };
}
const graph: ReviewGraph = { analysis_id: id,
  nodes: [{ id: 'section-1', kind: 'section', label: 'Paragraph 1', status: 'extracted', finding_ids: [] },
    { id: 'claim-1', kind: 'claim', label: 'Traceable claim', status: 'unclear', finding_ids: ['quote-finding'] },
    { id: 'authority-1', kind: 'authority', label: 'Example authority', status: 'verified', finding_ids: ['quote-finding'] }],
  edges: [{ id: 'edge-1', source: 'section-1', target: 'claim-1', label: 'contains claim' },
    { id: 'edge-2', source: 'claim-1', target: 'authority-1', label: 'unclear support' }] };
const evidence: FindingEvidence = { analysis_id: id, finding_id: 'quote-finding', evidence: [{
  id: 'evidence-1', excerpt: 'Equal access is a fundamental public right.',
  source_url: 'https://www.courtlistener.com/opinion/123/', source_start: 32, source_end: 74,
  source_sha256: 'a'.repeat(64), retrieved_at: '2026-10-08T08:00:00Z', method_version: 'quote-forensics-v1',
  model_version: null, prompt_version: null, provenance: 'synthetic',
}] };

const redTeamFixture: RedTeamResponse = {
  analysis_id: id,
  generated_at: '2026-10-08T08:00:00Z',
  total_weaknesses: 1,
  critical_count: 0,
  high_count: 1,
  medium_count: 0,
  low_count: 0,
  summary: '1 vulnerability identified across filing checks.',
  limitation: 'Synthesized from verified findings.',
  weaknesses: [
    {
      id: 'weakness-1',
      severity: 'high',
      vulnerability_type: 'altered_quotation',
      title: 'Quotation divergence in precedent authority',
      challenge_theory: 'Opposing counsel will highlight that the quotation diverges from source.',
      impact_summary: 'Could undermine the credibility of arguments relying on this passage.',
      remediation_recommendation: 'Verify the excerpt directly against official slip opinion.',
      linked_finding_ids: ['quote-finding'],
      linked_citation_ids: ['citation-1'],
      linked_claim_ids: ['claim-1'],
      linked_quote_ids: ['quote-1'],
    },
  ],
};

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(getResults).mockResolvedValue(fixture());
  vi.mocked(getGraph).mockResolvedValue(graph);
  vi.mocked(getEvidence).mockResolvedValue(evidence);
  vi.mocked(downloadReport).mockResolvedValue();
  vi.mocked(getRedTeam).mockResolvedValue(redTeamFixture);
  vi.mocked(runRedTeam).mockResolvedValue(redTeamFixture);
});
function open() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
  return render(<QueryClientProvider client={client}><MemoryRouter initialEntries={[`/analyses/${id}/results`]}>
    <Routes><Route path="/analyses/:id/results" element={<ResultsView />} /></Routes>
  </MemoryRouter></QueryClientProvider>);
}

it('labels partial coverage and unknown scores prominently, and prioritizes critical findings', async () => {
  open();
  expect(await screen.findByText('Incomplete review · partial')).toBeInTheDocument();
  expect(screen.getByText('Unknown')).toBeInTheDocument();
  expect(screen.getByText(/2 of 3 eligible checks evaluated · 1 unavailable/)).toBeInTheDocument();
  expect(screen.getByText(/1 critical finding requires attention/)).toBeInTheDocument();
  const buttons = screen.getAllByRole('button').filter(button => button.classList.contains('result-finding-button'));
  expect(buttons[0]).toHaveTextContent('Private identifier detected');
  expect(screen.getByText(/does not certify filing safety/)).toBeInTheDocument();
});

it('filters findings and loads owner-scoped evidence with source offsets and method', async () => {
  open();
  await screen.findByText('Unknown');
  fireEvent.change(screen.getByLabelText('Finding category'), { target: { value: 'quote' } });
  expect(screen.queryByRole('button', { name: /critical Private identifier/ })).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: /medium Quotation differs/ }));
  expect(await screen.findByRole('link', { name: /Open source/ })).toHaveAttribute('href', evidence.evidence[0]!.source_url);
  expect(getEvidence).toHaveBeenCalledWith(id, 'quote-finding', expect.any(AbortSignal));
  expect(screen.getAllByText('quote-forensics-v1').length).toBeGreaterThan(0);
  expect(screen.getByText('32–74 · Unicode code points')).toBeInTheDocument();
  expect(screen.getByText('a'.repeat(64))).toBeInTheDocument();
  expect(screen.getByText(/Next review action: compare the filing/)).toBeInTheDocument();
});

it('shows saved category values and keeps unrun categories unknown', async () => {
  const value = fixture();
  value.score.categories = [
    { type: 'privacy', eligible: 1, evaluated: 1, value: 75, deducted_points: 25 },
    { type: 'claim_support', eligible: 1, evaluated: 0, value: null, deducted_points: 0 },
  ];
  vi.mocked(getResults).mockResolvedValue(value);
  open();
  const categories = await screen.findByLabelText('Category signals');
  expect(categories).toHaveTextContent('privacy75/100');
  expect(categories).toHaveTextContent('1/1 evaluated · 25 points deducted');
  expect(categories).toHaveTextContent('claim supportUnknown');
  expect(categories).toHaveTextContent('0/1 evaluated · 0 points deducted');
  expect(validateResults(value, id).score.categories).toEqual(value.score.categories);
  expect(() => validateResults({ ...value, score: { ...value.score, categories: [
    { type: 'claim_support', eligible: 1, evaluated: 0, value: 100, deducted_points: 0 },
  ] } }, id)).toThrow();
});

it('accepts table of authorities findings and score categories', async () => {
  const value = fixture();
  value.findings.push({
    id: 'toa-finding', type: 'table_of_authorities', severity: 'medium',
    title: 'Authority missing from Table of Authorities: 576 U.S. 644',
    description: 'The body cites 576 U.S. 644, but that identity was not found in the table.',
    masked_excerpt: '576 U.S. 644', start: 40, end: 51, evidence_count: 1, ai_assisted: false,
  });
  value.score.categories = [
    { type: 'table_of_authorities', eligible: 2, evaluated: 2, value: 85, deducted_points: 15 },
  ];
  expect(validateResults(value, id).findings.some(item => item.type === 'table_of_authorities')).toBe(true);
  vi.mocked(getResults).mockResolvedValue(value);
  open();
  fireEvent.change(await screen.findByLabelText('Finding category'), { target: { value: 'table_of_authorities' } });
  expect(screen.getByRole('button', { name: /medium Authority missing from Table of Authorities/ })).toBeInTheDocument();
});

it('the accessible graph list exposes stored relationships and selects a linked finding', async () => {
  open();
  await screen.findByRole('heading', { name: 'Evidence relationships' });
  fireEvent.click(screen.getByText('Keyboard accessible graph list (3 nodes)'));
  fireEvent.click(screen.getByRole('button', { name: 'claim: Traceable claim · unclear' }));
  expect(await screen.findByRole('heading', { name: 'Quotation differs from source' })).toBeInTheDocument();
  expect(screen.getByText(/unclear support → Example authority/)).toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: 'section: Paragraph 1 · extracted' }));
  expect(screen.getByText(/No finding is linked to this node/)).toBeInTheDocument();
});

it('renders original quote and closest passage as string evidence with explicit uncertainty', async () => {
  open(); await screen.findByText('Unknown');
  fireEvent.click(screen.getByText('Quotation checks (1)'));
  expect(screen.getByText('close · String similarity 93%')).toBeInTheDocument();
  expect(screen.getByText(/String similarity does not establish equivalent meaning/)).toBeInTheDocument();
  expect(screen.getByText('Equal access is a fundamental public right.')).toBeInTheDocument();
});

it('no applicable checks remains unknown and cannot masquerade as a successful review', async () => {
  const value = fixture();
  value.coverage = { eligible: 0, evaluated: 0, unavailable: 0, pending: 0, truncated: false, limitation: null };
  value.findings = []; value.stages = []; value.quotes = []; value.claims = []; value.citations = [];
  vi.mocked(getResults).mockResolvedValue(value);
  open();
  expect(await screen.findByText(/No applicable checks have been evaluated/)).toBeInTheDocument();
  expect(screen.getByText(/No findings were recorded. Inspect coverage/)).toBeInTheDocument();
  expect(screen.getByText('Unknown')).toBeInTheDocument();
});

it('results failure has a retry path and does not expose a fabricated dashboard', async () => {
  vi.mocked(getResults).mockRejectedValueOnce(new Error('Private review expired'));
  open();
  expect(await screen.findByRole('alert')).toHaveTextContent('Private review expired');
  expect(screen.queryByText('Unknown')).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: 'Retry results' }));
  expect(await screen.findByText('Unknown')).toBeInTheDocument();
});

it('requests server report downloads using the current analysis and selected format', async () => {
  open(); await screen.findByText('Unknown');
  fireEvent.click(screen.getByRole('button', { name: 'Download Markdown' }));
  await waitFor(() => expect(downloadReport).toHaveBeenCalledWith(id, 'markdown'));
  await screen.findByRole('button', { name: 'Download HTML' });
});

it('rejects cross-analysis responses, impossible coverage, invalid scores and unsafe links', () => {
  const value = fixture();
  expect(validateResults(value, id).analysis_id).toBe(id);
  expect(() => validateResults(value, 'other-analysis')).toThrow();
  expect(() => validateResults({ ...value, coverage: { ...coverage, evaluated: 4 } }, id)).toThrow();
  expect(() => validateResults({ ...value, score: { ...value.score, value: 101 } }, id)).toThrow();
  expect(safeSourceURL('javascript:alert(1)')).toBe(false);
  expect(safeSourceURL('https://user:password@example.com/')).toBe(false);
  expect(safeSourceURL('https://www.courtlistener.com/opinion/123/')).toBe(true);
});

it('graph load failure preserves available independent findings', async () => {
  vi.mocked(getGraph).mockRejectedValue(new Error('Unavailable'));
  open();
  const alert = await screen.findByText('Graph unavailable.');
  expect(within(alert).getByRole('button', { name: 'Retry graph' })).toBeInTheDocument();
  expect(screen.getByRole('button', { name: /medium Quotation differs/ })).toBeInTheDocument();
});

it('integrates Red-Team mode in results jump navigation and triggers finding selection', async () => {
  open();
  expect(await screen.findByRole('link', { name: 'Red Team' })).toHaveAttribute('href', '#result-red-team');
  expect(await screen.findByRole('heading', { name: /Legal Red-Team Mode/ })).toBeInTheDocument();
  expect(screen.getByText(/1 vulnerability identified across filing checks/)).toBeInTheDocument();
  expect(screen.getByText('Quotation divergence in precedent authority')).toBeInTheDocument();
  expect(screen.getByText(/Opposing counsel will highlight/)).toBeInTheDocument();

  fireEvent.click(screen.getByRole('button', { name: /Jump to Finding/ }));
  expect(await screen.findByRole('heading', { name: 'Quotation differs from source' })).toBeInTheDocument();
});

it('renders expandable determination methodology and 5-hop evidence lineage chain (FR-205, FR-224)', async () => {
  open();
  await screen.findByText('Unknown');
  // Select quote finding
  fireEvent.click(screen.getByRole('button', { name: /medium Quotation differs/ }));

  // FR-205: Expandable "How was this determined?"
  expect(screen.getByText('How was this determined?')).toBeInTheDocument();
  expect(screen.getByText('Multi-tier quotation forensics')).toBeInTheDocument();
  expect(screen.getByText('Deterministic Forensic Check')).toBeInTheDocument();
  expect(screen.getByText(/String similarity measures lexical overlap/)).toBeInTheDocument();

  // FR-224: Visual Lineage Chain
  const lineage = screen.getByLabelText('Evidence lineage chain');
  expect(within(lineage).getByRole('heading', { name: 'Evidence Lineage Chain' })).toBeInTheDocument();
  expect(within(lineage).getByText('01')).toBeInTheDocument();
  expect(within(lineage).getByText('Document Span')).toBeInTheDocument();
  expect(within(lineage).getByText('Offsets 10–30')).toBeInTheDocument();

  expect(within(lineage).getByText('02')).toBeInTheDocument();
  expect(within(lineage).getByText('Extraction Target')).toBeInTheDocument();

  expect(within(lineage).getByText('03')).toBeInTheDocument();
  expect(within(lineage).getByText('Source Authority')).toBeInTheDocument();
  expect(await within(lineage).findByRole('link', { name: /Open official source/ })).toHaveAttribute(
    'href',
    'https://www.courtlistener.com/opinion/123/',
  );
  expect(within(lineage).getByText('Offsets 32–74')).toBeInTheDocument();

  expect(within(lineage).getByText('04')).toBeInTheDocument();
  expect(within(lineage).getByText('Verification Method')).toBeInTheDocument();
  expect(within(lineage).getByText('quote-forensics-v1')).toBeInTheDocument();
  expect(within(lineage).getByText('Provenance: synthetic')).toBeInTheDocument();

  expect(within(lineage).getByText('05')).toBeInTheDocument();
  expect(within(lineage).getByText('Finding Verdict')).toBeInTheDocument();
});

it('users can click score category cards to filter findings and clear filters (FR-186)', async () => {
  const value = fixture();
  value.score.categories = [
    { type: 'privacy', eligible: 1, evaluated: 1, value: 75, deducted_points: 25 },
    { type: 'quote', eligible: 1, evaluated: 1, value: 92, deducted_points: 8 },
  ];
  vi.mocked(getResults).mockResolvedValue(value);
  open();

  await screen.findByText('Unknown');
  // Both findings initially visible
  expect(screen.getByRole('button', { name: /critical Private identifier detected/ })).toBeInTheDocument();
  expect(screen.getByRole('button', { name: /medium Quotation differs/ })).toBeInTheDocument();

  // Click privacy category card
  const privacyBtn = screen.getByRole('button', { name: /privacy 75\/100/ });
  fireEvent.click(privacyBtn);

  // Now only privacy finding is shown
  expect(screen.getByRole('button', { name: /critical Private identifier detected/ })).toBeInTheDocument();
  expect(screen.queryByRole('button', { name: /medium Quotation differs/ })).not.toBeInTheDocument();

  // Clear button appears and works
  const clearPill = screen.getByRole('button', { name: 'Clear category filter' });
  fireEvent.click(clearPill);

  // Both findings restored
  expect(screen.getByRole('button', { name: /critical Private identifier detected/ })).toBeInTheDocument();
  expect(screen.getByRole('button', { name: /medium Quotation differs/ })).toBeInTheDocument();
});

it('provides zoom in, zoom out, fit to view and reset controls on the evidence graph (FR-105)', async () => {
  open();
  await screen.findByRole('heading', { name: 'Evidence relationships' });

  const zoomInBtn = screen.getByRole('button', { name: 'Zoom in graph' });
  const zoomOutBtn = screen.getByRole('button', { name: 'Zoom out graph' });
  const fitViewBtn = screen.getByRole('button', { name: 'Fit graph to view' });
  const resetBtn = screen.getByRole('button', { name: 'Reset graph view' });

  expect(zoomInBtn).toBeInTheDocument();
  expect(zoomOutBtn).toBeInTheDocument();
  expect(fitViewBtn).toBeInTheDocument();
  expect(resetBtn).toBeInTheDocument();

  fireEvent.click(zoomInBtn);
  expect(mockZoomIn).toHaveBeenCalled();

  fireEvent.click(zoomOutBtn);
  expect(mockZoomOut).toHaveBeenCalled();

  fireEvent.click(fitViewBtn);
  expect(mockFitView).toHaveBeenCalled();

  fireEvent.click(resetBtn);
  expect(mockFitView).toHaveBeenCalledTimes(2);

  fireEvent.click(screen.getByRole('button', { name: 'Download graph' }));
  await waitFor(() => expect(downloadReport).toHaveBeenCalledWith(id, 'graph-svg'));
});

it('renders unsupported claims as separate warning nodes in visual graph and accessible list (FR-106)', async () => {
  const customGraph: ReviewGraph = {
    analysis_id: id,
    nodes: [
      { id: 'section-1', kind: 'section', label: 'Paragraph 1', status: 'extracted', finding_ids: [] },
      { id: 'claim-warning', kind: 'claim', label: 'Unsupported fabricated claim', status: 'unsupported', finding_ids: ['critical-finding'] },
      { id: 'authority-1', kind: 'authority', label: 'Example authority', status: 'verified', finding_ids: [] },
    ],
    edges: [
      { id: 'edge-1', source: 'section-1', target: 'claim-warning', label: 'contains claim' },
      { id: 'edge-2', source: 'claim-warning', target: 'authority-1', label: 'contradicted' },
    ],
  };
  vi.mocked(getGraph).mockResolvedValue(customGraph);
  open();

  await screen.findByRole('heading', { name: 'Evidence relationships' });

  // Visual flow mock renders node labels: should include warning indicator
  expect(screen.getByText(/⚠️ UNSUPPORTED/)).toBeInTheDocument();

  // Keyboard accessible list exposes warning badge
  fireEvent.click(screen.getByText('Keyboard accessible graph list (3 nodes)'));
  expect(screen.getByText(/⚠️ \[Warning: Unsupported claim\]/)).toBeInTheDocument();
});

it('associates multiple claims with a single authority and provides cross-view navigation (FR-064)', async () => {
  const multiClaimGraph: ReviewGraph = {
    analysis_id: id,
    nodes: [
      { id: 'section-1', kind: 'section', label: 'Paragraph 1', status: 'extracted', finding_ids: [] },
      { id: 'claim-1', kind: 'claim', label: 'First Proposition', status: 'supported', finding_ids: ['quote-finding'] },
      { id: 'claim-2', kind: 'claim', label: 'Second Proposition', status: 'unsupported', finding_ids: ['critical-finding'] },
      { id: 'authority-shared', kind: 'authority', label: 'Brown v. Board of Education', status: 'verified', finding_ids: ['quote-finding', 'critical-finding'] },
    ],
    edges: [
      { id: 'e-1', source: 'section-1', target: 'claim-1', label: 'contains' },
      { id: 'e-2', source: 'section-1', target: 'claim-2', label: 'contains' },
      { id: 'e-3', source: 'claim-1', target: 'authority-shared', label: 'supported' },
      { id: 'e-4', source: 'claim-2', target: 'authority-shared', label: 'unsupported' },
    ],
  };
  vi.mocked(getGraph).mockResolvedValue(multiClaimGraph);
  open();

  await screen.findByRole('heading', { name: 'Evidence relationships' });
  fireEvent.click(screen.getByText('Keyboard accessible graph list (4 nodes)'));

  // Select the shared authority
  fireEvent.click(screen.getByRole('button', { name: /authority: Brown v. Board of Education/ }));

  // FR-064: Should show associated claims count and buttons
  expect(await screen.findByText(/Associated claims \(2\):/)).toBeInTheDocument();
  const claimsSection = screen.getByText(/Associated claims \(2\):/).closest('div')!;
  expect(within(claimsSection).getByRole('button', { name: /First Proposition/ })).toBeInTheDocument();
  expect(within(claimsSection).getByRole('button', { name: /Second Proposition/ })).toBeInTheDocument();

  // Cross-view finding buttons for both linked findings
  expect(screen.getByText(/Linked findings:/)).toBeInTheDocument();
  const findingButtons = screen.getAllByRole('button', { name: /Quotation differs from source|Private identifier detected/ });
  expect(findingButtons.length).toBeGreaterThanOrEqual(1);

  // Clicking an associated claim button switches selection to that claim
  fireEvent.click(within(claimsSection).getByRole('button', { name: /Second Proposition/ }));
  const selectionText = await screen.findByText(/Selected claim:/);
  expect(selectionText.parentElement).toHaveTextContent(/Selected claim:\s*Second Proposition/);
});

it('displays duplicate citation badges and repeated locations (FR-045)', async () => {
  const custom = fixture();
  custom.citations = [
    {
      id: 'citation-1',
      masked_raw_text: '347 U.S. 483',
      verification_status: 'verified',
      authority_id: 'authority-1',
      location: { start: 10, end: 22, page_number: 1, segment_id: 'segment-1' },
      duplicate_count: 2,
      repeated_locations: [
        { start: 10, end: 22, page_number: 1, segment_id: 'segment-1' },
        { start: 80, end: 92, page_number: 3, segment_id: 'segment-3' },
      ],
    },
  ];
  vi.mocked(getResults).mockResolvedValue(custom);
  open();

  await screen.findByRole('heading', { name: 'Inspect the source checks' });
  fireEvent.click(screen.getByText(/Citation occurrences \(1\)/));

  expect(await screen.findByText('Repeated (2x)')).toBeInTheDocument();
  expect(screen.getByText('Repeated in filing:')).toBeInTheDocument();
  expect(screen.getByText(/Span 10–22 \(Page 1\)/)).toBeInTheDocument();
  expect(screen.getByText(/Span 80–92 \(Page 3\)/)).toBeInTheDocument();
});



