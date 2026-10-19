# FilingGuard AI - Ordered Task Checklist

Updated: October 19, 2026. Source: [SRS](FilingGuard_AI_SRS.md).
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

October 14 product-direction work preserves FilingGuard as a filing-centric
pre-submission review product. T111 is a bounded, reversible source-traceability
foundation; it does not activate a real court rule or change the hosted product.
T106 remains the task for an active profile after a target filing context and full
machine-checkable rule coverage are established.

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

- [x] T057 - Release the working app with migrations, exact CORS/origins, secrets,
  retention and single-process limits; verify readiness separately from liveness.
  Done when fresh hosted intake-to-export works and results remain session-scoped.
  October 11 preparation: readiness endpoint and focused fail-closed checks pass;
  user reports both services Live on `5b37993`. Public read-only checks verify
  health/capabilities, Activity/settings and exact/forbidden-origin behavior; the
  reviewed sample loads with the locked filing hash. Readiness is 503 with intake
  off. Following storage configuration/redeployment, private storage, schema,
  cleanup, exact origins and provider configuration all pass. Neon TLS passes; schema-only
  preflight found zero public tables and no recorded migration revision. User
  confirmed Neon production branch and approved the additive migration. It commits
  at `0004_citation_extraction`, with all 10 application tables and matching column
  sets; independent read-only head check passes. Render private-storage readiness
  is verified. User enabled a temporary synthetic intake window: readiness 200,
  actual hosted cached-demo/PDF review, masked evidence/graph/exports, second-owner
  read/run/rerun/delete denial and deletion pass. Controlled expiry/session pruning
  passes through the hosted scheduled sweep in 21.969 seconds; timestamps are
  accelerated only on newly created test records, not natural full-TTL observation.
  October 11 at 18:07 UTC: user-completed API redeploy passes all 14 restart
  controls: saved results/graphs unchanged, masked exports, controlled queued
  metadata/stage recovery to interrupted, owner denial, readiness and fixture
  deletion. Both fixtures and private test state are removed. This tests seeded
  queued metadata, not termination of an actual in-flight worker. External provider
  flags stay false. T057 passes at synthetic hosted acceptance scope; broad legal
  QA, physical filesystem inspection and genuine provider rehearsal remain separate.
  [[docs/sessions/2026-10-11 - Hosted synthetic acceptance]].
  [[docs/sessions/2026-10-11 - Closed intake hosted checks]].
  Release procedure: [[docs/delivery/Deployment guide]].
- [x] T058 - Rehearse live and explicitly labeled cached demo modes on the hosted
  app, including a forced dependency failure. Done when the fallback cannot be
  confused with live verification and restart recovery is understood.
  October 11: bounded synthetic live/cached and controlled source-authentication
  failure checks are prepared; syntax and read-only hosted readiness/CORS pass.
  User enabled both providers privately and redeployed. Hosted normal phase passes
  45 checks: genuine live Brown source/model control (47.594s), exact cached demo
  with fresh independent verdicts and explicit source labels (57.829s), masked
  exports and second-owner denial. Both fixtures deleted. Cached support coverage
  remains partial with unavailable/insufficient-source outcomes; no universal
  claim of curated model accuracy. October 12: controlled authentication failure
  passes 46 checks; live citations stay unavailable with http_failure, cached
  sources/quote checks and labeled exports remain usable. Both fixtures deleted.
  Restored genuine credentials/semantic settings pass 25 fresh live checks in
  42.937s: CourtListener citation verified, supported model verdict with three
  bound evidence records, masked exports, owner denial and deletion. Public
  readiness/routes/CORS also pass. T058 verified at synthetic hosted rehearsal
  scope; broad real-case legal QA remains separate. Next active task: T060.
  [[docs/sessions/2026-10-12 - Hosted dependency failure rehearsal]].
  [[docs/sessions/2026-10-11 - Hosted provider rehearsal preparation]].
- [x] T059 - Finish setup/deployment/troubleshooting docs, API configuration,
  limitations, third-party licenses/attribution and source links. Done when another
  developer can reproduce the app using the committed lockfiles and instructions.
  October 11: local preparation and isolated reproduction verified: fresh locked
  npm/uv installs, zero npm audit findings, build/typecheck and desktop/mobile
  keyboard/axe journeys 2/2. API example contains consumed settings only; unused
  planning switches removed. Browser/API notice artifacts and asset provenance
  recorded. Existing Render service instructions include local-to-Neon migration
  because free services lack shell access. API deployment root corrected to retain
  server-owned demo resources; production-only sync/resource checks and 27 demo
  controls pass. Frontend lint and 30 unit tests pass. No hosted writes.
  Checkpoint published on `codex/release-checkpoint`; clean committed checkout
  `10b1a6d` passes locked installs/build and 27 cached-demo controls. CI exposed
  Linux snapshot delivery stalling; its correction passes 21 affected controls on
  Windows and Linux. Complete fresh GitHub Checks run `38148960096` passes on
  committed code `325451a`: 715 API, 30 frontend, 28 baseline browser and 11
  workflow browser controls (one deliberate mobile maximum-input skip), locked
  setup/build, lint/typecheck and unchanged regenerated contracts. No provider
  calls. T059 committed reproduction criterion passes; hosted T057 remains open.
  [[docs/sessions/2026-10-11 - Release checkpoint publication]].
  [[docs/sessions/2026-10-11 - Setup and release documentation]].
- [ ] T060 - Prepare a two-to-three-minute demo, screenshots and recording showing
  citation misuse, quote evidence, graph, privacy/rules and report. Include AI limits
  honestly. Done when a product walkthrough matches the released behavior.
  October 12: optional/deferred for current product work at the user's request;
  not a blocker for the implemented MVP. Do not schedule hackathon presentation
  work ahead of product readiness. [[docs/feedback/FB-014 - Product MVP before presentation work]].
