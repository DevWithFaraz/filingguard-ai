---
type: issue
status: resolved
date: 2026-10-11
tags: [issues, privacy]
---
# Email before sentence punctuation escapes masking

The actual outgoing batch-payload control revealed that `test@example.com.` was
not masked. The email pattern's final negative lookahead forbade a dot even when
it was sentence punctuation followed by whitespace/end. This could leave a common
identifier shape in an outgoing proposition. No confidential filing or observed
production disclosure is claimed; the reproduction uses a synthetic address.

The final lookahead now distinguishes sentence punctuation from an additional
domain component. Detection still scans the whole original filing before clipping;
masking preserves Unicode code-point length. Seven punctuation/domain suffix
controls and clipped-address checks pass. The batch test verifies the assembled
transport request excludes the original address while retaining source text.
The combined adapter/batch/proposition/document checks pass 84 tests.

This repairs a specific pattern, not a guarantee that all private data is found.
Related: [[TODO]] T022/T031/T054/T056,
[[apps/api/src/filingguard/modules/privacy/README]],
[[docs/decisions/ADR-013 - Shared authority model requests and bounded quota admission]],
[[docs/sessions/2026-10-11 - Accessibility performance and release gates]],
[[docs/issues/Index]].
