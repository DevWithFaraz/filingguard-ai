# Persistence

T009-T013 add SQLAlchemy models for Analysis, DocumentSegment, Citation, Authority,
Claim, ClaimAuthorityLink, Quote, Finding and EvidenceRecord. Keep relational IDs
and links queryable; use JSONB for immutable snapshots/metadata where appropriate.
Use transactions and analysis-scoped queries. No models or database connection yet.
