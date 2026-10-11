import { mkdir, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { renderStill } from '@remotion/renderer';
import { compositionSpec, mobileCompositionSpec, outRoot, prepareRender, stillFrames } from './common.mjs';

const mobile = process.argv.includes('--mobile');
const spec = mobile ? mobileCompositionSpec : compositionSpec;
const argument = process.argv.find((arg) => arg.startsWith('--frames='));
const frames = argument ? argument.slice('--frames='.length).split(',').map(Number) : stillFrames;
if (!frames.length || frames.some((frame) => !Number.isInteger(frame) || frame < 0 || frame >= compositionSpec.durationInFrames)) {
  throw new Error('--frames must contain comma-separated integer frames from 0 through 779');
}
const scaleArg = process.argv.find((arg) => arg.startsWith('--scale='));
const scale = scaleArg ? Number(scaleArg.slice('--scale='.length)) : 1;
if (!Number.isFinite(scale) || scale <= 0 || scale > 2) throw new Error('--scale must be >0 and <=2');
const destination = path.join(outRoot, mobile ? 'mobile-stills' : 'stills');
await mkdir(destination, { recursive: true });
const context = await prepareRender({ id: spec.id });
try {
  for (const frame of frames) {
    const output = path.join(destination, `frame-${String(frame).padStart(3, '0')}.png`);
    await renderStill({ composition: context.composition, serveUrl: context.serveUrl, puppeteerInstance: context.browser, frame, output, imageFormat: 'png', scale, overwrite: true, licenseKey: 'free-license', logLevel: 'warn' });
    console.log(`Still ${frame}: ${output}`);
  }
  await writeFile(path.join(destination, 'manifest.json'), JSON.stringify({ renderedAt: new Date().toISOString(), composition: spec, scale, frames }, null, 2) + '\n');
} finally {
  await context.close();
}
