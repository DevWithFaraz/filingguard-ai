# ADR-017: Word Add-in Integration Surface and Document Synchronization

- **Status**: Accepted
- **Date**: 2026-10-19
- **Decision Makers**: FilingGuard AI Core Team
- **Related Requirements**: SRS FR-290–FR-294, NFR-023, NFR-040, NFR-045, T211

---

## 1. Context and Problem Statement

Legal practitioners author briefs, motions, and pleadings primarily in Microsoft Word before filing. Providing pre-filing compliance and quotation verification directly within the authoring environment reduces context-switching and catches errors before export.

We need to choose the canonical external integration surface (Microsoft Word Add-in vs. Browser Extension), establish secure authorization that does not leak confidential drafts into untrusted stores, and define a reliable document synchronization protocol that maps review findings back to exact document locations.

---

## 2. Decision Drivers

1. **Workflow Alignment**: Legal filings are authored in desktop and web Microsoft Word; browser extensions only capture already-uploaded text or third-party web forms.
2. **Security & Data Isolation (NFR-045)**: No raw client text should be stored in third-party extension sync engines. All communication must run directly over TLS to the FilingGuard API using ephemeral session tokens.
3. **Document-Location Synchronization**: Findings must link bidirectionally to exact paragraphs and spans in the active Word document without corrupting document formatting.
4. **Maintenance & Extensibility**: Cross-platform compatibility across Word for Windows, Word for Mac, and Word on the Web via standard Office.js APIs.

---

## 3. Evaluated Options

- **Option A: Chrome / Edge Browser Extension**:
  - *Pros*: Simple web-centric development, access to DOM in web legal research tools.
  - *Cons*: Does not integrate into desktop Word; cannot inspect local `.docx` files during active authoring; requires broad browser permissions that raise law-firm security concerns.
  - *Verdict*: Rejected for primary integration surface.

- **Option B: Word Office Web Add-in (Taskpane using Office.js)**:
  - *Pros*: Native support across Word on Windows, Mac, and Web; standardized XML manifest; granular Word JavaScript API (`Word.run`, `context.document.body.paragraphs`); direct bidirectional selection synchronization; isolated iframe sandbox.
  - *Cons*: Requires HTTPS taskpane hosting and XML manifest sideloading or Microsoft 365 Admin Center deployment.
  - *Verdict*: **Selected as the canonical integration surface**.

---

## 4. Decision and Architecture

### 4.1. Integration Surface

The integration is implemented as an Office Web Add-in (`integrations/office-addin/`) consisting of:
- `manifest.xml`: Valid Office 1.1 XML manifest configuring a taskpane button (`FilingGuard Review`) on the Word Home ribbon.
- `taskpane.html`: Secure taskpane UI conforming to Content Security Policy (`default-src 'self' https:; style-src 'self' 'unsafe-inline'`).
- `taskpane.js`: Office.js client coordinating authentication, text extraction, review execution, and selection synchronization.

### 4.2. Secure Authorization

- The taskpane connects to the FilingGuard API via bearer session tokens (`/api/v1/sessions` or claimed identity credentials).
- The add-in supports token pass-through from the user's active browser session or secure credential entry.
- Credentials and filing text are transmitted strictly via TLS directly to the authorized API endpoint. No intermediary relay servers are used.

### 4.3. Document-Location Synchronization Protocol

1. **Extraction**:
   - The add-in queries `context.document.body.paragraphs` and extracts clean text blocks while maintaining a zero-indexed paragraph map: `paragraphMap[index] = { text, paragraphRef }`.
2. **Analysis Intake**:
   - The document is prepared via `POST /api/v1/analyses/text` with `document_name` and full extracted text.
3. **Finding Location Mapping**:
   - When a user clicks a finding in the taskpane:
     - The add-in matches the finding's `start_offset` and `end_offset` to the corresponding paragraph.
     - The add-in invokes `paragraph.select("Select")` or highlights the span via Office.js `search()` / `range.select()`.
   - Bidirectional navigation allows the attorney to jump directly from a cited hallucination or unverified authority to the offending sentence in Word.

---

## 5. Consequences

### Positive
- Direct access to FilingGuard integrity checks inside Microsoft Word where filings are authored.
- Zero local dependencies or native DLLs; runs in modern web taskpane sandbox.
- Precise paragraph-level synchronization preserves document formatting.

### Negative / Limitations
- Sideloading requires administrative permission in corporate/enterprise Microsoft 365 environments.
- Large multi-hundred page filings must be paginated/batched to respect Office.js memory boundaries.
