# Demo fixtures

The `synthetic-starter` fixture is entirely invented test material. It is not a
court opinion, legal rule or actual filing and must never appear as live verified
legal evidence. Its purpose is to start deterministic fixture-driven development.

- `filings/synthetic-starter.txt`: fabricated input with intentional issues.
- `authorities/synthetic-source.txt`: fabricated source for quote/claim test pairs.
- `manifest.json`: explicit mode, attribution and unvalidated status.
- `expected/synthetic-starter.json`: intended test scenarios, not execution results.

T014-T015 must add the full SRS demo, genuine public authorities with source URL,
retrieval time/hash and attribution, and reviewed expectations. The starter is not
the final acceptance fixture and has not been run through any analysis engine.

T016 must require explicit demo mode and match a versioned fixture ID/document
hash. Compute hashes when locking the fixtures. Never use this source or expected
results for arbitrary uploaded text, and never fall back to them silently.
