# Software Requirements Specification

## FilingGuard AI

**Project:** FilingGuard AI - Pre-Filing Assurance Engine  
**Event:** LexHack 2026  
**Version:** 1.1 (product-continuation amendment)
**Date:** September 25, 2026  
**Document Type:** Software Requirements Specification (SRS)  
**Active Deadline Constraint:** None; product development continues after LexHack.

### Product Continuation Amendment - September 28, 2026

The user confirmed the submission deadline was missed and now intends FilingGuard
AI to become a product. The original event/date, deadline estimates and submission
requirements below are historical context, not active time constraints. P0 now means
the core verified workflow, P1 its refinements and P2 larger product capabilities.
Keep scope phased and the existing free-credit budget; no paid upgrade is implied.
Security, retention, provider-processing review and domain-expert legal evaluation
must precede handling real confidential client filings or making production claims.
Anonymous private sessions remain the initial access model; account/team work is
still separate. The ordered tasks live in [[TODO]], with rationale in
[[docs/decisions/ADR-005 - Product continuation and reviewed demo]].

T015 was explicitly delegated to an AI assistant. The reviewed demo may expose
hash-bound, read-only sample expectations with that provenance and their conditions.
It must not claim human/expert validation, executed engine verdicts, a legal score,
or a live provider result. Changed/unrecognized inputs cannot reuse those expectations.
Production analysis and replay remain subject to the later engine acceptance criteria.

### Private Preparation Contract Clarification - September 28, 2026

The implemented development milestone prepares documents but does not run legal
checks. Versioned `/api/v1/analyses/text`, `/file` and `/demo` create private
preparation records with HTTP 201 and `execution_status=not_run`. The future
asynchronous legal pipeline's 202/status/findings contract remains separate.
The illustrative unversioned/multipart APIs below are design history; the generated
[[contracts/README]] owns the implemented HTTP shape. PDF intake uses a bounded raw
`application/pdf` body and encoded `X-Document-Name` header, avoiding filename URLs.

Anonymous ownership uses a server-issued 256-bit bearer in tab `sessionStorage`;
only SHA-256 and a server-set 55-minute expiry are persisted in AnonymousSession.
Analysis additionally stores a validated extracted-document JSON/JSONB snapshot;
page/paragraph offsets use half-open Unicode code points, not JavaScript UTF-16
indices. Original-input and extracted-text fingerprints remain separate.
Expiry denies access immediately; best-effort cleanup is not secure erasure.

Initial preparation limits are 10 MiB PDF bytes, 20 pages, 100,000 characters,
2,000 paragraphs, five documents per session and one active preparation per API
process. T023 must extend admission across complete legal jobs. Unknown court
profiles never imply compliance; the sole demo court is explicitly synthetic.
Local masking is a heuristic boundary, not a redaction guarantee or completed
provider integration. Intake is opt-in and off by default. Hosted/platform/privacy
release checks remain required before real confidential data or public enablement.
See [[docs/decisions/ADR-007 - Private preparation boundary]] and [[TODO]].

---

## 1. Introduction

### 1.1 Purpose

This Software Requirements Specification defines the product scope, system architecture, functional requirements, non-functional requirements, data model, integrations, user flows, acceptance criteria, and implementation priorities for **FilingGuard AI**, a LexHack 2026 legal technology project.

FilingGuard AI is a **pre-filing assurance engine** for AI-assisted legal filings. It helps lawyers, legal teams, students, and self-represented litigants review a draft filing before submission by checking whether cited authorities exist, whether quotations appear in the cited source, whether cited authorities support the propositions claimed, whether the filing contains privacy risks, and whether selected court-specific AI-use or disclosure rules may apply.

The project is intentionally framed as a legal AI safety and governance tool, not as a legal advice generator. Its core question is:

> Is this filing ready for human review before submission?

### 1.2 Product Vision

FilingGuard AI acts like a **CI/CD pipeline for legal filings**. Before a brief, motion, memorandum, or other filing reaches a court, the system runs a structured preflight process:

1. Parse the uploaded or pasted document.
2. Extract legal citations, quotations, claims, and sensitive identifiers.
3. Verify authorities through legal data sources.
4. Retrieve source material where possible.
5. Check whether quotations and propositions are grounded in the source.
6. Apply selected court and privacy rules.
7. Produce an explainable integrity score, argument graph, and audit report.

The product is designed to show that responsible legal AI should not ask users to "trust the AI." Instead, it should expose evidence, sources, uncertainty, and human-review flags.

### 1.3 Intended Audience

This SRS is intended for:

- LexHack judges and reviewers.
- Project developers.
- UI/UX designers.
- Legal domain advisors.
- Demo presenters.
- Future maintainers.
- Potential legal technology partners or mentors.

### 1.4 Definitions

| Term | Definition |
|---|---|
| Authority | A legal source cited in a filing, such as a case, statute, regulation, rule, or secondary source. |
| Citation | A textual reference to an authority, such as `573 U.S. 373`. |
| Claim | A legal or factual proposition made in the filing. |
| Proposition Verification | The process of checking whether an authority appears to support the proposition for which it is cited. |
| Quote Forensics | Exact, normalized, fuzzy, and semantic checking of quoted text against the source authority. |
| Claim-Authority Graph | A visual graph connecting claims to the authorities cited in support of them. |
| Filing Integrity Score | A transparent score summarizing authority, claim, quote, privacy, and court-rule risk. |
| Court Rule Engine | A rule-based module that applies jurisdiction-specific filing checks. |
| Red-Team Mode | A mode that highlights how opposing counsel, a court, or a reviewer might challenge the filing. |
| Evidence Lineage | Traceable chain from a finding back to document location, extracted citation, external source, retrieved passage, and analysis method. |
| P0 | Must-have MVP requirement for LexHack demo. |
| P1 | Important enhancement if core MVP is stable. |
| P2 | Stretch feature if time permits. |

### 1.5 References and Context

This document is based on the project planning conversation for LexHack 2026. The key design decisions were:

- Build **FilingGuard AI**, not a generic legal chatbot.
- Position the product as a **pre-filing assurance engine**.
- Make the **Claim-Authority Graph** the flagship innovation.
- Build a realistic MVP within the September 28, 2026 deadline.
- Use deterministic verification wherever possible.
- Use AI only for bounded semantic tasks with retrieved evidence.
- Clearly label uncertainty and avoid legal advice.

---

## 2. Project Context

### 2.1 Problem Statement

Generative AI is increasingly used to draft legal documents. This creates a serious legal AI safety problem: filings may contain nonexistent cases, malformed citations, fabricated quotations, misattributed quotations, or real cases cited for propositions they do not support. These errors can lead to sanctions, reputational damage, wasted court resources, and harm to clients or litigants.

Many tools focus on generating legal text. FilingGuard AI focuses on **checking legal text before it is filed**.

### 2.2 Opportunity

The strongest hackathon opportunity is not merely to check whether citations exist. A citation can be real and still be dangerously misused. FilingGuard AI therefore verifies the broader argument structure:

- Does the cited authority exist?
- Is the citation identity correct?
- Does the quoted language appear in the authority?
- Does the authority support the claim?
- Is sensitive information exposed?
- Does the selected court require AI-use disclosure or other filing warnings?
- Which findings require human review?

### 2.3 LexHack Alignment

FilingGuard AI aligns with likely LexHack evaluation dimensions:

