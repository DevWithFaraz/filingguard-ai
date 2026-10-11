# Curated pre-filing review fixture

Tasks: [[TODO#P0 / 3. Demo fixtures and public-access controls|T014-T016]].
This is an invented teaching filing, NOT a real case or court submission. It
deliberately combines unrelated subjects to isolate verification behaviors.

## Contents and provenance

- `filing.txt` and `filing.pdf`: the same fictional words; line/page offsets differ.
- `pdf-extraction.json`: canonical extracted PDF text, page offsets and hashes.
- `sources.json`: three public opinion snapshots, original URLs, retrieval times,
  IDs, SHA-256, attribution and text-conversion method. Original HTML is retained
  where CourtListener supplies HTML rather than plain text.
- `scenarios.json`: authored scenario definitions, not engine output.
- `expectations.json`: generated exact filing/source spans and proposed outcomes.
- `manifest.json`: content identity, explicit provenance and pending review status.
- `review.json`: versioned delegated-assistant review receipt, artifact hashes and
  five conditional judgments. Not human approval or executed engine results.

Brown (347 U.S. 483), Miranda (384 U.S. 436) and Obergefell (576 U.S. 644) resolved
through authenticated citation lookups during preparation. That observation does
not make a later live result verified. Snapshot material is cached public evidence;
the filing, identifiers, facts and demo court are synthetic. Combined opinions
contain dissents and syllabus text. The draft expectations select majority text;
retrieval must not treat an arbitrary match in a dissent as the Court's holding.

The invented 999 U.S. 999 citation is an offline not-found scenario, not an observed
live search result. Forced timeouts and absent text are explicit simulations.
No real court rule is asserted; the implemented synthetic profile is a teaching rule.
Private curated-demo runs use these exact hash-bound opinion snapshots for fresh
feature execution. Receipt method is cached-public-source-v1; source provenance
is cached_public. Semantic classifications require the opted-in provider, never
expectation replay. See [[docs/decisions/ADR-012 - Exact sample source replay with fresh findings]].

## Planted issues and controls

Eighteen scenarios cover three resolved authorities, an invented unresolved
authority, three proposed supported claims, a reversed Brown proposition, exact
and altered quotations, SSN-shaped/birth-date/account identifiers, a benign event
date, AI disclosure missing/inapplicable cases, missing source and provider timeout.
The SSN-shaped value is deliberately in an invalid issuance range, not a real SSN.
Exact versus altered quotation is a string fact. Semantic labels and fuzzy-match
thresholds need separate review and engine validation.

All spans are half-open Unicode-code-point intervals into the specific snapshot,
not normalized text or browser UTF-16 indexes. PDF extraction has a separate offset
space. Do not reuse paste-text spans against PDF text; T020 must map them correctly.

## Review and reproduction

User-delegated AI review is complete: [[docs/product/Demo fixture review]] records
judgments, five conditions and artifact hashes. T016's read-only demo adapter now
uses review.json to represent that provenance. Neither authoring expectations
nor passing integrity tests supplies human semantic review.
The reviewed artifact files retain their historical preparation wording and exact
hashes. Current status belongs here: October 11 local engines and genuine-model
review-to-export/reset acceptance pass against the synthetic fixture. Human/expert
semantic ground truth remains pending. Runtime source replay and the synthetic
profile are implemented; expectations are never replayed as executed findings.
This multi-authority fixture is not admitted by the legacy human-reviewed
singular-source replay loader. The
GET /api/v1/demos/curated-v1?mode=demo endpoint exposes reviewed expectations with
execution_status=not_run, all conditions and selected source passages. No public
live intake is enabled. Regeneration changes reviewed byte hashes and invalidates
admission; review relevant changes before deliberately replacing receipt hashes.

From root, regenerate draft spans/hashes with:
`node scripts/api.mjs run python ../../scripts/lock_demo_fixture.py`.
This deliberately resets status to awaiting human review. Build PDF using
`scripts/build_demo_pdf.py` with the bundled Python/ReportLab runtime; ReportLab
is not an API runtime dependency. Run the fixture tests with
`node scripts/api.mjs run pytest tests/unit/test_curated_demo.py`.

Re-fetching `apps/api/scripts/fetch_demo_sources.py` is an explicit network action
using the ignored token, not part of CI. It changes snapshots/timestamps; re-lock,
review and rerun tests after it. Selection rejects dissent-only types; this narrow
prep tool is not the future production authority-selection adapter.

[[data/demo/README]], [[docs/research/Provider access verification]],
[[docs/issues/BUG-004 - First opinion reference can be a dissent]].
