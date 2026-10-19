"""Comprehensive tests for verified real court profiles and deterministic rule evaluation."""

from datetime import date
from uuid import uuid4

import pytest

from filingguard.db.models import Analysis, Finding
from filingguard.integrations.providers.runtime import ProviderBudget
from filingguard.modules.analyses.runners import court_stage
from filingguard.modules.analyses.schemas import StageName
from filingguard.modules.court_rules.service import (
    CourtProfile,
    evaluate_disclosure,
    evaluate_format_rules,
    evaluate_page_limit,
    evaluate_required_headings,
    load_profile,
)


def test_load_txnd_profile_attributes():
    profile = load_profile("us-txnd-lr7-2f-v1")
    assert profile.id == "us-txnd-lr7-2f-v1"
    assert profile.version == "txnd-lr7-2f-2024-09"
    assert "Northern District of Texas" in profile.name
    assert "Local Civil Rule 7.2(f)" in profile.name
    assert "txnd.uscourts.gov" in profile.source
    assert profile.effective_from == date(2024, 9, 3)
    assert profile.effective_to == date(2099, 12, 31)
    assert profile.court_scope == "U.S. District Court for the Northern District of Texas"
    assert profile.judge_scope is None
    assert profile.is_demo is False

    rule = profile.ai_disclosure
    assert rule.rule_id == "txnd-lr-7-2f"
    assert rule.trigger == "ai_used"
    assert "Local Rule 7.2(f)" in rule.requirement
    assert rule.heading == "Use of Generative Artificial Intelligence"
    assert rule.placement == "first_page"


def test_load_profile_rejects_unsupported():
    with pytest.raises(ValueError, match="Unsupported court profile"):
        load_profile("unsupported-profile-id")


def test_profile_mode_mismatch_fails_closed():
    # Demo mode cannot evaluate real court profile
    res_demo_on_real = evaluate_disclosure(
        "us-txnd-lr7-2f-v1", "Text", ai_used=True, demo=True
    )
    assert res_demo_on_real.status == "unavailable"
    assert res_demo_on_real.reason == "Court profile scope does not match review mode"

    # Live review cannot evaluate demo profile
    res_live_on_demo = evaluate_disclosure(
        "synthetic-demo-v1", "Text", ai_used=True, demo=False
    )
    assert res_live_on_demo.status == "unavailable"
    assert res_live_on_demo.reason == "Court profile scope does not match review mode"


def test_txnd_effective_dates_boundary():
    # Before effective date: 2024-09-02
    res_before = evaluate_disclosure(
        "us-txnd-lr7-2f-v1",
        "Text",
        ai_used=True,
        demo=False,
        as_of=date(2024, 9, 2),
    )
    assert res_before.status == "unavailable"
    assert res_before.reason == "Court profile outside effective period"

    # On effective date: 2024-09-03
    res_on = evaluate_disclosure(
        "us-txnd-lr7-2f-v1",
        "Use of Generative Artificial Intelligence\n\nMotion text",
        ai_used=True,
        demo=False,
        as_of=date(2024, 9, 3),
    )
    assert res_on.status == "present"

    # Beyond effective date
    res_after = evaluate_disclosure(
        "us-txnd-lr7-2f-v1",
        "Text",
        ai_used=True,
        demo=False,
        as_of=date(2100, 1, 1),
    )
    assert res_after.status == "unavailable"
    assert res_after.reason == "Court profile outside effective period"


def test_txnd_not_triggered_when_ai_not_used():
    res = evaluate_disclosure(
        "us-txnd-lr7-2f-v1",
        "Argument text without disclosure",
        ai_used=False,
        demo=False,
        as_of=date(2024, 10, 1),
    )
    assert res.status == "not_triggered"
    assert res.rule_id == "txnd-lr-7-2f"
    assert "Local Rule 7.2(f)" in (res.requirement or "")


def test_txnd_paginated_first_page_presence():
    pages = [
        "IN THE UNITED STATES DISTRICT COURT\nUse of Generative Artificial Intelligence\nText",
        "Page two argument text.",
    ]
    res = evaluate_disclosure(
        "us-txnd-lr7-2f-v1",
        "\n\n".join(pages),
        ai_used=True,
        demo=False,
        pages=pages,
        as_of=date(2024, 10, 1),
    )
    assert res.status == "present"
    assert "Heading presence only" in (res.reason or "")
    assert "independent human review" in (res.reason or "")


def test_txnd_paginated_later_page_is_missing():
    pages = [
        "IN THE UNITED STATES DISTRICT COURT\nPage one text without disclosure.",
        "Page two argument text.\nUse of Generative Artificial Intelligence\nDetails.",
    ]
    res = evaluate_disclosure(
        "us-txnd-lr7-2f-v1",
        "\n\n".join(pages),
        ai_used=True,
        demo=False,
        pages=pages,
        as_of=date(2024, 10, 1),
    )
    assert res.status == "missing"
    assert "found on later page" in (res.reason or "")
    assert "requires placement on the first page" in (res.reason or "")


