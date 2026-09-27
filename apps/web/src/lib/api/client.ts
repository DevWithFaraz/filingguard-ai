import type { components } from './schema';

export const apiOrigin = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '');
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