| Evaluation Area | FilingGuard AI Alignment |
|---|---|
| Real-world impact | Addresses a live legal AI risk affecting courts, lawyers, and litigants. |
| Technical execution | Combines document parsing, legal APIs, deterministic checks, AI semantic analysis, graph visualization, and audit reporting. |
| UX | Offers a simple upload-to-report workflow with visual findings and clear review actions. |
| Originality | Moves beyond a legal chatbot or citation checker into full pre-filing assurance. |
| Presentation | Supports a memorable 2-3 minute demo with visible errors, graph view, red-team mode, and exportable report. |

### 2.4 Recommended Demo Scenario

The demo should use a prepared filing containing:

- Three correct citations.
- One nonexistent or unresolved citation.
- One real authority used for a misleading proposition.
- One quotation that differs from the source.
- One missing AI disclosure for a selected court profile.
- One privacy issue, such as a full birth date or mock account number.

The system should scan the document, produce a filing integrity score, display the Claim-Authority Graph, open at least two detailed findings, run Red-Team Mode, and generate a pre-filing assurance report.

---

## 3. Product Overview

### 3.1 Product Name

**FilingGuard AI**

Optional tagline:

> Know before you file.

Longer positioning statement:

> FilingGuard AI verifies legal authorities, quotations, argument support, privacy risks, and court-specific filing rules before an AI-assisted legal document reaches the court.

### 3.2 Product Type

Web application with:

- React + TypeScript frontend.
- Backend REST API.
- Document analysis pipeline.
- Legal data integrations.
- LLM-powered semantic analysis.
- PostgreSQL persistence for analysis results.
- Exportable audit report.

### 3.3 Target Users

| User | Needs |
|---|---|
| Attorney | Pre-file review of AI-assisted drafts; citation and quote safety checks. |
| Legal researcher | Authority verification and source-grounded claim review. |
| Law student | Learning how citations support propositions. |
| Self-represented litigant | Warnings about unsupported citations, privacy risks, and court rule issues. |
| Court clerk or reviewer | Structured audit view of possible filing defects. |
| Hackathon judge | Clear demonstration of practical AI safety in law. |

### 3.4 Core Value Proposition

Existing tools ask:

> Does this citation exist?

FilingGuard AI asks:

> Is the entire legal argument trustworthy enough for human review before filing?

---

## 4. Scope

### 4.1 In Scope for MVP

The LexHack MVP shall include:

- Upload or paste a legal document.
- Select jurisdiction/court profile.
- Indicate whether generative AI was used.
- Parse document text.
- Extract case citations.
- Verify citations through CourtListener or a mock-compatible adapter.
- Extract nearby claims/propositions around citations.
- Retrieve source opinion text when available.
- Classify proposition support as supported, partially supported, unclear, or potentially misrepresented.
- Extract quoted text and match against retrieved opinions.
- Detect common privacy risks through rules.
- Check selected AI disclosure rule.
- Build a basic Claim-Authority Graph.
- Calculate a transparent Filing Integrity Score.
- Show explainable finding detail pages.
- Generate a pre-filing assurance report.
- Include disclaimers that findings are not legal advice.

### 4.2 P1 Scope

If P0 is stable, add:

- Evidence lineage visualization.
- Red-Team Mode.
- More polished graph interactions.
- Grounded Q&A on findings.
- More court profiles.
- Report export as PDF or Markdown.
- Better confidence scoring.
- Background job progress updates.

### 4.3 P2 Scope

Stretch additions:

- Table of Authorities audit.
- Statute and regulation support beyond case law.
- Advanced local rule profiles.
- User accounts and saved projects.
- Collaboration/comments.
- Batch analysis.
- Word document add-in or browser extension.
- Advanced semantic retrieval over long opinions.

### 4.4 Out of Scope

The following are explicitly out of scope for the LexHack MVP:

- Giving legal advice.
- Predicting case outcomes.
- Drafting legal strategy.
- Replacing attorney review.
- Automated filing with courts.
- Payment/billing system.
- Multi-tenant enterprise access controls.
- Full nationwide court-rule coverage.
- Guaranteed citation completeness.
- Attorney-client privilege guarantees.
- Live integration with PACER or court e-filing systems.
- General "ask a lawyer" chatbot.
- Contract review unrelated to litigation filings.

---

## 5. Assumptions, Constraints, and Dependencies

### 5.1 Assumptions

- Users can provide text or PDF documents for analysis.
- The MVP demo can rely on a curated sample filing.
- CourtListener or an equivalent legal citation API is available for case citation lookup.
- LLM access is available for claim extraction and proposition classification.
- Not every citation can be resolved; unresolved status must be treated as uncertainty, not proof of fabrication.
- Hackathon judges value explainability, safety, and realistic constraints.
- The product is a prototype and not production legal software.

### 5.2 Constraints

- The project must be demo-ready by September 28, 2026 at 2:00 AM PKT.
- Development time is limited; P0 must be prioritized aggressively.
- Legal source coverage is incomplete.
- PDF parsing may produce imperfect text order.
- LLM outputs may be uncertain and must be grounded and constrained.
- Long filings may exceed context limits and require chunking.
- The product must avoid unauthorized practice of law.

### 5.3 Dependencies

| Dependency | Use |
|---|---|
| CourtListener Citation Lookup API | Citation parsing, verification, metadata, source links. |
| CourtListener opinions / legal source API | Opinion retrieval and passages where available. |
| LLM API | Claim extraction, proposition verification, explanation generation. |
| PDF parser | Extract text and page references from uploaded PDFs. |
| PostgreSQL | Store analyses, findings, graph nodes, and audit metadata. |
| React graph library | Render Claim-Authority Graph. |
| Fuzzy matching library | Quote forensics. |

---

## 6. Stakeholders

| Stakeholder | Interest |
|---|---|
| Hackathon participant team | Build a competitive, realistic, demoable project. |
| LexHack judges | Evaluate impact, technical execution, UX, originality, and presentation. |
| Attorneys | Reduce risk of filing unsupported or AI-tainted documents. |
| Law firms | Add review workflow before filing. |
| Courts | Reduce hallucinated or defective filings. |
| Clients/litigants | Avoid harm caused by unreliable filings. |
| Legal technologists | Demonstrate responsible AI architecture. |
| Legal educators | Teach relationship between claims and authorities. |

---

## 7. System Architecture

### 7.1 High-Level Architecture

```text
React + TypeScript Frontend
        |
        v
REST API / Backend Service
        |
        +-- Document Engine
        |     - PDF/text parsing
        |     - text segmentation
        |     - citation and quote extraction
        |
        +-- Authority Engine
        |     - citation verification
        |     - legal metadata retrieval
        |     - opinion retrieval
        |
        +-- AI Engine
        |     - claim extraction
        |     - proposition verification
        |     - grounded explanation
        |     - red-team analysis
        |
        +-- Rule Engine
        |     - court profiles
        |     - AI disclosure checks
        |     - privacy scanning
        |
        +-- Evidence Engine
        |     - source passage storage
        |     - lineage records
        |     - confidence scoring
        |
        +-- Scoring Engine
        |     - integrity score
        |     - category subscores
        |
        v
PostgreSQL
```

### 7.2 Recommended Implementation Stack

| Layer | Recommended Technology |
|---|---|
| Frontend | React, TypeScript, Vite |
| Styling | Tailwind CSS or existing design system |
| Graph View | React Flow or similar graph library |
| Backend | Spring Boot or Node/Express depending on team speed |
| Database | PostgreSQL |
| File Storage | Local storage for prototype; object storage later |
| PDF Parsing | Apache PDFBox, pdf.js, or backend parser |
| Citation API | CourtListener |
| AI | OpenAI or comparable LLM API |
| Deployment | Render, Railway, Fly.io, Vercel + backend host |

