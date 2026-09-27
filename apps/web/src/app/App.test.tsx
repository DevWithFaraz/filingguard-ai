import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router';
import { afterEach, expect, it, vi } from 'vitest';
import { App } from './App';

afterEach(() => vi.unstubAllGlobals());
it('shows genuine connection status but keeps submission disabled', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('{"status":"ok"}')));
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(<QueryClientProvider client={client}><MemoryRouter><App /></MemoryRouter></QueryClientProvider>);
  expect(await screen.findByText('API connected')).toBeInTheDocument();
  expect(screen.getByRole('button', { name: 'Run review' })).toBeDisabled();
  expect(screen.getByRole('textbox', { name: 'Filing text' })).toBeDisabled();
  client.clear();
});
