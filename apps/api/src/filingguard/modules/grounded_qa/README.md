# Grounded Q&A Module (`apps/api/src/filingguard/modules/grounded_qa`)

Implements Finding-grounded Q&A (FR-260 through FR-264).

## Responsibilities
- **Scoped evidence access (`FR-260`, `FR-261`):** Allows users to ask forensic questions about a specific finding (`finding_id`) within an analysis (`analysis_id`).
- **Strict answer grounding (`FR-262`):** Answers cite persisted evidence records (`evidence_record_ids`), source authority names, and official source URLs. Never generates unsupported or hallucinated authorities.
- **Refusal of broad legal advice (`FR-263`):** Detects questions requesting litigation strategy, probability of success, or substantive arguments (e.g. "What should I argue?", "Will I win?"), refusing with safe redirect to qualified independent legal counsel.
- **Exclusion of general document chat (`FR-264`):** Out-of-scope queries unrelated to the finding are rejected.
- **Missing-evidence transparency:** Explicitly reports when authorities or passages were not found in public court repositories, emphasizing that absence in a database does not prove fabrication.
- **Rate & abuse limiting:** Enforces per-analysis question limits (`MAX_QUESTIONS_PER_ANALYSIS = 20`) and question string constraints (1 to 500 characters).

## REST Endpoints
- `POST /api/v1/analyses/{analysis_id}/findings/{finding_id}/questions`
- `GET /api/v1/analyses/{analysis_id}/findings/{finding_id}/questions`