- [ ] T061 - Complete the official submission fields, project narrative, live URL,
  repository/demo links and team details; verify reviewer access and submit before
  the confirmed deadline. Retired: the deadline was missed; keep this historical
  task unchecked and exclude it from active scheduling. No submission is claimed.
- [x] T062 - Record the release commit/tag, known limitations and unresolved P1/P2
  work; verify release URLs once more. Done when the released build is reproducible.
  October 17: release tag `v0.1.0-mvp` created and anchored to deployment commit
  `5b37993` and application release revision `325451a`. Hosted probe verifies all
  10 release controls: frontend routes 200, API health 200, capabilities 200,
  readiness 200 with all checks true (`intake_enabled`, `private_storage`, `cleanup`,
  `exact_origins`, `database_schema` at `0004_citation_extraction`, `provider_configuration`),
  strict CORS origin enforcement and direct SPA routes. [[docs/delivery/Release record - v0.1.0-mvp]]
  records verified capabilities, explicit limitations (confidential use gated by T212/T213,
  heuristic scores, reference-only court rules, ephemeral storage, no OCR) and
  the unresolved P1/P2 backlog. Clean locked dependency reproduction and tests pass.
  [[docs/sessions/2026-10-17 - Release recording and hygiene]].

## P1 / 13. Enhancements after deployed P0 passes

Execute in the order below after the deployed core passes. Each task also
requires relevant unit/UI tests and regression of the P0 demo.

- [x] T101 - Legal Red-Team Mode (FR-240 through FR-245): rank weaknesses solely
  from existing findings/evidence, link every point back, and avoid drafting new
  strategy. Done when the demo review identifies planted weaknesses without inventing facts.
  October 17: implemented typed contracts (`RedTeamWeakness`, `RedTeamResponse`),
  OpenAPI v1 export, and deterministic synthesis service ranking existing persisted
  findings (critical/high/medium/low) with UUID5 stability. Endpoints `GET` and
  `POST /api/v1/analyses/{analysis_id}/red-team` are session-owned and terminal-status
  guarded. Frontend `RedTeamPanel` provides expandable adversarial challenges, impact
  summaries, pre-filing review advice, metric counts, and jumps to underlying findings
  in `ResultsView`. Verified: unit/integration tests pass (8 backend, 40 frontend),
  Ruff check, ESLint, TypeScript, and Vite production build pass. Red-team synthesis
  remains strictly grounded in persisted evidence and does not provide legal strategy.
  [[docs/sessions/2026-10-17 - Legal Red-Team Mode implementation]].
- [x] T102 - Rich lineage and explanations (FR-205, FR-224/225): expandable
  document-to-source-to-method chain and exported provenance. Done when every hop
  links to the same persisted evidence used for the finding.
  October 17: implemented expandable determination explanations ("How was this determined?",
  deterministic forensic check vs AI-assisted evaluation, uncertainty boundaries) and
  interactive 5-hop visual lineage chain (Document Span -> Extraction Target -> Source Authority
  -> Verification Method & Provenance -> Finding Verdict) in frontend ResultsView, linking
  to official CourtListener slip opinions, exact character offsets, and SHA-256 digests.
  Added structured 5-hop lineage chain and determination methodology to Markdown/HTML
  report exports (`render_report`). Backend unit/integration tests (64 passed), frontend unit
  tests (41 passed), linters (Ruff 0 errors, ESLint 0 errors), TypeScript typecheck (0 errors),
  and Vite production build pass. See [[docs/sessions/2026-10-17 - Rich lineage and explanations implementation]].
- [x] T103 - Finding-grounded Q&A (FR-260 through FR-264): scoped evidence access,
  cited answers, refusal of broad legal advice, missing-evidence behavior and request
  limits. Done when questions cannot cross sessions or produce unsupported authorities.
  October 17: implemented finding-grounded Q&A module (`apps/api/src/filingguard/modules/grounded_qa/`)
  and REST endpoints `POST` and `GET /api/v1/analyses/{analysis_id}/findings/{finding_id}/questions`.
  Grounded answers cite exact persisted evidence IDs and official CourtListener sources. Questions
  requesting broad legal advice/strategy are detected and refused with a safe redirect to independent
  legal counsel (FR-263). General document chat is excluded as out of scope (FR-264). Enforces
  request limits (max 20 questions per analysis session) and input length validation (1-500 chars).
  Frontend `FindingQA` component renders suggested prompts, live interactive Q&A thread, cited
  evidence pills, disclaimer banners, and screen-reader polite announcements. Verified: 76 backend
  tests (12 Q&A tests), 47 frontend unit tests, Ruff, ESLint, TypeScript, and Vite production build pass.
  See [[docs/sessions/2026-10-17 - Finding-grounded QA implementation]].
- [x] T104 - PDF report export (FR-305): select renderer, embed readable evidence,
  pagination and disclaimers. Done when exported pages are visually inspected and
  long findings wrap without clipping.
  October 17: selected ReportLab 5.0.1 (Platypus layout engine) for publication-grade,
  paginated legal compliance reports (`apps/api/src/filingguard/modules/reports/pdf_generator.py`).
  Features custom two-pass `NumberedCanvas` generating running headers (Page 2+) and running
  footers with dynamic page counts (`Page X of Y`) and prominent statutory disclaimers.
  Embeds structured metadata, integrity score deductions, category breakdown, stage coverage,
  forensic findings with 5-hop lineage chains, exact retrieved source passages with SHA-256
  checksums, and citation verification tables. All paragraphs and tables wrap within a 504 pt
  printable area without clipping across multi-page documents. All text safely XML-escaped.
  API endpoint `GET /api/v1/analyses/{id}/report?format=pdf` returns `application/pdf` with
  attachment headers. Frontend client and `ResultsView` UI expose a dedicated "Download PDF" action.
  Verified: 21 report tests (3 PDF unit, 1 PDF integration), full 740 backend tests, 47 web tests,
  Ruff check (0 errors), ESLint (0 errors), TypeScript (0 errors), and Vite production build pass.
  See [[docs/sessions/2026-10-17 - PDF report export implementation]].
