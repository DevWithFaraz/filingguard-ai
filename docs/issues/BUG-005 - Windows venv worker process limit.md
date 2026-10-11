---
type: issue
status: resolved
date: 2026-09-28
tags: [issues, windows, extraction]
---
# BUG-005 - Windows venv worker process limit

## Symptom and impact
During local synthetic-PDF testing, the new isolated worker failed even on a valid
fixture. No deployed user data or production incident was involved.

## Reproduction and cause
Windows Python 3.12 venv execution uses a launcher/redirector plus interpreter.
A Job Object limit of one active process rejected normal worker startup. Changing
to a bounded two-process allowance restored the same fixture extraction; this
does not permit an unbounded process tree.

## Fix and regression check
WindowsJob permits two active processes with per-process 256 MiB and kill-on-close.
Close the job before killing/draining the launcher on timeout so the interpreter
cannot retain pipes and block communicate(). Real-worker normal PDF, timeout,
encrypted/no-text/malformed and blank-page tests pass; browser PDF workflow passes.
Regression: `tests/unit/test_documents.py`, `tests/integration/test_intake.py`.
This confirms local Windows behavior, not Linux/hosted containment or a privilege sandbox.

## Related
[[docs/issues/Index]], [[docs/decisions/ADR-007 - Private preparation boundary]],
[[apps/api/src/filingguard/modules/documents/README]], [[TODO]] T017/T021.
