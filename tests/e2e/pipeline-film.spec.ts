import { expect, test } from '@playwright/test';
import { writeFile } from 'node:fs/promises';

test.use({ baseURL: process.env.FILINGGUARD_E2E_BASE_URL || 'http://127.0.0.1:5175' });

test('pipeline film decodes, stays paused on return, and fits desktop/mobile', async ({ page }, info) => {
  const errors: string[] = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.goto('/');
  const frame = page.locator('.pipeline-frame');
  const video = frame.locator('video');
  await expect(page.getByRole('textbox', { name: 'Filing text' })).toBeEnabled();
  expect(await page.locator('.pipeline-walkthrough').evaluate(element => element.previousElementSibling?.className)).toBe('home-hero');
  await frame.scrollIntoViewIfNeeded();
  await expect(frame).toHaveAttribute('data-playback', 'playing');
  await expect.poll(() => video.evaluate((element: HTMLVideoElement) => element.currentTime)).toBeGreaterThan(0.05);
  const media = await video.evaluate((element: HTMLVideoElement) => ({
    duration: element.duration, width: element.videoWidth, height: element.videoHeight,
    muted: element.muted, loop: element.loop, inline: element.playsInline,
  }));
  expect(media.duration).toBeCloseTo(26, 1);
  expect(media.width).toBe(info.project.name === 'mobile' ? 1920 : 2560);
  expect(media.height).toBe(info.project.name === 'mobile' ? 1080 : 1440);
  expect(media).toMatchObject({ muted: true, loop: true, inline: true });
  const pause = page.getByRole('button', { name: 'Pause film', exact: true });
  await pause.focus();
  await page.keyboard.press('Enter');
  await expect(video).toHaveJSProperty('paused', true);
  const time = await video.evaluate((element: HTMLVideoElement) => element.currentTime);
  await page.getByRole('heading', { name: 'FilingGuard-AI' }).scrollIntoViewIfNeeded();
  await frame.scrollIntoViewIfNeeded();
  await expect(frame).toHaveAttribute('data-playback', 'paused');
  await expect(page.getByRole('button', { name: 'Play film', exact: true })).toBeVisible();
  expect(await video.evaluate((element: HTMLVideoElement) => element.currentTime)).toBe(time);
  await page.evaluate(() => {
    Object.defineProperty(document, 'hidden', { configurable: true, get: () => true });
    document.dispatchEvent(new Event('visibilitychange'));
    Reflect.deleteProperty(document, 'hidden');
    document.dispatchEvent(new Event('visibilitychange'));
  });
  await expect(video).toHaveJSProperty('paused', true);
  await expect(page.locator('.pipeline-summary li')).toHaveCount(8);
  for (const width of info.project.name === 'mobile' ? [320, 390] : [1280, 1920]) {
    await page.setViewportSize({ width, height: info.project.name === 'mobile' ? 844 : 900 });
    await frame.scrollIntoViewIfNeeded();
    const bounds = await frame.boundingBox();
    expect(bounds!.x).toBeGreaterThanOrEqual(0);
    expect(bounds!.x + bounds!.width).toBeLessThanOrEqual(width + 0.1);
    expect(bounds!.width / bounds!.height).toBeCloseTo(16 / 9, 1);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  }
  for (const width of info.project.name === 'mobile' ? [1024, 390] : [640, 1920]) {
    await page.setViewportSize({ width, height: 900 });
    await frame.scrollIntoViewIfNeeded();
    await expect.poll(() => video.evaluate((element: HTMLVideoElement) => element.videoWidth)).toBe(width <= 767 ? 1920 : 2560);
    await expect(video).toHaveJSProperty('paused', true);
    expect(await video.evaluate((element: HTMLVideoElement) => element.currentTime)).toBeCloseTo(time, 2);
  }
  await video.evaluate((element: HTMLVideoElement) => new Promise<void>(resolve => {
    element.addEventListener('seeked', () => resolve(), { once: true });
    element.currentTime = 11.2;
  }));
  await page.locator('.pipeline-walkthrough').screenshot({ path: `../../.runtime/pipeline-film-${info.project.name}.png`, scale: 'css' });
  expect(errors).toEqual([]);
});

