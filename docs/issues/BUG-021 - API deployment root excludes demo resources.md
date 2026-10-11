---
type: issue
status: corrected-local-hosted-verification-pending
date: 2026-10-11
tags: [issues, deployment]
---
# API deployment root excludes demo resources

T059 release review found `render.yaml` scoped the API to `apps/api`, while
`demo_preview.FIXTURE_ROOT` resolves repository-root `data/demo/curated-v1`.
[Render's monorepo contract](https://render.com/docs/monorepo-support) states that
files outside a configured service root are unavailable at build/runtime.
The old health shell did not depend on those files; the current demo does.

The local manifest now leaves the API root unset and uses explicit
`uv sync --directory apps/api --locked --no-dev` and
`apps/api/.venv/bin/uvicorn` commands. The deployment guide requires the same
blank Root Directory setting on the existing service. No hosted incident or
success is claimed; this is an observed configuration/required-resource mismatch.

Local full-repository reproduction verifies cached demo loading and fresh
synthetic execution. The absence of the required fixture fails closed. Render
Linux build/runtime verification remains part of T057 after publication.

[[TODO]] T059/T057, [[docs/delivery/Deployment guide]],
[[apps/api/src/filingguard/modules/analyses/README]],
[[docs/sessions/2026-10-11 - Setup and release documentation]], [[docs/issues/Index]].
