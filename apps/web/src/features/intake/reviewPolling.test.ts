import { expect, it } from 'vitest';
import { reviewPollInterval } from './reviewPolling';

it('polls active jobs every second, backs off and stops on terminal states', () => {
  expect(reviewPollInterval('queued', false, 0)).toBe(1000);
  expect(reviewPollInterval('running', false, 0)).toBe(1000);
  expect(reviewPollInterval('running', true, 0)).toBe(2000);
  expect(reviewPollInterval('running', true, 10)).toBe(8000);
  for (const status of ['not_run', 'partial', 'completed', 'failed', 'interrupted']) {
    expect(reviewPollInterval(status, false, 0)).toBe(false);
  }
});
