import { createHash } from 'node:crypto';
import { constants } from 'node:fs';
import { access, copyFile, mkdir, readFile, readdir, stat, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { masterPath, mobileMasterPath, outRoot, posterPath, renditionPath, renditions, repoRoot } from './common.mjs';

const revision = process.argv.find((argument) => argument.startsWith('--revision='))?.slice('--revision='.length) || 'v1';
if (!/^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$/.test(revision)) throw new Error('Revision must be a simple directory name');
const destination = path.resolve(outRoot, 'revisions', revision);
const exists = async (file) => { try { await access(file); return true; } catch { return false; } };
const digest = async (file) => createHash('sha256').update(await readFile(file)).digest('hex');
const files = [masterPath, mobileMasterPath, posterPath];
for (const rendition of renditions) for (const extension of ['mp4', 'webm']) files.push(renditionPath(rendition.name, extension));
for (const report of ['master-report.json', 'mobile-master-report.json', 'media-report.json']) {
  const file = path.join(outRoot, report);
  if (await exists(file)) files.push(file);
}
// Save prior keyframe evidence as well as media before preview commands replace it.
for (const directory of ['stills', 'mobile-stills']) {
  const location = path.join(outRoot, directory);
  if (await exists(location)) for (const item of await readdir(location, { withFileTypes: true })) if (item.isFile()) files.push(path.join(location, item.name));
}
const manifest = [];
for (const source of files) {
  const relative = path.relative(repoRoot, source);
  const target = path.resolve(destination, relative);
  if (!target.toLowerCase().startsWith((destination + path.sep).toLowerCase())) throw new Error(`Backup target escapes revision: ${target}`);
  const sourceHash = await digest(source);
  await mkdir(path.dirname(target), { recursive: true });
  if (await exists(target)) {
    if (await digest(target) !== sourceHash) throw new Error(`Refusing to overwrite a different prior revision file: ${target}`);
  } else {
    await copyFile(source, target, constants.COPYFILE_EXCL);
    if (await digest(target) !== sourceHash) throw new Error(`Backup hash verification failed: ${target}`);
  }
  manifest.push({ source: relative.replaceAll(path.sep, '/'), copy: path.relative(destination, target).replaceAll(path.sep, '/'), bytes: (await stat(target)).size, sha256: sourceHash });
}
const manifestPath = path.join(destination, 'manifest.json');
if (!await exists(manifestPath)) await writeFile(manifestPath, JSON.stringify({ copiedAt: new Date().toISOString(), revision, method: 'copy-only; source and backup SHA256 matched', files: manifest }, null, 2) + '\n', { flag: 'wx' });
console.log(`Preserved ${manifest.length} files with verified SHA256 copies: ${destination}`);
