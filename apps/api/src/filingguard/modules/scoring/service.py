"""Versioned review deductions; unavailable checks never count as passes."""

VERSION = "integrity-v1"
WEIGHTS = {"info": 0, "low": 3, "medium": 8, "high": 15, "critical": 25}
LIMITATION = (
    "Provisional review score, not filing safety or legal readiness. "
    "Missing checks remain unknown and are displayed separately."
)


def score_review(stages, findings, *, status):
    deductions = [
        {
            "finding_id": str(f.id),
            "type": f.type,
            "severity": f.severity,
            "points": WEIGHTS[f.severity],
        }
        for f in findings
        if f.type != "system" and f.status != "resolved"
    ]
    substantive = any(
        s.name.value in {"citations", "propositions", "quotes"} and s.coverage.evaluated > 0
        for s in stages
    )
    value = (
        max(0, 100 - sum(d["points"] for d in deductions))
        if substantive and status in {"completed", "partial", "failed", "interrupted"}
        else None
    )
    risk = (
        None
        if value is None
        else (
            "high_risk"
            if value < 60 or any(d["severity"] in {"high", "critical"} for d in deductions)
            else "needs_review"
        )
    )
    categories = []
    terminal = status in {"completed", "partial", "failed", "interrupted"}
    stage_by_name = {s.name.value: s for s in stages}
    for category, stage_name in (
        ("citation", "citations"),
        ("claim_support", "propositions"),
        ("quote", "quotes"),
        ("privacy", "privacy"),
        ("court_rule", "court_rules"),
    ):
        stage = stage_by_name.get(stage_name)
        eligible = stage.coverage.eligible if stage else 0
        evaluated = stage.coverage.evaluated if stage else 0
        points = sum(d["points"] for d in deductions if d["type"] == category)
        categories.append(
            {
                "type": category,
                "eligible": eligible,
                "evaluated": evaluated,
                "value": max(0, 100 - points) if terminal and evaluated else None,
                "deducted_points": points,
            }
        )
    return {
        "value": value,
        "risk_level": risk,
        "provisional": True,
        "version": VERSION,
        "deductions": deductions,
        "categories": categories,
        "limitation": LIMITATION,
    }
