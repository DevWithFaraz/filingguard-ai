# FilingGuard AI - Ordered Task Checklist

Updated: October 11, 2026. Source: [SRS](FilingGuard_AI_SRS.md).
Product development continues after the missed LexHack deadline. No active time
constraint or feature freeze. Historical submission records remain in docs/delivery.

## How we work

Pick the first unchecked task whose dependencies are complete. Keep one task in
progress. Mark `[x]` only after its completion check passes; add a short evidence
note (test command, fixture result or deployed check). When blocked, record the
reason and work on the next independent task. Do not mark a feature done merely
because its folder, schema, mock response or screen exists.

P0 is the core product workflow. P1 extends a verified deployed core; P2 contains
larger product capabilities. Security and legal-quality release gates still apply
before real client use. More time does not change the free-credit budget or authorize
paid hosting. See [[docs/decisions/ADR-005 - Product continuation and reviewed demo]].

D007 non-home redesign is implemented and verified locally; homepage preserved.
User visual feedback can refine this direction. Full accessibility/performance
and hosted release checks remain separate gates below.
T050, T052 and T055 pass locally on October 11. The user requested solo work;
no further subagents. Genuine free-credit curated review-to-export/reset passes
all twelve SRS 18.2 controls in 52.803 seconds, with 187 ms initial progress and
641 ms dashboard rendering. T056 local regression is complete after correcting
the locked-fixture edit and new readiness route expectation; hosted release is
still a distinct gate.
October 11: the user lifted the no-commit/push constraint and authorized help
reviewing/publishing the release checkpoint and verifying the hosted workflow.
T036 citation partial outputs/coverage and T037 traceable claim extraction are
verified through contained workers. Transport-level filing masking, quote
forensics, saved result/evidence/graph/report ownership and deterministic scoring
are verified locally. External provider flags and public intake default off.
Immutable evidence IDs, conservative shared-authority batching and bounded quota
admission preserve source passages and independent verdicts. The integrated model
controls now pass; broad expert legal QA remains separate. Do not count fake
provider responses as live source/model verification. Older hosted API still
serves the health shell (/ready and /capabilities 404), so hosted intake-to-export
is not verified. T016 remains complete locally.
Latest evidence: [[docs/sessions/2026-10-11 - Accessibility performance and release gates]].
The accepted homepage and later pages evolve together. No billing upgrades or
public confidential filing use are authorized.
Confirmed constraints: solo participant, student aged 22; free credits only for LLM calls.
Implementation status: the local review workflow, results, graph and reports are
implemented; normal source-verification and semantic adapters are opt-in. Four
sourced curated propositions pass genuine model controls using cached public text.
Phase 1 deployment gate is verified;
Phase 2 typed contracts/migrations/evidence and Phase 3 storage/demo-admission
foundations are implemented, with integration work explicitly pending below.
User expanded scope to Phase 2/3 and requested UI planning/subagents. On September
28 the user explicitly changed the objective from a hackathon entry to a product.

## Scaffold delivered

- [x] D008 - Preview a glassmorphism material for the homepage input box, preserving
  layout and behavior. Record the established UI scope for future development.
  Done when desktop/mobile modes, readable contrast and accessibility fallbacks
  are verified locally. User aesthetic approval is separate.
  October 11: desktop/mobile keyboard/axe suite passes 2/2; production build passes.
  Isolated Chromium verifies normal glass and actual increased-contrast/reduced-
  transparency opaque fallbacks, with no overflow at 1440/390 widths. Screenshots
  inspected; Text/PDF/Demo mode switching verified. Ongoing scope saved in AGENTS.
  [[docs/sessions/2026-10-11 - Glass input composer preview]].
  [[docs/feedback/FB-013 - Glass composer and continuing UI scope]].

- [x] D007 - Redesign all non-home pages using the installed apple-design skill and
  the accepted homepage as the visual reference. Preserve the homepage for now.
  Add clear step navigation, timely primary actions, quick routes and access back
  to the homepage; integrate purposeful animation and reduced-motion equivalents.
  Done when the non-home flows follow the shared theme and desktop/mobile,
  navigation, keyboard and motion checks pass. User aesthetic acceptance is separate.
  Skill installation verified by exact file hash. Prepared document, results
  (including graph/report), sample, Activity, settings, privacy/limits and recovery
  states now share the homepage assets and glass navigation. Verified: 30 frontend
  tests, typecheck/lint/build, eight desktop/mobile browser journeys across four
  isolated suites, route focus, keyboard evidence/details/graph, actual saved
  Activity status, masking, export/reset and reduced-motion behavior. Public-page
  widths 320/768/1440 pass. Homepage code/styles unchanged. Full accessibility,
  physical-device/performance and user aesthetic approval remain separate.
  [[docs/sessions/2026-10-10 - Remaining workflow pages redesign]].
  [[docs/feedback/FB-012 - Match workflow pages to homepage theme]].

- [x] D006 - Programmatic pipeline film: Remotion workspace `apps/video`, brief/
  beat grid/critique harness, 26-second nine-beat silent 16:9 loop with a 4K master,
  website-size derivatives using curated synthetic
  fixture strings and the original logo, rendered MP4/WebM/poster, and a
  below-fold homepage band with pause control and reduced-motion poster. Done when
  stills pass the critique rubric (all >=8), media are within budget, and homepage
  typecheck/lint/tests/build plus desktop/mobile browser checks pass. User
  aesthetic acceptance is separate. See
  [[docs/feedback/FB-009 - Programmatic pipeline film]] and
  [[docs/decisions/ADR-010 - Remotion pipeline film]]. Verified October 7: all
  internal scores 8–9, metadata/byte budgets pass,20 unit tests,22 browser cases
  plus 2 post-copy layout checks, video/web typecheck, lint and final build pass.
  [[docs/sessions/2026-10-07 - Pipeline film visual revision]].

