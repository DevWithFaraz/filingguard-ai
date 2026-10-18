---
type: issue
status: resolved
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
Read-only hosted reviewed-sample GET on October 11 returns 200 with the locked
filing hash, three cached sources and 18 examples after the user reports deploying
`5b37993`. This verifies required resources are available at hosted runtime;
[[docs/sessions/2026-10-11 - Closed intake hosted checks]]. Hosted engine acceptance
remains T057 and is not implied by the read-only sample preview.

[[TODO]] T059/T057, [[docs/delivery/Deployment guide]],
[[apps/api/src/filingguard/modules/analyses/README]],
[[docs/sessions/2026-10-11 - Setup and release documentation]], [[docs/issues/Index]].
