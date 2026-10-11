# Demo fixtures

T014 curated material now lives in [[data/demo/curated-v1/README]], with genuine
public opinion snapshots and exact-span expectation drafts. Delegated AI review
is recorded separately from human approval; exact multi-authority cached-source
execution and reset are now verified locally under T016/T052. See
[[docs/product/Demo fixture review]] for judgments, provenance and conditions.

The `synthetic-starter` fixture is entirely invented test material. It is not a
court opinion, legal rule or actual filing and must never appear as live verified
legal evidence. Its purpose is to start deterministic fixture-driven development.

- `filings/synthetic-starter.txt`: fabricated input with intentional issues.
- `authorities/synthetic-source.txt`: fabricated source for quote/claim test pairs.
- `manifest.json`: explicit mode, attribution and unvalidated status.
- `expected/synthetic-starter.json`: intended test scenarios, not execution results.

T014-T015 added the curated SRS demo, genuine public authorities with source URL,
retrieval time/hash and attribution, and explicitly reviewed expectations. The
starter remains unreviewed and fails closed in the runtime demo adapter.

T016 requires explicit demo mode and matches a versioned fixture ID/document
hash. Hashes are validated before replay. Never use this source or expected
results for arbitrary uploaded text, and never fall back to them silently.