- [x] D005 - Replace hero bitmap with the supplied 3888x2592 JPG unchanged;
  remove double fading while retaining the readability overlay and S-shaped
  papers. Build and desktop/mobile homepage checks pass (mobile retry after
  initial timeout). See [[docs/sessions/2026-09-29 - Background replacement]].

- [x] D004 - Restore cursor-responsive papers with distinct gentle S-curves;
  use genuine Avalance SemiBold for the main heading and rebalance footer logo,
  tagline and navigation. Typecheck, lint, build and 10 desktop/mobile browser
  tests pass; screenshots and canvas pixels checked. Local only. See
  [[docs/sessions/2026-09-29 - Asymmetric paper and typography]].

- [x] D003 - Restore original logo colors; make the glass header full-width with
  square edges; replace warped paper/ribbons with clean layered sheets; add the
  original-logo footer. Typecheck, lint, build and 17 unit tests pass. Eight final
  WebGL/motion tests and both desktop/mobile header/footer checks pass. Width
  checks tolerate browser subpixel rounding; screenshots inspected. See
  [[docs/sessions/2026-09-29 - Header paper and footer refinement]]. Local only.

- [x] D002 - Refine the homepage: glass navigation, rounder composer/controls,
  expressive Avalance/GSAP motion, transparent Three.js hero depth and selectable
  document/source study. Preserve intake, keyboard/touch access, reduced motion
  and WebGL fallback. Evidence: 20 browser tests, 17 unit tests, typecheck, lint
  and build passed; final refinements passed 10 focused browser tests plus a
  two-test responsive screenshot pass. Canvas checks verify nonblank rendering,
  framing, stage/pointer changes and a transparent hero center. See
  [[docs/sessions/2026-09-29 - Glass homepage and evidence motion]].
  User aesthetic acceptance, physical-device benchmarks and public deployment
  are not implied. Video and detailed widget/grid ideas remain separate work.

- [x] D001 - Build and inspect the first supplied-image/Avalance homepage, functional
  Text/PDF/Demo composer, responsive navigation and initial GSAP motion. Verify
  existing intake, reduced motion, keyboard access, assets and desktop/tablet/phone
  screenshots. User approved prioritizing this design pass before T023.
  Evidence: 17 frontend tests and 12 desktop/mobile browser tests passed; build,
  typecheck and lint passed. Sampled layouts at 320/360/390/768/1024/1366/1440/1920px
  and reduced-motion checks pass. First pass awaits user aesthetic feedback; later
  scroll narrative/Three.js/video remain planned. See
  [[docs/sessions/2026-09-29 - First homepage design]].

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
  configured without live-provider calls; clean-checkout GitHub CI passed:
  https://github.com/DevWithFaraz/filingguard-ai/actions/runs/36319439962.
- [x] T008 - Deploy the shell and health API early; provision PostgreSQL, configure
  exact CORS/API origins, HTTPS and secrets. Keep uploads disabled until T018.
  Done when the public shell reaches the hosted API and a repeatable deploy works.
  Progress: user created Render/Neon accounts; read-only Neon connection passed,
  PostgreSQL 17.11 with client TLS enabled on a direct endpoint. No tables created.
  Hosted browser verification: frontend shows API connected; /activity and
  /settings return 200 on direct navigation; exact frontend origin allowed,
  unrelated origin receives no CORS allow-origin header. User supplied successful
  initial deployments and a second API deploy of 2879aba. Submission stays disabled.
  See [[docs/sessions/2026-09-27 - Hosted shell verification]].
  See [[docs/sessions/2026-09-27 - Neon connection verification]].

## P0 / 2. Persistence, evidence and contracts

Depends on T002-T003. SRS: section 11, FR-220 through FR-223, AUD-001 through AUD-004.

- [x] T009 - Define typed schemas for analysis lifecycle, stage states, findings,
  severities, citation/proposition/quote statuses, locations, confidence and
  coverage. Include unavailable, interrupted and partial states. Done when missing
  results cannot be represented as verified/passed by default.
  Evidence: required verdict provenance, unrun defaults, aggregate coverage,
  applicability and provisional-score guards; contract regression tests pass.
- [x] T010 - Implement SQLAlchemy sessions and Alembic configuration/migrations for
  Analysis, DocumentSegment, Citation, Authority, Claim, ClaimAuthorityLink, Quote,
  Finding and EvidenceRecord. Done when a fresh PostgreSQL database migrates and
  relationships round-trip correctly; add indexes for analysis-scoped lookups.
  Evidence: SQLite migration/downgrade and 64 persistence tests; isolated Neon
  migration/nine-entity round trip/cascade verification passed, test schema removed.
  No production/public schema was migrated.
- [x] T011 - Define evidence provenance: document/page/span, triggering citation or
  quote, source URL, retrieval timestamp/hash, excerpt offsets, method version and
  model/prompt versions. Done when a finding resolves back to stored evidence.
  Evidence: snapshot SHA-256/span validation before storage and on retrieval,
  owner-scoped finding-to-evidence round trip verified locally and on Neon.
- [x] T012 - Define versioned API requests/responses for text/file submission,
  status, findings, graph, report, court profiles and deletion. Implement routes
  with actual services as those become available; regenerate client types.
  Done when boundary validation and error envelopes are consistent.
  Evidence: v1 boundary models, regenerated OpenAPI/TypeScript components and
  sanitized 404/422/429/500 envelopes tested. Health and read-only demo are runtime routes;
  analysis routes must be connected to actual services as they become available.
