import type { components } from './schema';

export const apiOrigin = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '');

export type DemoPreview = components['schemas']['DemoPreview'];

function record(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function span(value: unknown): boolean {
  return record(value) && Number.isInteger(value.start) && Number.isInteger(value.end)
    && typeof value.start === 'number' && typeof value.end === 'number'
    && value.start >= 0 && value.end > value.start && typeof value.text === 'string';
}

export async function getDemo(signal?: AbortSignal): Promise<DemoPreview> {
  const response = await fetch(`${apiOrigin}/api/v1/demos/curated-v1?mode=demo`, {
    signal: signal ? AbortSignal.any([signal, AbortSignal.timeout(15000)]) : AbortSignal.timeout(15000),
    headers: { Accept: 'application/json' }, cache: 'no-store',
  });
  if (!response.ok) throw new Error('Reviewed sample unavailable');
  const value: unknown = await response.json();
  if (!record(value) || value.fixture_id !== 'curated-v1' || value.mode !== 'demo'
    || value.execution_status !== 'not_run' || value.review_kind !== 'delegated_assistant'
    || typeof value.document !== 'string' || typeof value.document_sha256 !== 'string'
    || !/^[a-f0-9]{64}$/.test(value.document_sha256)
    || typeof value.reviewer !== 'string' || typeof value.reviewed_at !== 'string'
    || !Array.isArray(value.limitations) || !value.limitations.every(item => typeof item === 'string')
    || !Array.isArray(value.sources) || !Array.isArray(value.examples)
    || !value.sources.every(source => record(source)
      && ['authority_id', 'case_name', 'citation', 'source_url', 'retrieved_at', 'sha256']
        .every(key => typeof source[key] === 'string') && source.provenance === 'cached_public'
      && /^https:\/\/www\.courtlistener\.com\/api\/rest\/v4\/opinions\/\d+\/$/.test(String(source.source_url)))
    || !value.examples.every(example => record(example)
      && ['id', 'category', 'expected_status', 'reason'].every(key => typeof example[key] === 'string')
      && ['citation', 'proposition', 'quote', 'privacy', 'court_rules'].includes(String(example.category))
      && span(example.filing_span) && (example.source_span === null || span(example.source_span))
      && (example.authority_id === null || typeof example.authority_id === 'string')
      && (example.simulation === null || typeof example.simulation === 'string')
      && (example.preconditions === null || (record(example.preconditions)
        && Object.values(example.preconditions).every(item => typeof item === 'string' || typeof item === 'boolean')))
      && ['accepted', 'conditional'].includes(String(example.judgment))
      && (example.judgment === 'conditional' ? typeof example.condition === 'string' : example.condition === null))) {
    throw new Error('Unexpected reviewed sample response');
  }
  // All contract fields above are validated before the sample can be rendered.
  const demo = value as DemoPreview;
  if (demo.examples.length !== 18 || demo.sources.length !== 3
    || new Set(demo.examples.map(item => item.id)).size !== 18
    || new Set(demo.sources.map(item => item.authority_id)).size !== 3
    || demo.examples.some(item => Array.from(demo.document)
      .slice(item.filing_span.start, item.filing_span.end).join('') !== item.filing_span.text
      || (item.authority_id !== null && !demo.sources.some(source => source.authority_id === item.authority_id)))) {
    throw new Error('Unexpected reviewed sample evidence');
  }
  return demo;
}
type Health = components['schemas']['HealthResponse'];

export async function getHealth(signal?: AbortSignal): Promise<Health> {
  const response = await fetch(`${apiOrigin}/api/v1/health`, {
    signal: signal ? AbortSignal.any([signal, AbortSignal.timeout(15000)]) : AbortSignal.timeout(15000),
    headers: { Accept: 'application/json' },
  });
  if (!response.ok) throw new Error('API unavailable');
  const value: unknown = await response.json();
  if (typeof value !== 'object' || value === null || !('status' in value) || value.status !== 'ok') {
    throw new Error('Unexpected health response');
  }
  return { status: 'ok' };
}
