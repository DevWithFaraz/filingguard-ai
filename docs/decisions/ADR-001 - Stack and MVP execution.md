---
type: decision
status: accepted
date: 2026-09-26
tags: [architecture, mvp]
---
# ADR-001 - Stack and MVP execution

## Context
The [[FilingGuard_AI_SRS|SRS]] leaves backend choices open and prioritizes a
deadline-constrained, evidence-grounded demo.

## Decision
Use the choices in [[docs/architecture/stack]]: React/TypeScript/Vite, Python/FastAPI,
PostgreSQL, Eyecite/CourtListener, pypdf/RapidFuzz and bounded OpenAI structured
outputs. Begin with one API process and persisted progress/partial results.
[[TODO|Tasks T002-T008 and T023-T027]] establish and verify this architecture.

## Rationale and alternatives
Python gives the analysis code direct access to the selected citation/PDF libraries.
Spring Boot or Node remain viable alternatives but would change the selected
processing setup. A durable distributed queue adds operational work before the
demo needs it; add one before scaling beyond in-process execution.

## Consequences and verification
In-process jobs are not durable. Restart detection must mark abandoned work
interrupted and provide rerun. A graph database is unnecessary for this MVP.
Dependencies and pipeline behavior remain unverified until their tasks pass.
Do not interpret this decision as production readiness.

Related: [[docs/decisions/Index]], [[docs/product/Features]],
[[docs/learnings/LEARN-001 - Scaffold is not runtime verification]].