- [x] T013 - Add repositories/transactions only where needed and cascade deletion
  rules for analysis-owned data. Done when a failed stage does not erase previously
  saved results and deletion does not leave private orphaned records/files.
  Evidence: owner-scoped file/DB deletion, creation compensation, failed commit/file
  deletion retries, bounded expiry sweeps and same-filesystem crash recovery pass.
  Recovery preserves committed stage output; app owns threaded cleanup/shutdown.
  Populated SQLite migration upgrade/downgrade preserves child data. Backend suite:
  233 passed, two host-dependent skips; Ruff and eight desktop/mobile browser checks
  pass. Migration 0002 has not been applied to Neon; Windows ACLs/Linux locking and
  hosted filesystem behavior still require deployment checks before private intake.
  See [[docs/sessions/2026-09-28 - Private analysis lifecycle cleanup]].

## P0 / 3. Demo fixtures and public-access controls

Depends on T009-T011; live authority fixtures also need T004. SRS: FR-008,
NFR-040 through NFR-044, sections 15 and 19.3. Demo setup is promoted to P0 because
sections 18 and 20 require it for acceptance.

- [x] T014 - Expand the synthetic starter into a full text/PDF demo containing
  three correct citations, one unresolved citation, a misleading proposition,
  altered quotation, disclosure omission and synthetic privacy issue. Add public
  opinion fixtures with provenance. Done when every planted issue is documented.
  Evidence: [[data/demo/curated-v1/README]]; three authenticated public-opinion
  snapshots, text/PDF word equivalence, exact-span/hash checks and PDF visual
  inspection pass. Eighteen draft scenarios document issues and controls; no
  analysis engine verdict or human review is inferred.
- [x] T015 - Review source-grounded expected results, including benign controls and
  source-unavailable cases. Keep string/semantic outcomes separate. Done when
  expectations link to exact filing and source spans, not LLM-generated labels alone.
  Scope change: user explicitly delegated the planned human-review step to Codex.
  Evidence: [[docs/product/Demo fixture review]]; 18 judgments against source
  passages, 13 accepted and five conditional. AI review is complete, not human or
  expert validation. Source hashes/spans pass; human_reviewed remains unset.
  T016 must represent this delegated review honestly before enabling replay.
- [x] T016 - Implement explicit live/demo adapters, fixture IDs/document hashes,
  visible mode labels and a reset action. Done when altered/unrecognized input
  cannot receive cached sample results and live failures stay unavailable.
  Scope clarification: an explicit read-only adapter exposes reviewed examples now;
  actual analysis replay remains dependent on the later pipeline/engine tasks.
  Expectations never become executed findings merely by loading a demo. The legacy
  human-reviewed replay gate remains separate from delegated assistant review.
  Verified milestone: hash-bound review receipt, public demo-only GET route,
  visible provenance, all 18 source-linked expectations/five conditions and reset.
  Changed files/input, unknown IDs and live mode rejected; safe unavailability and
  retry tested. 202 backend tests, 12 frontend tests and eight desktop/mobile
  browser checks pass. October 10 completion: exact curated demo now executes
  real citation/claim/quote/rule/privacy engines against hash-bound cached public
  opinions. Cached-source receipts, visible source mode, selectable court/AI use,
  reset/deletion, altered input/source rejection and live-outage separation pass
  focused API and desktop/mobile browser checks. No expected classifications are
  replayed. Genuine model calls remain opt-in; throttling stays unavailable.
  The legacy human-reviewed cached-result gate remains distinct and disabled.
  See [[docs/sessions/2026-10-10 - Curated demo acceptance]].
  See [[docs/sessions/2026-09-28 - Product continuation and reviewed demo]].
- [x] T017 - Implement private temporary storage, random server-side filenames,
  file signatures/size limits, page/character limits and deletion/retention.
  Done when traversal, invalid/oversized files and public file exposure are rejected.
  Evidence: private UUID bytes/receipts, traversal/signature/size/TTL/deletion checks,
  owner-scoped HTTP admission, real bounded PDF worker and chunked-body limits pass.
  No public file mount; parser logging/stderr suppressed, child env excludes secrets.
  Locally verified, not a production security certification. Hosted filesystem/ACL,
  Linux resource limits and exposure checks remain T057/T212 release gates.
  Public intake stays disabled. See [[docs/decisions/ADR-007 - Private preparation boundary]].
- [x] T018 - Add anonymous session-scoped ownership for results, reports and delete
  endpoints; apply origin/CSRF protections as appropriate to the chosen session
  transport, basic abuse limits and one active-analysis cap. Done when another
  session cannot read a result by knowing its ID. Accounts remain P2.
  Verified milestone: server-issued 256-bit tab bearer, persisted hash/55-minute
  expiry, exact origins, bounded quotas, and owner-scoped preparation/list/read/delete.
  Another valid session receives 404 for the same ID; real browser isolation passes.
  One global slot spans body buffering, parsing, preparation and local review jobs.
  October 10: saved results, graph, report and finding evidence reuse the same
  owner/expiry guards; API/browser foreign-session and deleted-resource tests pass.
  Hosted verification remains a release gate, not implied by local checks.
  See [[docs/decisions/ADR-007 - Private preparation boundary]].

## P0 / 4. Intake and document extraction

Depends on T006, T009-T013 and T017-T018. SRS: FR-001 through FR-007,
FR-020 through FR-023; FR-024/025 basics promoted for usable evidence locations.

