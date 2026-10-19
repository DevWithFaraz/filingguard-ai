# Legal Quality and Court Rule Governance Protocol

- **Document**: Legal Quality Framework & Operational Court-Rule Governance
- **Status**: Verified Specification / Release Gate
- **Date**: 2026-10-19
- **Governing Requirements**: SRS section 18 (Acceptance & Validation), FR-140–FR-147, FR-180–FR-187, T213
- **Related Documents**:
  - [[docs/product/FilingGuard product direction|FilingGuard Product Direction]]
  - [[docs/decisions/ADR-014 - Filing-centric court rules and separate Article 50 direction|ADR-014: Court Rules Direction]]
  - [[docs/research/Court rules and EU AI Act product direction - 2026-10-14|Research: Court Rules & Governance]]

---

## 1. Executive Summary & Purpose

FilingGuard AI operates as an analytical pair-review assistant, not an autonomous legal entity. Under no circumstances does the system certify legal compliance or provide legal advice.

To safeguard against automated overreliance and ensure long-term reliability in production legal workflows, this protocol establishes:
1. Calibrated confidence and uncertainty representation
2. Domain-expert legal quality review procedures
3. Operational ownership and lifecycle management for court rules
4. Standing order reconciliation protocols

---

## 2. Calibrated Confidence & Uncertainty Representation

Automated scores and status indicators must clearly separate verifiable facts from heuristic or statistical classifications:

### 2.1. Signal Calibration Tiers

| Signal Type | Verification Engine | Output Indicator | Legal Interpretation |
|---|---|---|---|
| **Citation Existence** | Eyecite parser + CourtListener primary DB | `verified`, `not_found`, `invalid` | Factual existence in verified legal reporter. Does not determine persuasive authority. |
| **Quotation Lexical Accuracy** | RapidFuzz + token normalization | `exact`, `normalized`, `close` | Verbatim text match against official slip opinion. |
| **Proposition Support** | Structured inference + fact extraction | `supported`, `partially_supported`, `unclear`, `misrepresented` | Heuristic review flag. Requires human comparison of highlighted passages. |
| **Table of Authorities** | Standalone TOA regex & reporter clustering | `missing_from_table`, `extra_table_entry` | Document-consistency signal only; not a formal court-rule determination. |
| **Integrity Score** | Deductive penalty engine (0–100) | Numerical score + Risk Band | Heuristic risk signal; not a judicial clearance or warranty of accuracy. |

### 2.2. Uncertainty Disclosures
- Every finding presentation card must include the expandable **"How was this determined?"** component (FR-205), distinguishing deterministic checks from AI-assisted classifications.
- When an authority or source passage is unreachable, the system records `unavailable` rather than a false-positive `pass`.

---

## 3. Domain-Expert Review & Validation Cadence

To ensure continuous quality calibration:
1. **Curated Ground-Truth Benchmark**:
   - A gold-standard benchmark of 25 authentic briefs (with planted citation errors, altered quotes, and out-of-circuit authorities) is maintained and evaluated before each minor release.
   - Quality threshold: 100% recall on synthetic hallucinated citations; >= 90% precision on proposition misrepresentation flags.
2. **Attorney-in-the-Loop Feedback Loop**:
   - The collaboration module (`FindingCollaboration`) records reviewer dispositions (`accepted`, `dismissed`, `needs_review`) and explanatory rationales.
   - False positive trends flagged by attorneys are triaged monthly to tune Eyecite regex patterns and proposition evaluation prompts.

---

## 4. Operational Court-Rule Governance & Maintenance

Local court rules and judge-specific standing orders evolve frequently. A robust update process prevents stale rule enforcement:

### 4.1. Court Profile Registry Lifecycle
- Every court profile schema (`us-txnd-lr7-2f-v1.json`) defines strict validity bounds:
  - `effective_from`: ISO date when the rule became operative.
  - `effective_to`: ISO date when the rule expires or requires mandatory re-verification.
  - `source`: URL and Special Order citation from the official court website.
- If the current analysis date exceeds `effective_to`, the rule engine marks the profile as `stale` and outputs a warning rather than evaluating stale criteria.

### 4.2. Update Cadence & Ownership
- **Owner**: Compliance & Legal Operations Team.
- **Bi-Monthly Audit**: Verify federal local rule changes via official court portals (e.g., `txnd.uscourts.gov`, `nysd.uscourts.gov`).
- **Emergency Standing Order Updates**: When a district issues an emergency amendment (e.g., generative AI disclosure requirements), a new versioned profile JSON (e.g. `us-txnd-lr7-2f-v2.json`) is authored with corresponding automated unit tests within 72 hours.

---

## 5. Scope Boundaries & Legal Ethics Safe Harbors

1. **No Legal Practice**: FilingGuard AI does not formulate legal strategy, calculate deadlines of limitation, or draft pleading arguments.
2. **No Privilege Claims**: Analysis results in multi-tenant environments are protected via strict tenancy isolation, but the software does not claim attorney-client privilege over database records.
3. **Transparent Limitations Banner**: All exported PDF and Markdown reports feature prominent disclaimers emphasizing that pre-filing review by a licensed attorney remains mandatory.