test('reduced motion shows the poster until play and handles preference changes', async ({ page }) => {
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await page.goto('/');
  const frame = page.locator('.pipeline-frame');
  const video = frame.locator('video');
  await frame.scrollIntoViewIfNeeded();
  await expect(frame).toHaveAttribute('data-playback', 'poster');
  await expect(frame.locator('source')).toHaveCount(0);
  await expect(frame.locator('.pipeline-poster')).toBeVisible();
  await expect.poll(() => frame.locator('.pipeline-poster').evaluate((element: HTMLImageElement) => element.complete && element.naturalWidth > 0)).toBe(true);
  await page.getByRole('button', { name: 'Play film', exact: true }).click();
  await expect(frame).toHaveAttribute('data-playback', 'playing');
  await expect(video).toHaveJSProperty('paused', false);
  await page.emulateMedia({ reducedMotion: 'no-preference' });
  await expect.poll(() => page.evaluate(() => matchMedia('(prefers-reduced-motion: reduce)').matches)).toBe(false);
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await expect(frame).toHaveAttribute('data-playback', 'poster');
  await expect(video).toHaveJSProperty('paused', true);
  await expect(frame.locator('.pipeline-poster')).toBeVisible();
  await page.getByRole('button', { name: 'Play film', exact: true }).click();
  await expect(frame).toHaveAttribute('data-playback', 'playing');
  await page.getByRole('button', { name: 'Pause film', exact: true }).click();
  await page.emulateMedia({ reducedMotion: 'no-preference' });
  await expect(video).toHaveJSProperty('paused', true);
  await expect(page.getByRole('button', { name: 'Play film', exact: true })).toBeVisible();
});

test('automatic playback suspends offscreen and on a hidden page', async ({ page }) => {
  await page.goto('/');
  const frame = page.locator('.pipeline-frame');
  const video = frame.locator('video');
  await frame.scrollIntoViewIfNeeded();
  await expect(frame).toHaveAttribute('data-playback', 'playing');
  await page.getByRole('heading', { name: 'FilingGuard-AI' }).scrollIntoViewIfNeeded();
  await expect(video).toHaveJSProperty('paused', true);
  await frame.scrollIntoViewIfNeeded();
  await expect(frame).toHaveAttribute('data-playback', 'playing');
  // Exercise the document-visibility event deterministically in headless Chromium.
  await page.evaluate(() => {
    Object.defineProperty(document, 'hidden', { configurable: true, get: () => true });
    document.dispatchEvent(new Event('visibilitychange'));
  });
  await expect(video).toHaveJSProperty('paused', true);
  await page.evaluate(() => {
    Reflect.deleteProperty(document, 'hidden');
    document.dispatchEvent(new Event('visibilitychange'));
  });
  await expect(frame).toHaveAttribute('data-playback', 'playing');
});

test('unavailable media retains the poster, stages and retry control', async ({ page }) => {
  await page.route(/pipeline-film-.*\.(mp4|webm)/, route => route.request().resourceType() === 'media' ? route.abort() : route.continue());
  await page.goto('/');
  const frame = page.locator('.pipeline-frame');
  await frame.scrollIntoViewIfNeeded();
  await expect(frame).toHaveAttribute('data-playback', 'failed');
  await expect(frame.locator('.pipeline-poster')).toBeVisible();
  await expect(page.getByRole('status').filter({ hasText: 'The film is unavailable' })).toBeVisible();
  await expect(page.locator('.pipeline-summary li')).toHaveCount(8);
  const retry = page.getByRole('button', { name: 'Retry film', exact: true });
  await retry.focus();
  await expect(retry).toBeFocused();
  await page.unroute(/pipeline-film-.*\.(mp4|webm)/);
  await page.keyboard.press('Enter');
  await expect(frame).toHaveAttribute('data-playback', 'playing');
});

