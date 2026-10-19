import { authorized, authorizedResponse } from './intake';

export interface ResultCoverage {
  eligible: number; evaluated: number; unavailable: number; pending: number;
  truncated: boolean; limitation: string | null;
}
export interface ResultLocation { start: number; end: number; page_number: number | null; segment_id: string | null }
export interface ResultFinding {
  id: string; type: string; severity: string; title: string; description: string;
  masked_excerpt: string | null; start: number | null; end: number | null;
  evidence_count: number; ai_assisted: boolean;
  claim_id?: string | null; authority_id?: string | null; citation_id?: string | null;
  quote_id?: string | null; segment_id?: string | null;
  status?: string; disposition_metadata?: Record<string, unknown>;
}
export interface ClaimCorrectionEntry {
  id: string;
  corrected_text: string;
  created_at: string;
}
export interface ResultClaim {
  id: string;
  text: string;
  location: ResultLocation;
  extraction_method: string;
  links: { id: string; citation_id: string; authority_id: string | null; support_status: string;
    explanation: string | null; confidence: number | null }[];
  corrected_text: string | null;
  correction_history: ClaimCorrectionEntry[];
  propositions_stale: boolean;
}
export interface ClaimCorrectionResponse {
  analysis_id: string;
  claim_id: string;
  original_text: string;
  corrected_text: string;
  history: ClaimCorrectionEntry[];
  propositions_stale: true;
  affected_link_ids: string[];
  limitation: string;
}
export interface ReviewResults {
  analysis_id: string; document_name: string; created_at: string; court_profile_id: string;
  mode: 'live' | 'demo'; status: string;
  stages: { name: string; status: string; coverage: ResultCoverage; reason: string | null; applicable: boolean }[];
  coverage: ResultCoverage;
  score: { value: number | null; risk_level: string | null; provisional: true; version: string;
    categories?: { type: string; eligible: number; evaluated: number; value: number | null; deducted_points: number }[];
    deductions: { finding_id: string; type: string; severity: string; points: number }[]; limitation: string };
  citations: { id: string; masked_raw_text: string; verification_status: string;
    authority_id: string | null; location: ResultLocation; reason?: string | null;
    limitation?: string | null; authority?: { case_name: string | null; source_url: string | null } | null;
    duplicate_count?: number | null; repeated_locations?: ResultLocation[] }[];
  claims: ResultClaim[];
  quotes: { id: string; text: string; location: ResultLocation; citation_id: string | null;
    match_status: string; similarity: number | null; closest_passage: string | null }[];
  findings: ResultFinding[]; limitation: string;
}
export interface ReviewGraph {
  analysis_id: string;
  nodes: { id: string; label: string; kind: 'section' | 'claim' | 'authority'; status: string; finding_ids?: string[] }[];
  edges: { id: string; source: string; target: string; label: string }[];
}
export interface FindingEvidence {
  analysis_id: string; finding_id: string;
  evidence: { id: string; excerpt: string; source_url: string | null; source_start: number;
    source_end: number; source_sha256: string; retrieved_at: string; method_version: string;
    model_version: string | null; prompt_version: string | null; provenance: string }[];
}

