export function reviewPollInterval(status: string | undefined, failed: boolean, failures: number): number | false {
  if (status !== 'queued' && status !== 'running') return false;
  return failed ? Math.min(8000, 2000 * (failures + 1)) : 1000;
}
