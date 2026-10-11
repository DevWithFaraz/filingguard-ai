# claims

Priority: P0. Tasks: T037 in the root TODO.md.

Extract propositions near citations and keep verbatim context and links.

Segments/citations in; claims and claim-authority relationships out. Never lose source locations.

Local extraction is implemented in `service.py` and `runner.py`. `claims_stage`
reads the immutable document snapshot, persisted review segments and citation
occurrences supplied by the parent worker. It retains the verbatim candidate
sentence, a preceding sentence for citation-only signals, or a conservative
paragraph/cross-segment fallback. Case/reporters/Id. abbreviations and recognized
citation spans protect sentence boundaries. This heuristic does not paraphrase
propositions, infer short-reference authorities, or judge legal support.

Identical contexts produce one Claim with a separate ClaimAuthorityLink for every
citation occurrence, including unresolved authorities. Every link starts `not_run`.
The document EvidenceRecord retains the exact snapshot/hash, Unicode-code-point
offsets, paragraph/page anchor, citation IDs, context kind and `claims-context-v1`
method version. Confidence stays unknown; extracting a claim is not verification.

Output is bounded to 100 contexts, 200 occurrence links and 6 MiB of JSON-encoded
document snapshots. The context cap contracts for large Unicode filings so
immutable evidence copies stay within the contained worker output budget. Coverage counts the
citation occurrences associated with contexts. Omitted contexts and upstream
extraction truncation remain explicitly unavailable/partial. Absent failed-upstream
input is unavailable; a known no-detection upstream skip is skipped with limits.

Focused synthetic unit tests cover Unicode, sentence/paragraph/page anchors,
multiple links, unresolved short references, citation-only context, abbreviation
controls, cross-segment spans, truncation and tampered provenance. Pipeline and
private API integration checks are owned by
[[apps/api/src/filingguard/modules/analyses/README]]. No provider is called here.

Related: [[TODO]] (T037), [[FilingGuard_AI_SRS#9.4 Claim Extraction]],
[[docs/decisions/ADR-004 - Truthful contracts and scoped evidence]],
[[docs/decisions/ADR-009 - Local citation occurrences before source verification]],
[[apps/api/src/filingguard/modules/citations/README]],
[[apps/api/src/filingguard/modules/evidence/README]].
