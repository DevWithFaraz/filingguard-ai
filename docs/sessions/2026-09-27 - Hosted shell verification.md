---
type: session
status: verified
date: 2026-09-27
tags: [deployment, verification]
---
# Hosted shell verification

Related: [[TODO]], [[docs/delivery/Deployment guide]],
[[docs/sessions/2026-09-27 - Neon connection verification]].

## Changes and evidence
User deployed the Render free API and static frontend from commit 2879aba,
configured the SPA rewrite and exact frontend CORS origin, then redeployed the
API successfully (dashboard screenshot). User connected a payment card;
no paid compute upgrade was requested or performed by the agent.

Live headless Chrome verification via Playwright passed:
- https://filingguard-ai.onrender.com displays API connected and submission disabled.
- Direct /activity and /settings navigation returns HTTP 200 and the proper views.
- API health returns 200 with status ok.
- Frontend Origin receives its exact Access-Control-Allow-Origin value.
- https://untrusted.example receives no Access-Control-Allow-Origin header.
  Public health remains readable outside browsers; CORS is not authorization.

Read-only Neon connection was verified in the preceding session. Hosted health
does not query PostgreSQL. No hosted migrations, analysis, upload or provider
integration is inferred. Full test suites and mobile checks were not rerun here.

## Caveats and handoff
A database credential was exposed in a user screenshot. Rotation was recommended;
the user declined. No credential is reproduced here. Rotation remains recommended
before real data use. Render cold starts and ephemeral storage remain constraints.

T008 is complete; Phase 1 is verified. Next is T009 typed lifecycle contracts,
not started in this session. Final frontend visual design remains pending user
planning. No code, commit or push was performed in this verification session.