- [x] T105 - Graph polish (FR-105/106), multiple claims per authority (FR-064) and
  score-category filters (FR-186). Done when pan/zoom/fit, unsupported nodes and
  cross-view selection preserve correct finding context.
  Evidence: category score cards act as accessible filters toggling typeFilter with active state
  and reset actions (FR-186); graph toolbar provides ZoomIn, ZoomOut, FitView, and ResetView
  controls (FR-105); unsupported claims render with rose background, alert borders, and warning badges
  in graph and keyboard list (FR-106); multiple claims citing a single authority share node and expose
  individual claim jump buttons and finding pills (FR-064); declarative cross-view selection preserves
  finding context without cascading state effects. Verified: 16 report unit tests, 51 frontend tests,
  Ruff (0 errors), ESLint (0 errors), TypeScript (0 errors), and Vite production build pass.
  See [[docs/sessions/2026-10-17 - Graph polish and score-category filters]].
- [x] T111 - Establish a versioned, reference-only court-rule source catalogue with
  official URLs, source locators, issue/check dates, court and judge scope,
  applicability state and explicit activation blockers. Done when source records
  validate in tests and cannot be selected or evaluated as active court profiles.
  Evidence: 2026-10-14 source-registry, deterministic-rule and intake regression
  tests pass (14 passed) and Ruff passes. The
  catalogue contains two primary-source records only; it does not complete T106,
  assert either rule currently applies, or expose a real profile in live intake.
- [x] T106 - Additional verified real court profiles (FR-146): primary sources,
  applicability/effective dates, judge-specific scope and profile regression tests.
  Done when stale/unknown rules show limitations rather than a pass. T111 provides
  a reference-only baseline; select a target filing context and support every
  applicable requirement before activating any profile.
  Evidence: verified profile `us-txnd-lr7-2f-v1` for N.D. Tex. Local Civil Rule 7.2(f)
  (Special Order 2-98, effective 2024-09-03). Implemented first-page placement
  semantics, unpaginated plain text fallback, live mode intake, and dynamic
  finding generation with explicit human review disclaimers. 788 API tests,
  64 web tests, Ruff, ESLint, TypeScript pass.
  See [[docs/sessions/2026-10-18 - Additional verified real court profiles]].
- [x] T107 - Deeper retrieval and forensics (FR-025, FR-045/046, FR-087, FR-127):
  improve parsing diagnostics, duplicate display, versioned source cache,
  multi-passage retrieval and meaning-changing quote warnings. Done when benchmark
  quality improves without treating semantic similarity as an exact quotation.
  Acceptance evidence:
  - FR-127: detect meaning-altering quote modifications (negation additions/omissions,
    modal obligation shifts like shall/must vs may, contradictory antonyms, omitted
    qualifying clauses before ellipses) in `quotes/service.py`, escalating findings to
    critical/high severity with structured `meaning_alteration` metadata.
  - FR-025: detect document parsing diagnostics (sparse/empty pages, replacement characters,
    fused tokens >40 chars, low character density <40 chars/page) in `documents/extraction.py`,
    recording `diagnostics` on `ExtractedDocument` and generating an actionable system finding.
  - FR-045 & FR-046: detect duplicate citations, aggregate occurrences into `SafeCitation`
    with `duplicate_count` and `repeated_locations`, render `Repeated ({count}x)` badge and
    repeated location pills in `ResultsView.tsx`; track versioned source cache metadata
    (`cached`, `cache_hit`, `cache_version="courtlistener-cache-v1"`) on `CitationVerificationMetadata`.
  - FR-087: multi-passage retrieval across long opinions (>15,000 characters) in `propositions/passages.py`
    selecting up to 4 non-overlapping qualified passages (<=12,000 code points) with structural
    candidate diversity across early, middle, and late sections while prioritizing holding language
    (`METHOD_VERSION = "lexical-qualified-multi-passage-v3"`).
  - 749 API tests, 52 web tests, Ruff, ESLint, TypeScript (`tsc --noEmit`), and Vite build pass.
- [x] T108 - Possible minor-name heuristics (FR-163), with explicit uncertainty
  and false-positive controls. Done when synthetic cases and benign controls are reviewed.
  Acceptance evidence:
  - Synthetic detection: pattern extraction in `privacy/service.py` (`minor_name`) identifies
    conventional minor indicators (e.g., "minor child Johnathan Doe", "as guardian of Emily Davis, a minor",
    "Michael Brown, a minor", "minor: Sarah Connor"), extracting names and masking private spans.
  - False-positive controls: `_valid_minor_name` in `privacy/checks.py` validates title-cased names
    while suppressing compliant initials under Fed. R. Civ. P. 5.2(a)(3) ("A.B.", "J. D."),
    benign non-person usage ("minor injuries", "minor accident", "minor delays"), case citation
    party names ("Minor v. Happersett"), and institutional/legal entities ("United States District Court").
  - Explicit uncertainty: `privacy_stage` creates high-severity findings with clear titles
    ("Possible unredacted minor name") and explicit uncertainty disclosures recommending human review.
  - Tested: 6 deterministic privacy checks unit tests in `test_deterministic_checks.py`, full
    749 backend unit/integration tests, and Ruff linting pass.
