---
type: issue
status: resolved
date: 2026-10-10
tags: [issues, reports, provenance]
---
# Report omits evidence cache provenance

## Symptom and reproduction
Export the executed curated-v1 sample. Saved evidence exposed cached_public
provenance, but Markdown/HTML omitted it, leaving source lookup mode unclear.

## Evidence and cause
The integration assertion for cached_public failed; the renderer included URL,
hash/time/method but omitted saved evidence provenance.

## Fix and regression check
Exports include source mode and per-evidence provenance. Demo mode states cached
public opinions with freshly computed classifications. Both export assertions
and existing HTML escaping checks pass in the 74-test focused run. Exports make
no additional provider calls.

## Related
[[TODO]] | [[apps/api/src/filingguard/modules/reports/README]]
[[docs/sessions/2026-10-10 - Curated demo acceptance]] | [[docs/issues/Index]]
