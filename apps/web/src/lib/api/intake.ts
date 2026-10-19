import type { components } from './schema';
import { apiOrigin } from './client';

export type PreparedDocument = components['schemas']['PreparedDocument'];
export type DocumentSummary = components['schemas']['DocumentSummary'];
export type Capabilities = components['schemas']['Capabilities'];
export type ReviewStatus = components['schemas']['AnalysisSummary'];
export type SafeFindings = components['schemas']['SafeFindingsResponse'];
type Session = { token: string; expires_at: string };
const sessionKey = 'filingguard-private-session-v1';
let issuing: Promise<Session> | null = null;

function record(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}
function session(value: unknown): value is Session {
  return record(value) && typeof value.token === 'string' && /^[A-Za-z0-9_-]{43}$/.test(value.token)
    && typeof value.expires_at === 'string' && Date.parse(value.expires_at) > Date.now();
}
export class IntakeError extends Error {
  constructor(public status: number, public code: string, message: string) { super(message); }
}
async function request(path: string, options: RequestInit = {}): Promise<unknown> {
  const response = await fetch(`${apiOrigin}/api/v1${path}`, {
    ...options, cache: 'no-store', credentials: 'omit',
    signal: options.signal ? AbortSignal.any([options.signal, AbortSignal.timeout(45000)])
      : AbortSignal.timeout(45000),
  });
  const value: unknown = await response.json();
  if (!response.ok) {
    if (response.status === 401) sessionStorage.removeItem(sessionKey);
    if (record(value) && record(value.error) && typeof value.error.code === 'string'
      && typeof value.error.message === 'string' && value.error.message.length < 255) {
      throw new IntakeError(response.status, value.error.code, value.error.message);
    }
    throw new IntakeError(response.status, 'unavailable', 'Document preparation unavailable');
  }
  return value;
}
async function privateSession(): Promise<Session> {
  try {
    const saved: unknown = JSON.parse(sessionStorage.getItem(sessionKey) ?? 'null');
    if (session(saved)) return saved;
  } catch { /* Invalid or inaccessible browser storage is not authorization. */ }
  if (!issuing) issuing = (async () => {
    const value = await request('/sessions', { method: 'POST' });
    if (!session(value)) throw new Error('Unexpected session response');
    sessionStorage.setItem(sessionKey, JSON.stringify(value));
    return value;
  })().finally(() => { issuing = null; });
  return issuing;
}
export async function authorizedResponse(path: string, options: RequestInit = {}): Promise<Response> {
  const owner = await privateSession();
  const response = await fetch(`${apiOrigin}/api/v1${path}`, {
    ...options, cache: 'no-store', credentials: 'omit',
    headers: { ...Object.fromEntries(new Headers(options.headers).entries()),
      Authorization: `Bearer ${owner.token}` },
    signal: options.signal ? AbortSignal.any([options.signal, AbortSignal.timeout(45000)])
      : AbortSignal.timeout(45000),
  });
  if (!response.ok) {
    if (response.status === 401) sessionStorage.removeItem(sessionKey);
    throw new IntakeError(response.status, 'unavailable', 'Review result unavailable');
  }
  return response;
}
export async function authorized(path: string, options: RequestInit = {}) {
  const owner = await privateSession();
  return request(path, { ...options,
    headers: { ...Object.fromEntries(new Headers(options.headers).entries()),
      Authorization: `Bearer ${owner.token}` } });
}
export async function getCapabilities(signal?: AbortSignal): Promise<Capabilities> {
  const value = await request('/capabilities', { signal });
  if (!record(value) || typeof value.intake_enabled !== 'boolean'
    || typeof value.legal_analysis_enabled !== 'boolean' || value.max_characters !== 100000
    || value.max_file_bytes !== 10485760 || !Array.isArray(value.profiles)) {
    throw new Error('Unexpected intake capabilities');
  }
  return value as Capabilities;
}
export function validateSummary(value: unknown): DocumentSummary {
  if (!record(value) || typeof value.analysis_id !== 'string'
    || !/^[a-f0-9-]{36}$/.test(value.analysis_id) || typeof value.document_name !== 'string'
    || !['live', 'demo'].includes(String(value.mode))
    || !['not_run', 'queued', 'running', 'completed', 'partial', 'failed', 'interrupted'].includes(String(value.execution_status))
    || typeof value.expires_at !== 'string' || !Number.isFinite(Date.parse(value.expires_at))
    || typeof value.ai_used !== 'boolean' || typeof value.court_profile_id !== 'string'
    || typeof value.paragraph_count !== 'number' || !Number.isInteger(value.paragraph_count)
    || value.paragraph_count < 1 || value.paragraph_count > 2000) {
    throw new Error('Unexpected document summary');
  }
  return value as DocumentSummary;
}
export function validatePrepared(value: unknown): PreparedDocument {
  validateSummary(value);
  if (!record(value) || typeof value.expires_at !== 'string' || Date.parse(value.expires_at) <= Date.now()
    || typeof value.masking_count !== 'number' || !Number.isInteger(value.masking_count)
    || value.masking_count < 0 || typeof value.masking_limitation !== 'string' || !record(value.document)
    || typeof value.document.text !== 'string' || !Array.isArray(value.document.paragraphs)
    || !Array.isArray(value.document.pages) || typeof value.document.input_sha256 !== 'string'
    || typeof value.document.text_sha256 !== 'string'
    || !/^[a-f0-9]{64}$/.test(value.document.input_sha256)
    || !/^[a-f0-9]{64}$/.test(value.document.text_sha256)
    || !['original-text-v1', 'pypdf-bounded-v1'].includes(String(value.document.method))) {
    throw new Error('Unexpected prepared document');
  }
  const text = Array.from(value.document.text);
  if (text.length > 100000 || text.length === 0 || value.document.paragraphs.length > 2000
    || value.document.paragraphs.length === 0 || value.paragraph_count !== value.document.paragraphs.length
    || value.document.pages.length > 20 || !value.document.pages.every((page, index) => record(page)
      && page.page_number === index + 1 && typeof page.start === 'number' && typeof page.end === 'number'
      && Number.isInteger(page.start) && Number.isInteger(page.end) && page.start >= 0
      && page.end >= page.start && page.end <= text.length)
    || !value.document.paragraphs.every((item, index) =>
      record(item) && item.paragraph_index === index && typeof item.start === 'number'
      && typeof item.end === 'number' && Number.isInteger(item.start) && Number.isInteger(item.end)
      && item.start >= 0 && item.end > item.start && item.end <= text.length
      && typeof item.text === 'string' && text.slice(item.start, item.end).join('') === item.text)) {
    throw new Error('Unexpected document offsets');
  }
  return value as PreparedDocument;
}
export async function prepareText(text: string, name: string, court: string, aiUsed: boolean) {
  return validatePrepared(await authorized('/analyses/text', { method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, document_name: name, court_profile_id: court, ai_used: aiUsed, mode: 'live' }),
  }));
}
export async function preparePDF(file: File, court: string, aiUsed: boolean) {
  const query = new URLSearchParams({ court_profile_id: court, ai_used: String(aiUsed) });
  return validatePrepared(await authorized(`/analyses/file?${query}`, { method: 'POST',
    headers: { 'Content-Type': 'application/pdf', 'X-Document-Name': encodeURIComponent(file.name) },
    body: file,
  }));
}
export async function prepareDemo(aiUsed = true, court = 'synthetic-demo-v1') {
  return validatePrepared(await authorized('/analyses/demo', { method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ fixture_id: 'curated-v1', mode: 'demo', ai_used: aiUsed, court_profile_id: court }),
  }));
}
export async function getPrepared(id: string, signal?: AbortSignal) {
  return validatePrepared(await authorized(`/analyses/${encodeURIComponent(id)}`, { signal }));
}
export async function getActivity(signal?: AbortSignal, matterId?: string) {
  const path = matterId ? `/analyses?matter_id=${encodeURIComponent(matterId)}` : '/analyses';
  const value = await authorized(path, { signal });
  if (!Array.isArray(value)) throw new Error('Unexpected activity response');
  return value.map(validateSummary).filter(item => Date.parse(item.expires_at) > Date.now());
}
export async function deletePrepared(id: string) {
  const value = await authorized(`/analyses/${encodeURIComponent(id)}`, { method: 'DELETE' });
  if (!record(value) || value.analysis_id !== id || value.deleted !== true) {
    throw new Error('Unexpected deletion response');
  }
}
export async function getReviewStatus(id: string, signal?: AbortSignal): Promise<ReviewStatus> {
  const value = await authorized(`/analyses/${encodeURIComponent(id)}/status`, { signal });
  if (!record(value) || value.analysis_id !== id || !Array.isArray(value.stages)
    || !['not_run', 'queued', 'running', 'completed', 'partial', 'failed', 'interrupted'].includes(String(value.status))) {
    throw new Error('Unexpected review status');
  }
  return value as ReviewStatus;
}
export async function getSafeFindings(id: string, signal?: AbortSignal): Promise<SafeFindings> {
  const value = await authorized(`/analyses/${encodeURIComponent(id)}/findings`, { signal });
  if (!record(value) || value.analysis_id !== id || !Array.isArray(value.findings)
    || typeof value.limitation !== 'string' || !value.findings.every(item => record(item)
      && typeof item.title === 'string' && typeof item.description === 'string'
      && (item.masked_excerpt === null || typeof item.masked_excerpt === 'string'))) {
    throw new Error('Unexpected review findings');
  }
  return value as SafeFindings;
}
export async function runLocalReview(id: string) {
  const value = await authorized(`/analyses/${encodeURIComponent(id)}/run`, { method: 'POST' });
  if (!record(value) || value.analysis_id !== id || value.status !== 'queued') {
    throw new Error('Unexpected review response');
  }
}
export async function prepareRerun(id: string): Promise<PreparedDocument> {
  return validatePrepared(await authorized(`/analyses/${encodeURIComponent(id)}/rerun`, { method: 'POST' }));
}