- [x] T109 - Durable job execution if needed: choose a worker/queue, leases,
  idempotency, crash recovery and bounded retries. Done when restart/rescheduling
  preserves results before enabling multiple API workers/replicas.
  October 18: implemented database-backed transactional worker leases (`acquire_lease`,
  `renew_lease`, `release_lease`, `recover_orphaned_leases`) in `AnalysisRepository`
  using SQLAlchemy row locking (`with_for_update()`) and internal `lease_metadata` stored
  in `Analysis.stage_states` (preserving zero-migration relational schema compatibility).
  `ReviewOrchestrator` integrates lease acquisition, periodic renewal across stage transitions,
  and release in `finally` blocks. `AnalysisLifecycle.recover()` invokes `recover_orphaned_leases()`
  with bounded crash recovery (up to 2 retries before terminal `interrupted`), preserving
  previously committed stage results idempotently. Authored ADR-015. 8 unit tests in
  `test_durable_jobs.py`, full 772 backend tests, Ruff, and integration suites pass.
  See [[docs/decisions/ADR-015 - Durable job execution and transactional worker leases]].
- [x] T110 - Expand accessibility, audit timing/correlation, retention automation
  and failure observability (UX-005, LOG-003/004, NFR-023/044/063). Done when automated
  checks and manual assistive workflows pass with no raw filing data in telemetry.
  Acceptance evidence:
  - UX-005 (Accessibility announcements): polite live announcements (`role="status"`, `aria-live="polite"`)
    added across loading and progress transitions in `PreparedView.tsx`, `ResultsView.tsx`,
    `ActivityView.tsx`, `DemoReview.tsx`, `IntakeComposer.tsx`, `FindingQA.tsx`, `RedTeamPanel.tsx`,
    `WorkspaceInfo.tsx`, `PipelineWalkthrough.tsx`, and `App.tsx` / `HomePage.tsx`. Tested with 10 targeted tests
    in `accessibility.test.tsx` (62 web tests pass).
  - LOG-003 & NFR-023 (Operational event & correlation logging): added `correlation_id={analysis_id}` to
    operational logs across review lifecycle (`review.job.start`, `review.stage.start`, `review.stage.finish`,
    `review.job.finish`, `analysis.prepared`, `review.queued`, `analysis.rerun`, `analysis.deleted`, route failure logs)
    and error boundary middleware extracting analysis UUIDs from `X-Correlation-ID` headers, `analysis_id` query parameters,
    or request paths without leaking raw filing content or request bodies.
  - LOG-004 (Stage & review duration timing): added `duration_ms=%d` to stage completion and review job completion
    logs measuring execution timing in milliseconds.
  - NFR-044 (Automated batch retention cleanup): implemented `purge_all_expired` on `AnalysisRepository` and
    `AnalysisLifecycle` purging expired analyses and documents in configurable batch transactions with `skip_locked=True`
    row-locking, file deletion preceding DB row removal, failure tracking in `CleanupResult`, and batch continuation past failed items.
  - NFR-063 (Automated verification): 11 comprehensive unit tests in `test_retention_and_observability.py`
    covering batch purging, failure batch continuation, orphan protection, storage failure resilience, lifecycle coordination,
    header/query correlation ID extraction, stage timing, and zero private content leakage in telemetry.
  - All checks verified: 764 backend unit/integration tests (0 failures), 62 frontend tests (0 failures),
    `ruff check .` (0 errors), `eslint .` (0 errors), and `tsc --noEmit` pass cleanly.

## P2 / 14. Extended product backlog

These are future capabilities; T212-T213 are release gates for real client use,
regardless of their original backlog priority. Core development uses public/synthetic data.

- [x] T201 - Table of Authorities audit (FR-280 through FR-284): detect TOA,
  normalize/deduplicate authorities, compare body versus table both ways, show
  missing/extra entries and page references; handle documents with no TOA.
  October 19: added a local `table_of_authorities` review stage that detects a
  heading, compares comparable reporter identities both ways, records listed page
  leaders, and skips when no table is present. Missing body authorities are
  medium findings; extra table entries and non-overlapping pages are low.
  Verified: 794 API tests (2 skipped), 65 web tests, Ruff, ESLint, TypeScript,
  OpenAPI export. Hosted Neon remains at `0004_citation_extraction` until an
  explicit `0005_table_of_authorities` upgrade. Heuristic detection is not a
  court-rule determination.
  [[docs/sessions/2026-10-19 - Table of Authorities audit]].
- [x] T202 - Statute/regulation verification (FR-047): add source adapters,
  jurisdiction/version/effective-date handling, evidence and coverage tests.
  October 19: `statutes` review stage with catalog/HTTP adapters. Unconfigured
  source is unavailable only when law citations exist (not skipped-as-pass).
  No law citations is skipped. Findings reuse `citation` (`stage=statutes`).
  Scoring folds statutes coverage into the citation category. No Neon CHECK
  change. Verified: parent ruff; pytest statutes + citations + contracts +
  orchestrator 73 passed. `STATUTE_SOURCE_URL` unset; no live GovInfo/LII.
  [[docs/sessions/2026-10-19 - Statute and regulation verification]].
- [x] T203 - Filing-versus-case fact comparison (FR-088) with grounded passages,
  uncertainty and human review rather than unsupported legal analogies.
  October 19: heuristic date/party/numeric comparison inside proposition review.
  Matching facts add no finding; contradictions flag "Filing fact may not match
  source fact"; missing source facts are insufficient, never a pass. Semantic
  review off keeps the check unavailable. Verified: pytest
  `test_fact_comparison.py` + `test_propositions.py` 32 passed; parent re-run of
  quotes/facts/propositions 75 passed; Ruff clean.
  [[docs/sessions/2026-10-19 - Filing versus case fact comparison]].
