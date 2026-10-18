import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import {
  askFindingQuestion,
  getFindingQuestions,
  GroundedAnswerResponse,
  ResultFinding,
} from '../../lib/api/results';
import { FindingQA } from './FindingQA';

vi.mock('../../lib/api/results', async (importOriginal) => ({
  ...(await importOriginal<typeof import('../../lib/api/results')>()),
  askFindingQuestion: vi.fn(),
  getFindingQuestions: vi.fn(),
}));

const mockFinding: ResultFinding = {
  id: 'finding-1234',
  type: 'quote',
  severity: 'high',
  title: 'Quotation differs from authentic source',
  description: 'Forensic comparison revealed inserted negation words.',
  masked_excerpt: 'The court held that liability is absolute.',
  start: 10,
  end: 50,
  evidence_count: 1,
  ai_assisted: false,
};

const analysisId = 'analysis-abcd-1234';

function renderWithClient(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  });
  return render(<QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>);
}

describe('FindingQA Component (FR-260 through FR-264)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(getFindingQuestions).mockResolvedValue({
      analysis_id: analysisId,
      finding_id: mockFinding.id,
      questions: [],
      count: 0,
      limit: 20,
    });
  });

  it('renders grounded Q&A heading, suggested prompt chips, and empty state', async () => {
    renderWithClient(<FindingQA analysisId={analysisId} finding={mockFinding} />);

    expect(screen.getByRole('heading', { name: /Grounded Finding Q&A/i })).toBeInTheDocument();
    expect(screen.getByText('Strictly Grounded')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Why was this flagged?' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'What evidence was used?' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'What source passage supports this?' })).toBeInTheDocument();
    expect(
      await screen.findByText(/No questions asked yet for this finding/i),
    ).toBeInTheDocument();
  });

  it('allows clicking a suggested prompt chip and submits question', async () => {
    const mockAnswer: GroundedAnswerResponse = {
      analysis_id: analysisId,
      finding_id: mockFinding.id,
      question: 'What evidence was used?',
      answer: 'This finding is grounded in 1 evidence record. Retrieved passage confirms discrepancy.',
      status: 'answered',
      refusal_reason: 'none',
      evidence_record_ids: ['rec-99887766-5544-3322-1100-aabbccddeeff'],
      source_authorities: ['Brown v. Board of Education'],
      source_urls: ['https://www.courtlistener.com/opinion/123/brown/'],
      method_version: 'grounded-qa-v1',
      created_at: new Date().toISOString(),
    };
    vi.mocked(askFindingQuestion).mockResolvedValue(mockAnswer);

    renderWithClient(<FindingQA analysisId={analysisId} finding={mockFinding} />);

    const chip = screen.getByRole('button', { name: 'What evidence was used?' });
    fireEvent.click(chip);

    await waitFor(() => {
      expect(askFindingQuestion).toHaveBeenCalledWith(
        analysisId,
        mockFinding.id,
        'What evidence was used?',
      );
    });

    expect(await screen.findByText(/Retrieved passage confirms discrepancy/i)).toBeInTheDocument();
    const article = screen.getByRole('article');
    expect(within(article).getByText(/Grounded Answer:/i)).toBeInTheDocument();
    expect(article.querySelector('.status-answered')).toHaveTextContent(/Grounded/);
    expect(screen.getByText(/Record rec-9988…/i)).toBeInTheDocument();
    expect(screen.getByText('Brown v. Board of Education')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /View authentic opinion on CourtListener/i })).toHaveAttribute(
      'href',
      'https://www.courtlistener.com/opinion/123/brown/',
    );
  });

  it('allows typing a custom question and displays answered status', async () => {
    const mockAnswer: GroundedAnswerResponse = {
      analysis_id: analysisId,
      finding_id: mockFinding.id,
      question: 'Why was this flagged?',
      answer: 'The quotation was flagged because words were altered.',
      status: 'answered',
      refusal_reason: 'none',
      evidence_record_ids: [],
      source_authorities: [],
      source_urls: [],
      method_version: 'grounded-qa-v1',
      created_at: new Date().toISOString(),
    };
    vi.mocked(askFindingQuestion).mockResolvedValue(mockAnswer);

    renderWithClient(<FindingQA analysisId={analysisId} finding={mockFinding} />);

    const input = screen.getByRole('textbox', { name: /Ask a question about this finding/i });
    fireEvent.change(input, { target: { value: 'Why was this flagged?' } });

    const submitBtn = screen.getByRole('button', { name: /Submit question/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(askFindingQuestion).toHaveBeenCalledWith(
        analysisId,
        mockFinding.id,
        'Why was this flagged?',
      );
    });

    expect(await screen.findByText('The quotation was flagged because words were altered.')).toBeInTheDocument();
  });

  it('displays legal advice refusal and disclaimer banner (FR-263)', async () => {
    const mockRefusal: GroundedAnswerResponse = {
      analysis_id: analysisId,
      finding_id: mockFinding.id,
      question: 'What should I argue in court?',
      answer: 'FilingGuard AI cannot provide legal advice or litigation strategy.',
      status: 'refused',
      refusal_reason: 'broad_legal_advice',
      evidence_record_ids: [],
      source_authorities: [],
      source_urls: [],
      method_version: 'grounded-qa-v1',
      created_at: new Date().toISOString(),
    };
    vi.mocked(askFindingQuestion).mockResolvedValue(mockRefusal);

    renderWithClient(<FindingQA analysisId={analysisId} finding={mockFinding} />);

    const input = screen.getByRole('textbox', { name: /Ask a question about this finding/i });
    fireEvent.change(input, { target: { value: 'What should I argue in court?' } });

    const submitBtn = screen.getByRole('button', { name: /Submit question/i });
    fireEvent.click(submitBtn);

    expect(await screen.findByText(/Refused: Legal Advice/i)).toBeInTheDocument();
    expect(screen.getByText(/Legal Advice Disclaimer:/i)).toBeInTheDocument();
    expect(screen.getByText(/FilingGuard AI cannot provide legal advice/i)).toBeInTheDocument();
  });

  it('displays missing source status when no evidence is available', async () => {
    const mockNoEvidence: GroundedAnswerResponse = {
      analysis_id: analysisId,
      finding_id: mockFinding.id,
      question: 'What source passage supports this?',
      answer: 'No corroborating evidence records could be retrieved from public court records.',
      status: 'no_evidence',
      refusal_reason: 'none',
      evidence_record_ids: [],
      source_authorities: [],
      source_urls: [],
      method_version: 'grounded-qa-v1',
      created_at: new Date().toISOString(),
    };
    vi.mocked(askFindingQuestion).mockResolvedValue(mockNoEvidence);

    renderWithClient(<FindingQA analysisId={analysisId} finding={mockFinding} />);

    const input = screen.getByRole('textbox', { name: /Ask a question about this finding/i });
    fireEvent.change(input, { target: { value: 'What source passage supports this?' } });

    const submitBtn = screen.getByRole('button', { name: /Submit question/i });
    fireEvent.click(submitBtn);

    expect(await screen.findByText(/Missing Source/i)).toBeInTheDocument();
    expect(screen.getByText(/No corroborating evidence records could be retrieved/i)).toBeInTheDocument();
  });

  it('displays rate-limit error message when 429 is encountered', async () => {
    vi.mocked(askFindingQuestion).mockRejectedValue(new Error('Request failed with status 429'));

    renderWithClient(<FindingQA analysisId={analysisId} finding={mockFinding} />);

    const input = screen.getByRole('textbox', { name: /Ask a question about this finding/i });
    fireEvent.change(input, { target: { value: 'Question 21' } });

    const submitBtn = screen.getByRole('button', { name: /Submit question/i });
    fireEvent.click(submitBtn);

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'Question limit reached (maximum 20 questions per analysis session).',
    );
  });
});
