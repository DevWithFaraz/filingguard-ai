# Production Data Protection and Deployment Threat Review

- **Document**: Production Security Review & Release Gate
- **Status**: Verified Specification / Production Gate Criteria
- **Date**: 2026-10-19
- **Governing Requirements**: SRS section 14 (Security), NFR-040–NFR-045, AUD-001–AUD-004, T212
- **Related Documents**:
  - [[docs/architecture/stack|Architecture Stack Decisions]]
  - [[docs/decisions/ADR-004 - In-memory and private-filesystem storage boundaries|ADR-004: Storage Boundaries]]
  - [[docs/decisions/ADR-006 - Private storage authorization and session isolation|ADR-006: Private Storage Authorization]]
  - [[docs/decisions/ADR-015 - Durable job execution and transactional worker leases|ADR-015: Durable Worker Leases]]

---

## 1. Executive Summary & Production Gate Scope

Before FilingGuard AI can be released for confidential real-client legal filings (beyond synthetic demos and public test documents), strict verification of production data protection, encryption, operational controls, and deployment threats must be completed.

This review formalizes the security and governance architecture required under **NFR-045**, establishing verification controls across seven key pillars:
1. Encryption in transit and at rest
2. Database backups, restore procedures, and point-in-time recovery
3. Explicit deletion policies and cryptographic unlinking
4. Least-privilege access and secret rotation
5. Third-party provider data retention agreements
6. STRIDE deployment threat analysis
7. Audit log isolation and zero-raw-filing leakage verification

---

## 2. Encryption Architecture

### 2.1. In-Transit Encryption (TLS 1.3)
- **Edge to Client**: All web client traffic is terminated via TLS 1.3 with HSTS enabled (`max-age=31536000; includeSubDomains; preload`).
- **Application to Neon Database**: PostgreSQL connections enforce SSL mode `verify-full` (`sslmode=require` / `verify-full`). Unencrypted TCP connections are rejected by database firewall rules.
- **Provider API Communication**: Outbound calls to CourtListener and inference providers (OpenAI / Groq) occur strictly over TLS 1.3 with verified CA bundles.

### 2.2. At-Rest Encryption
- **Database (PostgreSQL on Neon)**: Managed Lakebase Postgres provides AES-256 transparent data encryption (TDE) at the block storage layer. Relational tables holding extracted segments, citations, findings, and evidence digests are stored encrypted on disk.
- **Ephemeral Private File Storage**: Uploaded PDF filings temporarily stored in `PRIVATE_STORAGE_DIRECTORY` reside on an encrypted volume (LUKS on Linux / BitLocker on Windows).
- **Sensitive Identity Secrets**: User passwords/secrets for claimed accounts are hashed using PBKDF2-HMAC-SHA256 with 600,000 iterations and per-user cryptographic salts (`secrets.token_bytes(16)`). Plaintext secrets are never persisted.

---

## 3. Backup, Restore, and Point-in-Time Recovery

### 3.1. Neon Continuous WAL & Branch-First Restore
- Continuous Write-Ahead Log (WAL) archiving allows point-in-time recovery (PITR) up to 7 days on standard branches and 30 days on protected branches.
- Disaster recovery procedure:
  ```bash
  # 1. Create instant point-in-time restore branch via Neon CLI
  neon branch create --name recovery-branch --parent main --timestamp "2026-10-19T12:00:00Z"
  # 2. Verify schema and transaction integrity
  neon connection-string recovery-branch
  # 3. Promote recovery branch to production head
  ```

### 3.2. Ephemeral Storage Crash Resilience
- Because uploaded PDF blobs in `private_storage/` are strictly ephemeral with a maximum time-to-live of 4 hours, backup restore restores DB state while expired files are safely cleaned up via `AnalysisLifecycle.purge_all_expired()` without corrupting application state.

---

## 4. Deletion Policy & Cryptographic Unlinking

### 4.1. Immediate User Deletion (`DELETE /analyses/{id}`)
- Deleting an analysis triggers a transactional cascade delete in PostgreSQL (`ondelete="CASCADE"` across all 10 child tables: segments, citations, authorities, claims, links, quotes, findings, evidence, comments).
- Before committing the DB transaction, the underlying encrypted PDF file on disk is securely removed via `os.remove()` / `delete_file()`. If disk removal fails, DB deletion aborts to prevent orphaned state.

### 4.2. Automated Retention Cleanup (`purge_all_expired`)
- Under **NFR-044**, a recurring scheduled sweep executes `purge_all_expired(batch_size=50)`.
- Analyses older than `expires_at` are purged along with their associated storage files.
- Memory garbage collection sweeps remove expired tokens and in-memory rate-limiter buckets.

---

## 5. Least Privilege & Secret Rotation

| Secret / Credential | Scope | Rotation Cadence | Storage Mechanism |
|---|---|---|---|
| `DATABASE_URL` | Neon Postgres Connection | 90 days | Environment variable (Render / Secret Manager) |
| `COURTLISTENER_API_TOKEN` | Read-only Citation Lookup | 180 days | Environment variable |
| `OPENAI_API_KEY` | Structured Proposition Inference | 90 days | Environment variable |
| Session Token Salts | Session Hash Derivation | App Restart | In-memory `secrets.token_urlsafe()` |

- **Principle of Least Privilege**: The application database user has DDL/DML permissions within the `public` schema only; superuser and cross-database access are disabled. Outbound CourtListener token has read-only search permissions.

---

## 6. Third-Party Provider Retention Terms

A prerequisite for confidential legal filing review is ensuring third-party providers do not use prompt data for model training:
1. **CourtListener (Free Law Project)**:
   - Queries transmit parsed citations only (e.g. `347 U.S. 483`). Raw brief text is never sent to CourtListener.
2. **OpenAI / Groq Inference Providers**:
   - Organization accounts must execute the **Zero Data Retention (ZDR)** agreement or API data privacy addendum confirming inputs/outputs are not retained for model training or persistent caching.
   - PII masking (`mask_pii`) deterministic scanner runs *prior* to any semantic evaluation, replacing Social Security numbers, account numbers, and sensitive identifiers with neutral replacement markers.

---

## 7. STRIDE Deployment Threat Review

| Threat Category | Potential Vector | Mitigation in FilingGuard AI | Verification Status |
|---|---|---|---|
| **Spoofing** | Cross-tenant analysis access | Ephemeral session tokens (`owner_hash`), `_owned_analysis` query guards on every route | Verified (Integration tests pass) |
| **Tampering** | In-flight payload modification | TLS 1.3 strictly enforced; SHA-256 integrity checks on uploaded documents | Verified (Document extraction tests) |
| **Repudiation** | Denying sign-off on invalid citation | Reviewer disposition metadata records name, role, timestamp, and audit trail in `0009` | Verified (`test_collaboration.py`) |
| **Information Disclosure** | Filing leakage in error logs | `NFR-023`: Zero filing text in logs; correlation ID headers only; error boundary sanitization | Verified (`test_retention_and_observability.py`) |
| **Denial of Service** | Gigantic PDF intake / Memory exhaustion | 10 MB upload ceiling; 100k character bound; 20-page cap; single-flight admission semaphores | Verified (`test_intake.py`) |
| **Elevation of Privilege** | Route bypass without bearer token | `IntakeGuard` middleware blocks unauthenticated access to `/analyses`, `/matters`, `/batches` | Verified (`admission.py`) |

---

## 8. Release Gate Sign-Off

The technical controls specified in this document satisfy the security criteria for **T212**. Confidential client use may proceed once the administrative Zero Data Retention addendum is countersigned with the inference provider.