### 7.3 Architectural Principle

LLM output must not be treated as the source of truth.

The system shall use:

- Deterministic API lookups for citation existence.
- Retrieved primary source text for proposition verification.
- Exact and fuzzy string matching for quote checks.
- Rule-based detection for privacy and court compliance.
- LLMs only for bounded semantic tasks with source-grounded evidence.

### 7.4 Processing Pipeline

1. User submits document.
2. Backend creates analysis job.
3. Document Engine extracts text, pages, paragraphs, citations, and quotations.
4. Authority Engine resolves citations.
5. Authority Engine retrieves opinions or source snippets where possible.
6. AI Engine extracts claims around citations.
7. AI Engine checks claim support using retrieved text.
8. Quote Forensics checks quotations against source text.
9. Rule Engine runs court and privacy checks.
10. Scoring Engine calculates integrity score.
11. Evidence Engine records lineage.
12. Frontend displays dashboard, graph, findings, and report.

---

## 8. User Roles and Permissions

### 8.1 MVP Roles

| Role | Permissions |
|---|---|
| Anonymous user | Upload/paste document, run analysis, view results in current session, export report. |
| Demo user | Use prepared sample document and reset demo state. |

### 8.2 Future Roles

| Role | Permissions |
|---|---|
| Attorney user | Save analyses, manage matters, export reports. |
| Reviewer | Add comments and mark findings reviewed. |
| Admin | Manage court profiles, integrations, and user settings. |

User authentication is P2 and not required for LexHack MVP.

---

## 9. Functional Requirements

### 9.1 Document Intake

| ID | Requirement | Priority |
|---|---|---|
| FR-001 | The system shall allow users to paste legal text into a text input area. | P0 |
| FR-002 | The system shall allow users to upload a PDF document. | P0 |
| FR-003 | The system shall display file name, file size, and accepted format before analysis. | P0 |
| FR-004 | The system shall reject unsupported file formats with a clear error message. | P0 |
| FR-005 | The system shall allow users to select a court/jurisdiction profile before analysis. | P0 |
| FR-006 | The system shall ask whether generative AI was used in preparing the filing. | P0 |
| FR-007 | The system shall include a "Run Preflight" action that starts analysis. | P0 |
| FR-008 | The system shall provide a demo sample document that can be loaded instantly. | P1 |

### 9.2 Document Parsing

| ID | Requirement | Priority |
|---|---|---|
| FR-020 | The system shall extract plain text from pasted input. | P0 |
| FR-021 | The system shall extract text from uploaded PDFs. | P0 |
| FR-022 | The system shall preserve page numbers where available. | P0 |
| FR-023 | The system shall split text into paragraphs or logical chunks. | P0 |
| FR-024 | The system shall retain character offsets for extracted citations, quotes, and claims. | P1 |
| FR-025 | The system shall detect if parsing quality is poor and warn the user. | P1 |

### 9.3 Citation Verification

| ID | Requirement | Priority |
|---|---|---|
| FR-040 | The system shall detect legal case citations in the document. | P0 |
| FR-041 | The system shall send extracted citations to a legal citation verification service. | P0 |
| FR-042 | The system shall classify citation results as verified, not found, invalid, ambiguous, or service unavailable. | P0 |
| FR-043 | The system shall display case name, court, year, reporter citation, and source URL when available. | P0 |
| FR-044 | The system shall warn that "not found" does not conclusively prove fabrication. | P0 |
| FR-045 | The system shall detect duplicate citations and show repeated locations. | P1 |
| FR-046 | The system shall cache citation lookup responses during a session or analysis. | P1 |
| FR-047 | The system shall support statutes and regulations. | P2 |

### 9.4 Claim Extraction

| ID | Requirement | Priority |
|---|---|---|
| FR-060 | The system shall identify the sentence or paragraph surrounding each citation. | P0 |
| FR-061 | The system shall extract the proposition the citation appears to support. | P0 |
| FR-062 | The system shall associate each claim with one or more citations. | P0 |
| FR-063 | The system shall show the original document excerpt used for claim extraction. | P0 |
| FR-064 | The system shall allow multiple claims to be associated with a single authority. | P1 |
| FR-065 | The system shall allow users to manually correct extracted claims. | P2 |

### 9.5 Proposition Verification

| ID | Requirement | Priority |
|---|---|---|
| FR-080 | The system shall retrieve opinion text or relevant source passages for verified citations when available. | P0 |
| FR-081 | The system shall compare each extracted proposition against retrieved source text. | P0 |
| FR-082 | The system shall classify support as supported, partially supported, unclear, potentially misrepresented, or not enough source text. | P0 |
| FR-083 | The system shall provide evidence passages for each proposition result when available. | P0 |
| FR-084 | The system shall display a confidence level for proposition verification. | P0 |
| FR-085 | The system shall label proposition verification as a review flag, not a legal determination. | P0 |
| FR-086 | The system shall avoid unsupported conclusions when source text is unavailable. | P0 |
| FR-087 | The system shall support multi-passage retrieval from long opinions. | P1 |
| FR-088 | The system shall compare facts from the filing with facts in the cited case. | P2 |

### 9.6 Claim-Authority Graph

| ID | Requirement | Priority |
|---|---|---|
| FR-100 | The system shall generate graph nodes for document sections, claims, and authorities. | P0 |
| FR-101 | The system shall generate graph edges connecting claims to supporting authorities. | P0 |
| FR-102 | The graph shall visually distinguish verified, warning, critical, and unknown statuses. | P0 |
| FR-103 | Users shall be able to click a node to view finding details. | P0 |
| FR-104 | The graph shall summarize the structure of the legal argument. | P0 |
| FR-105 | The graph shall support zoom, pan, and fit-to-view interactions. | P1 |
| FR-106 | The graph shall show unsupported claims as separate warning nodes. | P1 |
| FR-107 | The graph shall export as an image for reports or Devpost screenshots. | P2 |

### 9.7 Quote Forensics

| ID | Requirement | Priority |
|---|---|---|
| FR-120 | The system shall extract quoted text from the filing. | P0 |
| FR-121 | The system shall associate quotations with nearby citations where possible. | P0 |
| FR-122 | The system shall check for exact quote matches in retrieved source text. | P0 |
| FR-123 | The system shall run normalized matching that ignores case, whitespace, and punctuation differences. | P0 |
| FR-124 | The system shall run fuzzy matching when exact matching fails. | P0 |
| FR-125 | The system shall show the closest matching source passage and similarity score when available. | P0 |
| FR-126 | The system shall classify quote status as exact match, normalized match, close match, not found, or source unavailable. | P0 |
| FR-127 | The system shall flag quotation changes that may alter meaning. | P1 |
| FR-128 | The system shall support semantic quote similarity when string matching is insufficient. | P2 |

### 9.8 Court Rule Engine

| ID | Requirement | Priority |
|---|---|---|
| FR-140 | The system shall provide at least one court profile for demo purposes. | P0 |
| FR-141 | The court profile shall define whether AI-use disclosure checks are enabled. | P0 |
| FR-142 | The system shall check whether required AI disclosure heading/text appears in the filing. | P0 |
| FR-143 | The system shall flag missing disclosure if the user indicates AI was used and the selected court requires disclosure. | P0 |
| FR-144 | The system shall show the relevant rule requirement text in the finding detail. | P0 |
| FR-145 | Court rules shall be stored in editable structured JSON or database configuration. | P0 |
| FR-146 | The system shall support additional court profiles. | P1 |
| FR-147 | The system shall support filing-format checks such as page limits or headings. | P2 |