def test_txnd_paginated_completely_missing():
    pages = [
        "IN THE UNITED STATES DISTRICT COURT\nPage one text without disclosure.",
        "Page two argument text.",
    ]
    res = evaluate_disclosure(
        "us-txnd-lr7-2f-v1",
        "\n\n".join(pages),
        ai_used=True,
        demo=False,
        pages=pages,
        as_of=date(2024, 10, 1),
    )
    assert res.status == "missing"
    assert "was not found on the first page" in (res.reason or "")


def test_txnd_unpaginated_plain_text():
    # Present in plain text
    text_with_heading = (
        "Preliminary Statement\n"
        "Use of Generative Artificial Intelligence\n"
        "Filing body text."
    )
    res_present = evaluate_disclosure(
        "us-txnd-lr7-2f-v1",
        text_with_heading,
        ai_used=True,
        demo=False,
        pages=None,
        as_of=date(2024, 10, 1),
    )
    assert res_present.status == "present"
    assert "Heading found in plain text" in (res_present.reason or "")
    assert "lacks page boundaries" in (res_present.reason or "")

    # Missing in plain text
    text_without_heading = "Preliminary Statement\nFiling body text."
    res_missing = evaluate_disclosure(
        "us-txnd-lr7-2f-v1",
        text_without_heading,
        ai_used=True,
        demo=False,
        pages=[],
        as_of=date(2024, 10, 1),
    )
    assert res_missing.status == "missing"
    assert "was not found" in (res_missing.reason or "")


def test_passing_mention_in_sentence_is_not_heading():
    text = (
        "We discuss the use of generative artificial intelligence in our legal analysis.\n"
        "However no separate heading was provided."
    )
    res = evaluate_disclosure(
        "us-txnd-lr7-2f-v1",
        text,
        ai_used=True,
        demo=False,
        as_of=date(2024, 10, 1),
    )
    assert res.status == "missing"


def test_unverified_and_unknown_court_evaluations():
    res_unverified = evaluate_disclosure("unverified", "text", ai_used=True, demo=False)
    assert res_unverified.status == "unavailable"
    assert res_unverified.reason == "Court rules not configured"

    res_unknown = evaluate_disclosure("nonexistent", "text", ai_used=True, demo=False)
    assert res_unknown.status == "unavailable"
    assert res_unknown.reason == "Court profile unavailable"


def test_court_stage_generates_dynamic_txnd_finding():
    analysis = Analysis(
        id=uuid4(),
        mode="live",
        court_profile_id="us-txnd-lr7-2f-v1",
        ai_used=True,
        document_name="Brief.pdf",
        document_sha256="0" * 64,
    )
    analysis.document_snapshot = {
        "text": "Page 1 content.\n\nPage 2 content.",
        "pages": [
            {"page_number": 1, "start": 0, "end": 16},
            {"page_number": 2, "start": 18, "end": 34},
        ],
    }

    result = court_stage(analysis, ProviderBudget(0))
    assert result.status.value == "completed"
    findings = [r for r in result.records if isinstance(r, Finding) and r.type == "court_rule"]
    assert len(findings) == 1
    f = findings[0]
    assert f.title == "Required N.D. Tex. Local Rule 7.2(f) AI-use disclosure missing"
    assert f.severity == "medium"
    assert "Local Rule 7.2(f)" in f.description
    assert "Automated detection checks heading presence only" in f.description
    assert "substantive legal compliance requires independent human review" in f.description
    assert f.rule_id == "txnd-lr-7-2f"


def test_court_stage_txnd_compliant_has_no_findings():
    page1 = "Use of Generative Artificial Intelligence\nDisclosed tools."
    page2 = "Substantive motion arguments."
    full_text = f"{page1}\n\n{page2}"
    analysis = Analysis(
        id=uuid4(),
        mode="live",
        court_profile_id="us-txnd-lr7-2f-v1",
        ai_used=True,
        document_name="Compliant.pdf",
        document_sha256="0" * 64,
    )
    analysis.document_snapshot = {
        "text": full_text,
        "pages": [
            {"page_number": 1, "start": 0, "end": len(page1)},
            {"page_number": 2, "start": len(page1) + 2, "end": len(full_text)},
        ],
    }

    result = court_stage(analysis, ProviderBudget(0))
    assert result.status.value == "completed"
    findings = [r for r in result.records if isinstance(r, Finding) and r.type == "court_rule"]
    assert findings == []
    assert "Heading presence only" in result.reason


