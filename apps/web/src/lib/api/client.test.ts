import { afterEach, describe, expect, it, vi } from 'vitest';
import { getHealth } from './client';

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
