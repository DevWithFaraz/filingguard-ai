# court_rules

Priority: P0 / Phase B. Tasks: T028-T029, T106 in the root TODO.md.

Load validated profiles and evaluate applicable disclosure checks.

Selected versioned profile and AI-use setting in; rule findings and applicability limits out.

`profiles/synthetic-demo-v1.json` is strictly parsed by `service.py` with an
explicit training source, effective period, fictional court, nullable judge scope
and demo-only flag. Unsupported, expired or wrong-mode profiles are unavailable;
`unverified` never passes a live court check.

`profiles/us-txnd-lr7-2f-v1.json` is the verified real court profile for the
U.S. District Court for the Northern District of Texas, Local Civil Rule 7.2(f)
(adopted via Special Order 2-98, effective September 3, 2024). It applies to live
filings (`is_demo: false`) and requires a separate heading on page one titled
`Use of Generative Artificial Intelligence` when Generative AI was used.

`source_registry.py` separately validates versioned `reference-only` primary-source
records. They support traceable maintenance research but cannot be loaded by
`load_profile`, selected for a live filing, or produce a pass. This distinction is
intentional: an order can be judge-specific, have an unconfirmed current status, or
require more than the evaluator's heading check can establish.

The disclosure evaluator checks the AI-used flag and standalone heading presence.
Placement rules support `first_page` and `anywhere`:
- For `first_page` rules with paginated documents, the evaluator inspects the
  first page; finding the heading on a subsequent page flags the placement error.
- Unpaginated plain text submissions verify presence while explicitly recording
  the absence of page boundaries.
- Automated heading detection is not content adequacy, legal sufficiency, or
  compliance certification. Independent human review is always required. Missing
  disclosures produce versioned rule findings and evidence records. See [[TODO]]
  T028-T029, T106 and [[docs/sessions/2026-10-18 - Additional verified real court profiles]].
