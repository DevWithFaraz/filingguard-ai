# documents

Priority: P0. Tasks: T019-T022 in the root TODO.md.

Parse text/PDF and preserve page/paragraph spans. Handle missing/poor text and limits.

Original bytes/text in; segments and extraction diagnostics out. Keep original offsets separate from normalization.

Implemented and locally verified: Text/PDF extraction, canonical snapshots,
paragraph/page diagnostics and private preparation (T019-T021). Pasted text remains
byte-for-byte UTF-8 equivalent, with no invented page numbers. PDFs join original
per-page extracted strings with form-feed separators. Paragraphs split on blank
lines; PDFs without blank lines can produce a logical page-sized paragraph.
All spans are half-open Unicode code points and revalidated against snapshot hash,
ordering, page coverage and exact substrings before persistence/retrieval.

`service.py` sends a <=10 MiB PDF to a short-lived worker with a 15-second deadline.
The worker has no inherited API/DB secrets, suppresses parser logs and never emits
raw exceptions. POSIX address-space/CPU/core limits are authored; Windows uses a
256 MiB per-process Job Object with two processes for the venv redirector/interpreter,
kill-on-close and timeout tree termination. This is resource containment, not a
filesystem/network privilege sandbox. Windows worker behavior is verified locally;
Linux resource/permission checks remain deployment gates. pypdf is not OCR.

Reject encrypted/no-text/malformed/oversized/over-page/over-character PDFs with safe
paste-text fallback. Mixed blank pages keep positions and warn. Sparse text (<20
non-whitespace characters) and replacement-character density (>2%) warn, without
claiming complete extraction-quality detection. Maximum 2,000 paragraphs.
`detect_parsing_diagnostics` (FR-025) analyzes extracted text for sparse or empty
pages, Unicode replacement characters, fused tokens (>40 characters without whitespace),
and low character density (<40 characters/page), recording diagnostic flags on
`ExtractedDocument` and generating an actionable system finding in `privacy_stage`.

`intake.py` saves a running preparation row, then segments, snapshot and completed
document stage transactionally; final legal status stays not_run. Failures compensate
file writes/creation, restart recovers unfinished preparations as interrupted.
No citation/claim/quote engine, score or external provider request is executed.
GET Activity returns only summaries, while exact original text is owner-scoped.
Court-profile eligibility is checked before a repository or storage access. Live
submissions accept only `unverified`; unsupported IDs remain unavailable rather
than creating an intake record or implying a court-rule pass.

Checks: `tests/unit/test_documents.py`, `tests/unit/test_intake_guard.py`,
`tests/integration/test_intake.py`, `tests/e2e/intake.spec.ts` (real API and browser).
See [[contracts/README]], [[apps/web/src/features/intake/README]],
[[apps/api/src/filingguard/modules/privacy/README]],
[[docs/decisions/ADR-007 - Private preparation boundary]].

October 11 maximum-input measurements: the actual Windows worker accepts a
20-page, exactly 10 MiB synthetic PDF in 1.859 seconds (47,459 extracted characters).
Exactly 100,000 characters / 2,000 paragraphs extract in 0.031 seconds.
One excess page, byte, character or paragraph rejects with the intended safe code.
These are local trusted-fixture measurements, not a guarantee for arbitrary PDFs,
OCR, Linux containment or hosted cold starts. Reproduce with
`scripts/verify_input_limits.py`; [[TODO]] T055 records browser timing evidence.
