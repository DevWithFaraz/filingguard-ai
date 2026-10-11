# privacy

Priority: P0. Tasks: T022, T030-T031 in the root TODO.md.

Detect sensitive patterns locally and provide masked review findings.

Original segments in; detections, severity and redacted provider excerpts with offset mappings out.

Implemented boundary milestone: `mask_excerpt` detects SSN, email, US phone,
contextual account/routing/card numbers and labelled birth dates locally. It detects
against the full filing before clipping an excerpt, so cut identifiers are still
masked. ASCII stars preserve Unicode-code-point length and original spans.
Names/contextual identifiers may be missed and benign matches remain possible.
This is not legal redaction compliance or a promise all private data is removed.

`checks.py` now emits SSN-shaped, contextual financial-account and valid full-DOB
signals with severity and masked context. The local review stage saves owner-scoped
findings with a human-redaction-review recommendation and exact private evidence;
the HTTP findings projection never returns raw evidence. Benign citation/date
controls and the curated fixture are tested. Detection is not legal compliance.

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
