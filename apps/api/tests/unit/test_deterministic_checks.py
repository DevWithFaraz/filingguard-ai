"""Synthetic rules are training data, not legal claims about a real court."""

from datetime import date

import pytest
from pydantic import ValidationError

from filingguard.modules.court_rules.service import (
    CourtProfile,
    evaluate_disclosure,
    load_profile,
)
from filingguard.modules.privacy.checks import detect_sensitive


def test_synthetic_profile_scope_and_disclosure():
    profile = load_profile("synthetic-demo-v1")
    assert profile.is_demo and profile.court_scope == "Fictional Demo Review Court"
    assert evaluate_disclosure(profile.id, "Argument only", True, demo=True).status == "missing"
    assert (
        evaluate_disclosure(profile.id, "AI USE DISCLOSURE\nReviewed", True, demo=True).status
        == "present"
    )
    assert (
        evaluate_disclosure(profile.id, "Argument only", False, demo=True).status == "not_triggered"
    )
    assert (
        evaluate_disclosure(profile.id, "Argument only", True, demo=False).status == "unavailable"
    )
    assert (
        evaluate_disclosure(
            profile.id, "Argument only", True, demo=True, as_of=date(2100, 1, 1)
        ).status
        == "unavailable"
    )
    assert evaluate_disclosure("unknown", "Argument only", True, demo=False).status == "unavailable"


def test_invalid_profile_metadata_is_rejected():
    source = load_profile("synthetic-demo-v1").model_dump(mode="json")
    source["effective_to"] = "2025-01-01"
    with pytest.raises(ValidationError):
        CourtProfile.model_validate(source)
    source["effective_to"] = "2099-12-31"
    source.pop("court_scope")
    with pytest.raises(ValidationError):
        CourtProfile.model_validate(source)


def test_privacy_signals_exclude_benign_numbers():
    text = (
        "Brown v. Board of Education, 347 U.S. 483 (1954). "
        "Event date 09/27/2026. Matter DEMO-001. "
        "SSN 900-12-3456; account number 000123456789; date of birth 04/17/2000."
    )
    signals = detect_sensitive(text)
    assert [signal.kind for signal in signals] == ["ssn", "financial_account", "birth_date"]
    assert all(text[signal.start : signal.end] not in signal.masked_snippet for signal in signals)
    assert detect_sensitive("DOB 02/30/2026; event date 09/27/2026.") == ()


def test_minor_name_heuristics_detect_synthetic_cases():
    cases = [
        ("Petitioner files on behalf of minor child Johnathan Doe.", "Johnathan Doe"),
        ("Plaintiff Jane Smith, as guardian of Emily Davis, a minor.", "Emily Davis"),
        ("The custody order pertains to Michael Brown, a minor.", "Michael Brown"),
        ("Identifying information: minor: Sarah Connor.", "Sarah Connor"),
    ]
    for text, expected_name in cases:
        signals = detect_sensitive(text)
        assert len(signals) == 1, f"Expected 1 signal for: {text}"
        sig = signals[0]
        assert sig.kind == "minor_name"
        assert sig.severity == "high"
        assert text[sig.start : sig.end] == expected_name
        assert expected_name not in sig.masked_snippet
        assert "*" * len(expected_name) in sig.masked_snippet


def test_minor_name_heuristics_exclude_benign_controls():
    benign_controls = [
        # Compliant initials under Rule 5.2(a)(3)
        "The minor child, A.B., was placed with relatives.",
        "Custody of minor child J. D., born in 2015.",
        "Next friend of M.H., a minor.",
        # Non-person usage of 'minor'
        "The driver suffered minor injuries in a minor accident with minor delays.",
        "The plaintiff made a minor modification to the vehicle.",
        # Case citations with 'Minor' as party name
        "In Minor v. Happersett, the Supreme Court discussed citizenship.",
        "See Smith versus Minor, 123 F.3d 456.",
        # Institutional entities and adult titles
        "United States District Court, Southern District of New York.",
        "Dr. Robert Ray and Attorney Jane Smith appeared.",
    ]
    for text in benign_controls:
        signals = detect_sensitive(text)
        minor_signals = [s for s in signals if s.kind == "minor_name"]
        assert minor_signals == [], f"Unexpected minor_name signal for benign text: {text}"


def test_privacy_stage_generates_minor_name_finding_with_explicit_uncertainty():
    from uuid import uuid4

    from filingguard.db.models import Analysis, Finding
    from filingguard.integrations.providers.runtime import ProviderBudget
    from filingguard.modules.analyses.runners import privacy_stage

    text = "Action brought by Mary Jenkins on behalf of minor child Tommy Jenkins."
    analysis = Analysis(
        id=uuid4(),
        mode="synthetic",
        document_name="Test doc",
        document_sha256="0" * 64,
    )
    analysis.document_snapshot = {"text": text, "diagnostics": []}
    result = privacy_stage(analysis, ProviderBudget(0))
    findings = [r for r in result.records if isinstance(r, Finding) and r.type == "privacy"]
    assert len(findings) == 1
    f = findings[0]
    assert f.title == "Possible unredacted minor name"
    assert f.severity == "high"
    assert "Fed. R. Civ. P. 5.2(a)(3)" in f.description
    assert "explicit uncertainty" in f.description
    assert "Tommy Jenkins" not in f.document_excerpt
    assert "*" in f.document_excerpt
