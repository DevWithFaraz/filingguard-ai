# Bounded provider transport

Tasks: T024, with T022/T031/T033/T038 integration in [[TODO]].

`runtime.py` provides a finite monotonic deadline, atomic attempt accounting and
two shared provider slots. The parent carries receipts across stages. A child with
zero remaining attempts may run local logic but cannot send an HTTP request.

`transport.py` owns fixed-host HTTPX clients, paths, auth headers, byte bounds,
stream closing and sanitized failure codes. No arbitrary URLs, redirects,
environment proxies, cookie replay, automatic SDK retries or raw HTTP logging.
CourtListener has at most one selected transient retry; Groq has none. Valid
Retry-After waits are never shortened to fit a budget. HTTP failures, including
404, are transport errors, not legal not-found verdicts. Domain adapters must
interpret successful source responses separately.

Defaults: 128 KiB request (path/query plus body), 4 MiB decoded response, two shared
in-flight calls, cooperative 20-second operation budget including waits/retries.
HTTP phase limits cannot forcibly stop arbitrary blocking code. The parent stage
supervisor provides the hard stop; never invoke this boundary from an unbounded
API/event-loop thread. See [[apps/api/src/filingguard/modules/analyses/README]].

`passages.py` prepares at most 8,000 filing or 12,000 source code points, preserving
original start/end and requested end with an explicit truncation flag. Filing
context is masked against the whole original snapshot before clipping. Byte caps
still apply to the assembled provider request. Relevance selection, prompt/schema
validation and provider-specific responses are not implemented by these helpers.

Current integration: real CourtListener/Groq adapters are explicitly opted in;
actual outgoing semantic payload masking is tested at the fixed-host transport.
Synthetic transports verify failure/ownership boundaries; separate genuine model
controls verify only their stated fixture scope. No test fixture supplies a cached
semantic verdict to a real request. See
[[docs/decisions/ADR-008 - Contained review deadlines and provider budgets]] and
[[docs/sessions/2026-10-02 - Provider budgets and hard deadlines]].

October 11: Groq retains only allowlisted numerical TPM limit/remaining/reset
receipts. Advisory token-cost admission waits stay within the hard stage deadline;
after admission the HTTP operation still has its 20-second cap. No Groq retry is
introduced. Organization-level concurrent use can still exhaust quota. Unfittable
waits reject before spending another attempt. See
[[docs/sessions/2026-10-11 - Accessibility performance and release gates]].
