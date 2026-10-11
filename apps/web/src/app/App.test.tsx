import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router';
import { afterEach, expect, it, vi } from 'vitest';
import { App } from './App';
import { demoFixture } from '../test/demoFixture';

afterEach(() => vi.unstubAllGlobals());
it('shows genuine connection status but keeps submission disabled', async () => {
  vi.stubGlobal('fetch', vi.fn().mockImplementation(() => Promise.resolve(new Response('{"status":"ok"}'))));
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(<QueryClientProvider client={client}><MemoryRouter><App /></MemoryRouter></QueryClientProvider>);
  expect(await screen.findByText('API connected')).toBeInTheDocument();
  expect(screen.getByText(/Local checks are available after preparation/)).toBeInTheDocument();
  expect(screen.getByRole('textbox', { name: 'Filing text' })).toBeDisabled();
  client.clear();
});

it('opens reviewed examples and reset clears selection and returns to disabled live intake', async () => {
  vi.stubGlobal('fetch', vi.fn().mockImplementation((url: string) => Promise.resolve(
    new Response(JSON.stringify(url.includes('/demos/') ? demoFixture() : { status: 'ok' })),
  )));
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(<QueryClientProvider client={client}><MemoryRouter><App /></MemoryRouter></QueryClientProvider>);
  fireEvent.click(screen.getByRole('button', { name: 'Open reviewed sample' }));
  expect(await screen.findByRole('heading', { name: 'Expected scenarios' })).toBeInTheDocument();
  expect(screen.getByText('Analysis not run')).toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: 'test 0 Quotation / Conditional' }));
  expect(screen.getByRole('region', { name: 'Selected scenario evidence' })).toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: 'Reset sample' }));
  expect(screen.queryByRole('region', { name: 'Selected scenario evidence' })).not.toBeInTheDocument();
  expect(screen.getByText(/Local checks are available after preparation/)).toBeInTheDocument();
  client.clear();
});
