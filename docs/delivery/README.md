# Delivery guide

The root [TODO.md](../../TODO.md) is the ordered task source. Do not duplicate its
checkboxes here. This directory holds confirmed event instructions, acceptance
evidence, deployment notes and the final submission checklist as work progresses.

See [[docs/delivery/LexHack requirements]] for the checked event requirements and
pending participant/account confirmations.

## Working order

1. Confirm event constraints and establish installs, health, types and CI.
2. Check provider access and deploy a shell early to expose hosting blockers.
3. Define persistence/evidence, demo fixtures and private/session-scoped intake.
4. Build extraction and a bounded pipeline with progress/partial results.
5. Add deterministic checks, authority retrieval, grounded propositions and quotes.
6. Build the shared findings model into score, detail view, graph and report.
7. Pass local and deployed acceptance, then record and submit.
8. Add P1 only after deployed P0 is stable; leave P2 after the event.

## Definition of done

A task is done when its actual behavior passes the TODO completion condition,
relevant tests pass, and its limitation/status is documented. A mock alone does
not establish live-provider behavior. A schema-valid LLM answer does not establish
correctness. Missing sources and failed checks remain visibly incomplete.

Keep the final four hours before the confirmed deadline for recording, regression
and submission. If time runs short, preserve the P0 end-to-end flow and report a
limitation honestly instead of filling gaps with fabricated verification results.

## Current verification boundary

Configuration syntax and file relationships can be checked without installing the
app. Runtime dependency resolution, API smoke tests, typechecks, migrations and
provider requests belong to the initial implementation tasks. No live application
deployment or external integration has been completed by the scaffold.