- [x] T019 - Implement paste/PDF/sample intake, filename/size feedback, court
  selection, AI-used input and submission validation. Done when both real input
  methods produce a valid analysis request with the selected metadata.
  Evidence: real desktop/mobile Text/PDF/Demo preparation, AI-used metadata, file
  feedback, reload, Activity and deletion pass. Court metadata is explicitly
  unverified or synthetic; real selectable court profiles require T028. Creation
  returns 201/not_run, not a fake 202 legal job; a later local-review action is
  now enabled on the prepared document page.
- [x] T020 - Extract PDF text with pypdf and preserve page boundaries, paragraph
  segments and stable offsets into original extracted text. Done when sample
  findings can point back to the correct page and original substring.
  Evidence: original UTF-8 hashes, canonical PDF page separators, exact half-open
  Unicode-code-point paragraph spans and blank-page positions round-trip through
  worker, DB and browser. No invented PDF page numbers for pasted text.
- [x] T021 - Handle scanned, encrypted, malformed, empty and poorly extracted PDFs
  with a clear paste-text fallback. Guard parsing resource consumption. Done when
  no-text extraction does not produce a misleading clean result.
  Evidence: real encrypted/no-text/malformed PDF rejection, limits, worker timeout/
  spawn failure, sanitized errors, sparse/blank/replacement-text warnings and browser
  paste-text fallback pass. Windows process-tree containment verified; POSIX limits
  are authored, not locally executed. Diagnostics are heuristics, not OCR/quality proof.
- [x] T022 - Apply local privacy detection/masking before preparing provider-bound
  filing excerpts; maintain offset mappings and original evidence securely.
  Done when outgoing semantic requests exclude detected sensitive identifiers.
  Depends also on privacy rules T030; build the boundary now, integrate then.
  Verified milestone: local pattern masking detects on full filing before slicing;
  clipped identifiers remain masked, with stable original offsets and no provider
  request. T030 local findings and masked responses now run. T024 adds bounded
  filing/source context and a fake outgoing JSON test, including clipping through
  a detected identifier. October 10: the actual Groq transport payload now derives
  every filing field from the full-snapshot masking boundary; wire-level SSN and
  clipped-identifier controls pass. Original evidence retains exact offsets.
  [[docs/sessions/2026-10-10 - Grounded review verification]].
  See [[docs/sessions/2026-09-28 - Private intake and document extraction]].
  See [[docs/sessions/2026-10-02 - Provider budgets and hard deadlines]].

## P0 / 5. Pipeline and partial results

Depends on T010-T013 and T019-T021. SRS: section 7.4; NFR-001 through NFR-004,
NFR-020 through NFR-023; LOG-001 through LOG-004.

- [x] T023 - Persist the analysis before returning 202; reserve the concurrency
  slot and execute stages through one in-process orchestrator. Done when duplicate
  clicks do not start duplicate work and stage transitions are saved.
  Evidence: atomic owner-scoped queue-before-202, shared preparation/review slot,
  duplicate/delete conflicts, per-stage commits and real local privacy plus
  synthetic-demo court runners verified via API and desktop/mobile browser tests.
  Four other legal stages remain explicitly unavailable; runs are partial.
  See [[docs/sessions/2026-10-01 - Local review pipeline]].
- [x] T024 - Enforce bounded input/passage sizes, provider concurrency, retry policy,
  rate-limit handling and overall timeout. Offload blocking PDF/DB work. Done when
  a timeout terminates affected work and liveness remains responsive.
  Evidence: contained stage workers enforce stage/overall work cutoffs and shutdown;
  stuck fake HTTP calls/descendants stop, liveness remains responsive and saved
  checks survive. Fixed-host HTTPX has shared two-request concurrency, bounded
  retries/Retry-After handling, total attempt receipts, request/response caps and
  sanitized errors. Filing/source passage caps retain offsets and clipping flags.
  Full API suite: 439 passed/two host skips; 20 frontend tests, TypeScript, Ruff,
  frontend lint and production build pass. Actual providers, POSIX/hosted containment
  and browser journeys were not run this session; intake remains off by default.
  DB finalization and OS process creation are not real-time guarantees. See
  [[docs/sessions/2026-10-02 - Provider budgets and hard deadlines]] and
  [[docs/decisions/ADR-008 - Contained review deadlines and provider budgets]].
- [x] T025 - Save partial results after each stage and mark abandoned jobs interrupted
  after restart. Add explicit rerun behavior. Done when one failed provider does
  not discard independent checks or leave the UI polling forever.
  Evidence: independent stage failure preserves previous commits and later checks;
  startup recovery interrupts abandoned jobs. `/rerun` clones a terminal live
  review into a new prepared ID, preserving old evidence.
- [x] T026 - Add one-second status polling with terminal-state stop, backoff and
  accessible progress/error states. Done when progress is visible within two
  seconds and navigation/unmount stops unused requests.
  Evidence: TanStack one-second polling, 2-8-second error backoff, terminal stop,
  abort signal forwarding and desktop/mobile browser progress checks.
- [x] T027 - Add correlation IDs and structured stage timing/status/error logs with
  credential/document redaction. Done when one failed analysis can be diagnosed
  without logging filing text, raw identifiers or provider request secrets.
  Evidence: analysis UUID keyed job/stage start, terminal status, duration and
  error type; tests assert synthetic identifiers/exception body are absent.
  T024 fake transport tests also verify HTTP log suppression and sanitized errors;
  actual provider-adapter integration still needs its own checks.

## P0 / 6. Deterministic privacy and court checks