### 9.9 Privacy Leak Scanning

| ID | Requirement | Priority |
|---|---|---|
| FR-160 | The system shall scan for Social Security number patterns. | P0 |
| FR-161 | The system shall scan for financial account number patterns. | P0 |
| FR-162 | The system shall scan for full birth date patterns. | P0 |
| FR-163 | The system shall flag possible minor names when detectable through simple patterns or demo input. | P1 |
| FR-164 | Privacy findings shall include severity levels. | P0 |
| FR-165 | Privacy findings shall recommend human redaction review without modifying the filing automatically. | P0 |
| FR-166 | The system shall avoid storing raw sensitive values in logs. | P0 |
| FR-167 | The system shall support configurable privacy rules by jurisdiction. | P2 |

### 9.10 Filing Integrity Score

| ID | Requirement | Priority |
|---|---|---|
| FR-180 | The system shall calculate an overall Filing Integrity Score from 0 to 100. | P0 |
| FR-181 | The score shall include authority integrity, claim grounding, quote integrity, privacy safety, and court compliance. | P0 |
| FR-182 | The system shall display subscores and counts behind the overall score. | P0 |
| FR-183 | The score shall be transparent and explainable. | P0 |
| FR-184 | Critical issues shall reduce the score more than warnings. | P0 |
| FR-185 | The system shall map score ranges to statuses such as ready for review, needs review, and high risk. | P0 |
| FR-186 | Users shall be able to click score categories to filter findings. | P1 |

### 9.11 Explainable AI

| ID | Requirement | Priority |
|---|---|---|
| FR-200 | Every AI-generated classification shall include an explanation. | P0 |
| FR-201 | Explanations shall cite retrieved evidence passages where available. | P0 |
| FR-202 | The UI shall distinguish deterministic checks from AI-assisted checks. | P0 |
| FR-203 | The UI shall show confidence and uncertainty. | P0 |
| FR-204 | The system shall not present AI conclusions as final legal determinations. | P0 |
| FR-205 | Users shall be able to expand "How was this determined?" for each finding. | P1 |

### 9.12 Evidence Lineage

| ID | Requirement | Priority |
|---|---|---|
| FR-220 | The system shall record the original document location for each finding. | P0 |
| FR-221 | The system shall record the extracted citation or quote that triggered the finding. | P0 |
| FR-222 | The system shall record source API metadata for verified authorities. | P0 |
| FR-223 | The system shall record retrieved evidence passages where available. | P0 |
| FR-224 | The system shall display a visual lineage chain for findings. | P1 |
| FR-225 | The system shall include lineage in exported reports. | P1 |

### 9.13 Legal Red-Team Mode

| ID | Requirement | Priority |
|---|---|---|
| FR-240 | The system shall provide a "Red Team Filing" action after analysis. | P1 |
| FR-241 | Red-Team Mode shall identify the highest-risk weaknesses in the filing. | P1 |
| FR-242 | Red-Team findings shall be based only on prior analysis results and retrieved evidence. | P1 |
| FR-243 | Red-Team Mode shall explain how opposing counsel or a reviewer might challenge the filing. | P1 |
| FR-244 | Red-Team Mode shall not draft new legal arguments for the user. | P1 |
| FR-245 | Red-Team findings shall link back to underlying citations, claims, quotes, or rule findings. | P1 |

### 9.14 Grounded Q&A

| ID | Requirement | Priority |
|---|---|---|
| FR-260 | Users shall be able to ask questions about a specific finding. | P1 |
| FR-261 | Answers shall be grounded in the finding, source passages, and analysis metadata. | P1 |
| FR-262 | Answers shall include citations to internal evidence or source links. | P1 |
| FR-263 | The system shall refuse broad legal advice questions. | P1 |
| FR-264 | General document chat unrelated to findings shall be out of scope for MVP. | P0 |

### 9.15 Table of Authorities Audit

| ID | Requirement | Priority |
|---|---|---|
| FR-280 | The system shall detect whether the document contains a Table of Authorities section. | P2 |
| FR-281 | The system shall compare authorities in the body with authorities in the Table of Authorities. | P2 |
| FR-282 | The system shall flag authorities in the body missing from the Table of Authorities. | P2 |
| FR-283 | The system shall flag authorities in the Table of Authorities not found in the body. | P2 |
| FR-284 | The system shall show page references where available. | P2 |

### 9.16 Report Generation

| ID | Requirement | Priority |
|---|---|---|
| FR-300 | The system shall generate a pre-filing assurance report after analysis. | P0 |
| FR-301 | The report shall include overall score, findings summary, critical issues, warnings, and passed checks. | P0 |
| FR-302 | The report shall include disclaimers and review limitations. | P0 |
| FR-303 | The report shall include source links and evidence passages where available. | P0 |
| FR-304 | The report shall export as Markdown or HTML. | P0 |
| FR-305 | The report shall export as PDF. | P1 |
| FR-306 | The report shall include Claim-Authority Graph image. | P2 |

---

## 10. Detailed Feature Specifications

### 10.1 Citation Verification

**Purpose:** Determine whether cited cases appear to exist and retrieve authoritative metadata.

**Inputs:**

- Document text.
- Extracted citation strings.
- Optional surrounding case names.

**Processing:**

1. Detect citation patterns.
2. Normalize citation strings.
3. Send text or citations to CourtListener citation lookup API.
4. Interpret response.
5. Store status and metadata.

**Outputs:**

- Verified authority record.
- Not found or ambiguous warning.
- Source link.
- Court/year/reporter metadata.
- Finding if unresolved or malformed.

**MVP Behavior:**

- Case citations only.
- One API adapter.
- Graceful fallback if API is unavailable.

**Acceptance Criteria:**

- Given a valid citation in the demo filing, the system shows verified status and metadata.
- Given a fabricated demo citation, the system shows unresolved/not found and a human-review warning.
- The system never states that "not found" conclusively means fabricated.

### 10.2 Claim-Authority Graph

**Purpose:** Show how claims in the filing are supported or undermined by cited authorities.

**Graph Node Types:**

- Document.
- Section or argument heading.
- Claim.
- Authority.
- Finding.

**Graph Edge Types:**

- contains.
- supports.
- cites.
- flagged_by.

**Status Colors:**

- Green: verified/supported.
- Yellow: needs review/partial/unclear.
- Red: critical issue/not found/mismatch.
- Gray: unavailable/no source.

**MVP Behavior:**

- Graph may be generated from citation-adjacent paragraphs.
- Full legal outline extraction is not required.
- Clicking a node opens detail panel.

**Acceptance Criteria:**

- Demo document produces a visible graph.
- At least one verified, one warning, and one critical path are visible.
- Graph statuses match findings dashboard.

### 10.3 Proposition Verification

**Purpose:** Determine whether a real authority appears to support the proposition asserted in the filing.

**Inputs:**

- Extracted claim/proposition.
- Citation metadata.
- Retrieved source text.

**Classification Labels:**

- Supported.
- Partially supported.
- Unclear.
- Potentially misrepresented.
- Not enough source text.

**MVP Prompting Rules:**

