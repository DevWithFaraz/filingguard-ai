import { spawn } from 'node:child_process';
import { existsSync } from 'node:fs';
import { mkdir, readFile, stat, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { bundle } from '@remotion/bundler';
import { RenderInternals, openBrowser, selectComposition } from '@remotion/renderer';

export const videoRoot = fileURLToPath(new URL('..', import.meta.url));
export const repoRoot = path.resolve(videoRoot, '../..');
export const outRoot = path.join(videoRoot, 'out');
export const mediaRoot = path.join(repoRoot, 'apps/web/src/assets/video');
export const masterPath = path.join(outRoot, 'pipeline-film-master.mp4');
export const mobileMasterPath = path.join(outRoot, 'pipeline-film-mobile-master.mp4');
export const posterPath = path.join(mediaRoot, 'pipeline-film-poster.webp');
export const stillFrames = [60, 144, 240, 336, 420, 510, 612, 690, 756, 0, 779];
export const compositionSpec = { id: 'PipelineFilm', width: 1920, height: 1080, fps: 30, durationInFrames: 780 };
export const mobileCompositionSpec = { ...compositionSpec, id: 'PipelineFilmMobile' };
const mib = 1024 * 1024;
export const renditions = [
  { name: 'desktop', width: 2560, height: 1440, budgetBytes: 12 * mib, maxrate: '3400k', bufsize: '6800k' },
  { name: 'mobile', width: 1920, height: 1080, budgetBytes: 8 * mib, maxrate: '2200k', bufsize: '4400k' },
];

export const renditionPath = (name, extension) => path.join(mediaRoot, `pipeline-film-${name}.${extension}`);

// Pinned Remotion 4.0.529 exports this resolver. It uses the already installed
// platform compositor package, so encoding needs no global FFmpeg installation.
export const binaryPath = (type) => {
  const result = RenderInternals.getExecutablePath({ type, binariesDirectory: null, indent: false, logLevel: 'error' });
  if (!existsSync(result)) throw new Error(`Missing bundled ${type}: ${result}`);
  return result;
};

export const runBinary = (executable, args, { stream = false } = {}) => new Promise((resolve, reject) => {
  const child = spawn(executable, args, { windowsHide: true, shell: false, stdio: ['ignore', 'pipe', 'pipe'] });
  let stdout = '';
  let stderr = '';
  child.stdout.on('data', (chunk) => { stdout += chunk; if (stream) process.stdout.write(chunk); });
  child.stderr.on('data', (chunk) => {
    stderr = (stderr + chunk).slice(-2 * 1024 * 1024);
    if (stream) process.stderr.write(chunk);
  });
  child.once('error', reject);
  child.once('close', (code) => code === 0 ? resolve({ stdout, stderr }) : reject(new Error(`${path.basename(executable)} exited ${code}: ${stderr}`)));
});

const browserExecutable = () => {
  if (process.env.REMOTION_BROWSER_EXECUTABLE) {
    const specified = path.resolve(process.env.REMOTION_BROWSER_EXECUTABLE);
    if (!existsSync(specified)) throw new Error(`REMOTION_BROWSER_EXECUTABLE does not exist: ${specified}`);
    return specified;
  }
  if (process.platform === 'win32') {
    const candidates = [
      path.join(process.env.ProgramFiles || 'C:/Program Files', 'Google/Chrome/Application/chrome.exe'),
      path.join(process.env['ProgramFiles(x86)'] || 'C:/Program Files (x86)', 'Microsoft/Edge/Application/msedge.exe'),
    ];
    const installed = candidates.find((candidate) => existsSync(candidate));
    if (installed) return installed;
  }
  // Let Remotion use its cached headless shell on other platforms.
  return undefined;
};

export const openRenderBrowser = async ({ gl = process.env.REMOTION_GL || (process.platform === 'win32' ? 'angle' : 'swangle') } = {}) => {
  if (!['angle', 'swangle'].includes(gl)) throw new Error('REMOTION_GL must be angle or swangle');
  const executable = browserExecutable();
  console.log(`Render browser: ${executable || 'Remotion cached headless shell'}; renderer: ${gl}`);
  return openBrowser('chrome', {
    browserExecutable: executable,
    chromiumOptions: { gl, headless: true },
    logLevel: 'warn',
  });
};

export const prepareRender = async ({ id = compositionSpec.id } = {}) => {
  const spec = id === compositionSpec.id ? compositionSpec : id === mobileCompositionSpec.id ? mobileCompositionSpec : null;
  if (!spec) throw new Error(`Unknown production composition: ${id}`);
  await mkdir(outRoot, { recursive: true });
  const serveUrl = await bundle({
    entryPoint: path.join(videoRoot, 'src/index.ts'),
    rootDir: videoRoot,
    publicDir: path.join(videoRoot, 'public'),
    outDir: path.join(outRoot, `bundle-${id}`),
  });
  const browser = await openRenderBrowser();
  try {
    const composition = await selectComposition({ serveUrl, id, puppeteerInstance: browser, logLevel: 'warn' });
    for (const [key, expected] of Object.entries(spec)) {
      if (composition[key] !== expected) throw new Error(`Composition ${key}: expected ${expected}, received ${composition[key]}`);
    }
    return { serveUrl, composition, browser, close: () => browser.close({ silent: true }) };
  } catch (error) {
    await browser.close({ silent: true });
    throw error;
  }
};

export const probeVideo = async (file) => {
  const { stdout } = await runBinary(binaryPath('ffprobe'), ['-v', 'error', '-show_format', '-show_streams', '-of', 'json', file]);
  const metadata = JSON.parse(stdout);
  const video = metadata.streams.filter((stream) => stream.codec_type === 'video');
  const audio = metadata.streams.filter((stream) => stream.codec_type === 'audio');
  const stream = video[0];
  const [numerator, denominator] = (stream?.avg_frame_rate || '0/1').split('/').map(Number);
  return {
    file: path.relative(repoRoot, file).replaceAll(path.sep, '/'),
    bytes: (await stat(file)).size,
    width: stream?.width || 0,
    height: stream?.height || 0,
    fps: denominator ? numerator / denominator : 0,
    durationSeconds: Number(metadata.format.duration || stream?.duration || 0),
    codec: stream?.codec_name || null,
    pixelFormat: stream?.pix_fmt || null,
    videoTracks: video.length,
    audioTracks: audio.length,
    frames: stream?.nb_frames ? Number(stream.nb_frames) : null,
  };
};

export const validateVideo = (media, { width, height, codec, budgetBytes = null }) => {
  const failures = [];
  if (media.width !== width || media.height !== height) failures.push(`Expected ${width}x${height}, got ${media.width}x${media.height}`);
  if (media.fps !== 30) failures.push(`Expected 30 fps, got ${media.fps}`);
  if (!Number.isFinite(media.durationSeconds) || Math.abs(media.durationSeconds - 26) > 1 / 30) failures.push(`Expected 26 seconds, got ${media.durationSeconds}`);
  if (!Number.isSafeInteger(media.bytes) || media.bytes <= 0) failures.push(`Expected a nonempty media file, got ${media.bytes} bytes`);
  if (media.videoTracks !== 1 || media.audioTracks !== 0) failures.push(`Expected one video/no audio; got ${media.videoTracks}/${media.audioTracks}`);
  if (media.codec !== codec) failures.push(`Expected codec ${codec}, got ${media.codec}`);
  if (media.pixelFormat !== 'yuv420p') failures.push(`Expected yuv420p, got ${media.pixelFormat}`);
  if (media.frames !== null && media.frames !== 780) failures.push(`Expected 780 frames, got ${media.frames}`);
  if (budgetBytes !== null && media.bytes > budgetBytes) failures.push(`Size ${media.bytes} exceeds ${budgetBytes} bytes`);
  return { ...media, budgetBytes, withinBudget: budgetBytes === null ? null : media.bytes <= budgetBytes, pass: failures.length === 0, failures };
};

// Chromium writes WebP; Remotion's minimal FFprobe build omits that decoder.
// Read the standard RIFF image header to verify its dimensions without a new tool.
export const probePoster = async () => {
  const data = await readFile(posterPath);
  if (data.toString('ascii', 0, 4) !== 'RIFF' || data.toString('ascii', 8, 12) !== 'WEBP') throw new Error('Poster is not a WebP RIFF file');
  let width = 0;
  let height = 0;
  for (let offset = 12; offset + 8 <= data.length;) {
    const tag = data.toString('ascii', offset, offset + 4);
    const size = data.readUInt32LE(offset + 4);
    const start = offset + 8;
    if (start + size > data.length) throw new Error('Truncated WebP chunk');
    if (tag === 'VP8X' && size >= 10) {
      width = data.readUIntLE(start + 4, 3) + 1;
      height = data.readUIntLE(start + 7, 3) + 1;
    } else if (tag === 'VP8 ' && size >= 10) {
      width = data.readUInt16LE(start + 6) & 0x3fff;
      height = data.readUInt16LE(start + 8) & 0x3fff;
    } else if (tag === 'VP8L' && size >= 5) {
      const bits = data.readUInt32LE(start + 1);
      width = (bits & 0x3fff) + 1;
      height = ((bits >>> 14) & 0x3fff) + 1;
    }
    if (width && height) break;
    offset = start + size + (size % 2);
  }
  const budgetBytes = 350 * 1024;
  const failures = [];
  if (width !== 1920 || height !== 1080) failures.push(`Expected 1920x1080, got ${width}x${height}`);
  if (data.length > budgetBytes) failures.push(`Size ${data.length} exceeds ${budgetBytes} bytes`);
  return { file: path.relative(repoRoot, posterPath).replaceAll(path.sep, '/'), bytes: data.length, width, height, format: 'webp', budgetBytes, withinBudget: data.length <= budgetBytes, pass: failures.length === 0, failures };
};

export const writeMediaReport = async () => {
  const master = validateVideo(await probeVideo(masterPath), { width: 3840, height: 2160, codec: 'h264' });
  const mobileMaster = validateVideo(await probeVideo(mobileMasterPath), { width: 1920, height: 1080, codec: 'h264' });
  const website = [];
  for (const rendition of renditions) {
    for (const extension of ['mp4', 'webm']) {
      website.push(validateVideo(await probeVideo(renditionPath(rendition.name, extension)), { ...rendition, codec: extension === 'mp4' ? 'h264' : 'vp9' }));
    }
  }
  const poster = await probePoster();
  const report = {
    measuredAt: new Date().toISOString(),
    expected: { durationSeconds: 26, fps: 30, frames: 780, audioTracks: 0 },
    binaries: { ffmpeg: binaryPath('ffmpeg'), ffprobe: binaryPath('ffprobe') },
    master, mobileMaster, website, poster,
    pass: [master, mobileMaster, ...website, poster].every((entry) => entry.pass),
    visualReview: 'Metadata checks do not establish visual quality, motion pacing, or user acceptance.',
  };
  await mkdir(outRoot, { recursive: true });
  await writeFile(path.join(outRoot, 'media-report.json'), JSON.stringify(report, null, 2) + '\n');
  for (const media of [master, mobileMaster, ...website, poster]) console.log(`${media.pass ? 'PASS' : 'FAIL'} ${media.file}: ${media.width}x${media.height}, ${(media.bytes / mib).toFixed(2)} MiB${media.durationSeconds ? `, ${media.durationSeconds}s, ${media.audioTracks} audio` : ''}`);
  if (!report.pass) throw new Error('Media metadata or budget checks failed; see out/media-report.json');
  return report;
};
