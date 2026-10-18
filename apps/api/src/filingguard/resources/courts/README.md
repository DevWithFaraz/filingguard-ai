# Court profiles

T028 defines a validated JSON format including court/judge scope, source URL,
verified/effective dates and profile version. The starter synthetic profile below
is a draft fixture contract, not a statement of real court rules. Real profiles
need checked primary sources. Stale/unsupported profiles cannot produce passes.

`reference-only/` holds versioned primary-source research records for possible
future profiles. `court_rules/source_registry.py` validates those records, but
they are deliberately not runtime profiles: live intake still accepts only
`unverified`, and the evaluation result remains unavailable. A source record must
not be promoted merely because its official URL is reachable. Confirm its current
force, exact court/judge and case scope, and every machine-checkable requirement
first. See [[docs/decisions/ADR-014 - Filing-centric court rules and separate Article 50 direction]].
