import type { DemoPreview } from '../lib/api/client';

// Transport validation material only; the browser tests load the actual reviewed fixture.
export function demoFixture(): DemoPreview {
  return {
    fixture_id: 'curated-v1', mode: 'demo', execution_status: 'not_run',
    review_kind: 'delegated_assistant', reviewer: 'Codex (AI assistant)', reviewed_at: '2026-09-27',
    document: 'A😀 source', document_sha256: 'a'.repeat(64), limitations: ['Synthetic test'],
    sources: ['brown', 'miranda', 'obergefell'].map(authority_id => ({
      authority_id, case_name: authority_id, citation: 'Test citation',
      source_url: 'https://www.courtlistener.com/api/rest/v4/opinions/105221/',
      retrieved_at: '2026-09-27T00:00:00Z', sha256: 'b'.repeat(64), provenance: 'cached_public',
    })),
    examples: Array.from({ length: 18 }, (_, index) => ({
      id: `test-${index}`, category: 'quote', expected_status: 'close', reason: 'Test scenario',
      filing_span: { start: 1, end: 2, text: '😀' }, source_span: null,
      authority_id: 'brown', simulation: null, preconditions: null,
      judgment: index < 5 ? 'conditional' : 'accepted', condition: index < 5 ? 'Test condition' : null,
    })),
  };
}
