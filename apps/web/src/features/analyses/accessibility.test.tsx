import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { App } from '../../app/App';
import { ActivityView } from '../intake/ActivityView';
import { DemoReview } from '../intake/DemoReview';
import { IntakeComposer } from '../intake/IntakeComposer';
import { PreparedView } from '../intake/PreparedView';
import { ResultsView } from './ResultsView';
import { FindingQA } from './FindingQA';
import { RedTeamPanel } from '../red-team/RedTeamPanel';
import { SettingsView } from '../../app/WorkspaceInfo';
import * as clientApi from '../../lib/api/client';
import * as intakeApi from '../../lib/api/intake';
import * as resultsApi from '../../lib/api/results';

vi.mock('../../lib/api/client', () => ({
  getHealth: vi.fn(),
  getDemo: vi.fn(),
  apiOrigin: '',
}));

vi.mock('../../lib/api/intake', () => ({
  getActivity: vi.fn(),
  getCapabilities: vi.fn(),
  getPrepared: vi.fn(),
  getReviewStatus: vi.fn(),
  getSafeFindings: vi.fn(),
  runLocalReview: vi.fn(),
  prepareRerun: vi.fn(),
  deletePrepared: vi.fn(),
  prepareText: vi.fn(),
  preparePDF: vi.fn(),
  prepareDemo: vi.fn(),
}));

vi.mock('../../lib/api/results', () => ({
  getResults: vi.fn(),
  getGraph: vi.fn(),
  getEvidence: vi.fn(),
  downloadReport: vi.fn(),
  getRedTeam: vi.fn(),
  runRedTeam: vi.fn(),
  askFindingQuestion: vi.fn(),
  getFindingQuestions: vi.fn(),
  safeSourceURL: vi.fn(),
}));

vi.mock('@xyflow/react', () => ({
  Background: () => null,
  Controls: () => null,
  Panel: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  ReactFlowProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  useReactFlow: () => ({ zoomIn: vi.fn(), zoomOut: vi.fn(), fitView: vi.fn() }),
  ReactFlow: () => <div data-testid="flow" />,
}));

function wrapWithClient(ui: React.ReactElement, initialRoute = '/') {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[initialRoute]}>{ui}</MemoryRouter>
    </QueryClientProvider>
  );
}