export type CurrentIdentity = { username: string; bound: boolean } | null;
export type MatterSummary = components['schemas']['MatterSummary'];
export type MatterDetail = components['schemas']['MatterDetail'];
export type FindingComment = components['schemas']['FindingCommentResponse'];
export type FindingDisposition = components['schemas']['FindingDispositionResponse'];
export type BatchSummary = components['schemas']['BatchSummary'];
export type BatchDetail = components['schemas']['BatchDetail'];

export function getSavedSessionToken(): string | null {
  try {
    const saved: unknown = JSON.parse(sessionStorage.getItem(sessionKey) ?? 'null');
    if (session(saved)) return saved.token;
  } catch {
    /* ignore */
  }
  return null;
}

export async function getCurrentIdentity(signal?: AbortSignal): Promise<CurrentIdentity> {
  try {
    const value = await authorized('/identities/me', { signal });
    if (record(value) && typeof value.username === 'string') {
      return value as { username: string; bound: boolean };
    }
    return null;
  } catch (err) {
    if (err instanceof IntakeError && err.status === 404) return null;
    return null;
  }
}

export async function claimIdentity(username: string, secret: string): Promise<{ username: string; bound: boolean }> {
  const value = await authorized('/identities', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, secret }),
  });
  return value as { username: string; bound: boolean };
}

