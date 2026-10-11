---
type: session
status: complete
date: 2026-10-08
tags: [sessions, analysis, documentation, citations]
---
# Codebase and vault analysis

## Task and scope

User requested analysis of the codebase, vault and Markdown documentation, and
a recommendation for the next work. Read [[Home]], [[TODO]], the documentation
workflow, SRS citation/semantic requirements, feature/architecture guides,
relevant decisions, issue/lesson indexes and recent citation/film handoffs.
Inspected runtime registration, contained execution, citation adapter/service,
API contracts/routes, browser review screens, test coverage and CI configuration.
This was a focused architectural/status review, not an exhaustive security audit.

## Findings and recommendation

**Next: T036, with actual citation-worker integration and failure/coverage
correctness as the acceptance focus.** T034/T035 are completed component
milestones; their test evidence does not establish normal source-verification
execution. Earlier unchecked T016/T018/T022/T031 remain documented cross-cutting
integration gates, rather than independent completed features to check off.

The product currently has a substantial local foundation: private Text/PDF/Demo
preparation, canonical document spans, anonymous ownership, deletion/expiry,
contained review workers, local privacy/synthetic court checks, citation
extraction and provider transport. CourtListener lookup/opinion retrieval and
deduplication exist as tested adapter/service components. The accepted homepage
and rendered pipeline film exist. The reviewed sample is read-only expectations,
not an executed live legal assessment.

Normal review registration still selects `citation_stage`, not
`verified_citation_stage`. The worker receives a detached document snapshot and
sanitized environment, with no provider credential field. `Settings()` in a
child may consult configuration, but no explicit reviewed provider-credential
handoff exists in the stage protocol. This boundary needs deliberate integration;
inherit-all environment variables would violate the recorded architecture.

Six fake-provider probes reproduced partial-result/coverage and record-limit
conflicts, with a single verified control passing. See
[[docs/issues/BUG-012 - Citation verification output conflicts with worker validation]].
The T035 persistence/API tests invoke the service and write stage results
directly. They establish those boundaries, not the full /run -> worker -> parent
commit path.

Another T036 acceptance gap is preservation of explanations: the adapter returns
`reason`/`limitation`, including the database-coverage warning, but the citation
service retains status/authority only. `SafeCitation` has no corresponding fields;
the endpoint's global limitation describes extraction coverage. Database absence
must be explained in persisted/user-visible results before claiming FR-044.

Claims/proposition prompts and production LLM integration, quote forensics,
scoring, full findings/detail screens, graph and reports remain planned. Their
module folders/dependencies do not establish runtime features. PreparedView
shows local checks/findings but does not yet render stored citation authorities.
Real court profiles are not configured. Only the earlier shell deployment has
recorded hosted verification; no new hosted behavior was checked here.

Recommended sequence after T036: local traceable claim extraction T037, bounded
source passages T038 with actual outbound masking integration T022/T031, then
grounded proposition evaluation T039-T041. Follow with quote checks T042-T044,
coverage-aware results/scoring/graph T045-T050, reports and integrated acceptance
T051-T056, then hosted release verification T057/T058. Finish T016 replay and
T018 report/graph ownership at their relevant integration points. TODO retains
the only task-status checklist; this sequence is a recommendation, not a second
completion tracker. T061 remains retired.

Keep public intake disabled until existing hosted migration, storage,
containment, ownership and confidentiality gates pass. No recommendation to add
P1/P2 infrastructure or another visual polish task ahead of the core workflow.

## Vault and documentation

Before these documentation changes, the rg-discovered non-ignored Markdown set
contained 154 files and 906 checked wikilink file targets, with no unresolved or
ambiguous file targets. The script resolved root-qualified paths and unique
basenames. It did not validate heading anchors, ordinary Markdown URLs, external
sources, binaries, attachments or ignored files. Link health is not evidence of
semantic accuracy.

TODO's introduction still identified T033 as latest and T034 as next, while its
task rows and latest handoff recorded T035 complete/T036 next. The citation
guide described T033-T035 components as planned. Corrected these descriptions
and qualified the adapter guide's stage integration claim. README now
distinguishes implemented source components from unintegrated runtime execution.
No task completion marks, requirements or runtime behavior changed.

The working tree already had 47 modified tracked entries and 157 untracked
entries before this review's documentation edits (204 git-status entries,
including directory entries). Local changes substantially exceed the old hosted
shell checkpoint. Do not assume the current workspace is reproducible from the
deployed/committed version. No commits, pushes or deployments performed.

The canvas skill was read, but its managed workspace location could not be
identified for this Windows Codex checkout. The review is therefore preserved
here as a native vault note, without claiming a rendered canvas.

## Verification

- Focused backend tests:
  `node scripts/api.mjs run pytest tests/unit/test_courtlistener_adapter.py tests/unit/test_citation_dedup.py tests/integration/test_citation_pipeline.py -q`:
  65 passed in 70.40 seconds; one existing Starlette/httpx deprecation warning.
- `npm run test:web`: 20 tests across four files passed.
- `npm run typecheck`: passed.
- `npm run lint:api`: passed.
- `npm run lint:web`: passed.
- Six synthetic direct runner/validation probes: one control accepted, four
  output-validation failures and one coverage-construction failure, recorded
  in BUG-012. Explicit fake credentials and MockTransport; no live requests.
- Wikilink file-target scan: results and limits above.
- After documentation edits: 156 Markdown files and 941 checked wikilink file
  targets, with no unresolved or ambiguous targets.
- Initial sandbox attempts failed before backend tests (uv trampoline path)
  and frontend tests (Vite realpath EPERM); reruns outside the sandbox succeeded.
  Those failures do not establish application regressions.

Checks not run: full backend suite, production build, Playwright/browser/device
journeys, fresh clean-checkout CI, contract regeneration comparison, live
CourtListener/Groq calls, external source/rule verification, Neon migrations and
hosted release/security/performance checks. Previous handoff outcomes remain
historical evidence and are not claimed as new verification.

## Blockers and next step

Source verification cannot be enabled merely by swapping runner registration:
resolve BUG-012, make credential/context delivery explicit, preserve lookup
explanations, and test normal worker/persistence execution under T036 first.
This analysis did not implement those changes or complete T036.

## Related

[[TODO]], [[FilingGuard_AI_SRS]], [[docs/product/Features]],
[[docs/architecture/stack]], [[docs/knowledge/Documentation Workflow]],
[[docs/learnings/LEARN-001 - Scaffold is not runtime verification]],
[[apps/api/src/filingguard/modules/analyses/README]],
[[apps/api/src/filingguard/modules/citations/README]],
[[apps/api/src/filingguard/integrations/courtlistener/README]],
[[docs/issues/BUG-012 - Citation verification output conflicts with worker validation]],
[[docs/sessions/2026-10-07 - Outbound citation deduplication and response caching]].

[[docs/sessions/Index]] | [[Home]]