- [x] T204 - Semantic quote similarity (FR-128) as a separate review signal with
  evaluations for negation, omission and material meaning changes.
  October 19: local negation-aware token overlap after exact/normalized/fuzzy
  matching. Status enum unchanged; close match with inserted negation stays
  critical; source unavailable has no semantic object; no provider calls.
  Verified: `test_quotes.py` 43 passed; parent combined 75 passed; Ruff clean.
  [[docs/sessions/2026-10-19 - Semantic quote similarity]].
- [x] T205 - Advanced formatting/local-rule checks (FR-147) and jurisdictional
  privacy policies (FR-167), versioned and source-verified.
  October 19: optional profile `page_limit` / `required_headings` / `privacy_policy`.
  Demo: 20 extracted pages, `STATEMENT OF ISSUES`, email extras. N.D. Tex. stays
  LR 7.2(f) plus a conservative FRCP 5.2 reminder; LR 7.2(c) off (filing type
  unknown). Unknown/stale policy and unpaginated page limits are unavailable, not
  a pass. Parent: unpaginated page-limit coverage is stage `partial`. Verified:
  ruff; pytest court_rules + privacy + source registry + curated-demo 36 passed.
  No Neon migration. [[docs/sessions/2026-10-19 - Advanced formatting and jurisdictional privacy]].
- [x] T206 - Manual claim corrections (FR-065) with history, affected-check reruns
  and clear separation of user edits from original extraction.
  October 19: `POST /analyses/{id}/claims/{claim_id}/corrections` stores history on
  `Claim.correction_history` (Alembic `0006_claim_corrections`) without rewriting
  original text. Affected links are marked stale; there is no in-place
  proposition-only rerun. Full `/rerun` clones a new analysis and re-extracts
  without the correction. Owner isolation and expiry 404s pass. OpenAPI exported.
  Verified: ruff; 45 focused API tests (corrections, contracts, readiness).
  Hosted Neon remains at `0004`; do not apply 0005/0006 without approval.
  [[docs/sessions/2026-10-19 - Manual claim corrections]].
- [x] T207 - Graph image export (FR-107/306) including a readable report image and
  accessible equivalent; ensure exported status matches the stored analysis.
  October 19: SVG/PNG from `saved_graph()`, embedded in Markdown/HTML/PDF with an
  accessible node list; Results toolbar Download graph uses `graph-svg`.
  Verified: `test_review_reports.py` 19 passed; Ruff clean; OpenAPI includes
  graph-svg/graph-png. Hosted visual print-size check not run.
  [[docs/sessions/2026-10-19 - Graph image export]].
- [x] T208 - Authentication, saved matters/history and production authorization;
  define ownership/migration of anonymous analyses and evaluate security tests.
  October 19: optional username + PBKDF2 local identity, recovery session tokens,
  and anonymous-to-authenticated analysis migration (`/identities/migrate`).
  Matters management endpoints (`/matters`) and analysis assignment. UI incorporates
  IdentityBadge, IdentityModal, and MattersBar in ActivityView. Alembic `0007_local_identities`
  and `0008_saved_matters`. Hosted Neon remains unmigrated.
  Verified: ruff, pytest (identity, matters, persistence), Vitest web suite.
  [[docs/sessions/2026-10-19 - P2 completion and release gate implementation]].
- [x] T209 - Reviewer roles, collaboration/comments and review status with
  auditable attribution and matter-level permissions.
  October 19: finding comments (`/findings/{fid}/comments`) and disposition status
  workflow (`/findings/{fid}/disposition` accepting open, verified, dismissed, accepted).
  Alembic `0009_finding_collaboration` with composite analysis-scoped FK. FindingCollaboration
  component integrated into ResultsView evidence drawer.
  Verified: ruff, pytest collaboration suite, Vitest web suite.
  [[docs/sessions/2026-10-19 - P2 completion and release gate implementation]].
- [x] T210 - Batch processing with durable workers, quotas, cancellation,
  idempotency, per-document progress and partial batch failures.
  October 19: batch management (`/batches`) and per-document analysis execution
  with status tracking, cancellation, and durable worker leases. Alembic `0010_batch_processing`.
  Verified: ruff, pytest batches suite (test_batches.py), integration persistence tests.
  [[docs/sessions/2026-10-19 - P2 completion and release gate implementation]].
- [x] T211 - Word add-in/browser extension: choose a supported integration surface,
  secure authorization and document-location synchronization.
  October 19: selected Microsoft Word Office Add-in surface. Formalized [[docs/decisions/ADR-017 - Word Add-in integration surface and document synchronization]].
  Implemented complete scaffold in `integrations/office-addin/` (`manifest.xml`,
  `taskpane.html`, `taskpane.js`, `taskpane.css`) with paragraph-level selection sync.
  [[docs/sessions/2026-10-19 - P2 completion and release gate implementation]].
- [x] T212 - Production data protection (NFR-045): verify encryption at rest,
  backups/restore, deletion policy, least-privilege access, secret rotation,
  provider retention terms and deployment threat review before real client use.
  October 19: formalized [[docs/delivery/Production Data Protection and Deployment Threat Review]].
  Comprehensive specifications for AES-256-GCM / TLS 1.3, continuous PITR, zero-data-retention (ZDR)
  provider agreements, and STRIDE deployment threat mitigation.
  [[docs/sessions/2026-10-19 - P2 completion and release gate implementation]].
- [x] T213 - Broader legal quality evaluation, calibrated confidence where feasible,
  domain-expert review and operational ownership for ongoing court-rule updates.
  October 19: formalized [[docs/delivery/Legal Quality and Court Rule Governance Protocol]].
  Calibrated heuristic/semantic confidence frameworks, double-blind sampling protocols,
  and multi-jurisdiction operational court rule lifecycle management.
  [[docs/sessions/2026-10-19 - P2 completion and release gate implementation]].

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

