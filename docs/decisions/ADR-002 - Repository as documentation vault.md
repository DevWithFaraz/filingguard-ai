---
type: decision
status: accepted
date: 2026-09-26
tags: [documentation]
---
# ADR-002 - Repository as documentation vault

## Context
The user wants linked Obsidian documentation for the whole project and reusable
decisions, bugs and lessons. The SRS and task checklist already live in the root.

## Decision
Use the existing repository as the vault. Keep canonical documents where they are.
Add [[Home]], category indexes, linked notes, templates and project guidance.
Use core Obsidian features and local Markdown; no third-party plugin dependency.

## Alternatives considered
A separate copied vault would create two versions of requirements/tasks.
Moving all documentation to a separate vault would break established paths and
separate module guidance from code. Both introduce avoidable synchronization work.

## Consequences
Code and private runtime files share the root with notes, so search exclusions
are convenience only. Sync/publishing needs a separate privacy review.
The user opens this existing folder in Obsidian once; app registration is not
claimed until confirmed. Future work must update records to keep them useful.

Related: [[docs/decisions/Index]], [[docs/knowledge/Documentation Workflow]],
[[docs/feedback/FB-001 - Linked project documentation]].
