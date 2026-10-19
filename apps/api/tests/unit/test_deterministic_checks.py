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


def test_unknown_privacy_policy_is_unavailable_not_a_pass():
    from filingguard.modules.court_rules.service import PrivacyPolicyBinding
    from filingguard.modules.privacy.service import resolve_privacy_policy

    binding = PrivacyPolicyBinding(
        policy_id="unknown-jurisdiction-v1",
        version="v0",
        source_url="https://example.invalid/unknown-privacy",
        source_checked_on=date(2026, 10, 19),
        extra_identifier_kinds=("email",),
    )
    resolved = resolve_privacy_policy(binding, is_demo=False)
    assert resolved.status == "unavailable"
    assert resolved.extra_identifier_kinds == ()
    assert "not a pass" in (resolved.reason or "")
    text = "Counsel: review@example.com"
    assert detect_sensitive(text) == ()
    assert detect_sensitive(text, extra_identifier_kinds=resolved.extra_identifier_kinds) == ()


def test_stale_privacy_policy_is_unavailable():
    from filingguard.modules.court_rules.service import load_profile
    from filingguard.modules.privacy.service import resolve_privacy_policy

    profile = load_profile("us-txnd-lr7-2f-v1")
    resolved = resolve_privacy_policy(
        profile.privacy_policy, is_demo=False, as_of=date(2100, 1, 1)
    )
    assert resolved.status == "unavailable"
    assert resolved.extra_identifier_kinds == ()


def test_demo_privacy_policy_enables_email_and_live_frcp_stays_conservative():
    from uuid import uuid4

    from filingguard.db.models import Analysis, Finding
    from filingguard.integrations.providers.runtime import ProviderBudget
    from filingguard.modules.analyses.runners import privacy_stage
    from filingguard.modules.court_rules.service import load_profile
    from filingguard.modules.privacy.service import resolve_privacy_policy

    demo = load_profile("synthetic-demo-v1")
    applied = resolve_privacy_policy(demo.privacy_policy, is_demo=True)
    assert applied.status == "applied"
    assert applied.extra_identifier_kinds == ("email",)

    live = load_profile("us-txnd-lr7-2f-v1")
    conservative = resolve_privacy_policy(live.privacy_policy, is_demo=False)
    assert conservative.status == "applied"
    assert conservative.extra_identifier_kinds == ()

    text = "Contact the training desk at review@example.com before filing."
    analysis = Analysis(
        id=uuid4(),
        mode="demo",
        court_profile_id="synthetic-demo-v1",
        document_name="Demo.txt",
        document_sha256="0" * 64,
        demo_fixture_id="curated-v1",
    )
    analysis.document_snapshot = {"text": text, "diagnostics": []}
    result = privacy_stage(analysis, ProviderBudget(0))
    findings = [r for r in result.records if isinstance(r, Finding) and r.type == "privacy"]
    assert [f.title for f in findings] == ["Possible email address"]
    assert result.coverage.limitation is None

    live_analysis = Analysis(
        id=uuid4(),
        mode="live",
        court_profile_id="us-txnd-lr7-2f-v1",
        document_name="Live.txt",
        document_sha256="0" * 64,
    )
    live_analysis.document_snapshot = {"text": text, "diagnostics": []}
    live_result = privacy_stage(live_analysis, ProviderBudget(0))
    live_findings = [
        r for r in live_result.records if isinstance(r, Finding) and r.type == "privacy"
    ]
    assert live_findings == []


def test_privacy_stage_unknown_policy_limitation_does_not_enable_extras(monkeypatch):
    from uuid import uuid4

    from filingguard.db.models import Analysis, Finding
    from filingguard.integrations.providers.runtime import ProviderBudget
    from filingguard.modules.analyses import runners
    from filingguard.modules.court_rules.service import CourtProfile, load_profile

    source = load_profile("synthetic-demo-v1").model_dump(mode="json")
    source["privacy_policy"]["policy_id"] = "unknown-jurisdiction-v1"

    def fake_load(_profile_id: str) -> CourtProfile:
        return CourtProfile.model_validate(source)

    monkeypatch.setattr(runners, "load_profile", fake_load)
    text = "Contact the training desk at review@example.com before filing."
    analysis = Analysis(
        id=uuid4(),
        mode="demo",
        court_profile_id="synthetic-demo-v1",
        document_name="Demo.txt",
        document_sha256="0" * 64,
        demo_fixture_id="curated-v1",
    )
    analysis.document_snapshot = {"text": text, "diagnostics": []}
    result = runners.privacy_stage(analysis, ProviderBudget(0))
    assert result.status.value == "completed"
    assert result.coverage.limitation is not None
    assert "not a pass" in result.coverage.limitation
    findings = [r for r in result.records if isinstance(r, Finding) and r.type == "privacy"]
    assert findings == []