Depends on T020 and T023. SRS: FR-140 through FR-145, FR-160 through FR-162,
FR-164 through FR-166. T028-T031 can run independently of LLM access.

- [x] T028 - Validate/load versioned JSON court profiles with source, effective
  dates, court/judge scope and demo flag. Add a clearly synthetic demo profile.
  Done when invalid/stale/unsupported profiles cannot silently pass compliance.
  Evidence: strict synthetic JSON profile with source, effective dates, court/
  judge scope and demo flag; unknown, stale and mode-mismatched scope unavailable.
  No real court rule is configured or claimed.
- [x] T029 - Evaluate AI-use/disclosure presence against the selected profile;
  show the triggering requirement and uncertainty. Done when the same filing
  behaves correctly for AI-used yes/no and disclosure present/missing.
  Evidence: yes/no and standalone-heading presence/missing controls; hash-gated
  demo yields a missing-disclosure finding with requirement and uncertainty.
- [x] T030 - Implement SSN, contextual account-number and full-date-of-birth
  detectors with severity, masked snippets and review recommendations. Test
  benign legal citations/dates to constrain false positives. Done when planted
  identifiers are detected without claiming definitive legal redaction compliance.
  Evidence: fixture/live checks detect planted identifiers; benign citation/event
  date controls pass. Masked snippets, severity and human-review recommendations
  are owner-scoped.
- [x] T031 - Integrate rule/privacy findings and T022 masking into the pipeline.
  Done when no-citation filings still receive these checks and raw sensitive
  identifiers are absent from logs, summaries and external semantic payloads.
  Local findings/evidence and masked HTTP views run, including no-citation filings.
  T024's boundary and actual production-adapter request construction enforce
  full-filing masking before selection. Worker integration verifies wire payloads,
  no-citation checks, stored evidence and sanitized logs. Broader privacy detection
  accuracy and hosted security are independent release gates.

## P0 / 7. Citation verification and source retrieval

Depends on T004, T011, T020 and T023. SRS: FR-040 through FR-044, FR-080.

- [x] T032 - Extract citations with Eyecite, preserve occurrences/offsets and
  handle unsupported/ambiguous formats without dropping them silently. Done when
  the fixture citations and original spans are correctly identified. Verified
  locally: five curated occurrences, exact original Unicode/page/paragraph spans,
  distinct extraction support vs unrun verification, explicit 200-occurrence cap,
  private masked reads and populated migration preservation. API 472 passed/two
  host skips; frontend 20 tests, TypeScript, Ruff, ESLint and build pass.
  No live lookup, production migration or deployment. See
  [[docs/sessions/2026-10-06 - Local citation extraction]].
- [x] T033 - Implement the CourtListener adapter with token handling, normalized
  identities and bounded error mapping. Return verified/not-found/invalid/
  ambiguous/unavailable separately. Done when timeout/429/5xx never becomes not-found.
  Evidence: CourtListenerAdapter and schemas in integrations/courtlistener/; 23 unit tests
  in tests/unit/test_courtlistener_adapter.py verify all statuses and error mappings
  without spending provider credits; timeouts, 429s and 5xx never become not-found;
  token is redacted; Ruff and pytest pass. See [[docs/sessions/2026-10-07 - CourtListener citation adapter]].
- [x] T034 - Retrieve opinion text and metadata for resolved authorities, preserving
  provenance and distinguishing missing text. Done when name/court/year/citation/
  source URL and available source passages appear in stored results.
  Evidence: CourtListenerAdapter opinion retrieval (`get_opinion`, `resolve_cluster_opinion`,
  `resolve_authority`), `OpinionTextParser` (HTML block boundary extraction without scripts/styles),
  and lead opinion prioritization over dissents (resolving [[docs/issues/BUG-004 - First opinion reference can be a dissent|BUG-004]]);
  persistent `Authority` entity and `SafeAuthority` API contract; `SafeCitation.authority` linking
  and stored results in `GET /api/v1/analyses/{id}/citations`; 33 unit tests in `test_courtlistener_adapter.py`
  and 17 integration tests in `test_citation_pipeline.py` pass; 390 unit tests, 20 frontend tests,
  Ruff, and TypeScript pass with zero provider spend. See [[docs/sessions/2026-10-07 - Opinion text retrieval and authority persistence]].
- [x] T035 - Deduplicate outbound lookups while retaining all filing occurrences;
  cache public source responses within an analysis. Done when repeats share one
  authority lookup and each original location remains inspectable.
  Evidence: `CourtListenerCache` caches lookups, opinions, and resolved authorities with
  whitespace normalization and hit tracking; `verify_citations_for_analysis` deduplicates
  lookups across document mentions, preserves all occurrences with their exact offsets/segments,
  and links repeats to a single `Authority` entity; `verified_citation_stage` constructs
  stage results but is not registered in normal review workers; 42 unit tests in
  `test_courtlistener_adapter.py`, 4 unit tests in
  `test_citation_dedup.py`, and 19 integration tests in `test_citation_pipeline.py` pass;
  403 backend unit tests, 20 frontend vitest tests, Ruff, and TypeScript pass with zero
  provider spend. See [[docs/sessions/2026-10-07 - Outbound citation deduplication and response caching]].
