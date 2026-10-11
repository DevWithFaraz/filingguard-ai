import { afterEach, describe, expect, it, vi } from 'vitest';
import { getDemo, getHealth } from './client';
import { demoFixture } from '../../test/demoFixture';

afterEach(() => vi.unstubAllGlobals());
describe('health boundary', () => {
  it('accepts an actual liveness response', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('{"status":"ok"}')));
    expect(await getHealth()).toEqual({ status: 'ok' });
  });
  it('does not treat missing fields as healthy', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('{}')));
    await expect(getHealth()).rejects.toThrow('Unexpected health response');
  });
  it('rejects provider/proxy errors', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('failed', { status: 503 })));
    await expect(getHealth()).rejects.toThrow('API unavailable');
  });
});

describe('reviewed demo boundary', () => {
  it('requires explicit demo transport and validates code-point spans', async () => {
    const fetch = vi.fn().mockResolvedValue(new Response(JSON.stringify(demoFixture())));
    vi.stubGlobal('fetch', fetch);
    expect((await getDemo()).execution_status).toBe('not_run');
    expect(fetch.mock.calls[0]![0]).toContain('/demos/curated-v1?mode=demo');
  });
  it.each(['mode', 'execution_status', 'review_kind'])('rejects a false %s marker', async key => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify({
      ...demoFixture(), [key]: 'live',
    }))));
    await expect(getDemo()).rejects.toThrow('Unexpected reviewed sample response');
  });
  it('rejects missing conditional review and unsafe source URLs', async () => {
    for (const kind of ['condition', 'url']) {
      const demo = demoFixture();
      if (kind === 'condition') demo.examples[0]!.condition = null;
      else demo.sources[0]!.source_url = 'javascript:alert(1)';
      vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify(demo))));
      await expect(getDemo()).rejects.toThrow('Unexpected reviewed sample response');
    }
  });
  it('rejects mismatched filing evidence and missing sources', async () => {
    for (const kind of ['span', 'source']) {
      const demo = demoFixture();
      if (kind === 'span') demo.examples[0]!.filing_span.text = 'Different';
      else demo.examples[0]!.authority_id = 'unknown';
      vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify(demo))));
      await expect(getDemo()).rejects.toThrow('Unexpected reviewed sample evidence');
    }
  });
  it('keeps errors unavailable rather than substituting fixture data', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('{}', { status: 503 })));
    await expect(getDemo()).rejects.toThrow('Reviewed sample unavailable');
  });
});
