# courtlistener adapter

Citation lookup, opinion retrieval, identity mapping, timeouts/retries and provider error mapping. Record source URLs/timestamps/hashes. Distinguish not-found from unavailable. Use approved hosts rather than arbitrary URLs found in a filing.

Status: unimplemented. Keep provider details out of domain modules. Demo responses
must be selected explicitly for recognized fixtures, never substituted silently
for an arbitrary live analysis.

T004 live access was verified by `scripts/check_provider_access.py`:
authenticated quota check, genuine lookup and public opinion plain text all
returned 200. See [[docs/research/Provider access verification]]. The script is a
development probe, not the production adapter; timeout/retry/error mapping and
bounded text extraction still need implementation.