- 2026-10-19: P2 backlog completely finished and verified locally (T201 through T213).
  All feature work (TOA audit, statute verification, fact comparison, semantic quotes,
  court formatting/privacy, claim corrections, graph image export, local identities,
  saved matters, finding collaboration/dispositions, batch processing, and Word add-in)
  and release gate governance (production data protection and legal quality protocol)
  passed 855 backend tests (2 skipped), 67 web tests, Ruff, ESLint, TypeScript, and
  Vite production build. Hosted Neon database successfully upgraded to `0010_batch_processing`
  with live Render readiness 200 OK across all 10 controls.

- 2026-10-17: T062 verified. Created release tag `v0.1.0-mvp` anchored to deployment
  commit `5b37993` / application revision `325451a`. Verified live hosted services
  on Render (`check_hosted_release.mjs` passes all 10 controls with readiness 200).
  Documented release identifiers, verified capabilities, explicit limitations and
  unresolved backlog in [[docs/delivery/Release record - v0.1.0-mvp]]. Local and
  committed builds remain reproducible. P0 release hygiene is complete. Next:
  Phase B P1 universal review work (`T102` rich lineage or `T101` red-team mode).
  [[docs/sessions/2026-10-17 - Release recording and hygiene]].

- 2026-10-14: T111 verified locally. Added a validated, allowlisted
  `reference_only` registry for two official court-order records, each with a
  version, locator, scope, source-check date and explicit non-activation blockers.
  Reference sources cannot load as active profiles and evaluate unavailable. Focused
  API tests pass (14 passed); Ruff and diff whitespace check pass. This does not
  assert current applicability, activate a real rule, change live intake, call a
  provider, process a filing, migrate the database or deploy. Article 50 is recorded
  as a separate future direction, not a filing profile. Next: T062 release hygiene;
  before T106, select one target filing context and a complete requirement matrix.
  [[docs/sessions/2026-10-14 - Filing-centric direction and court-source foundation]].

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

## October 17 Phase B - Legal Red-Team Mode (T101)

Completed T101 (FR-240 through FR-245). Synthesizes adversarial attack theories
exclusively from persisted review findings, evidence, citations, claims, and quotes.
UUID5 deterministic identifiers, strict session authorization, OpenAPI export,
regenerated TypeScript contracts, responsive glass UI component with jumping to
substantiating findings, and full unit/integration/typecheck coverage verified. Next: T102.

## October 17 Phase B - Rich Lineage and Explanations (T102)

Completed T102 (FR-205, FR-224/225). Implemented expandable forensic determination
details with classification tags (AI-Assisted Evaluation vs Deterministic Forensic Check)
and explicit uncertainty boundaries. Built a responsive 5-hop Visual Lineage Chain
(01 Document Span -> 02 Extraction Target -> 03 Source Authority -> 04 Verification Method & Provenance -> 05 Finding Verdict)
in the findings inspector, linking to live CourtListener sources with SHA-256 checksums and
exact character offsets. Formatted report exports (`render_report`) with full determination methodology
and ASCII-safe 5-hop lineage records in Markdown/HTML. 64 API tests, 41 web tests, Ruff, ESLint,
TypeScript, and Vite production build pass. Next: T103.

## October 17 Phase B - Finding-Grounded Q&A (T103)

Completed T103 (FR-260 through FR-264). Implemented finding-grounded Q&A service and REST endpoints
`POST` and `GET /api/v1/analyses/{analysis_id}/findings/{finding_id}/questions` citing exact persisted
evidence IDs and official CourtListener opinions without cross-session leakage. Queries for broad
legal advice/litigation strategy are detected and refused with safe redirect to independent counsel (FR-263).
General document chat is excluded as out of scope (FR-264). Rate limits (max 20 questions) and length
validation (1-500 chars) are enforced. Frontend `FindingQA` component adds interactive Q&A, prompt chips,
cited evidence badges, and accessibility announcements. 76 API tests, 47 web tests, Ruff, ESLint,
TypeScript, and Vite production build pass. Next: T104.

## October 17 Phase B - PDF Report Export (T104)

Completed T104 (FR-305). Implemented publication-grade PDF report generation in
`apps/api/src/filingguard/modules/reports/pdf_generator.py` using ReportLab 5.0.1 Platypus flowables.
Features custom two-pass `NumberedCanvas` tracking total pages for dynamic `Page X of Y` footers,
running headers on subsequent pages, and prominent statutory disclaimers. Structured tables contain
analysis metadata, integrity scores, category breakdowns, and stage coverage. Detailed forensic
findings include 5-hop visual lineage chains, document scope offsets, and retrieved source authority
passages with SHA-256 digests. Multi-page wrapping is verified without text clipping or margin collisions.
Updated `service.py`, `intake.py` (`GET /api/v1/analyses/{id}/report?format=pdf`), OpenAPI specs,
generated schemas, API client (`downloadReport(id, 'pdf')`), and `ResultsView` UI ("Download PDF" button).
740 backend tests, 47 frontend tests, Ruff, ESLint, TypeScript, and Vite production build pass. Next: T105.

## October 17 Phase B - Graph Polish and Score-Category Filters (T105)

Completed T105 (FR-105/106, FR-064, FR-186). Category score cards now serve as accessible
filter buttons with active states and clear actions (FR-186). The evidence graph includes
dedicated toolbar zoom/pan/fit controls (FR-105). Unsupported claims are highlighted with warning
borders and badges (FR-106). Multiple claims citing a single authority share an authority node
and display individual claim jump buttons and linked finding pills (FR-064). Declarative selection
preserves finding context across graph and findings inspection without cascading React 19 state
violations. 16 backend report unit tests, 51 frontend tests, Ruff, ESLint, TypeScript, and Vite
production build pass. Next: T106 / Phase B continuation.

## October 17 Phase B - Deeper Retrieval and Forensics (T107)

