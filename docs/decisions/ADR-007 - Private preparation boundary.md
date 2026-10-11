---
type: decision
status: accepted
date: 2026-09-28
tags: [decisions, security, intake]
---
# ADR-007 - Private preparation boundary

## Context
The user requested remaining Phase 3/4 implementation. Anonymous private sessions
are approved; legal engines/providers, reports and graphs are not implemented yet.
Public intake is disabled. Protect original evidence without simulating legal jobs
or migrating production as a side effect of development/testing.

## Decision and alternatives
Use server-issued 256-bit opaque bearer tokens in tab sessionStorage and persist
only SHA-256/55-minute expiry in AnonymousSession. Avoid cross-host ambient cookies;
credentials are omitted and credentialed CORS is disabled. Session issuance requires
an exact allowed Origin; authenticated private requests reject disallowed supplied
origins, while origin-less bearer clients are permitted. Token theft/XSS/tab cloning
can share access; this is temporary ownership, not an account or device identity.

Prepare Text/PDF/server-owned Demo with 201/not_run after actual extraction/storage.
Persist snapshot/segments and input/extraction hashes, but no fabricated findings
or score. A future 202 legal job must explicitly run the orchestrator. Activity
returns metadata only. Unknown real court rules remain unknown; demo court synthetic.
Raw PDF POST plus encoded filename header avoids multipart parser buffering and
filename query logs. Original filenames are display-only, never paths.

Before buffering: authenticate expiry/ownership, bound actual chunks and total
15-second body deadline, and acquire one process-wide preparation slot. Limits:
10 MiB/20 pages/100,000 code points/2,000 paragraphs; five documents/session;
10 submits/hour and 120 private requests/minute per owner; five session issues/
minute per socket peer; 256 live sessions and 1,024 live rate buckets. Do not trust
client X-Forwarded-For. A hosting proxy can make users share issuance limits;
trusted-proxy policy needs hosted evaluation. This is basic abuse resistance,
not DDoS protection. T023 must retain admission through complete analysis jobs.

Parse PDFs in a bounded short-lived process, not the API interpreter. Strip API/DB
credentials and suppress parser logs/stderr. Use 15-second kill/drain deadline;
POSIX 256 MiB address space/10-second CPU/core-disabled limits; Windows 256 MiB
per-process Job Object, two active processes for venv redirector/interpreter and
kill-on-close. Do not call this filesystem/network privilege isolation or malware
proofing. Malformed/encrypted/no-text/resource failures receive paste-text fallback.
Diagnostics cannot prove all pages were extracted correctly; no OCR is attempted.

Mask provider-bound excerpts locally against the complete canonical filing before
slicing, preserving original offsets with one star/code point. Pattern coverage is
limited and false positives/negatives possible. Provider payload integration and
privacy findings remain T022/T030/T031/T038, not completed by counting matches.

## Consequences
Intake is off by default. The disposable localhost preview overrides DB/root only
inside its child process and migrates its own temporary SQLite DB, never Neon.
Shutdown removes temporary preview data; crash leftovers need OS-temp cleanup.
Persistent configured deployments require deliberate migrations 0002/0003 and
hosted resource/ACL/exposure tests. Retention is best effort, not secure erasure.
Original text is private but not encrypted by this module. No confidential client
use before T212/T213. Public enablement/deployment needs separate authorization.

## Evidence and verification
Real Windows worker normal/timeout and encrypted/no-text/malformed inputs pass;
SQLite migrations/ownership/expiry/deletion and chunked limits pass. Real Chrome
desktop/mobile verify Text/PDF/Demo, reload, cross-session rejection, parser
fallback, Activity summaries and deletion. POSIX limits/ACLs, Render deployment,
new Neon migrations, actual provider masking and legal jobs remain unverified.

Containment references: [Windows job objects](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects),
[extended limits](https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-jobobject_extended_limit_information),
[subprocess timeout handling](https://docs.python.org/3/library/subprocess.html),
[pypdf extraction/no OCR](https://github.com/py-pdf/pypdf/blob/main/docs/user/extract-text.md).

## Related
[[docs/decisions/Index]], [[TODO]] T017-T022/T023/T057/T212,
[[contracts/README]], [[apps/api/src/filingguard/modules/documents/README]],
[[apps/api/src/filingguard/db/models/README]],
[[apps/api/src/filingguard/modules/privacy/README]],
[[apps/web/src/features/intake/README]],
[[docs/issues/BUG-005 - Windows venv worker process limit]].
