---
type: guide
status: active
tags:
  - documentation
---
# Documentation Workflow

Related: [[Home]], [[AGENTS]], [[TODO]], [[docs/templates/Index]].

## Read just enough context

Start with Home and the current TODO task. Follow its feature/module links, then
the relevant decisions, issues and lessons. Prefer current implementation and
verification evidence over an old plan. A note's presence is not proof that its
claim was tested. Link to a source instead of copying long content into many notes.

## One source for each responsibility

- Requirements: [[FilingGuard_AI_SRS]]. Record approved scope changes explicitly.
- Task status and ordering: [[TODO]]. Other notes reference task IDs, not copied checklists.
- Setup: [[README]]. Architecture: [[docs/architecture/stack]].
- Module responsibilities: linked from [[docs/product/Features]].
- Rationale/history: [[docs/decisions/Index]].
- Reproducible failures: [[docs/issues/Index]].
- Evidence-backed reusable lessons: [[docs/learnings/Index]].
- User observations and business inputs: [[docs/feedback/Index]].
- External sources and uncertainty: [[docs/research/Index]].
- Work handoffs: [[docs/sessions/Index]].

## Record material changes

After a substantive task, update its canonical docs and TODO status. Add a decision
only for a meaningful tradeoff, an issue only for an actual observed failure, and
a lesson only when evidence supports a reusable takeaway. Capture a short handoff
with tests run/not run, blockers and next step. Do not document every click or
duplicate the complete chat transcript.

Each new note should link to its index and the affected feature or decision.
Indexes must link back to new notes so they are discoverable. Use full vault paths
in links, especially for README notes. Standard Markdown links remain valid;
Obsidian wikilinks are used for cross-note navigation in this knowledge layer.

## Names and properties

Use descriptive names: `ADR-003 - Short decision`, `BUG-001 - Short symptom`,
`LEARN-002 - Short lesson`, `FB-002 - Short feedback`, or
`2026-09-26 - Short session topic`. Choose the next unused number per category.
Use frontmatter `type`, `status`, `date`, and `tags` when appropriate.

Decision states: proposed, accepted, superseded. Issue states: open, investigating,
resolved. Learning states: candidate, validated, superseded. Research states:
unverified, verified, stale. Keep verification dates and applicability explicit.
Do not overwrite history silently: mark old notes superseded and link replacements.

## Using templates

Create a note in the relevant folder and run **Templates: Insert template** using
Obsidian's command palette. Templates are in [[docs/templates/Index]]. Fill out
observations and evidence; remove irrelevant prompts. These are ordinary Markdown
templates using the core plugin, not automation that writes or verifies notes.

The [official Templates guide](https://obsidian.md/help/plugins/templates) explains
insertion and date/title variables. Edit templates in Source mode to preserve them.

## Reusing knowledge on another project

Export or reference a small set of relevant lesson notes, including conditions,
test evidence, version/dependency context and limits. Revalidate on the new system.
Do not import the full vault or treat an old implementation choice as universally
correct. A successful workaround on one app is a hypothesis on another until tested.

## Vault boundaries

The vault root is the existing project root. Source documents are not moved or
duplicated. New loose notes default to `docs/inbox`; non-sensitive note attachments
go to [[docs/attachments/README|docs/attachments]]. Code remains in its existing folders.

Configured excluded paths reduce search/graph noise; they are not encryption,
access controls or a promise that files will not sync. `.gitignore` controls Git,
not Obsidian Sync. Keep API keys and private runtime material out of documentation.
Do not enable vault publishing or third-party syncing without separately reviewing
the repository's secrets and private files. No sync or publishing is configured.

Shared vault settings are versionable. Per-device workspace layout and cache files
are ignored by Git. The root AGENTS guidance asks future project work to maintain
this workflow; another AI tool may need those instructions loaded explicitly.
