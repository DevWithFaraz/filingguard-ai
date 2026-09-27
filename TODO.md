# FilingGuard AI - Ordered Task Checklist

Updated: September 27, 2026. Source: [SRS](FilingGuard_AI_SRS.md).
Deadline recorded in the SRS: September 28, 2026, 02:00 Asia/Karachi.

## How we work

Pick the first unchecked task whose dependencies are complete. Keep one task in
progress. Mark `[x]` only after its completion check passes; add a short evidence
note (test command, fixture result or deployed check). When blocked, record the
reason and work on the next independent task. Do not mark a feature done merely
because its folder, schema, mock response or screen exists.

P0 is the submission target. P1 starts only after the P0 workflow passes on the
deployed environment. P2 is the post-hackathon backlog. Reserve the final four
hours before the recorded deadline for verification, recording and submission;
freeze new features then. This checklist covers the project backlog, not a promise
that every enhancement fits the remaining hackathon time.

Current task: T008 (deployment configuration prepared; awaiting hosting accounts).
Next task: T009 after the remaining Phase 1 deployment gate.
Blockers: hosting accounts, Neon DATABASE_URL and deployed verification.
Confirmed constraints: solo participant, student aged 22; free credits only for LLM calls.
Implementation status: health-connected frontend shell and test tooling implemented;
no analysis feature has been completed. Phase 1 is not complete until T008 passes.

## Scaffold delivered

- [x] S001 - Create the frontend/backend/module/test/documentation directory structure.
- [x] S002 - Add npm/Python manifests, runtime selections and editor/ignore settings.
- [x] S003 - Add environment examples and local PostgreSQL Compose configuration.
- [x] S004 - Add a health-only FastAPI entry point, smoke test and OpenAPI export script.
- [x] S005 - Document module responsibilities, architecture and the delivery sequence.
- [x] S006 - Add clearly synthetic starter fixtures; label expected results unvalidated.

These completed items describe authored files only. Dependency installation,
framework execution, provider connectivity and database readiness are not checked
off by scaffolding. T002-T003 establish a working development environment.

## P0 / 1. Confirm scope and establish the development loop

SRS: sections 4-5, 7, 19-20; NFR-060 through NFR-063.

- [x] T001 - Confirm the official LexHack deadline, timezone, submission fields,
  judging rules and team constraints. Confirm P0 scope and record any changes in
  `docs/delivery/`. Done when the submission checklist is grounded in official rules.
  Evidence: [[docs/delivery/LexHack requirements]]; participant confirmed solo,
  student, age 22; SRS P0 scope retained.
- [x] T002 - Install Node 24/Python 3.12 dependencies with npm and uv; resolve any
  compatibility issues, generate and commit both lockfiles, initialize Git if
  needed, and create local environment files without overwriting secrets. Done
  when clean locked installs work and secret files are ignored.
  Evidence: npm ci offline with scripts disabled; uv locked offline sync;
  esbuild transform; environment ignore checks; lockfiles committed in setup commit.
- [x] T003 - Run backend lint and health smoke test, frontend typecheck and contract
  export/generation. Start the API locally. Done when `/api/v1/health` returns 200,
  `/docs` loads and generated client types match OpenAPI.
  Evidence: all listed npm checks pass; one pytest test passes; running API
  returns HTTP 200 for both routes. See [[docs/sessions/2026-09-27 - Development loop]].
- [x] T004 - Check CourtListener token access, supported lookup/opinion endpoints,
  rate limits and available source text for demo authorities. Done when a genuine
  lookup and opinion fetch succeed without leaking credentials into logs.
  Evidence: authenticated usage, citation lookup for 576 U.S. 644 and opinion
  2812209 all returned 200; plain text available. See
  [[docs/research/Provider access verification]].
- [x] T005 - Check the selected free-tier LLM API access; select a structured-output model using
  supported/unsupported sample propositions, timing and cost. Set model/token
  budgets, timeouts and validated schemas. Done when parsed evidence-grounded
  output and refusal/error handling are demonstrated. Do not assume account access.
  Evidence: access and two strict-schema calls verified; 120B 5/5 versus 20B 3/5
  on synthetic cases; validator refusal/error tests pass. User selected provisional
  120B; model saved locally. Evaluation bound: 2,048 output tokens, low reasoning,
  20-second timeout, no retries; free-tier only, no paid fallback. Real-case
  validation and production adapters remain separate tasks.
  See [[docs/research/Provider access verification]].
