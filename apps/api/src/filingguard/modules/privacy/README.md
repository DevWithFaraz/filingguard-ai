# privacy

Priority: P0. Tasks: T022, T030-T031, T205 in the root TODO.md.

Detect sensitive patterns locally and provide masked review findings.

Original segments in; detections, severity and redacted provider excerpts with offset mappings out.

Implemented boundary milestone: `mask_excerpt` detects SSN, email, US phone,
contextual account/routing/card numbers and labelled birth dates locally. It detects
against the full filing before clipping an excerpt, so cut identifiers are still
masked. ASCII stars preserve Unicode-code-point length and original spans.
Names/contextual identifiers may be missed and benign matches remain possible.
This is not legal redaction compliance or a promise all private data is removed.

`checks.py` now emits SSN-shaped, contextual financial-account, valid full-DOB,
and possible unredacted minor-name signals (FR-163 / T108) with severity and masked context.
Minor-name heuristics (`_valid_minor_name`) inspect conventional legal indicators
(e.g., minor child, next friend, guardian ad litem, minor:) while strictly suppressing
false positives: compliant initials under Fed. R. Civ. P. 5.2(a)(3) (e.g. A.B.),
benign non-person usage (minor injuries/delays), case citation party contexts (Minor v. ...),
and institutional/legal entity tokens. The local review stage saves owner-scoped
findings with a high-severity alert, explicit uncertainty disclaimer, and exact private evidence;
the HTTP findings projection never returns raw evidence. Benign citation/date/minor
controls and the curated fixture are tested. Detection is not legal compliance.

T205 adds versioned jurisdictional privacy policy bindings on court profiles
(FR-167). `resolve_privacy_policy` consults a conservative catalog: unknown,
stale, source-mismatched or demo/live-mismatched policies are unavailable and
do not enable extra identifier kinds. Default detectors remain SSN, financial
account, full DOB and possible minor names. The synthetic demo may enable email
findings; the N.D. Tex. profile binds Fed. R. Civ. P. 5.2 as a reminder only
(no extra kinds). This is not nationwide privacy-rule coverage.

T022/T031 integration is implemented: the real semantic adapter masks the full
filing before selecting any outgoing proposition boundary. Fixed-host payload
tests verify detected identifiers never appear in outgoing requests. Original
owner-scoped snapshots remain unchanged;
preparation's local signal count is not a privacy pass or score. See [[TODO]],
[[apps/api/src/filingguard/modules/documents/README]],
[[docs/decisions/ADR-007 - Private preparation boundary]].

T024's `integrations/providers/passages.py` caps and masks filing context before
clipping, preserves code-point mappings and discloses truncation. A fake outgoing
HTTP payload test checks detected identifiers are absent. That verifies the helper
path. The later real adapter integration verifies T022/T031/T038 at the outgoing
request boundary. Future prompt fields still need their own masking review.
See [[apps/api/src/filingguard/integrations/providers/README]].
