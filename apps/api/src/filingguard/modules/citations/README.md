# citations

Priority: P0. Tasks: T032-T036 in [[TODO]].

Extract with Eyecite and resolve via the CourtListener adapter; retain occurrences.

Segments in; citations, resolved authority IDs, statuses and provenance out. Not-found is not proof of fabrication.

## Implemented extraction (T032)

`service.py` runs the installed, locked Eyecite locally without cleaning or rewriting
the canonical extracted text. Every retained occurrence has a half-open Unicode
code-point span, exact raw text, parser version, kind and extraction support.
Repeats keep distinct occurrence IDs/locations. A unique full-case reporter can
have a normalized lookup string; ambiguity retains candidate reporter names and
no normalized identity. Short/Id./supra/reference mentions remain unresolved.
Law/journal/unknown formats remain unsupported rather than authority verdicts.

A narrow numeric-reporter heuristic retains additional candidates, including
split-line/page formats Eyecite misses. It can produce false positives and miss
other formats. This limitation is explicit in the result and API. No heuristic
candidate is treated as a verified authority or resolved short reference.
Input is bounded to 100,000 characters; the first 200 ordered occurrences are
retained, with the total detected count and explicit truncation when more exist.

`runner.py` uses persisted paragraph IDs supplied to the contained stage worker.
It anchors the occurrence start, preserves original page/offsets and records
cross-segment/page warnings instead of pretending a spanning citation belongs
entirely to one paragraph/page. The parent revalidates exact slices, ownership,
anchors and warnings before one atomic stage write. Parser records contain no
authority ID and keep verification `not_run`.

Nonzero extraction is `partial`, with all authority checks unavailable and zero
evaluated checks. Zero detections is `skipped` only for detected supported formats,
with the incomplete-coverage caveat. Neither outcome establishes a clean filing.
Local privacy/court checks remain independent. No provider request or score is
produced. Eyecite's heavy imports run only in the citation worker.

`GET /api/v1/analyses/{id}/citations` is opt-in and owner/expiry scoped. It returns
up to 200 original locations, extraction metadata, stage coverage and masked raw
text. Full-snapshot masking prevents clipped identifiers evading detection; a
changed display omits normalized text. Heuristic masking is not complete redaction.
Reruns have fresh IDs; deletion cascades citation rows.

## Available verification components and integration boundary

T033-T035 implement the CourtListener adapter, opinion retrieval, authority
construction and analysis-scoped lookup deduplication. `verify_citations_for_analysis`
preserves occurrences and links repeats to shared authorities; `verified_citation_stage`
constructs extraction/verification results. Adapter/service and persistence/API
tests pass locally with fake responses. See
[[apps/api/src/filingguard/integrations/courtlistener/README]].

Normal registration selects `verified_citation_stage` only when source verification
is explicitly enabled; otherwise extraction remains local. The parent passes the
CourtListener credential only through that worker's private stdin. Partial source
outcomes now retain accurate coverage and retrieval receipts through parent
validation and atomic persistence. Unsupported/short/ambiguous local formats are
not sent as authority queries. Original occurrences and limits stay inspectable.
Distinct authority queries are capped at 25 independently of normalized aliases;
source snapshots and finding-detail snapshots each have a 6 MiB JSON budget.
Missing budgeted source text becomes unavailable, never a clipped complete opinion.
See [[docs/issues/BUG-012 - Citation verification output conflicts with worker validation]]
and [[docs/sessions/2026-10-10 - Grounded review verification]].
Live provider and hosted PostgreSQL checks remain pending. Recognized reporter
syntax does not establish that a case exists; database absence does not prove fabrication.

See [[apps/api/src/filingguard/modules/analyses/README]],
[[apps/api/src/filingguard/db/models/README]], [[contracts/README]] and
[[docs/decisions/ADR-009 - Local citation occurrences before source verification]].

Primary parser references:
[Eyecite API](https://freelawproject.github.io/eyecite/find.html),
[Eyecite models](https://github.com/freelawproject/eyecite/blob/main/eyecite/models.py).
Local behavior is verified against the installed locked version, not inferred from
the current upstream branch. Test outcomes are in the session handoff.
