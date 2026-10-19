"""Table of Authorities detection and both-way comparison."""

from uuid import uuid4

from filingguard.db.models import Analysis, Finding
from filingguard.integrations.providers.runtime import ProviderBudget
from filingguard.modules.analyses.schemas import StageName
from filingguard.modules.table_of_authorities.runner import table_of_authorities_stage
from filingguard.modules.table_of_authorities.service import (
    audit_table_of_authorities,
    detect_toa_span,
)


def _analysis(text: str, pages=None) -> Analysis:
    analysis = Analysis(
        id=uuid4(),
        mode="live",
        court_profile_id="unverified",
        ai_used=False,
        document_name="brief.txt",
        document_sha256="0" * 64,
    )
    analysis.document_snapshot = {"text": text, "pages": pages or []}
    return analysis


MATCHED = (
    "TABLE OF AUTHORITIES\n\n"
    "Brown v. Board of Education, 347 U.S. 483 (1954) .......... 2\n\n"
    "ARGUMENT\n"
    "The holding in 347 U.S. 483 controls the question presented.\n"
)

MIXED = (
    "TABLE OF AUTHORITIES\n\n"
    "Brown v. Board of Education, 347 U.S. 483 (1954) .......... 2\n"
    "Miranda v. Arizona, 384 U.S. 436 (1966) .................... 3\n\n"
    "ARGUMENT\n"
    "The holding in 347 U.S. 483 controls. See also 576 U.S. 644.\n"
)

NO_TABLE = "ARGUMENT\nThe holding in 347 U.S. 483 controls the question presented.\n"


def test_heading_detection_and_argument_end():
    span, uncertain = detect_toa_span(MATCHED)
    assert span is not None and not uncertain
    assert span.heading == "table_of_authorities"
    assert "ARGUMENT" not in MATCHED[span.start : span.end]


def test_no_table_is_not_a_pass():
    span, uncertain = detect_toa_span(NO_TABLE)
    assert span is None and not uncertain
    result = table_of_authorities_stage(_analysis(NO_TABLE), ProviderBudget(0))
    result.validate(StageName.TABLE_OF_AUTHORITIES)
    assert result.status.value == "skipped"
    assert result.coverage.eligible == 0
    assert result.records == ()
    assert "not evaluated" in (result.reason or "")


def test_matched_table_and_body_produce_no_differences():
    audit = audit_table_of_authorities(MATCHED)
    assert audit.detected
    assert audit.missing_from_table == []
    assert audit.extra_in_table == []
    result = table_of_authorities_stage(_analysis(MATCHED), ProviderBudget(0))
    result.validate(StageName.TABLE_OF_AUTHORITIES)
    assert result.status.value == "completed"
    assert result.coverage.evaluated == result.coverage.eligible >= 1
    findings = [row for row in result.records if isinstance(row, Finding)]
    assert findings == []


def test_missing_and_extra_authorities_are_flagged():
    audit = audit_table_of_authorities(MIXED)
    assert any("576" in key for key in audit.missing_from_table)
    assert any("384" in key for key in audit.extra_in_table)
    result = table_of_authorities_stage(_analysis(MIXED), ProviderBudget(0))
    result.validate(StageName.TABLE_OF_AUTHORITIES)
    findings = [row for row in result.records if isinstance(row, Finding)]
    titles = " ".join(item.title for item in findings)
    assert any("missing from Table of Authorities" in item.title for item in findings)
    assert any("not cited in body" in item.title for item in findings)
    assert "576 U.S. 644" in titles
    assert "384 U.S. 436" in titles
    missing = next(item for item in findings if "missing" in item.title)
    assert missing.severity == "medium"
    assert missing.start_offset is not None
    extra = next(item for item in findings if "not cited" in item.title)
    assert extra.severity == "low"
    assert "Listed pages:" in extra.description


def test_listed_pages_are_captured_and_mismatch_is_flagged():
    text = (
        "TABLE OF AUTHORITIES\n"
        "347 U.S. 483 .......... 9\n\n"
        "ARGUMENT\n"
        "See 347 U.S. 483.\n"
    )
    argument = text.index("ARGUMENT")
    pages = [
        {"page_number": 1, "start": 0, "end": argument},
        {"page_number": 2, "start": argument, "end": len(text)},
    ]
    result = table_of_authorities_stage(_analysis(text, pages), ProviderBudget(0))
    result.validate(StageName.TABLE_OF_AUTHORITIES)
    findings = [row for row in result.records if isinstance(row, Finding)]
    assert any("page references differ" in item.title for item in findings)
    mismatch = next(item for item in findings if "page references differ" in item.title)
    assert "9" in mismatch.description
    assert "2" in mismatch.description


def test_uncertain_bounds_are_unavailable_not_skipped():
    text = "TABLE OF AUTHORITIES\n347 U.S. 483 .......... 1\nno later heading appears here"
    span, uncertain = detect_toa_span(text)
    assert span is None and uncertain
    result = table_of_authorities_stage(_analysis(text), ProviderBudget(0))
    result.validate(StageName.TABLE_OF_AUTHORITIES)
    assert result.status.value == "unavailable"
    assert result.coverage.unavailable == 1
    assert result.records == ()
