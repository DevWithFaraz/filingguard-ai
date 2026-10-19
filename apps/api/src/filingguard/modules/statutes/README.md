# statutes

Priority: P2. Task: T202 in the root TODO.md.

Verify statute and regulation citations separately from case authorities.

Law citations in; jurisdiction, version/effective-date evidence, and explicit
unavailable/not-found coverage out.

## Implemented (T202)

`service.py` reuses local Eyecite `FullLawCitation` occurrences (`kind=law`) and a
narrow U.S.C./C.F.R. heuristic for strings the parser missed. Journals, unknown
reporters, short forms, and case citations are not treated as statutes.

`adapter.py` provides a catalog adapter and an HTTP adapter. Timeout, 429, 5xx,
network failure, and non-200 responses (including HTTP 404 of the lookup route)
are **unavailable**. Not-found is returned only from a 200 body with
`found: false` or a catalog miss. Not-found is not fabrication.

`runner.py` is a review stage. No law citations is `skipped` with zero eligible
checks. Law citations with no configured source (`STATUTE_SOURCE_URL` unset, the
default) is `unavailable` with a reason, not skipped-as-pass.
Lookups store jurisdiction, version, effective date, and coverage limits on
evidence metadata. Findings reuse `FindingType.CITATION` (`type=citation`,
`stage=statutes`). Case CourtListener verification is unchanged: law/journal
kinds stay `unsupported` and are never sent as case authority queries.

## Not verified / not implemented

- No live statute provider (GovInfo, LII, state codes) is enabled in production.
  Tests use fake HTTP and an in-memory catalog only.
- No Neon finding-type migration; statute findings reuse `citation`.
- State-code parsing beyond Eyecite law citations is incomplete.
- Live statute HTTP is off unless `STATUTE_SOURCE_URL` is set; filings that cite
  statutes then report the statutes stage as unavailable rather than a pass.
- Expert legal quality of version/effective-date matching is not evaluated.

See [[TODO]] T202, [[FilingGuard_AI_SRS]] FR-047, and
[[apps/api/src/filingguard/modules/citations/README]].
