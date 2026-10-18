import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router';
import { afterEach, expect, it, vi } from 'vitest';
import { IntakeComposer } from './IntakeComposer';
import { PreparedView } from './PreparedView';

afterEach(() => {
  vi.unstubAllGlobals();
  sessionStorage.clear();
});

function wrap(ui: React.ReactNode) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter>{ui}</MemoryRouter>
    </QueryClientProvider>,
  );
}

it('enables court profile dropdown in live mode and shows real and demo options', async () => {
  vi.stubGlobal('fetch', vi.fn().mockImplementation((url: string) => {
    if (url.includes('/capabilities')) {
      return Promise.resolve(new Response(JSON.stringify({
        intake_enabled: true,
        legal_analysis_enabled: true,
        max_file_bytes: 10485760,
        max_characters: 100000,
        profiles: [],
      })));
    }
    return Promise.resolve(new Response('{"status":"ok"}'));
  }));

  wrap(<IntakeComposer />);

  await waitFor(() => {
    expect(screen.getByLabelText('Court profile')).not.toBeDisabled();
  });

  const select = screen.getByLabelText('Court profile') as HTMLSelectElement;
  expect(select.value).toBe('unverified');

  const options = Array.from(select.options).map(opt => ({ value: opt.value, label: opt.textContent }));
  expect(options).toEqual([
    { value: 'unverified', label: 'Court rules not configured' },
    { value: 'us-txnd-lr7-2f-v1', label: 'N.D. Tex. Local Rule 7.2(f) (Generative AI Heading)' },
  ]);

  // Switch to demo mode
  fireEvent.click(screen.getByRole('button', { name: 'Demo' }));
  const demoOptions = Array.from(select.options).map(opt => ({ value: opt.value, label: opt.textContent }));
  expect(demoOptions).toEqual([
    { value: 'unverified', label: 'Court rules not configured' },
    { value: 'us-txnd-lr7-2f-v1', label: 'N.D. Tex. Local Rule 7.2(f) (Generative AI Heading)' },
    { value: 'synthetic-demo-v1', label: 'Synthetic demo court (not a real court)' },
  ]);
  expect(select.value).toBe('synthetic-demo-v1');
});

it('prepared view displays N.D. Tex. LR 7.2(f) for us-txnd-lr7-2f-v1', async () => {
  sessionStorage.setItem(
    'filingguard-private-session-v1',
    JSON.stringify({ token: 'a'.repeat(43), expires_at: new Date(Date.now() + 3600000).toISOString() }),
  );

  const preparedDoc = {
    analysis_id: '11111111-2222-3333-4444-555555555555',
    document_name: 'Motion.pdf',
    mode: 'live',
    court_profile_id: 'us-txnd-lr7-2f-v1',
    ai_used: true,
    expires_at: new Date(Date.now() + 3600000).toISOString(),
    execution_status: 'not_run',
    paragraph_count: 1,
    masking_count: 0,
    masking_limitation: 'Heuristic only',
    document: {
      text: 'Motion text',
      input_sha256: 'a'.repeat(64),
      text_sha256: '992a2a7e78072ae0062a74c43aef878931a7f7223b16a04870f2f3d53b53fca8',
      method: 'original-text-v1',
      pages: [],
      paragraphs: [{ paragraph_index: 0, page_number: null, start: 0, end: 11, text: 'Motion text' }],
    },
  };

  vi.stubGlobal('fetch', vi.fn().mockImplementation((url: string) => {
    if (url.includes('/analyses/11111111-2222-3333-4444-555555555555/status')) {
      return Promise.resolve(new Response(JSON.stringify({
        analysis_id: '11111111-2222-3333-4444-555555555555',
        status: 'not_run',
        mode: 'live',
        created_at: new Date().toISOString(),
        stages: [],
        coverage: { eligible: 0, evaluated: 0, unavailable: 0, pending: 0, truncated: false },
        overall_score: null,
        risk_level: null,
      })));
    }
    if (url.includes('/analyses/11111111-2222-3333-4444-555555555555')) {
      return Promise.resolve(new Response(JSON.stringify(preparedDoc)));
    }
    return Promise.resolve(new Response('{}'));
  }));

  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={['/analyses/11111111-2222-3333-4444-555555555555']}>
        <Routes>
          <Route path="/analyses/:id" element={<PreparedView />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );

  expect(await screen.findByText('N.D. Tex. LR 7.2(f)')).toBeInTheDocument();
});
