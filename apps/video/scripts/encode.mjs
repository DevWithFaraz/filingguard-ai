import { mkdir, stat } from 'node:fs/promises';
import { renderStill } from '@remotion/renderer';
import { binaryPath, masterPath, mobileMasterPath, mediaRoot, posterPath, prepareRender, probeVideo, renditionPath, renditions, runBinary, validateVideo, writeMediaReport } from './common.mjs';

const frameArg = process.argv.find((arg) => arg.startsWith('--poster-frame='));
const frame = frameArg ? Number(frameArg.slice('--poster-frame='.length)) : 144;
if (!Number.isInteger(frame) || frame < 0 || frame >= 780) throw new Error('--poster-frame must be an integer from 0 through 779');
const master = validateVideo(await probeVideo(masterPath), { width: 3840, height: 2160, codec: 'h264' });
if (!master.pass) throw new Error(`Refusing to encode an invalid master: ${master.failures.join('; ')}`);
const mobileMaster = validateVideo(await probeVideo(mobileMasterPath), { width: 1920, height: 1080, codec: 'h264' });
if (!mobileMaster.pass) throw new Error(`Refusing to encode an invalid mobile master: ${mobileMaster.failures.join('; ')}`);
await mkdir(mediaRoot, { recursive: true });
for (const rendition of renditions) {
  const input = rendition.name === 'mobile' ? mobileMasterPath : masterPath;
  for (const extension of ['mp4', 'webm']) {
    const output = renditionPath(rendition.name, extension);
    let budgetMet = false;
    for (let attempt = 0; attempt < 3 && !budgetMet; attempt++) {
      console.log(`Encoding ${rendition.name}.${extension}, quality attempt ${attempt + 1}`);
      const codecOptions = extension === 'mp4'
        ? ['-c:v', 'libx264', '-preset', 'slow', '-crf', String(21 + attempt * 2), '-movflags', '+faststart']
        : ['-c:v', 'libvpx-vp9', '-deadline', 'good', '-cpu-used', '4', '-row-mt', '1', '-tile-columns', '2', '-crf', String(28 + attempt * 2), '-b:v', rendition.name === 'desktop' ? '3000k' : '1900k'];
      await runBinary(binaryPath('ffmpeg'), [
        '-hide_banner', '-loglevel', 'warning', '-y', '-i', input,
        '-map', '0:v:0', '-an', '-vf', `scale=${rendition.width}:${rendition.height}:flags=lanczos`,
        '-r', '30', '-pix_fmt', 'yuv420p', '-threads', '2',
        ...codecOptions, '-maxrate', rendition.maxrate, '-bufsize', rendition.bufsize,
        '-map_metadata', '-1', output,
      ], { stream: true });
      budgetMet = (await stat(output)).size <= rendition.budgetBytes;
    }
    if (!budgetMet) throw new Error(`${output} still exceeds the size budget after three attempts; review before reducing quality further.`);
  }
}
const context = await prepareRender();
try {
  await renderStill({ composition: context.composition, serveUrl: context.serveUrl, puppeteerInstance: context.browser, frame, output: posterPath, imageFormat: 'webp', scale: 1, overwrite: true, licenseKey: 'free-license', logLevel: 'warn' });
  console.log(`Poster rendered at frame ${frame}: ${posterPath}`);
} finally {
  await context.close();
}
await writeMediaReport();
