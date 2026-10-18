---
type: session
status: verified
date: 2026-10-18
tags: [sessions, accessibility, retention, observability, timing, correlation, phase-b, verification]
---
# Accessibility retention and observability implementation

## Task and scope
Following task status in [[TODO]], addressed capability `T110`:
Expand accessibility (`UX-005`), audit timing/correlation (`LOG-003/004`, `NFR-023`), retention automation (`NFR-044`), and failure observability (`NFR-063`).

Requirements:
1. `UX-005`: Ensure loading and progress states are accessible to assistive technologies using polite live announcements (`role="status"`, `aria-live="polite"`).
2. `LOG-003` & `NFR-023`: Log operational events, errors, and unhandled failures with correlation IDs (`correlation_id=analysis_id`) without leaking filing content, excerpts, or provider payloads.
3. `LOG-004`: Log module-level execution timing (`duration_ms`) for all stage executions and total review execution duration.
4. `NFR-044`: Automate retention cleanup by adding repository batch purging for expired documents and analyses (`purge_all_expired`).
5. `NFR-063`: Add automated tests verifying these capabilities pass cleanly.

## Changes
- **Accessibility Announcements (`UX-005`):**
  - Updated `PreparedView.tsx`: added polite live status announcements for opening document, polling review status, local review execution, rerun preparation, deletion, and findings loading.
  - Updated `ResultsView.tsx`: added polite announcements (`role="status"`, `aria-live="polite"`) for results loading, claim graph computation, report downloads, graph node selection detail, finding evidence loading, and filter match counts.
  - Updated `ActivityView.tsx`: added polite announcements for session recovery and capability checking.
  - Updated `DemoReview.tsx`: added polite live status for curated sample loading.
  - Updated `IntakeComposer.tsx`: added polite announcements for document preparation and capability availability status/retry.
  - Updated `FindingQA.tsx`: added polite live status while fetching prior Q&A history and answering questions.
  - Updated `RedTeamPanel.tsx`: added polite announcements while retrieving and synthesizing red-team attack theories.
  - Updated `WorkspaceInfo.tsx` and `PipelineWalkthrough.tsx`: added polite live announcements for service availability and film status.
  - Updated `App.tsx` and `HomePage.tsx`: added polite status announcements on backend health/connection state indicators.
- **Correlation ID & Duration Telemetry (`LOG-003`, `LOG-004`, `NFR-023`):**
  - Updated `ReviewOrchestrator` (`apps/api/src/filingguard/modules/analyses/orchestrator.py`):
    - Added `correlation_id={analysis_id}` to all operational log messages (`review.job.start`, `review.stage.start`, `review.stage.finish`, `review.stage.persist_failed`, `review.submit_failed`, `review.job.finish`).
    - Added stage execution timing (`duration_ms=%d`) across all completed and failed stages.
    - Added total review job duration (`duration_ms=%d`) at job completion.
  - Updated API Routes (`apps/api/src/filingguard/api/routes/intake.py`):
    - Added correlation-tagged operational logs for `analysis.prepared`, `review.queued`, `analysis.rerun`, `analysis.deleted`, and failure routes (`review.queue_failed`, `analysis.rerun_failed`, `analysis.delete_failed`, `finding_qa.failed`, `red_team.failed`).
  - Updated Error Boundary Middleware (`apps/api/src/filingguard/api/errors.py`):
    - Added correlation ID extraction from `X-Correlation-ID` header, `analysis_id` query parameter, or UUID URL path parts to correlate unhandled exceptions with `correlation_id={analysis_id}` while preserving zero filing content leakage.
- **Retention Batch Purging (`NFR-044`):**
  - Implemented `AnalysisRepository.purge_all_expired(now=None, *, delete_file=None, batch_size=100, failed_ids_out=None) -> int` in `apps/api/src/filingguard/db/repository.py`:
    - Enforces timezone awareness on datetime inputs.
    - Locks batch rows with `with_for_update(skip_locked=True)` in bounded transactions.
    - Deletes stored physical files via `delete_file` before committing DB row deletion.
    - Ensures batches continue processing subsequent valid expired records even when an entire preceding batch encounters file deletion errors, without premature loop termination.
    - Automatically rolls back database operations if file deletion fails, avoiding orphaned files or inconsistent records.
  - Implemented `AnalysisLifecycle.purge_all_expired(now=None, *, batch_size=100) -> CleanupResult` in `apps/api/src/filingguard/modules/analyses/lifecycle.py`:
    - Accurately tracks retention failures in `CleanupResult.failures`.
    - Logs retention events (`retention.create_pdf`, `retention.delete`, `retention.purge_all_expired`).
- **Tests & Verification (`NFR-063`):**
  - Created [`apps/api/tests/unit/test_retention_and_observability.py`](file:///c:/Users/IT/Documents/FilingGuard%20AI/apps/api/tests/unit/test_retention_and_observability.py):
    - 11 unit tests covering batch purging, failure batch continuation, orphan protection, storage failure resilience, lifecycle failure counting, correlation ID emission, stage timing, header/query correlation extraction, and zero private content leakage in telemetry.
  - Created [`apps/web/src/features/analyses/accessibility.test.tsx`](file:///c:/Users/IT/Documents/FilingGuard%20AI/apps/web/src/features/analyses/accessibility.test.tsx):
    - 10 unit tests verifying `role="status"` and `aria-live="polite"` presence and messaging across all core view components.
- **Documentation:**
  - Updated canonical module guide [`apps/api/src/filingguard/modules/analyses/README.md`](file:///c:/Users/IT/Documents/FilingGuard%20AI/apps/api/src/filingguard/modules/analyses/README.md).
  - Updated checklist and work log in [[TODO]].

## Verification
- `npm run lint:api` (`ruff check .`) — passed (0 errors).
- `npm run lint:web` (`eslint .`) — passed (0 errors).
- `npm run typecheck` (`tsc --noEmit`) — passed (0 errors).
- `npm run test:web` (`vitest run`) — 8 passed test files, 62 passed tests (0 failures).
- `npm run test:api` (`pytest`) — 764 passed, 2 skipped (0 failures).

## Next step
`T110` is verified and checked off in [[TODO]].
Remaining Phase B tasks:
- `T106` - Additional verified real court profiles (`FR-146`): select target court filing context, verify primary sources and effective dates per ADR-014.
- `T109` - Durable job execution if multi-worker concurrency is required.