- [x] T006 - Add Vite entry points, React router/providers, shared layout, accessible
  primitives and dev/build scripts. Connect the API client and TanStack Query.
  Done when a browser screen can read backend health and production build passes.
  Evidence: production build passes; Playwright verifies API-connected status
  in desktop/mobile Chromium, navigation and disabled document submission.
- [x] T007 - Configure frontend lint, Vitest/Testing Library, backend test fixtures
  and Playwright; add CI for locked installs, lint, typecheck, tests and build.
  Done when a clean checkout passes the initial checks without live API keys.
  Evidence: fresh locked npm ci and uv sync pass; lint, typecheck, build,
  4 frontend tests, 10 backend tests and 4 browser tests pass locally. CI is
  configured without live-provider calls; remote run awaits the authorized push.
- [ ] T008 - Deploy the shell and health API early; provision PostgreSQL, configure
  exact CORS/API origins, HTTPS and secrets. Keep uploads disabled until T018.
  Done when the public shell reaches the hosted API and a repeatable deploy works.

## P0 / 2. Persistence, evidence and contracts

Depends on T002-T003. SRS: section 11, FR-220 through FR-223, AUD-001 through AUD-004.

- [ ] T009 - Define typed schemas for analysis lifecycle, stage states, findings,
  severities, citation/proposition/quote statuses, locations, confidence and
  coverage. Include unavailable, interrupted and partial states. Done when missing
  results cannot be represented as verified/passed by default.
- [ ] T010 - Implement SQLAlchemy sessions and Alembic configuration/migrations for
  Analysis, DocumentSegment, Citation, Authority, Claim, ClaimAuthorityLink, Quote,
  Finding and EvidenceRecord. Done when a fresh PostgreSQL database migrates and
  relationships round-trip correctly; add indexes for analysis-scoped lookups.
- [ ] T011 - Define evidence provenance: document/page/span, triggering citation or
  quote, source URL, retrieval timestamp/hash, excerpt offsets, method version and
  model/prompt versions. Done when a finding resolves back to stored evidence.
- [ ] T012 - Define versioned API requests/responses for text/file submission,
  status, findings, graph, report, court profiles and deletion. Implement routes
  with actual services as those become available; regenerate client types.
  Done when boundary validation and error envelopes are consistent.
- [ ] T013 - Add repositories/transactions only where needed and cascade deletion
  rules for analysis-owned data. Done when a failed stage does not erase previously
  saved results and deletion does not leave private orphaned records/files.

## P0 / 3. Demo fixtures and public-access controls

Depends on T009-T011; live authority fixtures also need T004. SRS: FR-008,
NFR-040 through NFR-044, sections 15 and 19.3. Demo setup is promoted to P0 because
sections 18 and 20 require it for acceptance.

- [ ] T014 - Expand the synthetic starter into a full text/PDF demo containing
  three correct citations, one unresolved citation, a misleading proposition,
  altered quotation, disclosure omission and synthetic privacy issue. Add public
  opinion fixtures with provenance. Done when every planted issue is documented.
- [ ] T015 - Create human-reviewed expected results, including benign controls and
  source-unavailable cases. Keep string/semantic outcomes separate. Done when
  expectations link to exact filing and source spans, not LLM-generated labels alone.
- [ ] T016 - Implement explicit live/demo adapters, fixture IDs/document hashes,
  visible mode labels and a reset action. Done when altered/unrecognized input
  cannot receive cached sample results and live failures stay unavailable.
- [ ] T017 - Implement private temporary storage, random server-side filenames,
  file signatures/size limits, page/character limits and deletion/retention.
  Done when traversal, invalid/oversized files and public file exposure are rejected.
- [ ] T018 - Add anonymous session-scoped ownership for results, reports and delete
  endpoints; apply origin/CSRF protections as appropriate to the chosen session
  transport, basic abuse limits and one active-analysis cap. Done when another
  session cannot read a result by knowing its ID. Accounts remain P2.

## P0 / 4. Intake and document extraction

Depends on T006, T009-T013 and T017-T018. SRS: FR-001 through FR-007,
FR-020 through FR-023; FR-024/025 basics promoted for usable evidence locations.

