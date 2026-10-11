import { writeFile } from 'node:fs/promises';
import { writeFileSync } from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { renderMedia } from '@remotion/renderer';
import { binaryPath, compositionSpec, masterPath, mobileCompositionSpec, mobileMasterPath, openRenderBrowser, outRoot, prepareRender, probeVideo, runBinary, validateVideo } from './common.mjs';

if (process.argv.includes('--smoke')) {
  for (const type of ['ffmpeg', 'ffprobe']) {
    const executable = binaryPath(type);
    const result = await runBinary(executable, ['-version']);
    console.log(`${type}: ${executable}\n${result.stdout.split(/\r?\n/)[0]}`);
  }
  const browser = await openRenderBrowser();
  await browser.close({ silent: true });
  console.log('Render toolchain smoke passed; no composition frames rendered.');
} else {
  const mobile = process.argv.includes('--mobile');
  const spec = mobile ? mobileCompositionSpec : compositionSpec;
  const output = mobile ? mobileMasterPath : masterPath;
  const scale = mobile ? 1 : 2;
  const concurrency = Number(process.env.REMOTION_CONCURRENCY || 2);
  if (!Number.isInteger(concurrency) || concurrency < 1 || concurrency > 8) throw new Error('REMOTION_CONCURRENCY must be an integer from 1 through 8');
  const context = await prepareRender({ id: spec.id });
  let lastBucket = -1;
  let lastLogAt = 0;
  const startedAt = Date.now();
  const progressPath = path.join(outRoot, mobile ? 'mobile-render-progress.json' : 'render-progress.json');
  let latestProgress = { progress: 0, renderedFrames: 0, encodedFrames: 0 };
  const saveProgress = (state, error) => {
    const now = Date.now();
    writeFileSync(progressPath, JSON.stringify({
      composition: spec.id, state, pid: process.pid, scale, concurrency,
      gl: process.env.REMOTION_GL || (process.platform === 'win32' ? 'angle' : 'swangle'),
      startedAt: new Date(startedAt).toISOString(), updatedAt: new Date(now).toISOString(),
      elapsedSeconds: (now - startedAt) / 1000, ...latestProgress,
      totalFrames: spec.durationInFrames, freeMemoryBytes: os.freemem(),
      ...(error ? { error: error.message || String(error) } : {}),
    }, null, 2) + '\n');
  };
  saveProgress('rendering');
  try {
    await renderMedia({
      composition: context.composition,
      serveUrl: context.serveUrl,
      puppeteerInstance: context.browser,
      outputLocation: output,
      codec: 'h264',
      imageFormat: 'png',
      pixelFormat: 'yuv420p',
      scale,
      crf: 16,
      x264Preset: 'medium',
      concurrency,
      muted: true,
      overwrite: true,
      licenseKey: 'free-license',
      logLevel: 'warn',
      onProgress: ({ progress, renderedFrames, encodedFrames }) => {
        latestProgress = { progress, renderedFrames, encodedFrames };
        const bucket = Math.floor(progress * 20);
        const now = Date.now();
        if (bucket !== lastBucket || now - lastLogAt >= 30000) {
          lastBucket = bucket;
          lastLogAt = now;
          saveProgress('rendering');
          console.log(`${new Date(now).toISOString()} ${mobile ? 'Mobile master' : '4K master'} ${Math.round(progress * 100)}%: ${renderedFrames}/${spec.durationInFrames} rendered, ${encodedFrames}/${spec.durationInFrames} encoded; ${Math.round((now - startedAt) / 1000)}s elapsed`);
        }
      },
    });
    const measured = validateVideo(await probeVideo(output), { width: spec.width * scale, height: spec.height * scale, codec: 'h264' });
    await writeFile(path.join(outRoot, mobile ? 'mobile-master-report.json' : 'master-report.json'), JSON.stringify(measured, null, 2) + '\n');
    if (!measured.pass) throw new Error(`Master checks failed: ${measured.failures.join('; ')}`);
    saveProgress('complete');
    console.log(`${mobile ? 'Mobile master' : '4K master'} verified: ${measured.width}x${measured.height}, ${measured.durationSeconds}s, ${measured.fps}fps, ${measured.audioTracks} audio tracks, ${measured.bytes} bytes`);
  } catch (error) {
    saveProgress('failed', error);
    throw error;
  } finally {
    await context.close();
  }
}