- [x] T036 - Test verified, unresolved, malformed, ambiguous, duplicate and provider
  failure cases. Done when unresolved findings explicitly state database coverage
  limitations and never assert that a case is fabricated merely because absent.
  October 8 analysis: include normal worker registration/credential delivery,
  mixed-result persistence, evaluated/unavailable coverage, 200-occurrence/record
  limits and truncation. Fix reproduced runner/validator conflicts before enabling
  source verification; preserve strict ownership/provenance checks. Adapter lookup
  reasons/coverage limitations must survive persistence and reach the API/UI.
  See [[docs/issues/BUG-012 - Citation verification output conflicts with worker validation]].
  Verified October 8–10: dedicated partial paths, typed receipts/relations,
  original spans, mixed outcomes and bounded 200/201 occurrence results pass
  worker/persistence checks. Source/query snapshot bounds preserve uncertainty.

## P0 / 8. Claims and grounded propositions

Depends on T005, T011, T022, T032-T034. SRS: FR-060 through FR-063,
FR-081 through FR-086, FR-200 through FR-204.

- [x] T037 - Extract the cited proposition from local sentence/paragraph context;
  retain verbatim excerpt/offsets and link claims to citations. Done when every
  extracted claim has traceable context and multiple links are representable.
- [x] T038 - Select bounded relevant passages from the cited authority, including
  surrounding qualifications. Done when long opinions fit provider budgets and
  truncated/insufficient coverage is explicitly recorded.
- [x] T039 - Implement versioned prompts and schema-validated classification:
  supported, partially supported, unclear, potentially misrepresented or not enough
  source text. Include short explanation, evidence IDs and confidence label.
  Done when the supported and misleading fixture claims produce defensible differences.
- [x] T040 - Validate returned evidence IDs/excerpts against stored passages;
  handle refusals/invalid output, source absence and prompt-injection attempts.
  Done when unsupported references are rejected and missing evidence yields uncertainty.
- [x] T041 - Save actual model/prompt/method metadata and communicate confidence
  as a heuristic unless calibrated. Done when semantic findings are visibly
  AI-assisted review signals with human-review recommendations, not legal conclusions.

## P0 / 9. Quote forensics

Depends on T020, T032-T034. SRS: FR-120 through FR-126.

- [x] T042 - Extract quotations and associate nearby citations with ambiguity
  handling. Done when an uncertain association is not treated as certain.
- [x] T043 - Implement exact, normalized and RapidFuzz comparison in that order;
  preserve original quote/source spans, closest passage and similarity score.
  Done when altered text is distinguishable from exact/format-only matches.
- [x] T044 - Classify exact/normalized/close/not-found/source-unavailable outcomes
  and test punctuation, whitespace, ellipses and missing sources. Done when
  similarity is not presented as proof that a quotation preserves meaning.

## P0 / 10. Score, findings and graph

Depends on T029-T044. SRS: FR-100 through FR-104, FR-180 through FR-185,
FR-200 through FR-204; UX-001 through UX-004; NFR-080 through NFR-082.

- [x] T045 - Define/version scoring weights and deductions for authorities,
  propositions, quotations, privacy and court checks. Keep coverage/incomplete
  checks separate and handle no applicable checks. Done when critical issues
  deduct more than warnings, calculations are reproducible and unknown is not a pass.
- [x] T046 - Build the dashboard with score breakdown, coverage, counts, prominent
  critical findings and ready-for-review/needs-review/high-risk labels. Done when
  the score never claims filing safety and partial analyses are clearly labeled.
- [x] T047 - Build filterable findings and a detail panel with original excerpt,
  source passage/link, method, uncertainty, reason and next review action. Done
  when a user can inspect the basis of each seeded issue without leaving the workflow.
- [x] T048 - Generate graph nodes for document sections, claims and authorities
  with stable IDs and relationship/status metadata. Done when node counts and
  relationships match persisted findings instead of a separate hardcoded graph.
- [x] T049 - Render React Flow with bounded layout, status text/icons and node
  selection opening finding detail. Include an equivalent keyboard-accessible
  list. Done when graph and list expose the same substantive evidence.
- [x] T050 - Verify mobile/desktop layout, contrast, labels, focus order, loading,
  empty/error states and screen-reader feedback. Done when color is not the only
  signal and the complete P0 review flow can be used with a keyboard.
  October 11: desktop/mobile sequential keyboard review-to-export/reset and
  WCAG-tagged axe scans pass 2/2, including empty/error states. Contrast and
  keyboard text-scroll failures repaired. Live-region semantics checked; physical
  NVDA/VoiceOver testing is separate. [[docs/issues/BUG-019 - Low contrast labels and inaccessible document scroll]].

## P0 / 11. Report and integrated acceptance

Depends on T045-T050. SRS: FR-300 through FR-304; sections 17-18; AUD-001 through AUD-004.

- [x] T051 - Generate on-screen and Markdown/HTML assurance reports from saved
  results: timestamps, selected profile/version, mode, score/coverage, findings,
  evidence, passed checks and limitations. Done when the export agrees with the UI
  and requires no new LLM classification; escape untrusted HTML content.
- [x] T052 - Complete the full demo journey: load sample, select court/AI use, run,
  inspect score/graph, open at least two findings and export. Done when all twelve
  SRS section 18.2 acceptance steps pass against expected fixtures.
  October 11: final genuine-model browser journey passes all twelve controls,
  including supported Brown/Miranda/Obergefell, reversed Brown misrepresented,
  invented source insufficient_source, evidence/graph/report and owner reset.
  Cached public source provenance remains explicit. Three actual requests for four
  sourced claims; no model retries, paid fallback or evidence pruning. Forced
  outages are separate contained-worker controls, not normal fixture expectations.
  AI-reviewed synthetic acceptance is not expert real-case legal validation.
  [[docs/decisions/ADR-013 - Shared authority model requests and bounded quota admission]].
  [[docs/sessions/2026-10-11 - Accessibility performance and release gates]].