- [ ] T019 - Implement paste/PDF/sample intake, filename/size feedback, court
  selection, AI-used input and submission validation. Done when both real input
  methods produce a valid analysis request with the selected metadata.
- [ ] T020 - Extract PDF text with pypdf and preserve page boundaries, paragraph
  segments and stable offsets into original extracted text. Done when sample
  findings can point back to the correct page and original substring.
- [ ] T021 - Handle scanned, encrypted, malformed, empty and poorly extracted PDFs
  with a clear paste-text fallback. Guard parsing resource consumption. Done when
  no-text extraction does not produce a misleading clean result.
- [ ] T022 - Apply local privacy detection/masking before preparing provider-bound
  filing excerpts; maintain offset mappings and original evidence securely.
  Done when outgoing semantic requests exclude detected sensitive identifiers.
  Depends also on privacy rules T030; build the boundary now, integrate then.

## P0 / 5. Pipeline and partial results

Depends on T010-T013 and T019-T021. SRS: section 7.4; NFR-001 through NFR-004,
NFR-020 through NFR-023; LOG-001 through LOG-004.

- [ ] T023 - Persist the analysis before returning 202; reserve the concurrency
  slot and execute stages through one in-process orchestrator. Done when duplicate
  clicks do not start duplicate work and stage transitions are saved.
- [ ] T024 - Enforce bounded input/passage sizes, provider concurrency, retry policy,
  rate-limit handling and overall timeout. Offload blocking PDF/DB work. Done when
  a timeout terminates affected work and liveness remains responsive.
- [ ] T025 - Save partial results after each stage and mark abandoned jobs interrupted
  after restart. Add explicit rerun behavior. Done when one failed provider does
  not discard independent checks or leave the UI polling forever.
- [ ] T026 - Add one-second status polling with terminal-state stop, backoff and
  accessible progress/error states. Done when progress is visible within two
  seconds and navigation/unmount stops unused requests.
- [ ] T027 - Add correlation IDs and structured stage timing/status/error logs with
  credential/document redaction. Done when one failed analysis can be diagnosed
  without logging filing text, raw identifiers or provider request secrets.

## P0 / 6. Deterministic privacy and court checks

Depends on T020 and T023. SRS: FR-140 through FR-145, FR-160 through FR-162,
FR-164 through FR-166. T028-T031 can run independently of LLM access.

- [ ] T028 - Validate/load versioned JSON court profiles with source, effective
  dates, court/judge scope and demo flag. Add a clearly synthetic demo profile.
  Done when invalid/stale/unsupported profiles cannot silently pass compliance.
- [ ] T029 - Evaluate AI-use/disclosure presence against the selected profile;
  show the triggering requirement and uncertainty. Done when the same filing
  behaves correctly for AI-used yes/no and disclosure present/missing.
- [ ] T030 - Implement SSN, contextual account-number and full-date-of-birth
  detectors with severity, masked snippets and review recommendations. Test
  benign legal citations/dates to constrain false positives. Done when planted
  identifiers are detected without claiming definitive legal redaction compliance.
- [ ] T031 - Integrate rule/privacy findings and T022 masking into the pipeline.
  Done when no-citation filings still receive these checks and raw sensitive
  identifiers are absent from logs, summaries and external semantic payloads.

## P0 / 7. Citation verification and source retrieval

Depends on T004, T011, T020 and T023. SRS: FR-040 through FR-044, FR-080.

- [ ] T032 - Extract citations with Eyecite, preserve occurrences/offsets and
  handle unsupported/ambiguous formats without dropping them silently. Done when
  the fixture citations and original spans are correctly identified.
- [ ] T033 - Implement the CourtListener adapter with token handling, normalized
  identities and bounded error mapping. Return verified/not-found/invalid/
  ambiguous/unavailable separately. Done when timeout/429/5xx never becomes not-found.
- [ ] T034 - Retrieve opinion text and metadata for resolved authorities, preserving
  provenance and distinguishing missing text. Done when name/court/year/citation/
  source URL and available source passages appear in stored results.
- [ ] T035 - Deduplicate outbound lookups while retaining all filing occurrences;
  cache public source responses within an analysis. Done when repeats share one
  authority lookup and each original location remains inspectable.
- [ ] T036 - Test verified, unresolved, malformed, ambiguous, duplicate and provider
  failure cases. Done when unresolved findings explicitly state database coverage
  limitations and never assert that a case is fabricated merely because absent.

