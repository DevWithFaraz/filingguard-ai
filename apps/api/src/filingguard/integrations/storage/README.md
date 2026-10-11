# Private temporary storage

T017 foundation for [[TODO]]; requirements: [[FilingGuard_AI_SRS#14.3 Security and Privacy]],
[[FilingGuard_AI_SRS#9.2 Document Parsing]] and [[docs/architecture/stack]].
Extraction/segmentation belongs to [[apps/api/src/filingguard/modules/documents/README]].

## Implemented interface

`PrivateTemporaryStorage()` owns a fresh random directory in OS temporary storage,
outside the application/public asset tree. Do not mount this directory as static
content or make its location available to callers. There is no route or static mount
in this adapter, and its creation has no effect on enabled upload endpoints.

- `store(pdf_bytes)` validates then exclusively writes `<random UUID4>.pdf`.
  Returns `StoredPDF(file_id, size_bytes, page_count, character_count)`.
- `read(file_id)` returns original bytes for a registered, unexpired opaque ID.
- `delete(file_id)` removes a registered file; repeated/unknown UUID deletion
  returns false. Unknown UUID reads fail. Malformed/noncanonical IDs are rejected.
- `cleanup_expired()` removes registered files whose retention has elapsed.
- `close()` or a context manager deletes owned files and the empty directory.

No interface accepts a client filename or filesystem path. UUIDs from another
adapter instance cannot access files. IDs are storage references, not authorization:
T018 session ownership must gate any eventual route. File-backed analyses now store
only this opaque reference in the DB; the original bytes remain outside the DB.

## Admission limits

Only bytes beginning with `%PDF-` are considered; pypdf performs strict parsing.
Limits are 10 MiB inclusive, 1-20 pages, and 100,000 extracted characters across
all pages. Encrypted, malformed, zero-page, blank and image-only/scanned PDFs with
no extractable text are rejected with fixed messages and safe reason codes.
Extracted text is discarded; no document text is returned in metadata or errors.

The locked pypdf 6.19 configuration is applied only within the parsing context:
2 MiB declared/decoded stream and combined-content limits, bounded Flate/LZW/
run-length decompression, 64 KiB Flate recovery input, 256 page-tree entries,
32 page-tree depth and 100 form invocations per page. External JBIG2 execution
is disabled. Before extraction, page content and form resource streams are decoded
and checked: at most 256 unique streams, 8 MiB total decoded content, 64 elements
per content array, 128 external resources per resource dictionary and nesting 16.
Oversized compressed content therefore fails before text extraction. A text visitor
checks the character budget during extraction, followed by an exact output check.

These conservative limits can reject valid complex PDFs. Visitor callbacks for
forms may count fragments more than once. This is no OCR or extraction-quality
assessment: blank/scanned pages within an otherwise text-bearing PDF are not rejected
individually. T020/T021 must preserve page coverage and offer a paste-text fallback.
Limits constrain particular parser operations, not total process memory or wall time;
fonts, object tables and intermediate text can still allocate before rejection.
A retained failure flag rejects visitor budget failures even when pypdf catches
the exception inside a form; other internal form errors can still yield partial text.
There is no isolated worker,
hard CPU timeout or guarantee against every malicious PDF. Offload/blocking-work
and execution isolation remain integration responsibilities. HTTP request streaming
and request-body limits must be applied before constructing these in-memory bytes.
Before public intake, configure privacy-safe third-party parser logging as well:
sanitizing returned exceptions alone does not constrain library log messages.

## Privacy, lifetime and filesystem safety

The default retention is one hour, measured with a monotonic clock. Reads lazily
delete expired files; `cleanup_expired()` is an explicit sweep, with no scheduler.
The default adapter registry is process-local; crash/restart can leave inaccessible
orphan files. The application now owns scheduled sweeps/shutdown. Public intake must
use the recoverable adapter below, not this process-local fallback. Neither is
durable evidence storage or secure erasure.

Directories request mode 0700 and exclusive file creation requests mode 0600.
Windows protection depends on inherited temp-directory ACLs; chmod is best effort
and does not establish a private ACL. The deployment must ensure its OS temp root
is private and never served, synced or published. Disk encryption remains future.

Operations validate canonical UUID4 IDs before lookup, then use only the registry.
Root/file identities are checked; symlinks, Windows reparse points, replacement
files, nonregular files and hardlinks are rejected. Reads additionally compare
the opened descriptor and use `O_NOFOLLOW` when available. Cleanup never recursively
walks foreign files or directories. In-process calls are serialized, but this is
not protection against a privileged local attacker racing filesystem replacement;
Windows has no portable `O_NOFOLLOW`, and checks/unlink are not atomic.

## Verification handoff

Focused synthetic PDFs are generated locally with `PdfWriter`; tests cover valid
round trips, boundary limits, compressed content, malformed/encrypted/scanned input,
opaque IDs, traversal, collisions, write failure, retention, deletion, cross-instance
isolation and filesystem replacement. Real symlink/POSIX permission checks depend
on host capabilities. Run from the vault root:

```powershell
node scripts/api.mjs run pytest tests/unit/test_storage.py
node scripts/api.mjs run ruff check src/filingguard/integrations/storage tests/unit/test_storage.py
```

No provider, DB, upload-route, session-ownership, hosted-public-exposure or production
filesystem verification is implied by these unit checks. Parent integration owns
T017 status and the broader documentation/session handoff.

## T013 recoverable storage and application integration

`RecoverableTemporaryStorage(absolute_directory)` adds a dedicated, stable,
server-selected root with a valid ownership marker, exclusive process lease and
per-file metadata receipts. The parent must exist; a foreign existing directory is
not claimed. Windows still relies on private inherited ACLs. Do not use a public
asset path, vault, synced folder or client-selected path. Keep this root stable
across process restarts. One process/replica may own it at a time.

Receipts retain UUID, file identity, SHA-256, size/counts and wall-clock expiry, not
filing text or client filenames. Recovery checks receipt schema, content hash,
identities, links and the entire flat namespace before removing recognized
UUID-named crash leftovers. Unknown files, directories and tampered material fail
closed without recursive deletion. At most 1,000 registered files are admitted;
this is a safety bound, not the public user's quota or concurrency policy.

Normal TTL is still one hour. Restored deadlines retain the recorded expiry with
remaining lifetime capped at one retention window; clock rollback is not a hard
expiry guarantee. Missing/failed file deletion is retried; one failing file does
not stop attempts on other files. Default `close()` attempts all registered files,
then releases the lease, leaving only root ownership/lease metadata when successful.
An OS purge failure preserves receipts for a later restart and raises a safe error.

The app's lifespan owns storage and a threaded sweeper. Configure
`PRIVATE_STORAGE_DIRECTORY` to opt into recovery and database lifecycle cleanup;
`CLEANUP_INTERVAL_SECONDS` defaults to 60 (allowed 1-3600). Without a configured
root the public shell uses the old temporary adapter and makes no DB connection.
With a root, sweeps initialize DB recovery even without new intake, after operator-
applied migrations. File expiry is attempted before DB calls and after DB failure.
Shutdown waits for an in-flight sweep before closing storage/engine. These are
best-effort sweeps: DB stalls, disk errors and downtime can delay deletion.

Crash recovery is verified for abrupt process termination on the same filesystem,
not power-loss durability, cross-host recovery or Render disk replacement. Retained
DB results can outlive original ephemeral PDF bytes. An opt-in private upload route
now enforces bounded bodies, ownership and worker extraction. Public/default
uploads remain disabled; hosted exposure/platform checks are not complete.
See [[docs/decisions/ADR-006 - Retryable private lifecycle cleanup]] and
[[apps/api/src/filingguard/modules/analyses/README]].

Checks: `tests/unit/test_managed_storage.py`, `tests/unit/test_runtime.py` and
`tests/integration/test_lifecycle.py`. New migration checks are in
`tests/integration/test_persistence.py`. Platform-dependent permission checks are
not evidence of a deployed Windows/Linux security configuration.

HTTP preparation uses worker-validated bytes and `_store_validated` so the parent
never reparses an untrusted PDF. This internal API trusts only the server-owned
validated worker result; clients cannot supply page/character counts. Direct
adapter `.store()` retains validation for trusted unit/internal use and is not
the HTTP parsing boundary. Display filenames never select filesystem paths.
See [[apps/api/src/filingguard/modules/documents/README]].
