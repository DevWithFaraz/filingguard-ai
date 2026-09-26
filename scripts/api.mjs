import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const root = fileURLToPath(new URL('../', import.meta.url));
const [command, ...args] = process.argv.slice(2);
if (!['sync', 'run'].includes(command)) {
  console.error('Usage: node scripts/api.mjs <sync|run> [arguments]');
  process.exit(1);
}

const locked = command === 'run' ? ['--locked'] : [];
const child = spawn('uv', [command, '--directory', path.join(root, 'apps/api'), ...locked, ...args], {
  cwd: root,
  env: { ...process.env, UV_CACHE_DIR: path.join(root, '.runtime/tool-cache/uv') },
  stdio: 'inherit',
});
child.on('error', (error) => {
  console.error(`Cannot start uv: ${error.message}`);
  process.exitCode = 1;
});
child.on('exit', (code) => {
  process.exitCode = code ?? 1;
});