def _demo_profile_with(*, max_pages: int | None = None, heading: str | None = None):
    data = load_profile("synthetic-demo-v1").model_dump(mode="json")
    if max_pages is not None:
        data["page_limit"]["max_pages"] = max_pages
    if heading is None:
        data["required_headings"] = []
    else:
        data["required_headings"] = [
            {
                "rule_id": "demo-test-heading",
                "heading": heading,
                "placement": "anywhere",
                "requirement": "Synthetic heading check for tests.",
            }
        ]
    return CourtProfile.model_validate(data)


def test_page_limit_exceeded_is_finding_not_a_pass():
    profile = _demo_profile_with(max_pages=2, heading=None)
    pages = ["page one", "page two", "page three"]
    result = evaluate_page_limit(profile, pages)
    assert result is not None
    assert result.status == "exceeded"
    assert result.rule_id == "demo-page-limit"
    assert "exceeds the versioned limit of 2" in (result.reason or "")


def test_required_heading_missing_and_present():
    profile = _demo_profile_with(heading="STATEMENT OF ISSUES")
    missing = evaluate_required_headings(profile, "Argument without the heading.", pages=None)
    assert len(missing) == 1
    assert missing[0].status == "missing"
    assert missing[0].rule_id == "demo-test-heading"

    present = evaluate_required_headings(
        profile, "STATEMENT OF ISSUES\nArgument follows.", pages=None
    )
    assert present[0].status == "present"
    assert "Heading presence only" in (present[0].reason or "")


def test_format_rules_unpaginated_page_limit_is_unavailable():
    profile = load_profile("synthetic-demo-v1")
    results = evaluate_format_rules(profile, "STATEMENT OF ISSUES\nBody", pages=None)
    page_limit = next(item for item in results if item.check == "page_limit")
    heading = next(item for item in results if item.check == "heading")
    assert page_limit.status == "unavailable"
    assert "not a pass" in (page_limit.reason or "")
    assert heading.status == "present"


def test_demo_live_mode_mismatch_unchanged_with_format_fields():
    profile = load_profile("synthetic-demo-v1")
    assert profile.page_limit is not None
    assert profile.required_headings
    res_demo_on_real = evaluate_disclosure(
        "us-txnd-lr7-2f-v1", "Text", ai_used=True, demo=True
    )
    assert res_demo_on_real.status == "unavailable"
    assert res_demo_on_real.reason == "Court profile scope does not match review mode"
    res_live_on_demo = evaluate_disclosure(
        "synthetic-demo-v1", "Text", ai_used=True, demo=False
    )
    assert res_live_on_demo.status == "unavailable"
    assert res_live_on_demo.reason == "Court profile scope does not match review mode"


def test_court_stage_demo_heading_and_page_limit():
    pages = [f"page {index}" for index in range(21)]
    text = "\n\n".join(pages)
    analysis = Analysis(
        id=uuid4(),
        mode="demo",
        court_profile_id="synthetic-demo-v1",
        ai_used=False,
        document_name="Long.pdf",
        document_sha256="0" * 64,
        demo_fixture_id="curated-v1",
    )
    cursor = 0
    page_spans = []
    for page in pages:
        page_spans.append(
            {
                "page_number": len(page_spans) + 1,
                "start": cursor,
                "end": cursor + len(page),
            }
        )
        cursor += len(page) + 2
    analysis.document_snapshot = {"text": text, "pages": page_spans}
    result = court_stage(analysis, ProviderBudget(0))
    result.validate(StageName.COURT_RULES)
    assert result.status.value == "completed"
    assert result.coverage.eligible == result.coverage.evaluated == 3
    findings = [r for r in result.records if isinstance(r, Finding) and r.type == "court_rule"]
    titles = {f.title for f in findings}
    assert "Synthetic page limit exceeded" in titles
    assert "Synthetic required heading missing" in titles
    assert all(f.title != "Synthetic AI-use disclosure missing" for f in findings)


def test_court_stage_unpaginated_page_limit_is_partial_not_a_pass():
    analysis = Analysis(
        id=uuid4(),
        mode="demo",
        court_profile_id="synthetic-demo-v1",
        ai_used=False,
        document_name="Brief.txt",
        document_sha256="0" * 64,
        demo_fixture_id="curated-v1",
    )
    analysis.document_snapshot = {"text": "STATEMENT OF ISSUES\nArgument.", "pages": []}
    result = court_stage(analysis, ProviderBudget(0))
    result.validate(StageName.COURT_RULES)
    assert result.status.value == "partial"
    assert result.coverage.unavailable == 1
    assert result.coverage.evaluated == 2
    assert "not a pass" in (result.coverage.limitation or "").lower()
