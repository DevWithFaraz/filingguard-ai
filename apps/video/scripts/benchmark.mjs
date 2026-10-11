import { mkdir, stat, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { renderStill, selectComposition } from '@remotion/renderer';
import { compositionSpec, openRenderBrowser, outRoot } from './common.mjs';

// Uses an existing bundle so a performance probe cannot modify a running render.
const gl = process.argv.find((arg) => arg.startsWith('--gl='))?.slice(5) || 'angle';
const imageFormat = process.argv.find((arg) => arg.startsWith('--image-format='))?.slice('--image-format='.length) || 'png';
if (!['png', 'jpeg'].includes(imageFormat)) throw new Error('--image-format must be png or jpeg');
const jpegQuality = Number(process.argv.find((arg) => arg.startsWith('--quality='))?.slice('--quality='.length) || 100);
if (!Number.isInteger(jpegQuality) || jpegQuality < 1 || jpegQuality > 100) throw new Error('--quality must be an integer from 1 through 100');
const label = `${gl}-${imageFormat}${imageFormat === 'jpeg' ? `-q${jpegQuality}` : ''}`;
const directory = path.join(outRoot, 'benchmark');
await mkdir(directory, { recursive: true });
const browser = await openRenderBrowser({ gl });
try {
  const serveUrl = path.join(outRoot, `bundle-${compositionSpec.id}`);
  const composition = await selectComposition({ serveUrl, id: compositionSpec.id, puppeteerInstance: browser, logLevel: 'warn' });
  const measurements = [];
  for (const frame of [336, 756]) {
    const output = path.join(directory, `${label}-frame-${frame}.${imageFormat === 'jpeg' ? 'jpg' : 'png'}`);
    const startedAt = performance.now();
    await renderStill({ composition, serveUrl, puppeteerInstance: browser, frame, output, imageFormat, ...(imageFormat === 'jpeg' ? { jpegQuality } : {}), scale: 2, overwrite: true, licenseKey: 'free-license', logLevel: 'warn' });
    const seconds = (performance.now() - startedAt) / 1000;
    measurements.push({ frame, seconds, bytes: (await stat(output)).size, output });
    console.log(`${label}: 4K frame ${frame} rendered in ${seconds.toFixed(2)}s`);
  }
  await writeFile(path.join(directory, `${label}.json`), JSON.stringify({ measuredAt: new Date().toISOString(), scale: 2, gl, imageFormat, ...(imageFormat === 'jpeg' ? { jpegQuality } : {}), bundle: serveUrl, measurements, averageSeconds: measurements.reduce((sum, item) => sum + item.seconds, 0) / measurements.length }, null, 2) + '\n');
} finally {
  await browser.close({ silent: true });
}