- The AI must only evaluate against provided source text.
- If source text is insufficient, it must say so.
- The AI must return structured JSON.
- The AI must provide evidence passages or state that none were found.

**Acceptance Criteria:**

- Real authority with matching proposition is marked supported in demo.
- Real authority with misleading proposition is marked potentially misrepresented or partially supported.
- Missing source text leads to not enough source text, not speculation.

### 10.4 Quote Forensics

**Purpose:** Detect fabricated, altered, or misattributed quotations.

**Matching Stages:**

1. Exact string match.
2. Normalized match.
3. Fuzzy match.
4. Optional semantic comparison.

**Output Fields:**

- Quote text.
- Associated citation.
- Match status.
- Similarity score.
- Closest passage.
- Risk explanation.

**Acceptance Criteria:**

- Exact quote in source is marked exact match.
- Altered quote in demo is marked not found or close match.
- UI shows closest matching passage and similarity score.

### 10.5 Court Rule Engine

**Purpose:** Apply selected court-specific filing checks.

**Rule Profile Example:**

```json
{
  "courtId": "txnd",
  "courtName": "U.S. District Court for the Northern District of Texas",
  "checks": {
    "aiDisclosure": {
      "enabled": true,
      "requiredWhenAiUsed": true,
      "requiredHeading": "Use of Generative Artificial Intelligence",
      "severity": "high"
    }
  }
}
```

**MVP Behavior:**

- Include at least one court profile.
- If AI used is yes and disclosure text is missing, generate finding.
- If AI used is no, explain that the system did not perform AI-use factual verification.

**Acceptance Criteria:**

- Demo filing without required heading triggers a missing disclosure warning.
- Demo filing with required heading passes the check.

### 10.6 Privacy Leak Scanning

**Purpose:** Detect personal identifiers that may require redaction.

**P0 Patterns:**

- Social Security number-like values.
- Tax ID-like values.
- Full birth dates.
- Financial account-like numbers.

**P1 Patterns:**

- Minor names where context suggests minor status.
- Addresses and phone numbers.

**Output:**

- Finding severity.
- Redacted preview.
- Location.
- Reason.
- Suggested review action.

**Acceptance Criteria:**

- Mock SSN in demo is detected.
- Raw sensitive values are masked in UI summaries and logs.

### 10.7 Legal Red-Team Mode

**Purpose:** Surface the strongest challenges to the filing from a skeptical reviewer perspective.

**Inputs:**

- Citation findings.
- Claim support findings.
- Quote findings.
- Privacy findings.
- Court rule findings.

**Output:**

- Ranked list of weaknesses.
- Severity.
- Underlying evidence.
- Attack theory phrased as review risk.

**MVP/P1 Boundary:**

Red-Team Mode is P1 because it depends on stable P0 analysis. It is highly valuable for the final demo if core checks are completed.

### 10.8 Grounded Q&A

**Purpose:** Allow users to ask why a finding was flagged.

**Allowed Questions:**

- Why was this claim marked weak?
- What evidence did you use?
- What source passage supports this?
- Why is this quote suspicious?

**Disallowed Questions:**

- What should I argue in court?
- Should I file this motion?
- Will I win?
- Rewrite my legal strategy.

**Acceptance Criteria:**

- Answer includes source-grounded explanation.
- Broad legal advice request is refused with safe redirect to human legal review.

---

## 11. Data Model

### 11.1 Core Entities

Implementation clarification (September 27, 2026): analysis/stage execution states
are separate from legal verdicts. Missing results default to `not_run`; partial,
unavailable and interrupted checks never become passes. Coverage must reconcile
with stage counts, skipped stages must be explicitly inapplicable, and scores are
nullable/provisional until sufficient checks complete. All private entities are
analysis-scoped, with server-owned ownership/expiry and composite foreign keys.
Evidence may exist independently of a finding and retains an immutable hashed
source snapshot, exact excerpt offsets and method/version provenance. These
clarifications implement the existing reliability/audit requirements without
expanding legal coverage. See [ADR-004](docs/decisions/ADR-004%20-%20Truthful%20contracts%20and%20scoped%20evidence.md).

#### Analysis

T013 implementation clarification (September 28): `stored_file_id` is an internal,
nullable unique UUID4 reference to private temporary PDF bytes, never a filesystem
path or authorization credential. Original-input SHA-256 covers PDF bytes for file
inputs and UTF-8 text for pasted inputs; extracted/snapshot hashes remain separate.
Coordinated deletion, expiry and same-filesystem interruption recovery follow
[ADR-006](docs/decisions/ADR-006%20-%20Retryable%20private%20lifecycle%20cleanup.md).
This does not enable public intake or claim durable upload storage/secure erasure.

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| createdAt | timestamp | Creation time |
| status | enum | not_run, queued, running, completed, partial, failed, interrupted |
| documentName | string | Uploaded filename or generated label |
| jurisdictionId | string | Selected court profile |
| aiUsed | boolean | User-provided input |
| overallScore | nullable integer | 0-100; no score for unexamined input |
| riskLevel | nullable enum | ready_for_review, needs_review, high_risk; provisional results cannot imply readiness |

#### DocumentSegment

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| analysisId | UUID | Parent |
| pageNumber | integer | Nullable |
| paragraphIndex | integer | Logical ordering |
| text | text | Segment text |
| startOffset | integer | Nullable |
| endOffset | integer | Nullable |

#### Citation

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| analysisId | UUID | Parent |
| rawText | string | Citation as found |
| normalizedText | string | Normalized citation |
| segmentId | UUID | Source segment |
| pageNumber | integer | Nullable |
| verificationStatus | enum | verified, not_found, invalid, ambiguous, unavailable |
| authorityId | UUID | Nullable |

#### Authority

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| source | string | CourtListener or other |
| externalId | string | API identifier |
| caseName | string | Case name |
| citation | string | Official/reporter citation |
| court | string | Court |
| year | integer | Decision year |
| sourceUrl | string | Link to source |
| opinionTextAvailable | boolean | Whether text is available |

#### Claim

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| analysisId | UUID | Parent |
| text | text | Extracted proposition |
| segmentId | UUID | Source segment |
| extractionMethod | enum | heuristic, ai |
| confidence | decimal | 0-1 |

#### ClaimAuthorityLink

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| claimId | UUID | Claim |
| citationId | UUID | Citation |
| authorityId | UUID | Authority |
| supportStatus | enum | supported, partially_supported, unclear, misrepresented, insufficient_source |
| confidence | decimal | 0-1 |
| explanation | text | Grounded explanation |

#### Quote

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| analysisId | UUID | Parent |
| quoteText | text | Extracted quote |
| segmentId | UUID | Source location |
| citationId | UUID | Associated citation |
| matchStatus | enum | exact, normalized, close, not_found, source_unavailable |
| similarity | decimal | 0-1 |
| closestPassage | text | Nullable |

#### Finding

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| analysisId | UUID | Parent |
| type | enum | citation, claim_support, quote, privacy, court_rule, system |
| severity | enum | info, low, medium, high, critical |
| title | string | Short title |
| description | text | Explanation |
| status | enum | open, reviewed, resolved |
| sourceEntityType | string | citation, claim, quote, etc. |
| sourceEntityId | UUID | Linked entity |

#### EvidenceRecord

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| findingId | nullable UUID | Optional finding; checks without warnings also retain evidence |
| sourceType | enum | document, api, opinion_text, ai_analysis, rule |
| sourceLabel | string | Human-readable source |
| text | text | Evidence excerpt |
| url | string | Optional source URL |
| pageNumber | integer | Optional |
| metadata | jsonb | Additional provenance |

