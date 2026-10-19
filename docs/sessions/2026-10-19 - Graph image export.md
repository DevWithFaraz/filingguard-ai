---
type: session
status: in-progress
date: 2026-10-19
tags: [sessions]
---
# Graph image export

## Task and scope
T207 (FR-107/FR-306): export the saved Claim-Authority Graph as a readable report
image with an accessible equivalent. TODO.md was not updated, per the request.

## Changes
Reports now build SVG (and PNG) from `saved_graph()` nodes/edges, including
wrapped labels, stored verification/support statuses, and a disclaimer that the
figure is a review graph, not a legal conclusion. Long graphs split across
pages instead of clipping.

Markdown/HTML/PDF reports embed that image plus a node/relationship list.
`GET /analyses/{id}/report?format=graph-svg|graph-png` downloads the same
image. The results graph toolbar **Download graph** requests `graph-svg`.

## Verification
- `uv run ruff check` on reports/export files: passed
- `uv run pytest tests/unit/test_review_reports.py`: 19 passed
- `vitest run src/features/analyses/results.test.tsx`: 18 passed
- `vitest run src/features/analyses/accessibility.test.tsx`: 10 passed

Not run: full API integration suite, Playwright e2e, hosted/browser screenshot
readability, screen-reader review of the exported HTML figure.

## Blockers and next step
Next: mark T207 complete in TODO.md after product/visual review of a real
export. PNG text depends on a system TTF (Arial/DejaVu); SVG/PDF do not.

## Related
[[apps/api/src/filingguard/modules/reports/README]]
[[apps/web/src/features/reports/README]]
[[apps/web/src/features/analyses/README]]
[[docs/sessions/Index]] | [[TODO]]
