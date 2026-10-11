---
type: decision
status: accepted
date: 2026-10-10
tags: [decisions, demo, provenance]
---
# Exact sample source replay with fresh findings

## Context
T016/T052 need cached public opinions in the executable curated journey.
Delegated-assistant review supports controlled development, not human-reviewed
classification replay. The legacy `demo.py` human-review gate remains distinct.

## Decision and alternatives
`demo_sources.py` admits explicit demo mode, curated-v1 identity, exact filing
text/hash and reviewed artifact/source hashes. It adapts the three retained public
opinions to the normal citation engine without initializing an HTTP client.
Extraction, claims, quotes, rules and privacy run fresh. No expectation status
is copied into a finding or model response. Unknown queries remain unavailable;
unsupported parser occurrences stay unverified. Live mode never falls back here.

Receipts use `cached-public-source-v1`; opinion evidence uses `cached_public`.
UI/reports disclose this mode. Genuine semantic review requires provider opt-in
and passes normal v3 evidence checks. Preview defaults to no provider calls;
`--live-semantic` uses the selected free-credit model, at most five attempts per
analysis, no source HTTP requests, retries or paid fallback. Reset deletes saved
private analysis outputs. Court and AI-use selections are explicit.

## Consequences
Cache admission validates retained source identity, not current law or expert
correctness. Changed material fails closed and needs re-review. Missing providers
remain visible. Legacy human-reviewed result replay remains disabled.
Expert legal, physical-device and hosted acceptance remain separate gates.

## Evidence and verification
Source-admission, contained API and desktop/mobile checks exercise altered input,
unknown IDs, source tampering, live separation, exact hashes, quote outcomes,
stored views/exports, choices, ownership and reset/deletion. Outcomes:
[[docs/sessions/2026-10-10 - Curated demo acceptance]].

## Related
[[TODO]] | [[docs/decisions/ADR-005 - Product continuation and reviewed demo]]
[[apps/api/src/filingguard/modules/analyses/README]] | [[data/demo/curated-v1/README]]
[[docs/decisions/Index]]