## P0 / 8. Claims and grounded propositions

Depends on T005, T011, T022, T032-T034. SRS: FR-060 through FR-063,
FR-081 through FR-086, FR-200 through FR-204.

- [ ] T037 - Extract the cited proposition from local sentence/paragraph context;
  retain verbatim excerpt/offsets and link claims to citations. Done when every
  extracted claim has traceable context and multiple links are representable.
- [ ] T038 - Select bounded relevant passages from the cited authority, including
  surrounding qualifications. Done when long opinions fit provider budgets and
  truncated/insufficient coverage is explicitly recorded.
- [ ] T039 - Implement versioned prompts and schema-validated classification:
  supported, partially supported, unclear, potentially misrepresented or not enough
  source text. Include short explanation, evidence IDs and confidence label.
  Done when the supported and misleading fixture claims produce defensible differences.
- [ ] T040 - Validate returned evidence IDs/excerpts against stored passages;
  handle refusals/invalid output, source absence and prompt-injection attempts.
  Done when unsupported references are rejected and missing evidence yields uncertainty.
- [ ] T041 - Save actual model/prompt/method metadata and communicate confidence
  as a heuristic unless calibrated. Done when semantic findings are visibly
  AI-assisted review signals with human-review recommendations, not legal conclusions.

## P0 / 9. Quote forensics

Depends on T020, T032-T034. SRS: FR-120 through FR-126.

- [ ] T042 - Extract quotations and associate nearby citations with ambiguity
  handling. Done when an uncertain association is not treated as certain.
- [ ] T043 - Implement exact, normalized and RapidFuzz comparison in that order;
  preserve original quote/source spans, closest passage and similarity score.
  Done when altered text is distinguishable from exact/format-only matches.
- [ ] T044 - Classify exact/normalized/close/not-found/source-unavailable outcomes
  and test punctuation, whitespace, ellipses and missing sources. Done when
  similarity is not presented as proof that a quotation preserves meaning.

## P0 / 10. Score, findings and graph

Depends on T029-T044. SRS: FR-100 through FR-104, FR-180 through FR-185,
FR-200 through FR-204; UX-001 through UX-004; NFR-080 through NFR-082.

- [ ] T045 - Define/version scoring weights and deductions for authorities,
  propositions, quotations, privacy and court checks. Keep coverage/incomplete
  checks separate and handle no applicable checks. Done when critical issues
  deduct more than warnings, calculations are reproducible and unknown is not a pass.
- [ ] T046 - Build the dashboard with score breakdown, coverage, counts, prominent
  critical findings and ready-for-review/needs-review/high-risk labels. Done when
  the score never claims filing safety and partial analyses are clearly labeled.
- [ ] T047 - Build filterable findings and a detail panel with original excerpt,
  source passage/link, method, uncertainty, reason and next review action. Done
  when a user can inspect the basis of each seeded issue without leaving the workflow.
- [ ] T048 - Generate graph nodes for document sections, claims and authorities
  with stable IDs and relationship/status metadata. Done when node counts and
  relationships match persisted findings instead of a separate hardcoded graph.
- [ ] T049 - Render React Flow with bounded layout, status text/icons and node
  selection opening finding detail. Include an equivalent keyboard-accessible
  list. Done when graph and list expose the same substantive evidence.
- [ ] T050 - Verify mobile/desktop layout, contrast, labels, focus order, loading,
  empty/error states and screen-reader feedback. Done when color is not the only
  signal and the complete P0 review flow can be used with a keyboard.

## P0 / 11. Report and integrated acceptance

Depends on T045-T050. SRS: FR-300 through FR-304; sections 17-18; AUD-001 through AUD-004.

- [ ] T051 - Generate on-screen and Markdown/HTML assurance reports from saved
  results: timestamps, selected profile/version, mode, score/coverage, findings,
  evidence, passed checks and limitations. Done when the export agrees with the UI
  and requires no new LLM classification; escape untrusted HTML content.
- [ ] T052 - Complete the full demo journey: load sample, select court/AI use, run,
  inspect score/graph, open at least two findings and export. Done when all twelve
  SRS section 18.2 acceptance steps pass against expected fixtures.