function record(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}
function integer(value: unknown): value is number { return typeof value === 'number' && Number.isInteger(value) && value >= 0; }
function coverage(value: unknown): boolean {
  return record(value) && integer(value.eligible) && integer(value.evaluated)
    && integer(value.unavailable) && integer(value.pending)
    && value.evaluated + value.unavailable + value.pending === value.eligible
    && typeof value.truncated === 'boolean' && (value.limitation === null || typeof value.limitation === 'string');
}
function location(value: unknown): boolean {
  return record(value) && integer(value.start) && integer(value.end) && value.end > value.start;
}
function rows(value: unknown, max: number, check: (item: Record<string, unknown>) => boolean): boolean {
  return Array.isArray(value) && value.length <= max && value.every(item => record(item) && typeof item.id === 'string' && check(item));
}
const statuses = ['not_run', 'queued', 'running', 'completed', 'partial', 'failed', 'interrupted'];
export function validateResults(value: unknown, id: string): ReviewResults {
  if (!record(value) || value.analysis_id !== id || !['live', 'demo'].includes(String(value.mode))
    || typeof value.document_name !== 'string' || typeof value.created_at !== 'string'
    || !Number.isFinite(Date.parse(value.created_at)) || typeof value.court_profile_id !== 'string'
    || !statuses.includes(String(value.status)) || !coverage(value.coverage)
    || !record(value.score) || value.score.provisional !== true || typeof value.score.version !== 'string'
    || !(value.score.value === null || (integer(value.score.value) && value.score.value <= 100))
    || !(value.score.risk_level === null || ['needs_review', 'high_risk'].includes(String(value.score.risk_level)))
    || !Array.isArray(value.score.deductions) || typeof value.score.limitation !== 'string'
    || !(value.score.categories === undefined || (Array.isArray(value.score.categories) && value.score.categories.length <= 6
      && new Set(value.score.categories.map(item => record(item) ? item.type : null)).size === value.score.categories.length
      && value.score.categories.every(item => record(item) && ['citation', 'claim_support', 'quote', 'privacy', 'court_rule', 'table_of_authorities'].includes(String(item.type))
        && integer(item.eligible) && integer(item.evaluated) && item.evaluated <= item.eligible && integer(item.deducted_points)
        && (item.value === null || (integer(item.value) && item.value <= 100))
        && (item.evaluated > 0 || item.value === null))))
    || !value.score.deductions.every(item => record(item) && typeof item.finding_id === 'string' && integer(item.points))
    || !Array.isArray(value.stages) || value.stages.length > 9 || !value.stages.every(item => record(item)
      && typeof item.name === 'string' && [...statuses, 'skipped', 'unavailable'].includes(String(item.status))
      && coverage(item.coverage) && typeof item.applicable === 'boolean'
      && (item.reason === null || typeof item.reason === 'string'))
    || !rows(value.findings, 2000, item => ['citation', 'claim_support', 'quote', 'privacy', 'court_rule', 'table_of_authorities', 'system'].includes(String(item.type))
      && ['info', 'low', 'medium', 'high', 'critical'].includes(String(item.severity))
      && typeof item.title === 'string' && typeof item.description === 'string' && integer(item.evidence_count)
      && (item.masked_excerpt === null || typeof item.masked_excerpt === 'string'))
    || !rows(value.citations, 200, item => typeof item.masked_raw_text === 'string' && typeof item.verification_status === 'string' && location(item.location))
    || !rows(value.claims, 200, item => typeof item.text === 'string' && location(item.location) && Array.isArray(item.links)
      && item.links.every(link => record(link) && typeof link.support_status === 'string' && (link.explanation === null || typeof link.explanation === 'string'))
      && (item.corrected_text === undefined || item.corrected_text === null || typeof item.corrected_text === 'string')
      && (item.propositions_stale === undefined || typeof item.propositions_stale === 'boolean')
      && (item.correction_history === undefined || (Array.isArray(item.correction_history)
        && item.correction_history.length <= 20
        && item.correction_history.every(entry => record(entry) && typeof entry.id === 'string'
          && typeof entry.corrected_text === 'string' && typeof entry.created_at === 'string'))))
    || !rows(value.quotes, 50, item => typeof item.text === 'string' && location(item.location)
      && ['not_run', 'exact', 'normalized', 'close', 'not_found', 'source_unavailable'].includes(String(item.match_status))
      && (item.similarity === null || (typeof item.similarity === 'number' && Number.isFinite(item.similarity) && item.similarity >= 0 && item.similarity <= 1))
      && (item.closest_passage === null || typeof item.closest_passage === 'string'))
    || typeof value.limitation !== 'string') throw new Error('Unexpected review results');
  return value as unknown as ReviewResults;
}
export async function submitClaimCorrection(
  analysisId: string,
  claimId: string,
  correctedText: string,
): Promise<ClaimCorrectionResponse> {
  const value = await authorized(
    `/analyses/${encodeURIComponent(analysisId)}/claims/${encodeURIComponent(claimId)}/corrections`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ corrected_text: correctedText }),
    },
  );
  if (!record(value) || value.analysis_id !== analysisId || value.claim_id !== claimId
    || typeof value.original_text !== 'string' || typeof value.corrected_text !== 'string'
    || value.propositions_stale !== true || typeof value.limitation !== 'string'
    || !Array.isArray(value.history) || !Array.isArray(value.affected_link_ids)) {
    throw new Error('Unexpected claim correction response');
  }
  return value as unknown as ClaimCorrectionResponse;
}
export async function getResults(id: string, signal?: AbortSignal): Promise<ReviewResults> {
  return validateResults(await authorized(`/analyses/${encodeURIComponent(id)}/results`, { signal }), id);
}
export async function getGraph(id: string, signal?: AbortSignal): Promise<ReviewGraph> {
  const value = await authorized(`/analyses/${encodeURIComponent(id)}/graph`, { signal });
  if (!record(value) || value.analysis_id !== id
    || !rows(value.nodes, 2200, item => typeof item.label === 'string' && typeof item.status === 'string'
      && ['section', 'claim', 'authority'].includes(String(item.kind))
      && (item.finding_ids === undefined || (Array.isArray(item.finding_ids) && item.finding_ids.every(id => typeof id === 'string'))))
    || !rows(value.edges, 2500, item => typeof item.source === 'string' && typeof item.target === 'string' && typeof item.label === 'string')) {
    throw new Error('Unexpected evidence graph');
  }
  const graph = value as unknown as ReviewGraph;
  const ids = new Set(graph.nodes.map(node => node.id));
  if (ids.size !== graph.nodes.length || graph.edges.some(edge => !ids.has(edge.source) || !ids.has(edge.target))) {
    throw new Error('Unexpected graph relationships');
  }
  return graph;
}
export async function getEvidence(id: string, findingId: string, signal?: AbortSignal): Promise<FindingEvidence> {
  const value = await authorized(`/analyses/${encodeURIComponent(id)}/findings/${encodeURIComponent(findingId)}/evidence`, { signal });
  if (!record(value) || value.analysis_id !== id || value.finding_id !== findingId
    || !rows(value.evidence, 400, item => typeof item.excerpt === 'string' && integer(item.source_start)
      && integer(item.source_end) && item.source_end > item.source_start
      && typeof item.source_sha256 === 'string' && /^[a-f0-9]{64}$/.test(item.source_sha256)
      && typeof item.retrieved_at === 'string' && Number.isFinite(Date.parse(item.retrieved_at))
      && typeof item.method_version === 'string'
      && ['live', 'synthetic', 'cached_public'].includes(String(item.provenance))
      && (item.source_url === null || safeSourceURL(item.source_url)))) throw new Error('Unexpected finding evidence');
  return value as unknown as FindingEvidence;
}
export function safeSourceURL(value: unknown): value is string {
  if (typeof value !== 'string') return false;
  try { const url = new URL(value); return ['https:', 'http:'].includes(url.protocol) && !url.username && !url.password; }
  catch { return false; }
}
export async function downloadReport(
  id: string,
  format: 'markdown' | 'html' | 'pdf' | 'graph-svg' | 'graph-png',
): Promise<void> {
  const response = await authorizedResponse(`/analyses/${encodeURIComponent(id)}/report?format=${format}`);
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  const ext = format === 'html' ? 'html'
    : format === 'pdf' ? 'pdf'
    : format === 'graph-svg' ? 'svg'
    : format === 'graph-png' ? 'png'
    : 'md';
  anchor.download = `filingguard-${id}.${ext}`;
  document.body.append(anchor); anchor.click(); anchor.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export interface RedTeamWeakness {
  id: string;
  vulnerability_type: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  title: string;
  challenge_theory: string;
  impact_summary: string;
  remediation_recommendation: string;
  linked_finding_ids: string[];
  linked_citation_ids: string[];
  linked_claim_ids: string[];
  linked_quote_ids: string[];
}

export interface RedTeamResponse {
  analysis_id: string;
  generated_at: string;
  weaknesses: RedTeamWeakness[];
  summary: string;
  total_weaknesses: number;
  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
  limitation: string;
}

export function validateRedTeamResponse(value: unknown, id: string): RedTeamResponse {
  if (!record(value) || value.analysis_id !== id
    || typeof value.generated_at !== 'string' || !Number.isFinite(Date.parse(value.generated_at))
    || typeof value.summary !== 'string' || !integer(value.total_weaknesses)
    || !integer(value.critical_count) || !integer(value.high_count)
    || !integer(value.medium_count) || !integer(value.low_count)
    || value.total_weaknesses !== (Number(value.critical_count) + Number(value.high_count) + Number(value.medium_count) + Number(value.low_count))
    || (Array.isArray(value.weaknesses) && value.total_weaknesses !== value.weaknesses.length)
    || typeof value.limitation !== 'string'
    || !rows(value.weaknesses, 100, item => typeof item.title === 'string'
      && ['critical', 'high', 'medium', 'low'].includes(String(item.severity))
      && typeof item.challenge_theory === 'string'
      && typeof item.impact_summary === 'string'
      && typeof item.remediation_recommendation === 'string'
      && Array.isArray(item.linked_finding_ids))) {
    throw new Error('Unexpected red-team review response');
  }
  return value as unknown as RedTeamResponse;
}

export async function getRedTeam(id: string, signal?: AbortSignal): Promise<RedTeamResponse> {
  const value = await authorized(`/analyses/${encodeURIComponent(id)}/red-team`, { signal });
  return validateRedTeamResponse(value, id);
}

export async function runRedTeam(id: string): Promise<RedTeamResponse> {
  const value = await authorized(`/analyses/${encodeURIComponent(id)}/red-team`, { method: 'POST' });
  return validateRedTeamResponse(value, id);
}

export interface GroundedAnswerResponse {
  analysis_id: string;
  finding_id: string;
  question: string;
  answer: string;
  status: 'answered' | 'refused' | 'no_evidence';
  refusal_reason: 'broad_legal_advice' | 'out_of_scope' | 'none';
  evidence_record_ids: string[];
  source_authorities: string[];
  source_urls: string[];
  method_version: string;
  created_at: string;
}

export interface GroundedQuestionHistory {
  analysis_id: string;
  finding_id: string;
  questions: GroundedAnswerResponse[];
  count: number;
  limit: number;
}

export function validateGroundedAnswerResponse(value: unknown, analysisId: string, findingId: string): GroundedAnswerResponse {
  if (!record(value) || value.analysis_id !== analysisId || value.finding_id !== findingId
    || typeof value.question !== 'string'
    || typeof value.answer !== 'string'
    || !['answered', 'refused', 'no_evidence'].includes(String(value.status))
    || !['broad_legal_advice', 'out_of_scope', 'none'].includes(String(value.refusal_reason))
    || !Array.isArray(value.evidence_record_ids)
    || !Array.isArray(value.source_authorities)
    || !Array.isArray(value.source_urls)
    || typeof value.method_version !== 'string'
    || typeof value.created_at !== 'string') {
    throw new Error('Unexpected grounded Q&A response');
  }
  return value as unknown as GroundedAnswerResponse;
}

export function validateGroundedQuestionHistory(value: unknown, analysisId: string, findingId: string): GroundedQuestionHistory {
  if (!record(value) || value.analysis_id !== analysisId || value.finding_id !== findingId
    || !integer(value.count) || !integer(value.limit)
    || !Array.isArray(value.questions)) {
    throw new Error('Unexpected grounded Q&A history response');
  }
  return value as unknown as GroundedQuestionHistory;
}

export async function askFindingQuestion(
  analysisId: string,
  findingId: string,
  question: string,
  signal?: AbortSignal,
): Promise<GroundedAnswerResponse> {
  const value = await authorized(
    `/analyses/${encodeURIComponent(analysisId)}/findings/${encodeURIComponent(findingId)}/questions`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question }),
      signal,
    },
  );
  return validateGroundedAnswerResponse(value, analysisId, findingId);
}

export async function getFindingQuestions(
  analysisId: string,
  findingId: string,
  signal?: AbortSignal,
): Promise<GroundedQuestionHistory> {
  const value = await authorized(
    `/analyses/${encodeURIComponent(analysisId)}/findings/${encodeURIComponent(findingId)}/questions`,
    { signal },
  );
  return validateGroundedQuestionHistory(value, analysisId, findingId);
}