### 11.2 Optional Entities

- CourtRuleProfile.
- PrivacyRule.
- RedTeamFinding.
- GroundedQuestion.
- ReportExport.
- TableOfAuthoritiesEntry.

---

## 12. API Specification

### 12.1 REST Endpoints

#### Create Analysis from Text

`POST /api/analyses/text`

Request:

```json
{
  "documentName": "Demo Motion",
  "text": "...",
  "jurisdictionId": "txnd",
  "aiUsed": true
}
```

Response:

```json
{
  "analysisId": "uuid",
  "status": "queued"
}
```

#### Create Analysis from File

`POST /api/analyses/file`

Multipart fields:

- file
- jurisdictionId
- aiUsed

Response:

```json
{
  "analysisId": "uuid",
  "status": "queued"
}
```

#### Get Analysis Status

`GET /api/analyses/{analysisId}`

Response:

```json
{
  "analysisId": "uuid",
  "status": "completed",
  "overallScore": 78,
  "riskLevel": "needs_review"
}
```

#### Get Findings

`GET /api/analyses/{analysisId}/findings`

Response:

```json
{
  "findings": [
    {
      "id": "uuid",
      "type": "quote",
      "severity": "high",
      "title": "Quotation not found in cited authority",
      "description": "The quoted sentence could not be matched exactly or approximately."
    }
  ]
}
```

#### Get Graph

`GET /api/analyses/{analysisId}/graph`

Response:

```json
{
  "nodes": [
    { "id": "claim-1", "type": "claim", "label": "Police required a warrant...", "status": "warning" }
  ],
  "edges": [
    { "id": "edge-1", "source": "claim-1", "target": "authority-1", "type": "cites" }
  ]
}
```

#### Get Report

`GET /api/analyses/{analysisId}/report`

Response:

```json
{
  "format": "markdown",
  "content": "# FilingGuard AI Assurance Report..."
}
```

#### Run Red-Team Mode

`POST /api/analyses/{analysisId}/red-team`

Response:

```json
{
  "findings": [
    {
      "severity": "high",
      "weakness": "A central claim relies on an authority marked partially supported.",
      "linkedFindingIds": ["uuid"]
    }
  ]
}
```

#### Ask About Finding

`POST /api/findings/{findingId}/questions`

Request:

```json
{
  "question": "Why was this claim marked weak?"
}
```

Response:

```json
{
  "answer": "The authority exists, but the retrieved passage describes a fact-specific balancing test rather than the categorical rule stated in the filing.",
  "evidenceRecordIds": ["uuid"]
}
```

### 12.2 External Integrations

| Integration | Purpose | Priority |
|---|---|---|
| CourtListener Citation Lookup | Parse and verify case citations. | P0 |
| CourtListener Opinion API | Retrieve source opinions and metadata. | P0/P1 |
| LLM API | Claim extraction, proposition verification, explanation, red-team mode. | P0/P1 |
| PDF parser | Extract text from uploaded filings. | P0 |

---

## 13. UI/UX Requirements

### 13.1 Design Principles

- Serious legal-tech interface, not a playful chatbot.
- Fast path from upload to findings.
- Every warning must show why it exists.
- The Claim-Authority Graph should be visually memorable.
- Use clear severity language.
- Avoid implying legal advice.
- Keep the demo path simple enough for judges to understand within 2-3 minutes.

### 13.2 Primary Screens

#### Screen 1: Preflight Intake

Required elements:

- Product name: FilingGuard AI.
- Tagline: Know before you file.
- Upload zone.
- Paste text option.
- Jurisdiction selector.
- AI-used selector.
- Run Preflight button.
- Load Demo Filing button.
- Disclaimer: prototype; not legal advice.

#### Screen 2: Analysis Progress

Required progress steps:

- Parsing document.
- Mapping arguments.
- Extracting authorities.
- Verifying citations.
- Retrieving sources.
- Checking quotations.
- Testing claim support.
- Running privacy checks.
- Checking court requirements.
- Building assurance report.

#### Screen 3: Results Dashboard

Required elements:

- Filing Integrity Score.
- Risk label.
- Counts for critical, warning, passed.
- Category subscores.
- Finding filters.
- Top critical findings.
- View Argument Graph button.
- Generate Assurance Report button.
- Red Team Filing button if implemented.

#### Screen 4: Claim-Authority Graph

Required elements:

- Interactive graph.
- Status legend.
- Clickable nodes.
- Side panel with claim, authority, support status, evidence, and source link.

#### Screen 5: Finding Detail

Required elements:

- Finding title.
- Severity.
- Original document excerpt.
- Source authority details.
- Evidence passage.
- How determined section.
- Confidence and limitations.
- Human-review recommendation.

#### Screen 6: Report

Required elements:

- Summary.
- Score and category breakdown.
- Critical findings.
- Warning findings.
- Passed checks.
- Evidence links.
- Legal disclaimer.
- Export/download.

### 13.3 Accessibility

| ID | Requirement | Priority |
|---|---|---|
| UX-001 | Text contrast shall meet WCAG AA where feasible. | P0 |
| UX-002 | Findings shall not rely on color alone; icons/text labels must accompany colors. | P0 |
| UX-003 | Buttons and inputs shall be keyboard accessible. | P0 |
| UX-004 | Graph findings shall also be available in list form. | P0 |
| UX-005 | Loading states shall be understandable to screen readers where feasible. | P1 |

---

## 14. Non-Functional Requirements

### 14.1 Performance

| ID | Requirement | Priority |
|---|---|---|
| NFR-001 | Demo document analysis should complete within 60 seconds under normal conditions. | P0 |
| NFR-002 | The UI should show progress within 2 seconds of starting analysis. | P0 |
| NFR-003 | Dashboard should render within 3 seconds after analysis completion. | P0 |
| NFR-004 | The system should support documents up to 20 pages for MVP. | P0 |
| NFR-005 | Long documents should be chunked rather than sent as one unbounded LLM prompt. | P1 |

### 14.2 Reliability

| ID | Requirement | Priority |
|---|---|---|
| NFR-020 | External API failure shall not crash the analysis. | P0 |
| NFR-021 | The system shall mark affected checks as unavailable when dependencies fail. | P0 |
| NFR-022 | Partial results shall be displayed when some modules fail. | P0 |
| NFR-023 | The system shall log errors with correlation IDs. | P1 |

### 14.3 Security and Privacy

| ID | Requirement | Priority |
|---|---|---|
| NFR-040 | Uploaded documents shall not be exposed publicly. | P0 |
| NFR-041 | Sensitive values detected by privacy scanner shall be masked in logs. | P0 |
| NFR-042 | API keys shall be stored in environment variables, not source code. | P0 |
| NFR-043 | The system shall validate file type and file size. | P0 |
| NFR-044 | The system shall avoid storing uploaded documents longer than necessary for the prototype. | P1 |
| NFR-045 | Future production versions shall encrypt stored documents and reports at rest. | P2 |

### 14.4 Maintainability

| ID | Requirement | Priority |
|---|---|---|
| NFR-060 | Analysis modules shall be separated by responsibility. | P0 |
| NFR-061 | Court rules shall be configurable outside application code. | P0 |
| NFR-062 | External API clients shall be isolated behind adapters. | P0 |
| NFR-063 | Requirement-critical functions shall include tests or demo validation. | P1 |

### 14.5 Usability

