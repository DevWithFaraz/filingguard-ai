# scoring

Priority: P0. Tasks: T045-T046 in the root TODO.md.

Calculate versioned deductions, category scores and coverage deterministically.

Findings/check states in; score, breakdown and incomplete status out. Unknown checks never count as passes.

`service.py` calculates `integrity-v1` from saved open findings: info 0, low 3,
medium 8, high 15, critical 25 points. Resolved/system findings do not deduct.
The value is clamped at zero; deductions include stable finding IDs. This is a
review-priority heuristic, not a calibrated legal-risk probability. Warnings about
uncertainty can deduct; coverage still shows missing checks separately.
Category values use the same versioned deductions and each stage's eligible/
evaluated counts. Statute-stage coverage is added to the citation category;
statute findings still use type `citation`. An unevaluated category is unknown, even when the overall score
exists; category scores remain provisional review signals.

No score is issued before a terminal analysis and at least one evaluated
citation/proposition/quote check. Every score remains provisional. High/critical
findings or a value below 60 produce `high_risk`; other scored analyses remain
`needs_review`. No current analysis is represented as legally ready to file.

Focused tests cover deterministic weights, active/local-only gates, missing
coverage, resolved findings and report agreement. See
[[docs/decisions/ADR-011 - Grounded review and saved result boundaries]].