test('normal-view playback advances through every beat and wraps the full loop', async ({ page }, info) => {
  test.setTimeout(60000);
  const errors: string[] = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.goto('/');
  const frame = page.locator('.pipeline-frame');
  const video = frame.locator('video');
  await frame.scrollIntoViewIfNeeded();
  await expect(frame).toHaveAttribute('data-playback', 'playing');
  await video.evaluate((element: HTMLVideoElement) => {
    const targets = [1.8, 4.8, 8, 11.2, 14, 17, 20.4, 23, 24.5];
    const trace = { times: [] as { wallMs: number; time: number }[],
      samples: [] as { target: number; time: number; hash: number; average: number }[], wraps: 0, last: -1 };
    Object.assign(element, { filmLoopTrace: trace });
    const started = performance.now();
    const canvas = document.createElement('canvas');
    canvas.width = 160; canvas.height = 90;
    const context = canvas.getContext('2d')!;
    const record = (_now: number, metadata: VideoFrameCallbackMetadata) => {
      const time = metadata.mediaTime;
      trace.times.push({ wallMs: performance.now() - started, time });
      if (time < trace.last - 0.5 && trace.last > 25) trace.wraps++;
      trace.last = time;
      const target = targets[trace.samples.length];
      if (target !== undefined && time >= target) {
        context.drawImage(element, 0, 0, canvas.width, canvas.height);
        const { data } = context.getImageData(0, 0, canvas.width, canvas.height);
        let hash = 0; let sum = 0;
        for (let index = 0; index < data.length; index += 4) {
          hash = (hash + data[index] * ((index % 97) + 1) + data[index + 1] * 7 + data[index + 2] * 13) % 1000000007;
          sum += data[index] + data[index + 1] + data[index + 2];
        }
        trace.samples.push({ target, time, hash, average: sum / (canvas.width * canvas.height * 3) });
      }
      if (trace.wraps === 0) element.requestVideoFrameCallback(record);
    };
    element.requestVideoFrameCallback(record);
  });
  for (const time of [11.2, 20.4, 24.5]) {
    await expect.poll(() => video.evaluate((element: HTMLVideoElement) => element.currentTime), { timeout: 30000 }).toBeGreaterThanOrEqual(time);
    await frame.screenshot({ path: `../../.runtime/pipeline-loop-${info.project.name}-${time}.png` });
  }
  await expect.poll(() => video.evaluate(element => (element as HTMLVideoElement & { filmLoopTrace: { wraps: number } }).filmLoopTrace.wraps),
    { timeout: 10000 }).toBe(1);
  const trace = await video.evaluate(element => (element as HTMLVideoElement & {
    filmLoopTrace: { times: { wallMs: number; time: number }[]; samples: { target: number; time: number; hash: number; average: number }[]; wraps: number };
  }).filmLoopTrace);
  expect(trace.samples).toHaveLength(9);
  expect(new Set(trace.samples.map(sample => sample.hash)).size).toBe(9);
  expect(trace.samples.every(sample => sample.average > 5)).toBe(true);
  expect(trace.times.length).toBeGreaterThan(100);
  expect(Math.max(...trace.times.map(sample => sample.time))).toBeGreaterThan(25.5);
  await expect(video).toHaveJSProperty('paused', false);
  expect(errors).toEqual([]);
  const media = await video.evaluate((element: HTMLVideoElement) => ({ source: element.currentSrc,
    duration: element.duration, width: element.videoWidth, height: element.videoHeight }));
  const evidence = JSON.stringify({ project: info.project.name, media, errors, ...trace }, null, 2);
  await writeFile(`../../.runtime/pipeline-loop-${info.project.name}.json`, evidence);
  await info.attach('Full pipeline loop evidence', { body: evidence, contentType: 'application/json' });
});
