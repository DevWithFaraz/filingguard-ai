# red_team

Priority: P1. Tasks: T101 in [[TODO]].

Rank weaknesses grounded only in existing findings and retrieved sources.

Saved findings/evidence in; linked review critiques out. Do not draft new legal arguments.

## Design and invariants
- `schemas.py`: defines `RedTeamWeakness` and `RedTeamResponse` strictly adhering to `Contract`.
- `service.py`: `synthesize_weaknesses()` and `synthesize_red_team()` evaluate persisted findings across citations, claims, quotes, privacy leaks, and court rules.
- **FR-241 & FR-243**: Weaknesses are classified by vulnerability type, ranked deterministically by severity (critical, high, medium, low), and articulate the adversarial challenge theory explaining how opposing counsel or the court will exploit the defect.
- **FR-242**: Findings are synthesized solely from persisted analysis records and evidence.
- **FR-244**: The engine provides objective remediation hints; it never drafts new legal arguments or substitutes for human legal judgment.
- **FR-245**: Every weakness links back to its underlying finding IDs, citation IDs, claim IDs, and quote IDs.
- Deterministic IDs derived via UUID5 ensure identical findings produce stable weakness identifiers across repeated requests.