- [x] T053 - Test provider outages, rate limits, absent opinion text, LLM refusal,
  malformed uploads, no citations, interruption and retry. Done when independent
  results survive and every affected check communicates its actual state.
- [x] T054 - Run access-isolation, secret/log redaction, upload abuse, prompt
  injection and deletion/retention checks. Done when test reports document outcomes
  and no confidential material appears in fixtures or publicly served assets.
- [x] T055 - Measure demo performance: <=60-second normal analysis, <=2-second
  initial progress, <=3-second completed dashboard. Test the 20-page limit and
  maximum accepted inputs. Done when measured results and remaining limits are recorded.
  October 11: six model-disabled desktop/mobile analyses finish in 12.946–14.086s,
  progress 208–318ms and dashboard 472–783ms. Genuine cached-source/model journey:
  52.803s / 187ms / 641ms. Maximum 100,000-character, 2,000-paragraph browser flow:
  18.795s / 1,054ms / 544ms. Exact 20-page/10 MiB PDF worker extraction: 1.859s;
  excess page/byte/character/paragraph rejected. Local Windows/Chromium measurements;
  physical-device, hosted cold-start and arbitrary-PDF timings remain unverified.
  [[docs/sessions/2026-10-11 - Accessibility performance and release gates]].
- [x] T056 - Run lint, typechecks, unit/integration tests, frontend build and
  Playwright journey; review source provenance and requirement coverage. Done when
  no blocking failures remain and acceptance evidence is linked to the tasks.
  October 11: 709 backend controls passed in the initial full run; all 76 controls
  in the affected suites pass after correcting three failures, verifying all 712
  non-skipped controls (two Windows host skips). Frontend 30 tests, lint/typecheck/
  build, API Ruff, 11 isolated browser controls including the genuine model journey,
  three performance controls and source provenance/requirement review pass. Fixture
  hashes and all 18 expectation spans verified; 176 vault notes / 1,181 links have
  zero missing targets. Audit reports zero production vulnerabilities. Physical
  assistive-device, Linux containment and hosted acceptance remain scoped T057 gates.
  [[docs/sessions/2026-10-11 - Accessibility performance and release gates]].

## P0 / 12. Release and submission

Depends on T051-T056. SRS: DEP-001 through DEP-005, sections 19 and 23.

- [ ] T057 - Release the working app with migrations, exact CORS/origins, secrets,
  retention and single-process limits; verify readiness separately from liveness.
  Done when fresh hosted intake-to-export works and results remain session-scoped.
  October 11 preparation: readiness endpoint and focused fail-closed checks pass;
  public read-only probe observes health 200, exact CORS and SPA routes 200, but
  /ready and /capabilities remain 404. No hosting credentials/dashboard session are
  available; no hosted mutation/migration or intake enablement occurred.
  Release procedure: [[docs/delivery/Deployment guide]].
- [ ] T058 - Rehearse live and explicitly labeled cached demo modes on the hosted
  app, including a forced dependency failure. Done when the fallback cannot be
  confused with live verification and restart recovery is understood.
- [ ] T059 - Finish setup/deployment/troubleshooting docs, API configuration,
  limitations, third-party licenses/attribution and source links. Done when another
  developer can reproduce the app using the committed lockfiles and instructions.
  October 11: local preparation and isolated reproduction verified: fresh locked
  npm/uv installs, zero npm audit findings, build/typecheck and desktop/mobile
  keyboard/axe journeys 2/2. API example contains consumed settings only; unused
  planning switches removed. Browser/API notice artifacts and asset provenance
  recorded. Existing Render service instructions include local-to-Neon migration
  because free services lack shell access. API deployment root corrected to retain
  server-owned demo resources; production-only sync/resource checks and 27 demo
  controls pass. Frontend lint and 30 unit tests pass. No publication or hosted writes.
  Remains unchecked pending reproduction from a committed release checkpoint.
  [[docs/sessions/2026-10-11 - Setup and release documentation]].
- [ ] T060 - Prepare a two-to-three-minute demo, screenshots and recording showing
  citation misuse, quote evidence, graph, privacy/rules and report. Include AI limits
  honestly. Done when a product walkthrough matches the released behavior.
- [ ] T061 - Complete the official submission fields, project narrative, live URL,
  repository/demo links and team details; verify reviewer access and submit before
  the confirmed deadline. Retired: the deadline was missed; keep this historical
  task unchecked and exclude it from active scheduling. No submission is claimed.
- [ ] T062 - Record the release commit/tag, known limitations and unresolved P1/P2
  work; verify release URLs once more. Done when the released build is reproducible.

## P1 / 13. Enhancements after deployed P0 passes

Execute in the order below after the deployed core passes. Each task also
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

## P2 / 14. Extended product backlog

These are future capabilities; T212-T213 are release gates for real client use,
regardless of their original backlog priority. Core development uses public/synthetic data.

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

- 2026-10-07: T033 verified locally. Implemented CourtListenerAdapter and schemas
  with token validation, cluster extraction, and bounded error mapping. Returns
  verified/not-found/invalid/ambiguous/unavailable separately; timeouts, 429 rate
  limits, 5xx server errors, connection failures, budget exhaustion, and deadlines
  map to unavailable and never become not-found. Configured pytest cache/basetemp
  isolation in pyproject.toml. 23 adapter unit tests and Ruff pass locally with zero
  provider spending. Next: T034. [[docs/sessions/2026-10-07 - CourtListener citation adapter]].