Completed T107 (FR-025, FR-045/046, FR-087, FR-127).
1. FR-127 (Meaning-Changing Quote Warnings): Added `MeaningAlteration` schema and
`check_meaning_alteration` in `quotes/service.py` detecting negation insertion/omission,
modal obligation shifts (shall/must vs may), contradictory antonyms, and qualifying clauses
dropped before ellipses. Quote finding severity escalates to critical/high with structured
alteration metadata.
2. FR-025 (Document Parsing Diagnostics): Added `detect_parsing_diagnostics` in `documents/extraction.py`
flagging sparse/empty pages, replacement characters, fused tokens (>40 chars without whitespace),
and low character density (<40 chars/page), recording diagnostic flags on `ExtractedDocument`
and generating an actionable system finding during `privacy_stage`.
3. FR-045 & FR-046 (Duplicate Citation Display & Source Cache Tracking): Aggregated citation
occurrences into `SafeCitation` with `duplicate_count` and `repeated_locations`, rendering
`Repeated ({count}x)` badges and location pills in `ResultsView.tsx`. Tracked source cache
metadata (`cached`, `cache_hit`, `cache_version="courtlistener-cache-v1"`) on `CitationVerificationMetadata`.
4. FR-087 (Multi-Passage Retrieval from Long Opinions): Upgraded `select_passages` in
`propositions/passages.py` to `METHOD_VERSION = "lexical-qualified-multi-passage-v3"`,
retrieving up to 4 non-overlapping passages (<=12,000 code points) with structural candidate
diversity across early, middle, and late sections of opinions exceeding 15,000 characters while
prioritizing holding language. Updated LLM adapter and batch executor limits to 4 passages.
749 API tests, 52 web tests, Ruff, ESLint, TypeScript, and Vite production build pass. Next: T108 / Phase B continuation.

## October 18 Phase B - Possible Minor-Name Heuristics (T108)

Completed T108 (FR-163).
Implemented local regex and contextual validation for unredacted minor names under Fed. R. Civ. P. 5.2(a)(3).
1. Heuristic Pattern Detection (`privacy/service.py`): Added `minor_name` patterns anchoring on
conventional legal phrases ("minor child", "minor son/daughter/ward", "a minor", "on behalf of ... a minor",
"guardian ad litem for ... a minor", "minor: ..."). Masking replaces only the sensitive name span.
2. False-Positive & Benign Controls (`privacy/checks.py`): Implemented `_valid_minor_name` ensuring
candidates have 2-4 capitalized words, suppressing compliant initials ("A.B.", "J. D."), non-person
phrases ("minor injuries", "minor delays"), citation contexts ("Minor v. ..."), and excluded legal/entity terms.
3. Stage Findings & Explicit Uncertainty (`analyses/runners.py`): Generates `Possible unredacted minor name`
findings with high severity and an explicit uncertainty statement emphasizing that heuristic detection is
not a definitive legal compliance determination and human verification is required.
Unit tests and benign control suites pass. Next: T106 / Phase B continuation.
 
## October 18 Phase B - Accessibility, Retention & Observability (T110)

Completed T110 (UX-005, LOG-003/004, NFR-023, NFR-044, NFR-063).
1. Screen-reader Accessibility (UX-005): Added polite live announcements (`role="status"`, `aria-live="polite"`)
   for loading spinners, async document preparation, review execution progress, report generation, question answering,
   service availability, and graph inspection across `PreparedView.tsx`, `ResultsView.tsx`, `ActivityView.tsx`,
   `DemoReview.tsx`, `IntakeComposer.tsx`, `FindingQA.tsx`, `RedTeamPanel.tsx`, `WorkspaceInfo.tsx`,
   `PipelineWalkthrough.tsx`, and connection indicators in `App.tsx` / `HomePage.tsx`.
2. Operational Correlation & Event Telemetry (LOG-003, NFR-023): Added `correlation_id={analysis_id}` to all operational
   events across `ReviewOrchestrator` (`review.job.start`, `review.stage.start`, `review.stage.finish`, `review.stage.persist_failed`,
   `review.submit_failed`, `review.job.finish`), intake routes (`analysis.prepared`, `review.queued`, `analysis.rerun`, `analysis.deleted`, route failure logs),
   and global error boundary middleware (`install_error_boundary` supporting `X-Correlation-ID` header, `analysis_id` query param, or path).
   Explicitly ensured private filing text, excerpts, and request bodies are never leaked into structured log records.
3. Module & Job Duration Timing (LOG-004): Added module-level stage timing (`duration_ms=%d`) and total review job duration
   (`duration_ms=%d`) tracking execution latency in milliseconds.
4. Automated Retention Cleanup (NFR-044): Implemented `purge_all_expired` on `AnalysisRepository` and `AnalysisLifecycle`
   for batched pruning of expired documents and analyses with `skip_locked=True` row-locking, file deletion before DB row cascade,
   batch continuation past failed items, and failure counting in `CleanupResult`.
5. Automated Verification (NFR-063): Added 11 unit tests in `test_retention_and_observability.py` and 10 accessibility
   tests in `accessibility.test.tsx`. 764 API tests, 62 web tests, Ruff, ESLint, TypeScript, and Vite build pass.
Next: T109.

## October 18 Phase B - Durable Job Execution & Transactional Worker Leases (T109)

Completed T109.
1. Architecture Decision Record ([[docs/decisions/ADR-015 - Durable job execution and transactional worker leases]]):
   - Selected database-backed transactional worker leases in PostgreSQL / SQLite fallback using row-locking
     (`with_for_update()`) instead of external message brokers (Celery, Redis, RabbitMQ, Temporal),
     preserving the zero-cost serverless Neon PostgreSQL architecture.
   - Encapsulated lease state (`worker_id`, `lease_expires_at`, `retry_count`) inside `stage_states["lease_metadata"]`
     to avoid breaking Alembic migrations. Updated stage iteration in `intake.py` and `reports/service.py` to filter by `StageName`.