describe('UX-005 Accessibility Live Announcements', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(intakeApi.getCapabilities).mockResolvedValue({
      intake_enabled: true,
      legal_analysis_enabled: false,
      max_file_bytes: 10485760,
      max_characters: 100000,
      profiles: [],
    });
  });

  it('renders polite live announcements for app connection status', () => {
    vi.mocked(clientApi.getHealth).mockReturnValue(new Promise(() => {}));
    wrapWithClient(<App />);
    const connection = screen.getByRole('status');
    expect(connection).toHaveAttribute('aria-live', 'polite');
    expect(connection).toHaveTextContent(/Connecting/);
  });

  it('renders polite live announcements while loading document preparation in PreparedView', () => {
    vi.mocked(intakeApi.getPrepared).mockReturnValue(new Promise(() => {}));
    vi.mocked(intakeApi.getReviewStatus).mockReturnValue(new Promise(() => {}));
    wrapWithClient(
      <Routes>
        <Route path="/analyses/:id" element={<PreparedView />} />
      </Routes>,
      '/analyses/test-doc-id'
    );
    const loadingSection = screen.getByRole('status');
    expect(loadingSection).toHaveAttribute('aria-live', 'polite');
    expect(loadingSection).toHaveTextContent(/Opening your document/);
  });

  it('renders polite live announcements while loading results in ResultsView', () => {
    vi.mocked(resultsApi.getResults).mockReturnValue(new Promise(() => {}));
    wrapWithClient(
      <Routes>
        <Route path="/analyses/:id/results" element={<ResultsView />} />
      </Routes>,
      '/analyses/test-results-id/results'
    );
    const loadingNotice = screen.getByRole('status');
    expect(loadingNotice).toHaveAttribute('aria-live', 'polite');
    expect(loadingNotice).toHaveTextContent(/Loading private review results/);
  });

  it('renders polite live announcements in ActivityView when fetching session', () => {
    vi.mocked(intakeApi.getCapabilities).mockReturnValue(
      Promise.resolve({
        intake_enabled: true,
        legal_analysis_enabled: false,
        max_file_bytes: 10485760,
        max_characters: 100000,
        profiles: [],
      })
    );
    vi.mocked(intakeApi.getActivity).mockReturnValue(new Promise(() => {}));
    wrapWithClient(<ActivityView />);
    const statuses = screen.getAllByRole('status');
    const politeStatuses = statuses.filter(s => s.getAttribute('aria-live') === 'polite');
    expect(politeStatuses.length).toBeGreaterThan(0);
  });

  it('renders polite live announcements in DemoReview when loading reviewed sample', () => {
    vi.mocked(clientApi.getDemo).mockReturnValue(new Promise(() => {}));
    wrapWithClient(<DemoReview onReset={vi.fn()} />);
    const loading = screen.getByRole('status');
    expect(loading).toHaveAttribute('aria-live', 'polite');
    expect(loading).toHaveTextContent(/Loading reviewed sample/);
  });

  it('renders polite live announcements in RedTeamPanel while loading critiques', () => {
    vi.mocked(resultsApi.getRedTeam).mockReturnValue(new Promise(() => {}));
    wrapWithClient(<RedTeamPanel analysisId="test-id" onSelectFinding={vi.fn()} />);
    const loading = screen.getByRole('status');
    expect(loading).toHaveAttribute('aria-live', 'polite');
    expect(loading).toHaveTextContent(/Loading adversarial review critiques/);
  });

  it('renders polite live announcements in FindingQA while loading questions', () => {
    vi.mocked(resultsApi.getFindingQuestions).mockReturnValue(new Promise(() => {}));
    const mockFinding: resultsApi.ResultFinding = {
      id: 'f-1',
      type: 'citation',
      severity: 'high',
      title: 'Test Finding',
      description: 'Test Description',
      masked_excerpt: null,
      start: 0,
      end: 10,
      evidence_count: 1,
      ai_assisted: false,
    };
    wrapWithClient(<FindingQA analysisId="test-id" finding={mockFinding} />);
    const loading = screen.getByRole('status');
    expect(loading).toHaveAttribute('aria-live', 'polite');
    expect(loading).toHaveTextContent(/Loading previous questions/);
  });

  it('renders polite live announcements in IntakeComposer on capability error', async () => {
    vi.mocked(intakeApi.getCapabilities).mockRejectedValue(new Error('Network error'));
    wrapWithClient(<IntakeComposer />);
    const status = await screen.findByRole('status');
    expect(status).toHaveAttribute('aria-live', 'polite');
    expect(status).toHaveTextContent(/Intake availability could not be checked/);
  });

  it('renders polite live announcements in SettingsView while loading availability', () => {
    vi.mocked(intakeApi.getCapabilities).mockReturnValue(new Promise(() => {}));
    wrapWithClient(<SettingsView />);
    const status = screen.getByRole('status');
    expect(status).toHaveAttribute('aria-live', 'polite');
    expect(status).toHaveTextContent(/Loading service availability/);
  });

  it('renders polite live announcements in PreparedView while loading review findings', async () => {
    vi.mocked(intakeApi.getPrepared).mockResolvedValue({
      analysis_id: 'test-doc-id',
      execution_status: 'running',
      document_name: 'Test Doc',
      mode: 'live',
      court_profile_id: 'unverified',
      ai_used: false,
      expires_at: new Date(Date.now() + 600000).toISOString(),
      document: {
        text: 'Sample',
        paragraphs: [{ paragraph_index: 0, text: 'Sample', start: 0, end: 6 }],
        pages: [{ page_number: 1, start: 0, end: 6 }],
        input_sha256: 'a'.repeat(64),
        text_sha256: 'b'.repeat(64),
        method: 'original-text-v1',
      },
      paragraph_count: 1,
      masking_count: 0,
      masking_limitation: 'None',
    });
    vi.mocked(intakeApi.getReviewStatus).mockResolvedValue({
      analysis_id: 'test-doc-id',
      status: 'running',
      mode: 'live',
      demo_fixture_id: null,
      court_profile_id: 'unverified',
      created_at: new Date().toISOString(),
      score_is_provisional: true,
      overall_score: null,
      risk_level: null,
      stages: [
        {
          name: 'privacy',
          status: 'running',
          reason: null,
          applicable: true,
          coverage: {
            eligible: 1,
            evaluated: 0,
            unavailable: 0,
            pending: 1,
            truncated: false,
            limitation: null,
          },
        },
      ],
    });
    vi.mocked(intakeApi.getSafeFindings).mockReturnValue(new Promise(() => {}));
    wrapWithClient(
      <Routes>
        <Route path="/analyses/:id" element={<PreparedView />} />
      </Routes>,
      '/analyses/test-doc-id'
    );
    const loading = await screen.findByText(/Loading review findings/);
    expect(loading).toHaveAttribute('role', 'status');
    expect(loading).toHaveAttribute('aria-live', 'polite');
  });
});