| ID | Requirement | Priority |
|---|---|---|
| NFR-080 | A first-time user should understand the product within 30 seconds. | P0 |
| NFR-081 | Critical findings should be visible without scrolling on results page. | P0 |
| NFR-082 | Each finding should include a next-step review recommendation. | P0 |
| NFR-083 | The app should include a prepared demo document. | P1 |

---

## 15. Security, Privacy, and Compliance

### 15.1 Security Requirements

- Validate uploaded file type and size.
- Store API keys only in environment variables.
- Do not commit secrets.
- Mask sensitive detected values.
- Avoid logging full document text in production logs.
- Use HTTPS in deployed demo if possible.
- Restrict CORS to known frontend domain in deployment.

### 15.2 Privacy Requirements

The system must be designed with legal-document sensitivity in mind.

For the prototype:

- Clearly state that users should not upload confidential real client documents.
- Provide a demo sample.
- Keep storage minimal.
- Allow users to delete or reset analysis results if persistence is implemented.

For future production:

- Encryption at rest.
- Role-based access.
- Audit logs.
- Data retention controls.
- Matter-level access boundaries.
- Confidentiality mode.

### 15.3 Compliance Disclaimers

The app must display disclaimers:

- FilingGuard AI is a prototype.
- It is not a lawyer.
- It does not provide legal advice.
- It does not guarantee that a filing is correct, complete, compliant, or safe to submit.
- It may miss authorities, rules, or privacy risks.
- API coverage may be incomplete.
- All findings require human legal review.

---

## 16. Logging and Auditability

### 16.1 Logging Requirements

| ID | Requirement | Priority |
|---|---|---|
| LOG-001 | The system shall log analysis start, completion, and failure events. | P0 |
| LOG-002 | The system shall log external API errors without leaking full document content. | P0 |
| LOG-003 | The system shall assign a correlation ID to each analysis. | P1 |
| LOG-004 | The system shall log module-level timing for performance diagnostics. | P1 |

### 16.2 Auditability Requirements

| ID | Requirement | Priority |
|---|---|---|
| AUD-001 | Every finding shall be traceable to a document excerpt or system rule. | P0 |
| AUD-002 | Every authority finding shall include source metadata when available. | P0 |
| AUD-003 | Every AI-assisted finding shall identify that AI was used. | P0 |
| AUD-004 | Exported reports shall include timestamp and selected court profile. | P0 |
| AUD-005 | Evidence lineage shall be visible in the UI. | P1 |

---

## 17. Error Handling

### 17.1 User-Facing Error Categories

| Error | Required Behavior |
|---|---|
| Unsupported file type | Show accepted formats and allow retry. |
| File too large | Show size limit and allow smaller file. |
| PDF parsing failed | Offer paste-text fallback. |
| Citation API unavailable | Continue analysis and mark citation checks unavailable. |
| LLM unavailable | Continue deterministic checks and mark semantic checks unavailable. |
| No citations found | Show that no authorities were detected and still run privacy/rule checks. |
| Source opinion unavailable | Mark proposition/quote checks as source unavailable. |

### 17.2 Error Message Style

Messages should be specific and calm:

- Good: "We could not retrieve source text for this citation, so claim support could not be verified."
- Avoid: "The citation is fake."
- Avoid: "The AI failed."

---

## 18. Testing Strategy

### 18.1 Test Types

| Test Type | Scope | Priority |
|---|---|---|
| Unit tests | Citation parsing, quote matching, scoring, privacy regexes. | P0 |
| Integration tests | CourtListener adapter, LLM structured output parser. | P1 |
| UI tests | Intake, progress, dashboard, graph, detail panel. | P1 |
| End-to-end demo test | Load sample, run analysis, show expected findings. | P0 |
| Accessibility checks | Keyboard navigation, color labels, contrast. | P1 |

### 18.2 Demo Acceptance Test

The project is demo-ready when:

1. User can load the demo filing.
2. User can select court profile and AI-used setting.
3. Analysis completes without crashing.
4. Dashboard shows overall score and category breakdown.
5. At least one verified citation is shown.
6. At least one unresolved citation is shown.
7. At least one proposition issue is shown.
8. At least one quote issue is shown.
9. At least one court-rule or privacy issue is shown.
10. Claim-Authority Graph renders.
11. A detailed finding shows evidence and explanation.
12. Assurance report is generated.

### 18.3 Acceptance Criteria by MVP Feature

| Feature | Acceptance Criteria |
|---|---|
| Intake | Paste text and PDF upload both reach analysis pipeline. |
| Citation verification | Demo citations are correctly classified. |
| Proposition verification | Supported and misleading propositions receive different statuses. |
| Quote forensics | Exact and altered quotes are distinguished. |
| Court rule engine | Missing demo AI disclosure is flagged. |
| Privacy scanning | Demo sensitive identifier is detected and masked. |
| Score | Score changes based on critical/warning findings. |
| Graph | Graph shows claims connected to authorities. |
| Report | Report includes summary, findings, evidence, and disclaimers. |

---

## 19. Deployment Requirements

### 19.1 MVP Deployment

The LexHack demo should be deployed as:

- Frontend: Vercel, Netlify, or similar.
- Backend: Render, Railway, Fly.io, or similar.
- Database: Managed PostgreSQL or in-memory fallback for demo.
- Environment variables configured for API keys.

### 19.2 Deployment Acceptance

| ID | Requirement | Priority |
|---|---|---|
| DEP-001 | Public demo URL shall load successfully. | P0 |
| DEP-002 | Demo filing shall run successfully in deployed environment. | P0 |
| DEP-003 | README shall explain setup, API keys, and limitations. | P0 |
| DEP-004 | Devpost submission shall include screenshots and live demo link if available. | P0 |
| DEP-005 | System shall degrade gracefully if external legal API is unavailable during judging. | P0 |

### 19.3 Fallback Plan

If live API access fails during demo:

- Use cached CourtListener responses for the sample document.
- Clearly label cached demo mode.
- Still demonstrate pipeline, graph, findings, and report.

---

## 20. MVP, P1, and P2 Priority Plan

### 20.1 P0 - Must-Have LexHack MVP

P0 is the build target before polish.

- Paste/upload document.
- Court profile selection.
- AI-used input.
- Text extraction.
- Citation extraction.
- Citation verification.
- Claim extraction around citations.
- Proposition verification against retrieved text.
- Quote forensics.
- Privacy scan.
- AI disclosure rule check.
- Filing Integrity Score.
- Results dashboard.
- Claim-Authority Graph.
- Finding detail with evidence.
- Assurance report.
- Safety disclaimers.
- Demo sample.

### 20.2 P1 - High-Impact Enhancements

P1 should be added only after P0 works end to end.

- Red-Team Mode.
- Evidence lineage visual chain.
- Grounded Q&A for findings.
- PDF export.
- Better graph interactions.
- Additional court profiles.
- More robust chunking and caching.
- Accessibility improvements.
- Detailed logging/correlation IDs.

### 20.3 P2 - Stretch Features

P2 should not block the submission.

- Table of Authorities audit.
- Statute/regulation verification.
- User accounts.
- Saved matters.
- Collaboration.
- Manual claim correction.
- Word add-in.
- Batch processing.
- Advanced court formatting checks.
- Graph export image.

---

