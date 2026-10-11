// Read-only shell/readiness check. Never sends documents, credentials or migrations.
import { mkdir, writeFile } from 'node:fs/promises';
const web = 'https://filingguard-ai.onrender.com';
const api = 'https://filingguard-api.onrender.com';
async function check(path, origin) {
  try {
    const response = await fetch(path, { headers: origin ? { Origin: origin } : {}, signal: AbortSignal.timeout(60000) });
    let body;
    if (response.headers.get('content-type')?.includes('application/json')) body = await response.json();
    else await response.body?.cancel();
    return { status: response.status, origin: response.headers.get('access-control-allow-origin'), body };
  } catch { return { status: null, origin: null }; }
}
const health = await check(`${api}/api/v1/health`, web);
const [ready, capabilities, forbidden, activity, settings] = await Promise.all([
  check(`${api}/api/v1/ready`), check(`${api}/api/v1/capabilities`),
  check(`${api}/api/v1/health`, 'https://invalid-origin.example'),
  check(`${web}/activity`), check(`${web}/settings`),
]);
const receipt = {
  checked_at: new Date().toISOString(), scope: 'Read-only public endpoints; no hosted intake, mutations or migrations',
  liveness_status: health.status, readiness_status: ready.status,
  readiness: ready.body?.status === 'ready',
  readiness_checks: Object.fromEntries(Object.entries(ready.body?.checks || {}).filter(([k,v]) => /^[a-z_]{1,40}$/.test(k) && typeof v === 'boolean')),
  capabilities_status: capabilities.status,
  intake_enabled: typeof capabilities.body?.intake_enabled === 'boolean' ? capabilities.body.intake_enabled : null,
  exact_origin: health.status === 200 && health.origin === web,
  forbidden_origin_has_no_allow_header: forbidden.status === 200 && forbidden.origin === null,
  activity_status: activity.status, settings_status: settings.status,
};
await mkdir('.runtime', { recursive: true });
await writeFile('.runtime/hosted-release-receipt.json', JSON.stringify(receipt, null, 2) + '\n');
console.log(JSON.stringify(receipt, null, 2));
if (receipt.liveness_status !== 200 || receipt.readiness_status !== 200 ||
    receipt.capabilities_status !== 200 || !receipt.readiness || !receipt.intake_enabled ||
    !receipt.exact_origin || !receipt.forbidden_origin_has_no_allow_header ||
    receipt.activity_status !== 200 || receipt.settings_status !== 200) process.exitCode = 2;
