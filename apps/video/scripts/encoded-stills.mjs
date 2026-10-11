import { mkdir, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { binaryPath, outRoot, renditionPath, renditions, runBinary } from './common.mjs';

// Decoded frames allow a visual comparison of the actual website files against
// Remotion PNGs. They are review material, not automated visual pass claims.
const argument = process.argv.find((arg) => arg.startsWith('--frames='));
const frames = argument ? argument.slice('--frames='.length).split(',').map(Number) : [336, 756];
if (!frames.length || frames.some((frame) => !Number.isInteger(frame) || frame < 0 || frame >= 780)) throw new Error('--frames must contain integer frames from 0 through 779');
const destination = path.join(outRoot, 'encoded-stills');
await mkdir(destination, { recursive: true });
const decoded = [];
for (const rendition of renditions) {
  for (const extension of ['mp4', 'webm']) {
    const input = renditionPath(rendition.name, extension);
    for (const frame of frames) {
      const output = path.join(destination, `${rendition.name}-${extension}-frame-${String(frame).padStart(3, '0')}.png`);
      await runBinary(binaryPath('ffmpeg'), [
        '-hide_banner', '-loglevel', 'error', '-y', '-ss', String(frame / 30), '-i', input,
        '-map', '0:v:0', '-an', '-frames:v', '1', '-update', '1', output,
      ]);
      decoded.push({ input, frame, output });
      console.log(`Decoded ${rendition.name}.${extension} frame ${frame}: ${output}`);
    }
  }
}
await writeFile(path.join(destination, 'manifest.json'), JSON.stringify({ decodedAt: new Date().toISOString(), decoded }, null, 2) + '\n');