- [ ] T053 - Test provider outages, rate limits, absent opinion text, LLM refusal,
  malformed uploads, no citations, interruption and retry. Done when independent
  results survive and every affected check communicates its actual state.
- [ ] T054 - Run access-isolation, secret/log redaction, upload abuse, prompt
  injection and deletion/retention checks. Done when test reports document outcomes
  and no confidential material appears in fixtures or publicly served assets.
- [ ] T055 - Measure demo performance: <=60-second normal analysis, <=2-second
  initial progress, <=3-second completed dashboard. Test the 20-page limit and
  maximum accepted inputs. Done when measured results and remaining limits are recorded.
- [ ] T056 - Run lint, typechecks, unit/integration tests, frontend build and
  Playwright journey; review source provenance and requirement coverage. Done when
  no blocking failures remain and acceptance evidence is linked to the tasks.

## P0 / 12. Release and submission

Depends on T051-T056. SRS: DEP-001 through DEP-005, sections 19 and 23.

- [ ] T057 - Release the working app with migrations, exact CORS/origins, secrets,
  retention and single-process limits; verify readiness separately from liveness.
  Done when fresh hosted intake-to-export works and results remain session-scoped.
- [ ] T058 - Rehearse live and explicitly labeled cached demo modes on the hosted
  app, including a forced dependency failure. Done when the fallback cannot be
  confused with live verification and restart recovery is understood.
- [ ] T059 - Finish setup/deployment/troubleshooting docs, API configuration,
  limitations, third-party licenses/attribution and source links. Done when another
  developer can reproduce the app using the committed lockfiles and instructions.
- [ ] T060 - Prepare a two-to-three-minute demo, screenshots and recording showing
  citation misuse, quote evidence, graph, privacy/rules and report. Include AI limits
  honestly. Done when the presentation fits the official event format.
- [ ] T061 - Complete the official submission fields, project narrative, live URL,
  repository/demo links and team details; verify reviewer access and submit before
  the confirmed deadline. Done when submission confirmation is saved.
- [ ] T062 - Record the release commit/tag, known limitations and unresolved P1/P2
  work; verify submitted URLs once more. Done when the submitted build is reproducible.

## P1 / 13. Enhancements after deployed P0 passes

Execute in the order below while preserving the submission buffer. Each task also
requires relevant unit/UI tests and regression of the P0 demo.

- [ ] T101 - Legal Red-Team Mode (FR-240 through FR-245): rank weaknesses solely
  from existing findings/evidence, link every point back, and avoid drafting new
  strategy. Done when the demo review identifies planted weaknesses without inventing facts.
- [ ] T102 - Rich lineage and explanations (FR-205, FR-224/225): expandable
  document-to-source-to-method chain and exported provenance. Done when every hop
  links to the same persisted evidence used for the finding.
- [ ] T103 - Finding-grounded Q&A (FR-260 through FR-264): scoped evidence access,
  cited answers, refusal of broad legal advice, missing-evidence behavior and request
  limits. Done when questions cannot cross sessions or produce unsupported authorities.
- [ ] T104 - PDF report export (FR-305): select renderer, embed readable evidence,
  pagination and disclaimers. Done when exported pages are visually inspected and
  long findings wrap without clipping.
- [ ] T105 - Graph polish (FR-105/106), multiple claims per authority (FR-064) and
  score-category filters (FR-186). Done when pan/zoom/fit, unsupported nodes and
  cross-view selection preserve correct finding context.
- [ ] T106 - Additional verified real court profiles (FR-146): primary sources,
  applicability/effective dates, judge-specific scope and profile regression tests.
  Done when stale/unknown rules show limitations rather than a pass.
- [ ] T107 - Deeper retrieval and forensics (FR-025, FR-045/046, FR-087, FR-127):
  improve parsing diagnostics, duplicate display, versioned source cache,
  multi-passage retrieval and meaning-changing quote warnings. Done when benchmark
  quality improves without treating semantic similarity as an exact quotation.
- [ ] T108 - Possible minor-name heuristics (FR-163), with explicit uncertainty
  and false-positive controls. Done when synthetic cases and benign controls are reviewed.
- [ ] T109 - Durable job execution if needed: choose a worker/queue, leases,
  idempotency, crash recovery and bounded retries. Done when restart/rescheduling
  preserves results before enabling multiple API workers/replicas.
