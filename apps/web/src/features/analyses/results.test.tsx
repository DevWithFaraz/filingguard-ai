import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router';
import { beforeEach, expect, it, vi } from 'vitest';
import { downloadReport, getEvidence, getGraph, getResults, safeSourceURL, validateResults,
  type FindingEvidence, type ReviewGraph, type ReviewResults } from '../../lib/api/results';
import { ResultsView } from './ResultsView';

vi.mock('../../lib/api/results', async importOriginal => ({
  ...await importOriginal<typeof import('../../lib/api/results')>(),
  getResults: vi.fn(), getGraph: vi.fn(), getEvidence: vi.fn(), downloadReport: vi.fn(),
}));
vi.mock('@xyflow/react', () => ({
  Background: () => null, Controls: () => null,
  ReactFlow: ({ nodes, onNodeClick }: { nodes: { id: string; data: { label: string } }[];
    onNodeClick: (event: unknown, node: { id: string }) => void }) => <div data-testid="flow">
    {nodes.map(node => <button key={node.id} onClick={() => onNodeClick(null, node)}>{node.data.label}</button>)}</div>,
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
        authority_id: 'authority-1', support_status: 'unclear', explanation: 'Limited passage coverage.', confidence: null }] }],
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

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(getResults).mockResolvedValue(fixture());
  vi.mocked(getGraph).mockResolvedValue(graph);
  vi.mocked(getEvidence).mockResolvedValue(evidence);
  vi.mocked(downloadReport).mockResolvedValue();
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
  expect(screen.getByText('quote-forensics-v1')).toBeInTheDocument();
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