## 21. Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Scope creep | Project unfinished by deadline | Strict P0/P1/P2 boundary. |
| Citation API unavailable | Core demo weakens | Cache demo responses; show graceful degradation. |
| Opinion text unavailable | Proposition/quote checks limited | Mark source unavailable; use demo authorities with available source text. |
| LLM hallucination | Unsafe explanations | Use source-grounded prompts, structured output, disclaimers. |
| PDF parsing errors | Bad extraction | Offer paste-text fallback and demo sample. |
| Legal advice concern | Product risk | Strong disclaimers; focus on review flags, not legal conclusions. |
| Privacy exposure | Sensitive data risk | Warn users not to upload real confidential files; mask logs. |
| UI graph complexity | Time sink | Use simple graph first; polished interactions are P1. |
| Performance delays | Poor demo | Use prepared demo, progress states, background processing. |

---

## 22. Requirements Traceability Matrix

| Requirement ID | Feature Area | Priority | User Need | Acceptance Evidence |
|---|---|---|---|---|
| FR-001 | Intake | P0 | User can submit text. | Paste demo text and start analysis. |
| FR-002 | Intake | P0 | User can upload filing. | Upload PDF and extract text. |
| FR-005 | Intake | P0 | Apply court-specific rules. | Court selector visible and stored. |
| FR-006 | Intake | P0 | AI disclosure check depends on AI-use input. | AI-used input affects rule finding. |
| FR-040 | Citation | P0 | Detect authorities. | Citations listed from demo. |
| FR-041 | Citation | P0 | Verify against legal source. | API response stored/displayed. |
| FR-042 | Citation | P0 | Classify citation risk. | Verified/not found/ambiguous statuses visible. |
| FR-044 | Citation | P0 | Avoid overclaiming. | Not-found disclaimer visible. |
| FR-060 | Claim Extraction | P0 | Identify cited proposition. | Claim text shown for citation. |
| FR-062 | Claim Extraction | P0 | Connect claim to authority. | Claim-authority link exists. |
| FR-080 | Proposition | P0 | Use source text. | Retrieved passage shown. |
| FR-082 | Proposition | P0 | Classify support. | Support status visible. |
| FR-083 | Proposition | P0 | Explain result. | Evidence passage displayed. |
| FR-100 | Graph | P0 | Visualize argument structure. | Graph nodes render. |
| FR-102 | Graph | P0 | Show risk visually. | Status colors and labels visible. |
| FR-103 | Graph | P0 | Inspect graph detail. | Node click opens detail panel. |
| FR-120 | Quote | P0 | Find quoted text. | Quotes extracted from demo. |
| FR-122 | Quote | P0 | Verify exact quotes. | Exact match status shown. |
| FR-124 | Quote | P0 | Detect altered quotes. | Fuzzy result and closest passage shown. |
| FR-140 | Court Rules | P0 | Apply jurisdiction profile. | Demo court profile exists. |
| FR-142 | Court Rules | P0 | Check AI disclosure. | Required heading detected or missing. |
| FR-160 | Privacy | P0 | Detect sensitive identifiers. | Demo SSN-like value flagged. |
| FR-166 | Privacy | P0 | Protect sensitive data. | Logs/UI mask raw sensitive value. |
| FR-180 | Scoring | P0 | Summarize readiness. | Overall score displayed. |
| FR-181 | Scoring | P0 | Explain score categories. | Category subscores displayed. |
| FR-200 | Explainability | P0 | Understand AI result. | Explanation shown. |
| FR-202 | Explainability | P0 | Separate AI from deterministic checks. | Finding detail shows method. |
| FR-220 | Evidence Lineage | P0 | Trace finding to source. | Document excerpt and source link shown. |
| FR-240 | Red Team | P1 | Stress-test filing. | Red-team output ranks weaknesses. |
| FR-260 | Grounded Q&A | P1 | Ask why finding exists. | Finding-specific answer cites evidence. |
| FR-280 | TOA Audit | P2 | Audit Table of Authorities. | Missing/extra TOA entries shown. |
| FR-300 | Report | P0 | Export review artifact. | Report generated. |
| FR-302 | Report | P0 | Avoid legal advice risk. | Disclaimer included. |
| NFR-001 | Performance | P0 | Fast demo. | Demo completes within 60 seconds. |
| NFR-020 | Reliability | P0 | Handle API failures. | Dependency failure shows unavailable status. |
| NFR-040 | Security | P0 | Protect uploads. | No public exposure of uploaded file. |
| NFR-042 | Security | P0 | Protect secrets. | API keys in env vars. |
| UX-002 | Accessibility | P0 | Do not rely only on color. | Findings include text/icon status. |
| AUD-001 | Auditability | P0 | Trace every finding. | Each finding has source excerpt/rule. |
| DEP-001 | Deployment | P0 | Share demo. | Public URL loads. |
| DEP-005 | Deployment | P0 | Judging resilience. | Cached demo fallback works. |

---

## 23. Recommended Build Order

1. Create project skeleton and demo sample filing.
2. Build intake screen with paste text and sample loader.
3. Implement citation extraction and static mocked results.
4. Add CourtListener adapter.
5. Add dashboard and findings list.
6. Add claim extraction around citations.
7. Add proposition verification for selected demo citations.
8. Add quote extraction and matching.
9. Add court rule JSON and AI disclosure check.
10. Add privacy regex scanner.
11. Add Filing Integrity Score.
12. Add Claim-Authority Graph.
13. Add assurance report.
14. Add Red-Team Mode if time remains.
15. Polish UI, deploy, rehearse demo, and prepare Devpost submission.

---

## 24. Final Product Narrative

FilingGuard AI is not another tool for generating legal text. It is a safety layer for legal work created in the age of generative AI.

Its core insight is that legal filings fail not only when citations are invented, but also when real citations are used for false propositions, when quotations are altered, when private identifiers leak into public filings, and when court-specific AI disclosure rules are missed.

The MVP is realistic for LexHack because it focuses on one coherent workflow:

> Upload filing -> run preflight -> inspect graph and findings -> generate assurance report.

The strongest demo message is:

> Existing tools ask whether a citation is real. FilingGuard asks whether the entire argument is trustworthy enough to file.

---

## 25. Appendix: Sample Finding Language

### Citation Finding

**Citation could not be resolved**

The citation `999 F.9th 1234` could not be matched against the available legal source database. This may indicate a fabricated citation, a typo, an unsupported reporter, or incomplete database coverage. Human verification is required.

### Proposition Finding

**Authority may not support the stated proposition**

The filing states that the cited case creates a categorical rule. The retrieved opinion passage instead describes a fact-specific balancing test. FilingGuard marks this as potentially misrepresented for human review.

### Quote Finding

**Quotation not found in cited authority**

The quoted sentence does not appear exactly in the retrieved opinion text. The closest matching passage is similar but uses materially different wording. Review the source before relying on this quotation.

### Court Rule Finding

**AI disclosure may be required**

The selected court profile requires an AI-use disclosure when generative AI was used. The required disclosure heading was not detected in the filing.

### Privacy Finding

**Possible sensitive identifier detected**

The filing appears to contain a Social Security number-like value. Public court filings may require redaction of personal identifiers. Review before filing.

---

## 26. Appendix: Prototype Disclaimer Text

FilingGuard AI is a hackathon prototype for pre-filing review support. It is not a law firm, lawyer, court system, or legal advice service. Its findings are automated review signals based on available document text, selected rules, external data sources, and AI-assisted analysis. FilingGuard AI may be incomplete, incorrect, or unavailable, and it may miss legal authorities, filing rules, privacy issues, or source-text problems. All results require review by a qualified human before any legal filing is submitted.

