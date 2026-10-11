# court_rules

Priority: P0. Tasks: T028-T029 in the root TODO.md.

Load validated profiles and evaluate applicable disclosure checks.

Selected versioned profile and AI-use setting in; rule findings and applicability limits out.

`profiles/synthetic-demo-v1.json` is strictly parsed by `service.py` with an
explicit training source, effective period, fictional court, nullable judge scope
and demo-only flag. Unsupported, expired or wrong-mode profiles are unavailable;
`unverified` never passes a live court check. No real court profile is asserted.

The disclosure evaluator checks the AI-used flag and a standalone heading only.
Presence is not content adequacy or legal sufficiency. Missing synthetic disclosure
produces a rule finding with versioned rule evidence; the stage state shows the
triggering training requirement and uncertainty. API/browser tests cover this
through the hash-bound curated demo. See [[TODO]] T028-T029 and
[[docs/sessions/2026-10-01 - Local review pipeline]].
