# table_of_authorities

Priority: P2. Task: T201 in the root TODO.md.

Compare normalized authority entries in the table and filing body.

Parsed document in; missing/extra authorities, listed page references, and
explicit no-table coverage out.

## Implemented audit (T201)

`service.py` looks for a standalone heading (`TABLE OF AUTHORITIES`,
`TABLE OF CASES`, or `INDEX OF AUTHORITIES`) near the start of the filing and
ends the section at a later known heading such as `ARGUMENT`. Uncertain bounds
do not invent a table. Comparable Eyecite identities (full cases, laws, journals,
and reporter candidates) are deduplicated and compared both ways. Short forms,
Id., and supra mentions are excluded. Leader dots or wide spacing before trailing
arabic page numbers are recorded when present.

`runner.py` is a local review stage. No table is `skipped` with zero eligible
checks, not a pass. Missing body authorities are medium findings; extra table
entries and non-overlapping listed pages are low findings. Scores remain
provisional. This is a document-consistency signal, not a court-rule or legal
sufficiency determination.

See [[TODO]] T201, [[FilingGuard_AI_SRS]] FR-280 through FR-284, and
[[docs/sessions/2026-10-19 - Table of Authorities audit]].
