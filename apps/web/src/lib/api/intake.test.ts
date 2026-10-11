import { afterEach, expect, it, vi } from 'vitest';
import { getActivity, getReviewStatus, getSafeFindings, preparePDF, prepareRerun,
  prepareText, runLocalReview, validatePrepared } from './intake';

const id = 'b9127518-6920-45c2-915b-18ce3fa7d876';
const text = 'Claim 😀.';
function prepared() {
  return { analysis_id: id, document_name: 'Synthetic', mode: 'live', court_profile_id: 'unverified',
    ai_used: false, expires_at: new Date(Date.now() + 3600000).toISOString(), execution_status: 'not_run',
    paragraph_count: 1, masking_count: 0, masking_limitation: 'Heuristic only', document: { text,
      input_sha256: 'a'.repeat(64), text_sha256: 'b'.repeat(64), method: 'original-text-v1', pages: [],
      paragraphs: [{ paragraph_index: 0, page_number: null, start: 0, end: Array.from(text).length, text }] } };
}
afterEach(() => { vi.unstubAllGlobals(); sessionStorage.clear(); });

it('validates original code-point spans and rejects expired, malformed and invented results', () => {
  expect(validatePrepared(prepared()).document.text).toBe(text);
  expect(() => validatePrepared({ ...prepared(), execution_status: 'fabricated' })).toThrow();
  expect(validatePrepared({ ...prepared(), execution_status: 'running' }).execution_status).toBe('running');
  expect(() => validatePrepared({ ...prepared(), expires_at: '2000-01-01T00:00:00Z' })).toThrow();
  const altered = prepared();
  altered.document.paragraphs[0]!.end++;
  expect(() => validatePrepared(altered)).toThrow('offsets');
});

it('issues a session once, authorizes submissions and never saves filings in browser storage', async () => {
  const fetch = vi.fn().mockResolvedValueOnce(new Response(JSON.stringify({ token: 'a'.repeat(43),
    expires_at: new Date(Date.now() + 3600000).toISOString() }), { status: 201 }))
    .mockImplementation(() => Promise.resolve(new Response(JSON.stringify(prepared()), { status: 201 })));
  vi.stubGlobal('fetch', fetch);
  await prepareText(text, 'Synthetic', 'unverified', false);
  await prepareText(text, 'Synthetic', 'unverified', false);
  expect(fetch).toHaveBeenCalledTimes(3);
  expect(fetch.mock.calls[1]![1].headers.Authorization).toBe(`Bearer ${'a'.repeat(43)}`);
  expect(fetch.mock.calls[1]![1].cache).toBe('no-store');
  expect(sessionStorage.getItem('filingguard-private-session-v1')).not.toContain(text);
});

it('sends PDF filename in an encoded header, not an access-log URL', async () => {
  sessionStorage.setItem('filingguard-private-session-v1', JSON.stringify({ token: 'a'.repeat(43),
    expires_at: new Date(Date.now() + 3600000).toISOString() }));
  const fetch = vi.fn().mockResolvedValue(new Response(JSON.stringify(prepared()), { status: 201 }));
  vi.stubGlobal('fetch', fetch);
  await preparePDF(new File(['%PDF-'], 'Synthetic private name.pdf'), 'unverified', true);
  expect(fetch.mock.calls[0]![0]).not.toContain('private');
  expect(new Headers(fetch.mock.calls[0]![1].headers).get('X-Document-Name')).toBe('Synthetic%20private%20name.pdf');
});

it('does not automatically retry a rejected submission and drops its invalid session', async () => {
  sessionStorage.setItem('filingguard-private-session-v1', JSON.stringify({ token: 'a'.repeat(43),
    expires_at: new Date(Date.now() + 3600000).toISOString() }));
  const fetch = vi.fn().mockResolvedValue(new Response(JSON.stringify({ error: { code: 'unauthorized',
    message: 'Session authorization is required' } }), { status: 401 }));
  vi.stubGlobal('fetch', fetch);
  await expect(prepareText(text, 'Synthetic', 'unverified', false)).rejects.toThrow('Session authorization');
  expect(fetch).toHaveBeenCalledTimes(1);
  expect(sessionStorage.length).toBe(0);
});

it('accepts metadata-only activity without requiring or retaining filing content', async () => {
  sessionStorage.setItem('filingguard-private-session-v1', JSON.stringify({ token: 'a'.repeat(43),
    expires_at: new Date(Date.now() + 3600000).toISOString() }));
  const full = prepared();
  const summary = { analysis_id: full.analysis_id, document_name: full.document_name, mode: full.mode,
    court_profile_id: full.court_profile_id, ai_used: full.ai_used, expires_at: full.expires_at,
    execution_status: full.execution_status, paragraph_count: full.paragraph_count };
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify([summary]))));
  expect((await getActivity())[0]).not.toHaveProperty('document');
});

it('uses owner-scoped review endpoints and accepts only masked findings', async () => {
  sessionStorage.setItem('filingguard-private-session-v1', JSON.stringify({ token: 'a'.repeat(43),
    expires_at: new Date(Date.now() + 3600000).toISOString() }));
  const fetch = vi.fn().mockResolvedValueOnce(new Response(JSON.stringify({ analysis_id: id, status: 'queued' })))
    .mockResolvedValueOnce(new Response(JSON.stringify({ analysis_id: id, status: 'running', stages: [] })))
    .mockResolvedValueOnce(new Response(JSON.stringify({ analysis_id: id, limitation: 'Human review required',
      findings: [{ title: 'Possible identifier', description: 'Review redaction', masked_excerpt: '***' }] })))
    .mockResolvedValueOnce(new Response(JSON.stringify(prepared()), { status: 201 }));
  vi.stubGlobal('fetch', fetch);
  await runLocalReview(id);
  expect((await getReviewStatus(id)).status).toBe('running');
  expect((await getSafeFindings(id)).findings[0]?.masked_excerpt).toBe('***');
  expect((await prepareRerun(id)).analysis_id).toBe(id);
  expect(fetch.mock.calls.map(call => call[0])).toEqual([
    `/api/v1/analyses/${id}/run`, `/api/v1/analyses/${id}/status`,
    `/api/v1/analyses/${id}/findings`, `/api/v1/analyses/${id}/rerun`,
  ]);
  expect(fetch.mock.calls[0]![1].method).toBe('POST');
  expect(fetch.mock.calls[3]![1].method).toBe('POST');
});

it('forwards query cancellation to the private status request', async () => {
  sessionStorage.setItem('filingguard-private-session-v1', JSON.stringify({ token: 'a'.repeat(43),
    expires_at: new Date(Date.now() + 3600000).toISOString() }));
  const fetch = vi.fn().mockResolvedValue(new Response(JSON.stringify({ analysis_id: id,
    status: 'queued', stages: [] })));
  vi.stubGlobal('fetch', fetch);
  const controller = new AbortController();
  await getReviewStatus(id, controller.signal);
  const forwarded = fetch.mock.calls[0]![1].signal as AbortSignal;
  controller.abort();
  expect(forwarded.aborted).toBe(true);
});
