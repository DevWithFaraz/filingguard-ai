---
type: session
status: verified-foundation
date: 2026-09-27
tags: [demo, provenance, frontend]
---
# Curated fixture and font intake

## Changes

T014 created [[data/demo/curated-v1/README|fictional text/PDF material]] paired with
three public CourtListener sources and 18 exact-span expectation drafts. A bounded
subagent built the deterministic PDF/extraction mapping and fixture tests; parent
retrieved sources, authored the filing/scenarios and integrated docs. No LLM call.
Miranda's first reference was a dissent; corrected before fixture lock and recorded
in [[docs/issues/BUG-004 - First opinion reference can be a dissent]].

User supplied eight GC Avalance Demo TTF weights. Included README is personal-use
only; user reports direct creator permission via DM for this site. Proceed on
that report, retain evidence; no independent license verification or embedding
was performed. Background will follow and does not block fixture/backend work.
See [[docs/product/UI direction]], [[docs/feedback/FB-003 - Image-backed filing composer]].

## Checks and limits

Backend suite: 184 passed, 2 platform-specific skipped; existing Starlette/httpx
deprecation warning. Backend Ruff passed. Focused curated/demo tests: 18 passed.
PDF: one page, 3,314 bytes; exact word preservation and extraction offsets tested,
deterministic repeat build verified, rendered page visually inspected. Sources
have original URLs/IDs, UTC retrieval times, content hashes and transformation
metadata. Metadata/hash tests are not legal-accuracy tests.

No frontend changes, new production migration, live engine evaluation, public
intake, hosted redeploy or Git push. Cached replay is still disabled and the
multi-authority fixture is not supported by the current singular-source loader.
Synthetic court profile evaluation remains unimplemented. User's Obsidian graph
changes were untouched.

## Next

T015 human review of [[docs/product/Demo fixture review]]; then T016 adapter/reset
integration. Keep unreviewed semantic expectations separate from engine results.
T013/T017/T018 lifecycle/access integration also remains pending in [[TODO]].

[[docs/sessions/Index]], [[docs/product/Features]], [[TODO]].
