import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, expect, it, vi } from 'vitest';
import { submitClaimCorrection, type ResultClaim } from '../../lib/api/results';
import { ClaimCorrectionForm } from './ClaimCorrectionForm';

vi.mock('../../lib/api/results', async importOriginal => ({
  ...await importOriginal<typeof import('../../lib/api/results')>(),
  submitClaimCorrection: vi.fn(),
}));

const claim: ResultClaim = {
  id: 'claim-1',
  text: 'Original extraction from the filing.',
  location: { start: 0, end: 36, page_number: null, segment_id: 'segment-1' },
  extraction_method: 'heuristic',
  links: [],
  corrected_text: null,
  correction_history: [],
  propositions_stale: false,
};

function renderForm(value: ResultClaim = claim) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <ClaimCorrectionForm analysisId="analysis-1" claim={value} />
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  vi.mocked(submitClaimCorrection).mockResolvedValue({
    analysis_id: 'analysis-1',
    claim_id: 'claim-1',
    original_text: claim.text,
    corrected_text: 'User-corrected extraction.',
    history: [{ id: 'entry-1', corrected_text: 'User-corrected extraction.', created_at: '2026-10-19T12:00:00Z' }],
    propositions_stale: true,
    affected_link_ids: [],
    limitation: 'Stale after correction.',
  });
});

it('labels original extraction and saves a user correction', async () => {
  renderForm();
  expect(screen.getByText('Original extraction')).toBeInTheDocument();
  const field = screen.getByLabelText('Correct extracted claim');
  fireEvent.change(field, { target: { value: 'User-corrected extraction.' } });
  fireEvent.click(screen.getByRole('button', { name: 'Save correction' }));
  await waitFor(() => {
    expect(submitClaimCorrection).toHaveBeenCalledWith(
      'analysis-1',
      'claim-1',
      'User-corrected extraction.',
    );
  });
});

it('shows user-corrected extraction separately from original text', () => {
  renderForm({
    ...claim,
    corrected_text: 'User-corrected extraction.',
    propositions_stale: true,
    correction_history: [{
      id: 'entry-1',
      corrected_text: 'User-corrected extraction.',
      created_at: '2026-10-19T12:00:00Z',
    }],
  });
  expect(screen.getAllByText('User-corrected extraction').length).toBeGreaterThan(0);
  expect(screen.getByText('Original extraction from the filing.')).toBeInTheDocument();
  expect(screen.getByRole('status')).toHaveTextContent(/stale/i);
});
