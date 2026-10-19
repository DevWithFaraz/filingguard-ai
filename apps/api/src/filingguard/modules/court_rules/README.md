# court_rules

Priority: P0 / Phase B. Tasks: T028-T029, T106, T205 in the root TODO.md.

Load validated profiles and evaluate applicable disclosure, optional page-limit
and extra heading checks.

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

Optional `page_limit` and `required_headings` fields are evaluated only when
present on the selected in-scope profile. Page limits need extracted page
boundaries; unknown length is an unavailable limitation, never a pass. Extra
headings reuse standalone-line matching and first-page/anywhere placement.
N.D. Tex. LR 7.2(c) length limits are not activated: they depend on filing type
(principal brief 25 pages, reply 10, other local rules such as LR 56.5) which
this evaluator does not receive. The live profile therefore keeps formatting
fields absent rather than claiming a nationwide or even district-wide page check.

Optional `privacy_policy` bindings carry a versioned policy id, source URL and
checked date. The privacy catalog applies extra identifier kinds only when the
id/version/source are known and current.

The disclosure evaluator checks the AI-used flag and standalone heading presence.
Placement rules support `first_page` and `anywhere`:
- For `first_page` rules with paginated documents, the evaluator inspects the
  first page; finding the heading on a subsequent page flags the placement error.
- Unpaginated plain text submissions verify presence while explicitly recording
  the absence of page boundaries.
- Automated heading detection is not content adequacy, legal sufficiency, or
  compliance certification. Independent human review is always required. Missing
  disclosures produce versioned rule findings and evidence records. See [[TODO]]
  T028-T029, T106, T205 and
  [[docs/sessions/2026-10-19 - Advanced formatting and jurisdictional privacy]].
