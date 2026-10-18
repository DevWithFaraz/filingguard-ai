import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { getRedTeam, runRedTeam, validateRedTeamResponse, type RedTeamResponse } from '../../lib/api/results';
import { RedTeamPanel } from './RedTeamPanel';

vi.mock('../../lib/api/results', async importOriginal => ({
  ...await importOriginal<typeof import('../../lib/api/results')>(),
  getRedTeam: vi.fn(),
  runRedTeam: vi.fn(),
}));

const analysisId = 'b9127518-6920-45c2-915b-18ce3fa7d876';

function sampleResponse(overrides: Partial<RedTeamResponse> = {}): RedTeamResponse {
  return {
    analysis_id: analysisId,
    generated_at: '2026-10-17T12:00:00Z',
    total_weaknesses: 2,
    critical_count: 1,
    high_count: 1,
    medium_count: 0,
    low_count: 0,
    summary: '2 vulnerabilities identified across filing checks: 1 critical, 1 high.',
    limitation: 'Synthesized from verified findings.',
    weaknesses: [
      {
        id: 'weakness-crit',
        severity: 'critical',
        vulnerability_type: 'privacy_exposure',
        title: 'Unredacted sensitive identifier in filing text',
        challenge_theory: 'Opposing counsel will move to seal or strike the filing.',
        impact_summary: 'Rule violation and sanctions risk.',
        remediation_recommendation: 'Redact private identifier before filing.',
        linked_finding_ids: ['finding-pii'],
        linked_citation_ids: [],
        linked_claim_ids: [],
        linked_quote_ids: [],
      },
      {
        id: 'weakness-high',
        severity: 'high',
        vulnerability_type: 'altered_quotation',
        title: 'Substantive quotation divergence in precedent',
        challenge_theory: 'Opposing party will demonstrate that the cited opinion does not support the proposition.',
        impact_summary: 'Weakens judicial credibility and risks ethical scrutiny.',
        remediation_recommendation: 'Re-verify source text against slip opinion.',
        linked_finding_ids: ['finding-quote'],
        linked_citation_ids: ['citation-1'],
        linked_claim_ids: ['claim-1'],
        linked_quote_ids: ['quote-1'],
      },
    ],
    ...overrides,
  };
}

function renderPanel(onSelectFinding = vi.fn()) {
  const client = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });
  return {
    ...render(
      <QueryClientProvider client={client}>
        <RedTeamPanel analysisId={analysisId} onSelectFinding={onSelectFinding} />
      </QueryClientProvider>,
    ),
    client,
    onSelectFinding,
  };
}

describe('RedTeamPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders loading status while query is pending', () => {
    vi.mocked(getRedTeam).mockReturnValue(new Promise(() => {}));
    renderPanel();
    expect(screen.getByText('Loading adversarial review critiques…')).toBeInTheDocument();
  });

  it('renders error notice and retries query upon retry button click', async () => {
    vi.mocked(getRedTeam).mockRejectedValueOnce(new Error('Network error'));
    renderPanel();
    expect(await screen.findByRole('alert')).toHaveTextContent('Red-team critiques currently unavailable.');

    vi.mocked(getRedTeam).mockResolvedValueOnce(sampleResponse());
    fireEvent.click(screen.getByRole('button', { name: 'Retry' }));

    expect(await screen.findByRole('heading', { name: 'Legal Red-Team Mode' })).toBeInTheDocument();
    expect(screen.getByText(/2 vulnerabilities identified/)).toBeInTheDocument();
  });

  it('renders clean state when zero vulnerabilities are detected', async () => {
    vi.mocked(getRedTeam).mockResolvedValue(sampleResponse({
      total_weaknesses: 0,
      critical_count: 0,
      high_count: 0,
      summary: 'No high-risk filing vulnerabilities detected across evaluated checks.',
      weaknesses: [],
    }));
    renderPanel();

    expect(await screen.findByText('No High-Risk Vulnerabilities Detected')).toBeInTheDocument();
    expect(screen.getByText(/No critical precedent misrepresentations/)).toBeInTheDocument();
  });

  it('displays ranked weaknesses, toggles details, and triggers jump to finding', async () => {
    const data = sampleResponse();
    vi.mocked(getRedTeam).mockResolvedValue(data);
    const onSelect = vi.fn();
    renderPanel(onSelect);

    expect(await screen.findByText('Unredacted sensitive identifier in filing text')).toBeInTheDocument();
    expect(screen.getByText('Substantive quotation divergence in precedent')).toBeInTheDocument();

    // First card is expanded by default (index === 0)
    expect(screen.getByText('Opposing counsel will move to seal or strike the filing.')).toBeInTheDocument();

    // Jump to finding triggers callback
    const jumpBtn = screen.getByRole('button', { name: /Jump to Finding/ });
    fireEvent.click(jumpBtn);
    expect(onSelect).toHaveBeenCalledWith('finding-pii');

    // Expand second card
    const toggleHigh = screen.getByRole('button', { name: /Substantive quotation divergence in precedent/ });
    fireEvent.click(toggleHigh);
    expect(screen.getByText('Re-verify source text against slip opinion.')).toBeInTheDocument();
  });

  it('triggers runRedTeam mutation when re-run button is clicked', async () => {
    const initial = sampleResponse();
    const updated = sampleResponse({
      summary: 'Re-analyzed: 1 vulnerability remains.',
      total_weaknesses: 1,
      critical_count: 0,
      high_count: 1,
      weaknesses: [initial.weaknesses[1]!],
    });

    vi.mocked(getRedTeam).mockResolvedValue(initial);
    vi.mocked(runRedTeam).mockResolvedValue(updated);
    renderPanel();

    expect(await screen.findByText(/2 vulnerabilities identified/)).toBeInTheDocument();

    const rerunBtn = screen.getByRole('button', { name: 'Re-run red team analysis' });
    fireEvent.click(rerunBtn);

    await waitFor(() => {
      expect(runRedTeam).toHaveBeenCalledWith(analysisId);
    });

    expect(await screen.findByText('Re-analyzed: 1 vulnerability remains.')).toBeInTheDocument();
  });
});

describe('validateRedTeamResponse', () => {
  it('validates a well-formed red team payload', () => {
    const payload = sampleResponse();
    const result = validateRedTeamResponse(payload, analysisId);
    expect(result.analysis_id).toBe(analysisId);
    expect(result.weaknesses.length).toBe(2);
  });

  it('rejects cross-analysis mismatch', () => {
    const payload = sampleResponse();
    expect(() => validateRedTeamResponse(payload, 'wrong-id')).toThrow(
      'Unexpected red-team review response',
    );
  });

  it('rejects count discrepancies', () => {
    const payload = sampleResponse({ total_weaknesses: 99 });
    expect(() => validateRedTeamResponse(payload, analysisId)).toThrow(
      'Unexpected red-team review response',
    );
  });

  it('rejects invalid weakness structure', () => {
    const payload = {
      ...sampleResponse(),
      weaknesses: [{ id: 'invalid' }],
    };
    expect(() => validateRedTeamResponse(payload, analysisId)).toThrow(
      'Unexpected red-team review response',
    );
  });
});
