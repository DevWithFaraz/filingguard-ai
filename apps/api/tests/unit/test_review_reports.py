from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest

from filingguard.modules.analyses.schemas import Coverage, StageName, StageState, StageStatus
from filingguard.modules.reports.service import render_report, safe_text
from filingguard.modules.scoring.service import score_review


def finding(severity, *, kind="quote", status="open"):
    return SimpleNamespace(id=uuid4(), type=kind, severity=severity, status=status)


def stages(*, legal=True, unavailable=0):
    return [
        StageState(
            name=StageName.QUOTES if legal else StageName.PRIVACY,
            status=StageStatus.PARTIAL if unavailable else StageStatus.COMPLETED,
            coverage=Coverage(eligible=1 + unavailable, evaluated=1, unavailable=unavailable),
            reason="A dependency is unavailable" if unavailable else None,
        )
    ]


def test_scoring_weights_are_deterministic_and_critical_exceeds_warning():
    severe, warning = finding("critical"), finding("medium")
    first = score_review(stages(), [severe], status="partial")
    second = score_review(stages(), [warning], status="partial")
    assert first["value"] < second["value"]
    assert first == score_review(stages(), [severe], status="partial")
    assert first["version"] == "integrity-v1"
    assert first["deductions"][0]["finding_id"] == str(severe.id)
    assert first["deductions"][0]["points"] > second["deductions"][0]["points"]


@pytest.mark.parametrize("status", ["not_run", "queued", "running"])
def test_active_or_unrun_analysis_has_no_score(status):
    result = score_review(stages(), [finding("high")], status=status)
    assert result["value"] is None and result["risk_level"] is None


def test_local_privacy_checks_cannot_become_legal_readiness_score():
    result = score_review(stages(legal=False), [finding("low", kind="privacy")], status="partial")
    assert result["value"] is None
    assert result["risk_level"] is None
    by_type = {row["type"]: row for row in result["categories"]}
    assert by_type["privacy"]["value"] == 97
    assert by_type["quote"]["value"] is None
    assert by_type["citation"]["evaluated"] == 0


def test_missing_legal_checks_remain_unknown_and_provisional():
    unavailable = StageState(
        name=StageName.PROPOSITIONS,
        status=StageStatus.UNAVAILABLE,
        coverage=Coverage(eligible=3, unavailable=3),
        reason="Source unavailable",
    )
    unknown = score_review([unavailable], [], status="partial")
    assert unknown["value"] is None
    some = score_review(stages(unavailable=3), [], status="partial")
    assert some["provisional"] is True
    assert some["risk_level"] != "ready_for_review"
    assert "unknown" in some["limitation"].lower()


def test_system_warnings_and_resolved_findings_do_not_deduct_twice():
    result = score_review(
        stages(),
        [
            finding("critical", kind="system"),
            finding("critical", status="resolved"),
            finding("info"),
        ],
        status="partial",
    )
    assert result["value"] == 100
    assert result["risk_level"] != "ready_for_review"
    assert len(result["deductions"]) == 1


def test_score_saturates_at_zero():
    assert (
        score_review(stages(), [finding("critical") for _ in range(8)], status="partial")["value"]
        == 0
    )


def test_explanation_echoes_and_new_identifiers_are_masked():
    filing = "SSN 123-45-6789 and client@example.com"
    output = safe_text("Model repeats 123-45-6789; alternate new@example.com", filing)
    assert "123-45-6789" not in output and "new@example.com" not in output
    assert "***********" in output


def report_input():
    return {
        "analysis_id": str(uuid4()),
        "created_at": datetime.now(UTC),
        "mode": "live",
        "status": "partial",
        "court_profile_id": "unverified",
        "limitation": "Human review required. Not legal advice.",
        "score": score_review(stages(), [finding("high")], status="partial"),
        "coverage": {
            "evaluated": 1,
            "eligible": 2,
            "unavailable": 1,
            "pending": 0,
            "truncated": False,
        },
        "stages": [stages()[0].model_dump(mode="json")],
        "findings": [
            {
                "severity": "high",
                "title": "<script>alert('x')</script>",
                "description": "<img src=x onerror=alert(1)>",
                "masked_excerpt": "<b>source</b>",
                "evidence_count": 1,
            }
        ],
        "citations": [],
        "claims": [],
        "quotes": [],
    }


def test_html_escapes_all_untrusted_finding_markup():
    report = render_report(report_input(), format="html")
    assert "<script>" not in report and "<img " not in report
    assert "&lt;script&gt;" in report and "&lt;img " in report
    assert "&lt;b&gt;source&lt;/b&gt;" in report


def test_report_uses_given_saved_results_without_new_classification(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("Export attempted a new model classification")

    monkeypatch.setattr(
        "filingguard.integrations.llm.adapter.GroqPropositionAdapter.review", forbidden
    )
    results = report_input()
    rendered = render_report(results)
    assert results["analysis_id"] in rendered
    assert "1/2 evaluated" in rendered
    assert "1 unavailable" in rendered
    assert "integrity-v1" in rendered