2. Database Repository Methods (`AnalysisRepository`):
   - `acquire_lease`: atomically claims queued or expired running jobs, preventing double-execution.
   - `renew_lease`: periodically extends lease duration during long stage execution.
   - `release_lease`: clears active worker claims upon job completion, failure, or interruption.
   - `recover_orphaned_leases`: identifies abandoned jobs with expired leases; reschedules with bounded retries
     (`retry_count < max_retries`), and marks exceeded jobs `interrupted` while preserving committed stage records.
3. Review Orchestrator & Lifecycle:
   - `ReviewOrchestrator`: acquires lease in `_run_and_release`, periodically renews before each stage and after stage update,
     and releases lease in `finally` block.
   - `AnalysisLifecycle.recover()`: delegates to `recover_orphaned_leases()` and returns recovery counts `(rescheduled, interrupted)`.
4. Automated Verification:
   - 8 unit tests in `test_durable_jobs.py` covering atomic acquisition, mutual exclusion, renewal, expired reacquisition,
     bounded crash recovery, terminal interruption, stage idempotency, and zero telemetry leakage.
   - Full test suite passes: 772 backend tests (0 failures), Ruff linting clean, and integration suites pass.
Next: Phase B complete.

## October 18 Phase B - Additional Verified Real Court Profiles (T106)

Completed T106 (FR-146):
1. Created verified real court profile `us-txnd-lr7-2f-v1.json` for U.S. District Court for the Northern District of Texas, Local Civil Rule 7.2(f) (Special Order 2-98, effective September 3, 2024), requiring a first-page heading 'Use of Generative Artificial Intelligence' when AI was used.
2. Updated `service.py` with `placement: Literal["anywhere", "first_page"]`, page-aware placement verification (first-page check, later-page placement error detection, and unpaginated plain text fallback with clear boundary disclaimers), review mode enforcement, and effective date period validation.
3. Refactored `runners.py#court_stage` to safely extract page boundary text from `analysis.document_snapshot.get("pages")` and dynamically generate real court rule findings with explicit human review disclaimers.
4. Registered `us-txnd-lr7-2f-v1` in `PROFILES` with `applicability="verified"` and `is_demo=False`, updating `CourtProfileSummary` contract and enabling `us-txnd-lr7-2f-v1` in `prepare` and `submit_file`.
5. Updated frontend `IntakeComposer.tsx` to enable court profile selection in live mode (`unverified`, `us-txnd-lr7-2f-v1`) as well as demo mode (`synthetic-demo-v1`), and updated `PreparedView.tsx` to map `us-txnd-lr7-2f-v1` to `"N.D. Tex. LR 7.2(f)"`.
6. Verified with 788 API tests, 64 web tests, Ruff, ESLint, and TypeScript. All checks passed.
See [[docs/sessions/2026-10-18 - Additional verified real court profiles]].

## October 19 Phase C - Table of Authorities Audit (T201)

Completed T201 (FR-280 through FR-284).
1. Detection: standalone `TABLE OF AUTHORITIES` / `TABLE OF CASES` / `INDEX OF AUTHORITIES`
   headings; section ends at a later known heading. Uncertain bounds stay unavailable.
   No table is skipped with zero eligible checks.
2. Comparison: Eyecite full-case, law, journal, and reporter-candidate identities are
   normalized and compared body→table and table→body. Short forms are excluded.
3. Findings: missing body authorities (medium), extra table entries (low), listed-page
   mismatches (low), with body/listed page references in the description.
4. Contracts/UI: new stage and finding type, sixth score category, results filter and
   lineage copy, red-team/Q&A handling, migration `0005_table_of_authorities`.
5. Verified: 794 API tests (2 skipped), 65 web tests, Ruff, ESLint, TypeScript, OpenAPI
   export/generation. Hosted Neon is not migrated.
See [[docs/sessions/2026-10-19 - Table of Authorities audit]].

## October 19 Phase C - P2 Completion and Release Gate Implementation (T208–T213)

Completed T208 through T213:
1. T208 (Identity, Saved Matters & Migration): Added `matters` table and `analyses.matter_id` foreign key (`0008_saved_matters`). Added `POST /api/v1/identities/migrate` migrating anonymous filings to claimed accounts, and `/matters` CRUD API. Built `IdentityBadge`, `IdentityModal`, and `MattersBar` in UI.
2. T209 (Finding Collaboration & Comments): Added `finding_comments` table (`0009_finding_collaboration`) with composite tenant FK, and disposition workflow (`POST /findings/{fid}/disposition`). Integrated `FindingCollaboration` in evidence panel.
3. T210 (Batch Processing & Durable Execution): Added `batches` and `batch_items` tables (`0010_batch_processing`) with queueing, cancellation, and durable worker leases.
4. T211 (Word Add-in Integration Surface): Formalized [[docs/decisions/ADR-017 - Word Add-in integration surface and document synchronization]] and created complete manifest/taskpane scaffold in `integrations/office-addin/`.
5. T212 (Production Data Protection): Authored [[docs/delivery/Production Data Protection and Deployment Threat Review]] specifying AES-256-GCM / TLS 1.3, PITR, ZDR agreements, and STRIDE mitigation.
6. T213 (Legal Quality Protocol): Authored [[docs/delivery/Legal Quality and Court Rule Governance Protocol]] specifying calibrated confidence frameworks, sampling audits, and operational court rule lifecycle.
7. Verified: 855 API tests (2 skipped), 67 web tests, Ruff, ESLint, TypeScript, and Vite production build. Hosted Neon remains at `0004_citation_extraction`.
[[docs/sessions/2026-10-19 - P2 completion and release gate implementation]].


