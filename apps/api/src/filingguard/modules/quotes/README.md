# quotes

Priority: P0. Tasks: T042-T044 in the root TODO.md.

Associate quotations with authorities; exact, normalized, then fuzzy comparison.

Quotes/source text in; status, closest passage, offsets and similarity out. Similarity is not legal support.

Implemented locally: `service.py` extracts straight/curly delimited quotations and
explicitly heuristic indented/Markdown blocks, preserves original Unicode spans,
and associates sentence-local nearby citations. Quote-forensics-v2 also accepts
one preceding cited sentence with an explicit `The Court stated:` attribution
(held/explained/said/wrote/observed variants), within the existing 300-character
and paragraph/page limits. Extra intervening sentences remain unassociated.
Distinct nearby authorities remain
ambiguous; no arbitrary authority is selected. Apostrophes and unmatched delimiters
are not treated as quotation pairs.

`compare_quote` runs exact, case/whitespace/punctuation-normalized and RapidFuzz
partial alignment in order. Normalization retains a map to original source code
points, including casefold expansions. A fuzzy score of at least 0.85 is labeled
close; lower scores remain not found and may retain the closest inspected passage.
Closest passages and scores represent string
similarity only. Meaning alterations (FR-127) are explicitly inspected in `check_meaning_alteration`:
negations added or omitted, modal obligation shifts (e.g. shall/must versus may),
omitted qualifying clauses preceding ellipses, and contradictory antonyms escalate
finding severity to `critical` or `high` with structured `meaning_alteration` metadata.
Semantic equivalence and legal support are never inferred. Short unmatched quotations
do not receive unreliable fuzzy scores. Missing/invalid provenance or bounded-resource
failures remain source unavailable, distinct from a searched source with no match.

`quotes_stage(analysis, budget)` consumes the canonical document snapshot and detached
owner-scoped `review_segments`, `review_citations`, `review_authorities`. It produces
Quote, Finding and document/source EvidenceRecord rows with validated SHA-256 hashes,
original excerpts/offsets, source URL/retrieval identity and method version. It makes
no provider requests. Source provenance is validated before asserting comparison
outcomes. Finding descriptions preserve association uncertainty and matching limits.
CourtListener's `courtlistener_api_v4` transport label maps to evidence provenance
`live`; the provider label remains separate metadata, with a regression control.

Limits: first 50 quotations, 2,000 characters per comparison quote, 500,000 per
source, and 4 MiB cumulative evidence snapshot bytes. Unprocessed occurrences remain
pending with truncated coverage; unavailable sources remain unavailable. Supported
formats are heuristic, so absence of detected quotes is skipped, not a document-wide
certification. IPC/persistence/API integration is owned by the analysis orchestrator.

Verification: `tests/unit/test_quotes.py` covers original Unicode spans, smart quotes,
block controls, exact/normalized/altered/ellipses outcomes, missing source/provenance,
distinct authority ambiguity, unrelated sentences, source offsets and bounded coverage.
Integration/hosted/provider checks are separate acceptance evidence in [[TODO]].

Related: [[FilingGuard_AI_SRS#9.7 Quote Forensics]],
[[apps/api/src/filingguard/modules/evidence/README]],
[[apps/api/src/filingguard/modules/analyses/README]].
