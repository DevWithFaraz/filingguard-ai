---
type: delivery
status: verified
date: 2026-10-17
tags: [delivery, release, verification, provenance]
---
# Release record — v0.1.0-mvp

## Release identifiers
- **Release tag:** `v0.1.0-mvp`
- **Application release commit:** `325451ada388dc908b7a28c9d2b8dd8362a52338` (passing [GitHub Actions Checks run 38148960096](https://github.com/DevWithFaraz/filingguard-ai/actions/runs/38148960096))
- **Deployment rollout commit:** `5b379934eef192b005fe45da9b0a1dcf1f6188e4` (user-verified Live on Render)
- **Branch:** `codex/release-checkpoint`
- **Database migration head:** `0004_citation_extraction` (Neon PostgreSQL 17.11 with client TLS)

## Verified live endpoints
Checked on 2026-10-17:
- **Frontend SPA:** `https://filingguard-ai.onrender.com` (routes `/`, `/activity`, `/settings` return HTTP 200 via rewrite)
- **API Liveness:** `https://filingguard-api.onrender.com/api/v1/health` (HTTP 200, CORS exact-origin `https://filingguard-ai.onrender.com`)
- **API Capabilities:** `https://filingguard-api.onrender.com/api/v1/capabilities` (HTTP 200, intake and storage confirmed)
- **API Readiness:** `https://filingguard-api.onrender.com/api/v1/ready` (HTTP 200 when intake is active; fail-closed HTTP 503 when intake is off; verified `private_storage`, `database_schema`, `cleanup`, `exact_origins`, `provider_configuration`)
- **CORS strict origin control:** Forbidden origin (`https://invalid-origin.example`) receives no `Access-Control-Allow-Origin` header.

## Working MVP features
- **Document Preparation & Intake:** Text paste, PDF upload (up to 20 pages / 10 MiB / 100k characters / 2,000 paragraphs), and curated demo. Bounded process containment.
- **Privacy Masking:** Pre-transport detection and redaction for SSNs, financial account numbers, and dates of birth. Outbound semantic payloads and public views exclude raw PII.
- **Citation Verification:** Eyecite extraction with exact character offsets; deduplicated authority resolution via CourtListener adapter; transparent partial-coverage and provider-outage labels.
- **Proposition Grounding:** Cited proposition context extraction; bounded opinion passage selection; Groq `openai/gpt-oss-120b` structured output (supported / misrepresented / unclear / insufficient source) with explicit evidence record links.
- **Quote Forensics:** Exact, normalized, and RapidFuzz quote comparison against retrieved opinion text with character-level difference highlighting.
- **Provisional Scoring & Findings:** Transparent risk categories (ready for review / needs review / high risk), zero green passes for unrun/unavailable checks, React Flow claim-authority graph with accessible list equivalent.
- **Report Export:** Self-contained Markdown and HTML assurance reports with security headers and full evidence lineage.
- **Accessibility & Design:** WCAG-compliant keyboard navigation (0 axe violations), Avalance brand typography, purple/lilac/yellow glassmorphism identity, and `prefers-reduced-motion` compliance.

## Explicit known limitations
1. **Confidential Real-Client Use Gated:** Must NOT be used for confidential client filings until [[TODO]] `T212` (production encryption, backup, access control, provider retention terms) and `T213` (domain-expert evaluation, calibrated confidence) are verified.
2. **Provisional Model Review Signals:** LLM proposition assessments and risk scores are heuristics to assist human review, not legal advice, certifications, or guarantees of court acceptance.
3. **Court Rules:** Only `synthetic-demo-v1` is active (in demo mode). Live filings default to `unverified` and evaluate as `unavailable`. T111 provides reference-only records; activating real court profiles awaits `T106`.
4. **Platform & Quotas:** Render free tier is ephemeral (local files wiped on container restart) and spins down after 15 minutes of inactivity; maximum 1 active review job per session; maximum 5 stored filings per session; 55-minute session TTL.
5. **OCR Not Supported:** Scanned PDFs without an embedded text layer are rejected with a clear user prompt to paste text.

## Unresolved backlog
- **Phase B (P1 universal review):**
  - `T101` — Legal Red-Team Mode (`FR-240`–`FR-245`)
  - `T102` — Rich lineage and explanations (`FR-205`, `FR-224/225`)
  - `T103` — Finding-grounded Q&A (`FR-260`–`FR-264`)
  - `T104` — PDF report export (`FR-305`)
  - `T105` — Graph polish & multi-claim authorities (`FR-105/106`, `FR-064`)
  - `T107` — Deeper retrieval and multi-passage forensics (`FR-045`, `FR-127`)
  - `T108` — Minor-name detection heuristics (`FR-163`)
  - `T109` — Durable background worker queue
  - `T110` — Expanded telemetry and automated audit timing
- **Phase C (P1 court profile):**
  - `T106` — Active verified real court profile (requires defined target filing context and complete requirement matrix)
- **Phase D (Separate track):**
  - EU AI Act Article 50 transparency assessment discovery
- **Phase E (P2 release gates for real clients):**
  - `T212` — Production data protection
  - `T213` — Expert legal quality validation and rule governance

## Reproducibility verification
- Clean checkout reproducible from locked dependency manifests:
  - Node: `package-lock.json` (`npm ci --ignore-scripts`)
  - Python: `apps/api/uv.lock` (`uv sync --directory apps/api --locked`)
- Full backend suite: 715 controls passed, zero failures.
- Frontend test suite: 30/30 passed.
- Production build: clean Vite build and OpenAPI TypeScript client agreement.

[[docs/delivery/README]] | [[docs/delivery/Deployment guide]] | [[TODO]]