- 2026-10-07: D006 verified locally. Rebuilt the film background/depth and
  evidence motion; fixed Authority typography/connectors and transition tails.
  Both masters, four web videos and poster pass metadata/byte budgets; internal
  critique scores are 8–9. Video/web typecheck, lint, final build, 20 unit tests,
  22 desktop/mobile browser cases and 2 post-copy checks pass. User aesthetic
  review remains open; previous exports are preserved. Next ordered task: T033,
  not started. [[docs/sessions/2026-10-07 - Pipeline film visual revision]].

- 2026-10-06: D006 planning resumed. Recorded the user's six responses, specified
  a 4K master with smaller web encodes, and prepared a 780-frame beat plan and
  critique criteria. Rejected copy is removed from the planned film direction;
  existing scene drafts still need alignment. Documentation links/timing checked;
  no video render, application test, homepage change, commit or push. See
  [[docs/sessions/2026-10-06 - Programmatic video choices and beat plan]].

- 2026-10-06: T032 verified locally. Eyecite retains five curated occurrences,
  duplicates and original Unicode spans. Parser support is separate from source
  verification; local extraction remains partial/unverified. Private masked reads,
  segment/page anchors, truncation, IPC rejection and populated migration pass.
  API 472 passed/two host skips; frontend 20 tests, TypeScript, Ruff, ESLint and
  build pass. No provider spending, hosted migration, commit or deployment.
  Next: T033. See [[docs/sessions/2026-10-06 - Local citation extraction]].

- 2026-10-02: T024 verified locally: contained stage cutoffs/shutdown preserve
  partial findings; provider budgets, retry/rate-limit policy and bounded context
  are tested without live requests. API 439 passed/two host skips; frontend 20
  tests, TypeScript, Ruff, frontend lint and build pass. T022/T031 remain open for
  real semantic request integration. No migration, commit, deployment or provider
  spending. Next: T032. See
  [[docs/sessions/2026-10-02 - Provider budgets and hard deadlines]].

- 2026-10-01: T023/T025-T030 verified locally. Owner-scoped local review now
  persists stage states and masked privacy/synthetic disclosure findings, with
  explicit unavailable citation-dependent stages, fresh-ID rerun, polling and
  redacted correlation logs. API 270 passed/two host skips; frontend 20 tests,
  lint/typecheck/build and desktop/mobile Chrome intake flow passed. T024 and
  T031/T022 outbound-provider boundaries remain open; no provider call, production
  migration, commit or deployment. See [[docs/sessions/2026-10-01 - Local review pipeline]].

- 2026-09-30: user accepted the initial homepage direction and wants future pages
  designed on the same theme. Began T023 review-job foundation. 265 API tests pass
  with two host-dependent skips; 17 frontend tests, typecheck, lint and build pass.
  Real legal runners, demo replay, provider-bound masking and public enablement remain
  pending. No deployment or provider call. See
  [[docs/sessions/2026-09-30 - Review job foundation]].

- 2026-09-29: D001 first homepage design implemented locally using supplied assets,
  GC Avalance and GSAP/CSS. Real preparation flows retained and browser-verified.
  User visual review precedes further art-direction refinement; T023 is next backend
  work. No deployment, commit, provider spending or database migration performed.

- 2026-09-28: user expanded scope to remaining Phase 3 and Phase 4. Private
  preparation/session/extraction foundations verified locally; T017/T019-T021
  completed at local development scope, T016/T018/T022 integration remains open.
  No paid/provider call, Neon migration, commit/push or public deployment.
  See [[docs/sessions/2026-09-28 - Private intake and document extraction]].

- 2026-09-28: user changed objective to product development with no deadline.
  T016 read-only reviewed demo verified; real engine replay remains pending. Added
  user's logo to the shell, product amendment/ADR and canonical module notes.
  No provider spending, database migration or hosted deployment performed.
  See [[docs/sessions/2026-09-28 - Product continuation and reviewed demo]].

- 2026-09-27: T009-T012 contracts, persistence and provenance verified; nine-entity
  isolated Neon migration/round trip/cascade passed and disposable schema removed.
  Phase 3 demo gate/private storage implemented, integration not complete. See
  [[docs/sessions/2026-09-27 - Contracts persistence and UI planning]].
  Final UI remains planning: [[docs/product/UI direction]].

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

## October 10 grounded review verification

User-expanded parallel scope implemented T037 onward locally. Checked tasks above
refer to exact-span, masking, provenance, quote comparison, stored-view/report and
ownership checks, with synthetic provider controls explicitly labeled. Real-case
semantic differentiation beyond the two live controls, the full twelve-step curated
journey, comprehensive accessibility/performance and hosted release are separate open
criteria. See [[docs/sessions/2026-10-10 - Grounded review verification]] and
[[docs/decisions/ADR-011 - Grounded review and saved result boundaries]].

October 10 v3 model verification: supported and reversed Brown fixture controls
returned supported/misrepresented with two bound source records each, 2.765 seconds
for two calls. Seven calls total across v1/v2 diagnostics and v3; no retries or
paid fallback. [[docs/research/Grounded proposition live acceptance - 2026-10-10]].

Final backend verification October 10: 671 passed, two Windows host skips; Ruff
passes. Frontend 30 tests, lint, TypeScript, OpenAPI generation and build pass.
Browser results checks pass 2/2 and intake/shell checks pass 10/10 in separate
fresh previews. The combined run hit the intended session quota; no guard was
relaxed. T053/T054 are verified at local test scope (outages/refusal/interruption/
input abuse, scoped results/evidence/reports, retention/deletion, masking and logs),
not a production security certification. Full curated acceptance, accessibility/performance and
hosted rollout remain open. [[docs/sessions/2026-10-10 - Grounded review verification]].
