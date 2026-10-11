---
type: decision
status: accepted
date: 2026-10-06
tags: [decisions, citations, evidence]
---
# Local citation occurrences before source verification

## Context
T032 needs inspectable original filing occurrences before T033's CourtListener
adapter exists. The generic stage boundary previously disallowed all records from
incomplete stages. Calling parser success a completed source check would conflate
syntax recognition with case existence and create misleading coverage.

## Decision and alternatives
Keep parser support and authority verification separate. Store typed extraction
metadata in Citation.extraction_metadata (migration 0004); retain original raw
Unicode spans and paragraph/page anchors. Recognized full-case syntax can have a
normalized lookup string, but authority ID stays null and verification `not_run`.
Retain ambiguity, unresolved short references and unsupported formats. A narrow
numeric reporter fallback is explicitly heuristic and incomplete, including
cross-line/page candidates; it never resolves a source.

Allow only partial CITATIONS output consisting of unverified Citation rows, with
zero evaluated checks and unavailable authority coverage. Keep other incomplete
record paths rejected. Use the existing contained worker and parent-only atomic
persistence, passing minimal persisted segment IDs/locations. Revalidate every
returned slice, anchor and cross-boundary warning. Retain the first 200 ordered
occurrences with total count and explicit truncation.

Zero detections skips the detected-supported-format check with a limited-coverage
caveat. It does not certify the document is citation-free or ready to file.
Expose bounded private masked reads for future results screens; normalized text is
omitted if its original display overlaps a masked identifier.

Rejected: treating all parser matches as verified, silently dropping ambiguous
reporters, linking short citations by a guessed antecedent, cleaning input without
an offset map, or broadening every partial stage to permit substantive findings.
No live lookup or extra provider spending is needed for extraction.

## Consequences
T032 can be tested independently of account access and network reliability.
Repeated citations remain separate occurrences; outbound deduplication is T035.
Reporter recognition and heuristic candidates can be false positives; unsupported
formats can still be missed. Original documents stay private, and heuristic
masking is not complete redaction. Heavy Eyecite imports stay out of independent
privacy/profile workers. Legacy empty metadata means unrun, not inferred parsed.
Hosted process/resource and PostgreSQL behavior remain release checks.

## Evidence and verification
Installed Eyecite 2.7.8 recognizes the five curated full-case occurrences, including
the repeated Brown citation and intentionally invented reporter citation. The
invented citation remains unverified. Targeted local tests cover exact Unicode
spans, ambiguity, references, unsupported formats, cross-boundary anchors, IPC,
owner/expiry/deletion/rerun, masking, truncation and populated SQLite migration.
See [[docs/sessions/2026-10-06 - Local citation extraction]] for actual regression
commands/outcomes and checks not run.
Primary references: [Eyecite API](https://freelawproject.github.io/eyecite/find.html),
[Eyecite models](https://github.com/freelawproject/eyecite/blob/main/eyecite/models.py).

## Related
[[TODO]] (T032-T036), [[FilingGuard_AI_SRS#9.3 Citation Verification]],
[[apps/api/src/filingguard/modules/citations/README]],
[[apps/api/src/filingguard/modules/analyses/README]],
[[apps/api/src/filingguard/db/models/README]], [[contracts/README]],
[[docs/architecture/stack]],
[[docs/decisions/ADR-004 - Truthful contracts and scoped evidence]],
[[docs/decisions/ADR-008 - Contained review deadlines and provider budgets]].

[[docs/decisions/Index]]
