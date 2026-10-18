---
type: session
status: verified
date: 2026-10-17
tags: [sessions, reports, pdf, export, phase-b, verification]
---
# PDF report export implementation

## Task and scope
User authorized starting the next task: [[TODO]] `T104` (PDF report export: `FR-305`).
The requirements specify:
1. Select a production-grade renderer (`ReportLab 5.0.1` selected and locked).
2. Embed readable evidence: analysis metadata, integrity score deductions, category breakdown, stage coverage, forensic findings with 5-hop visual lineage chains, exact retrieved source authority passages with SHA-256 digests, and citation verification records.
3. Professional pagination with running header (Page 2+) and running footer with dynamic two-pass page numbers (`Page X of Y`) via `NumberedCanvas`, plus prominent statutory disclaimers.
4. Ensure long findings, descriptions, and code spans wrap naturally without clipping across multiple pages within a 504 pt printable width (0.75-inch margins).
5. Add PDF download support in API (`GET /api/v1/analyses/{id}/report?format=pdf`), frontend API client (`downloadReport(id, 'pdf')`), and frontend UI button in `ResultsView.tsx`.

## Changes
- **Dependency management (`apps/api/`):**
  - Added `reportlab>=5.0.1` and `pillow>=11.1.0` to `apps/api/pyproject.toml`.
  - Locked dependencies via `uv lock` in `apps/api/uv.lock`.
- **PDF Engine (`apps/api/src/filingguard/modules/reports/pdf_generator.py`):**
  - Implemented `generate_pdf_report(results: dict[str, Any]) -> bytes` using ReportLab Platypus.
  - Implemented `NumberedCanvas(canvas.Canvas)` two-pass canvas pattern capturing total page count and drawing running headers on Page 2+ and dynamic `Page X of Y` footers with statutory notices on every page.
  - Formatted executive summary metadata table, legal assurance disclaimer callout, integrity scores, category breakdowns, stage coverage, findings with 5-hop visual lineage chain (Document Span -> Extraction Target -> Source Authority -> Verification Method -> Finding Verdict), retrieved source passages, and citation verification tables.
  - Sanitized untrusted text using `html.escape()` to avoid XML parsing exceptions in Platypus Paragraphs.
- **Service & Route integration (`apps/api/`):**
  - Updated `render_report(results, format="markdown" | "html" | "pdf")` in `modules/reports/service.py`.
  - Updated `review_report` endpoint in `api/routes/intake.py` to accept `format: Literal["markdown", "html", "pdf"] = "markdown"` and return `application/pdf` with `.pdf` attachment filename.
  - Documented PDF export in canonical module note `apps/api/src/filingguard/modules/reports/README.md`.
- **Contracts & Schema Synchronization (`contracts/`, `apps/web/`):**
  - Exported updated OpenAPI specification (`npm run contracts:export`) updating `contracts/openapi.json`.
  - Regenerated TypeScript schema definitions (`npm run contracts:generate`) updating `apps/web/src/lib/api/schema.d.ts`.
- **Frontend client & UI (`apps/web/`):**
  - Updated `downloadReport(id, format: 'markdown' | 'html' | 'pdf')` in `apps/web/src/lib/api/results.ts`.
  - Added `<button className="secondary-button" onClick={() => report.mutate('pdf')}>Download PDF</button>` to `ResultsView.tsx`.
- **Verification & Tests:**
  - Authored unit tests in `apps/api/tests/unit/test_review_reports.py`:
    - `test_render_report_pdf_valid_bytes_and_structure`
    - `test_render_report_pdf_handles_long_finding_wrapping_and_multipage`
    - `test_pdf_escapes_xml_and_untrusted_markup`
  - Added integration test assertion in `apps/api/tests/integration/test_review_results.py` validating `GET /report?format=pdf` response headers, content type `application/pdf`, and non-empty byte payload.

## Verification
- `uv --directory apps/api run --locked pytest tests/unit/test_review_reports.py tests/integration/test_review_results.py` — 21 passed.
- `uv --directory apps/api run --locked pytest` — 740 passed, 2 skipped (Windows host).
- `uv --directory apps/api run --locked ruff check .` — passed (0 errors).
- `npm run test:web` — passed (47 passed across 7 test files).
- `npm run lint:web` — passed (ESLint exited 0).
- `npm run typecheck` — passed (`tsc --noEmit` exited 0).
- `npm run build` — passed (Vite production bundle built cleanly).

## Blockers and next step
No blockers. T104 is verified and marked complete in [[TODO]].
Next task in [[TODO]] under Phase B:
- `T105` - Graph polish (`FR-105/106`), multiple claims per authority (`FR-064`) and score-category filters (`FR-186`): pan/zoom/fit, unsupported nodes and cross-view selection preserving correct finding context.

## Related
[[TODO]] `T101`, `T102`, `T103`, `T104`, `T105`, `T212`, `T213`;
[[FilingGuard_AI_SRS]];
[[docs/product/FilingGuard product direction]];
[[apps/api/src/filingguard/modules/reports/README]];
[[apps/web/src/features/analyses/ResultsView]].

[[docs/sessions/Index]] | [[TODO]]
