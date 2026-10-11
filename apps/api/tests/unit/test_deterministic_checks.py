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