export async function loginIdentity(username: string, secret: string): Promise<Session> {
  const value = await request('/identities/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, secret }),
  });
  if (!session(value)) throw new Error('Unexpected identity login response');
  sessionStorage.setItem(sessionKey, JSON.stringify(value));
  return value;
}

export function logoutIdentity(): void {
  sessionStorage.removeItem(sessionKey);
}

export async function migrateAnalyses(sourceToken: string): Promise<{ migrated_count: number }> {
  const value = await authorized('/identities/migrate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ source_session_token: sourceToken }),
  });
  return value as { migrated_count: number };
}

export async function listMatters(signal?: AbortSignal): Promise<MatterSummary[]> {
  const value = await authorized('/matters', { signal });
  if (!Array.isArray(value)) throw new Error('Unexpected matters response');
  return value as MatterSummary[];
}

export async function createMatter(
  name: string,
  caseNumber?: string,
  clientId?: string,
  description?: string,
): Promise<MatterSummary> {
  const value = await authorized('/matters', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      name,
      case_number: caseNumber || null,
      client_id: clientId || null,
      description: description || null,
    }),
  });
  return value as MatterSummary;
}

export async function getMatter(id: string, signal?: AbortSignal): Promise<MatterDetail> {
  const value = await authorized(`/matters/${encodeURIComponent(id)}`, { signal });
  return value as MatterDetail;
}

export async function assignMatter(matterId: string, analysisId: string): Promise<void> {
  await authorized(`/matters/${encodeURIComponent(matterId)}/analyses/${encodeURIComponent(analysisId)}`, {
    method: 'POST',
  });
}

export async function unassignMatter(matterId: string, analysisId: string): Promise<void> {
  await authorized(`/matters/${encodeURIComponent(matterId)}/analyses/${encodeURIComponent(analysisId)}`, {
    method: 'DELETE',
  });
}

export async function listFindingComments(
  analysisId: string,
  findingId: string,
  signal?: AbortSignal,
): Promise<FindingComment[]> {
  const value = await authorized(
    `/analyses/${encodeURIComponent(analysisId)}/findings/${encodeURIComponent(findingId)}/comments`,
    { signal },
  );
  if (!Array.isArray(value)) throw new Error('Unexpected comments response');
  return value as FindingComment[];
}

export async function addFindingComment(
  analysisId: string,
  findingId: string,
  authorName: string,
  authorRole: string,
  content: string,
): Promise<FindingComment> {
  const value = await authorized(
    `/analyses/${encodeURIComponent(analysisId)}/findings/${encodeURIComponent(findingId)}/comments`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ author_name: authorName, author_role: authorRole, content }),
    },
  );
  return value as FindingComment;
}

export async function setFindingDisposition(
  analysisId: string,
  findingId: string,
  status: 'open' | 'accepted' | 'dismissed' | 'needs_review',
  rationale: string,
  reviewerName: string,
  reviewerRole: string,
): Promise<FindingDisposition> {
  const value = await authorized(
    `/analyses/${encodeURIComponent(analysisId)}/findings/${encodeURIComponent(findingId)}/disposition`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        status,
        rationale,
        reviewer_name: reviewerName,
        reviewer_role: reviewerRole,
      }),
    },
  );
  return value as FindingDisposition;
}

