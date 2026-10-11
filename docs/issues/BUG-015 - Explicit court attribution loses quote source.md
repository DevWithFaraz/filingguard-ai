---
type: issue
status: resolved
date: 2026-10-10
tags: [issues, quotes, demo]
---
# Explicit court attribution loses quote source

## Symptom and reproduction
Run curated-v1 through real contained workers with cached public opinions. Both
Brown quotations became source_unavailable, despite valid source hashes. Expected:
the exact and deliberately altered quotes receive exact/close outcomes.

## Evidence and cause
`test_demo_execution.py` observed no citation association. The matcher rejected
the sentence boundary between the citation and `The Court stated: "..."`.

## Fix and regression check
Quote-forensics-v2 accepts one immediately preceding cited sentence followed by
the explicit `The Court stated/held/explained/said/wrote/observed:` bridge. The
300-character limit, extra-sentence/paragraph/page rejection and distinct-citation
ambiguity remain. Four new controls, existing ambiguity controls and contained
curated execution pass in the 74-test focused run. Exact/close now differ.

## Related
[[TODO]] | [[apps/api/src/filingguard/modules/quotes/README]]
[[docs/sessions/2026-10-10 - Curated demo acceptance]] | [[docs/issues/Index]]