- [ ] T110 - Expand accessibility, audit timing/correlation, retention automation
  and failure observability (UX-005, LOG-003/004, NFR-023/044/063). Done when automated
  checks and manual assistive workflows pass with no raw filing data in telemetry.

## P2 / 14. Post-hackathon backlog

These are future product work, not prerequisites for the LexHack submission.

- [ ] T201 - Table of Authorities audit (FR-280 through FR-284): detect TOA,
  normalize/deduplicate authorities, compare body versus table both ways, show
  missing/extra entries and page references; handle documents with no TOA.
- [ ] T202 - Statute/regulation verification (FR-047): add source adapters,
  jurisdiction/version/effective-date handling, evidence and coverage tests.
- [ ] T203 - Filing-versus-case fact comparison (FR-088) with grounded passages,
  uncertainty and human review rather than unsupported legal analogies.
- [ ] T204 - Semantic quote similarity (FR-128) as a separate review signal with
  evaluations for negation, omission and material meaning changes.
- [ ] T205 - Advanced formatting/local-rule checks (FR-147) and jurisdictional
  privacy policies (FR-167), versioned and source-verified.
- [ ] T206 - Manual claim corrections (FR-065) with history, affected-check reruns
  and clear separation of user edits from original extraction.
- [ ] T207 - Graph image export (FR-107/306) including a readable report image and
  accessible equivalent; ensure exported status matches the stored analysis.
- [ ] T208 - Authentication, saved matters/history and production authorization;
  define ownership/migration of anonymous analyses and evaluate security tests.
- [ ] T209 - Reviewer roles, collaboration/comments and review status with
  auditable attribution and matter-level permissions.
- [ ] T210 - Batch processing with durable workers, quotas, cancellation,
  idempotency, per-document progress and partial batch failures.
- [ ] T211 - Word add-in/browser extension: choose a supported integration surface,
  secure authorization and document-location synchronization.
- [ ] T212 - Production data protection (NFR-045): verify encryption at rest,
  backups/restore, deletion policy, least-privilege access, secret rotation,
  provider retention terms and deployment threat review before real client use.
- [ ] T213 - Broader legal quality evaluation, calibrated confidence where feasible,
  domain-expert review and operational ownership for ongoing court-rule updates.

## Scope exclusions

Do not add automatic court filing, case-outcome prediction, legal-strategy
generation, generic legal chat, billing, PACER integration or unrelated contract
review without a new scope decision. OCR is deferred. The score is a review signal,
not a legal certification. No claim of nationwide coverage or privilege protection.

## SRS priority reconciliation

The SRS labels some capabilities P1 in its individual tables but requires them
for an effective P0 demo elsewhere. This checklist promotes only the minimum
needed: sample input (T014-T016), evidence offsets (T020), bounded passage handling
(T024/T038), basic source deduplication (T035), correlation IDs (T027), retention
and access isolation (T017-T018), and focused tests (T003/T036/T044/T052-T056).
Advanced versions remain P1. P0 evidence capture remains distinct from P1 lineage
visualization. Markdown/HTML export is P0; dedicated PDF export is P1.

## Work log

- 2026-09-27: began P0 phase 1; verified official deadline/rules in
  [[docs/delivery/LexHack requirements]]. T001 awaits team confirmation. Adopted
  the user's renamed TODO.md as canonical and repaired old TDOD references.
- 2026-09-27: user confirmed solo student, age 22, and free credits only. T001
  complete; T002 started. Provider choice remains pending; OpenAI is no longer a
  required provider. Sandbox network access required an installation escalation.
- 2026-09-26: added the project Obsidian vault and Home.md navigation, linked
  category indexes/templates, and persistent documentation guidance. Future
  task work should follow docs/knowledge/Documentation Workflow.md. No feature
  task was marked complete by this documentation change.
- 2026-09-26: scaffold authored; analysis features are unimplemented. Complete
  dependency installation and runtime checks in T002-T003 before building features.
- 2026-09-26: static verification passed for six JSON files, one TOML manifest,
  nine Python syntax trees, fixture paths and all 91 unique task IDs. Compose
  configuration parsed successfully; Docker reported inaccessible user config,
  so no daemon or container readiness is inferred. Dependencies, framework tests
  and frontend typecheck have not been run.

For future completions append: date, task ID, change summary, acceptance evidence,
remaining caveat and the next task. Keep the checkbox and current-task line in sync.
