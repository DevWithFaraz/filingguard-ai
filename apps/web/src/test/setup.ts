import '@testing-library/jest-dom/vitest';
import { cleanup } from '@testing-library/react';
import { afterEach } from 'vitest';

// jsdom has no media-query implementation. Browser tests exercise both motion modes.
Object.defineProperty(window, 'matchMedia', { writable: true, value: (media: string) => ({
  matches: false, media, onchange: null, addListener() {}, removeListener() {},
  addEventListener() {}, removeEventListener() {}, dispatchEvent: () => false,
}) });

afterEach(cleanup);
