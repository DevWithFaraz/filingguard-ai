"""Unit tests for Legal Red-Team Mode (FR-240 through FR-245)."""

from types import SimpleNamespace
from uuid import uuid4

from filingguard.modules.red_team.service import synthesize_weaknesses


def test_empty_findings_produces_zero_weaknesses_and_clear_summary():
    analysis_id = uuid4()
    response = synthesize_weaknesses(analysis_id, [])

    assert response.analysis_id == analysis_id
    assert response.total_weaknesses == 0
    assert response.critical_count == 0
    assert response.high_count == 0
    assert response.medium_count == 0
    assert response.low_count == 0
    assert "No high-risk adversarial vulnerabilities" in response.summary
    assert "not legal strategy or legal advice" in response.limitation


def test_synthesizes_misrepresented_authority_as_critical():
    analysis_id = uuid4()
    f_id = uuid4()
    claim_id = uuid4()
    cit_id = uuid4()

    finding = SimpleNamespace(
        id=f_id,
        type="claim_support",
        severity="critical",
        title="Misrepresented holding of Brown v. Board of Education",
        description=(
            "The filing claims separate facilities were affirmed, but Brown held the opposite."
        ),
        claim_id=claim_id,
        citation_id=cit_id,
        quote_id=None,
    )
    claim = SimpleNamespace(id=claim_id)
    citation = SimpleNamespace(id=cit_id)

    response = synthesize_weaknesses(
        analysis_id, [finding], citations=[citation], claims=[claim]
    )

    assert response.total_weaknesses == 1
    assert response.critical_count == 1
    weakness = response.weaknesses[0]
    assert weakness.vulnerability_type == "misrepresented_authority"
    assert weakness.severity == "critical"
    assert "Rule 11" in weakness.challenge_theory or "impeach" in weakness.challenge_theory
    assert weakness.linked_finding_ids == [f_id]
    assert weakness.linked_claim_ids == [claim_id]
    assert weakness.linked_citation_ids == [cit_id]


def test_synthesizes_unverified_citation_as_critical():
    analysis_id = uuid4()
    f_id = uuid4()
    cit_id = uuid4()

    finding = SimpleNamespace(
        id=f_id,
        type="citation",
        severity="critical",
        title="Citation not found: 999 U.S. 999",
        description="The citation could not be found in CourtListener or official reporters.",
        claim_id=None,
        citation_id=cit_id,
        quote_id=None,
    )
    citation = SimpleNamespace(id=cit_id)

    response = synthesize_weaknesses(analysis_id, [finding], citations=[citation])

    assert response.total_weaknesses == 1
    assert response.critical_count == 1
    weakness = response.weaknesses[0]
    assert weakness.vulnerability_type == "unverified_citation"
    assert weakness.severity == "critical"
    assert "non-existent authority" in weakness.challenge_theory
    assert weakness.linked_finding_ids == [f_id]
    assert weakness.linked_citation_ids == [cit_id]


def test_synthesizes_critical_privacy_exposure():
    analysis_id = uuid4()
    f_id = uuid4()

    finding = SimpleNamespace(
        id=f_id,
        type="privacy",
        severity="critical",
        title="Social Security number pattern detected",
        description="Found unredacted SSN pattern on page 1.",
        claim_id=None,
        citation_id=None,
        quote_id=None,
    )

    response = synthesize_weaknesses(analysis_id, [finding])

    assert response.total_weaknesses == 1
    assert response.critical_count == 1
    weakness = response.weaknesses[0]
    assert weakness.vulnerability_type == "privacy_exposure"
    assert weakness.severity == "critical"
    assert "Fed. R. Civ. P. 5.2" in weakness.challenge_theory or "seal" in weakness.challenge_theory
    assert weakness.linked_finding_ids == [f_id]


def test_synthesizes_altered_quotation_and_missing_court_disclosure():
    analysis_id = uuid4()
    quote_f_id = uuid4()
    quote_id = uuid4()
    rule_f_id = uuid4()

    quote_finding = SimpleNamespace(
        id=quote_f_id,
        type="quote",
        severity="high",
        title="Quotation text altered from source opinion",
        description="Quotation in filing alters wording from Miranda v. Arizona.",
        claim_id=None,
        citation_id=None,
        quote_id=quote_id,
    )
    quote = SimpleNamespace(id=quote_id)

    rule_finding = SimpleNamespace(
        id=rule_f_id,
        type="court_rule",
        severity="high",
        title="Missing required AI disclosure heading",
        description="Filing used AI but lacks mandatory disclosure heading.",
        claim_id=None,
        citation_id=None,
        quote_id=None,
    )

    response = synthesize_weaknesses(
        analysis_id, [quote_finding, rule_finding], quotes=[quote]
    )

    assert response.total_weaknesses == 2
    assert response.high_count == 2
    types = {w.vulnerability_type for w in response.weaknesses}
    assert types == {"altered_quotation", "court_rule_violation"}


def test_deterministic_sorting_and_id_stability():
    analysis_id = uuid4()
    crit_id = uuid4()
    high_id = uuid4()
    med_id = uuid4()

    f_med = SimpleNamespace(
        id=med_id,
        type="claim_support",
        severity="medium",
        title="Broad claim with qualified support",
        description="Source contains nuances.",
        claim_id=None,
        citation_id=None,
        quote_id=None,
    )
    f_crit = SimpleNamespace(
        id=crit_id,
        type="claim_support",
        severity="critical",
        title="Misrepresented holding",
        description="Direct contradiction.",
        claim_id=None,
        citation_id=None,
        quote_id=None,
    )
    f_high = SimpleNamespace(
        id=high_id,
        type="quote",
        severity="high",
        title="Altered quotation",
        description="Mismatch.",
        claim_id=None,
        citation_id=None,
        quote_id=None,
    )

    # Supply out of order: med, crit, high
    resp1 = synthesize_weaknesses(analysis_id, [f_med, f_crit, f_high])
    resp2 = synthesize_weaknesses(analysis_id, [f_high, f_med, f_crit])

    assert [w.severity for w in resp1.weaknesses] == ["critical", "high", "medium"]
    assert [w.severity for w in resp2.weaknesses] == ["critical", "high", "medium"]

    # UUIDs derived via UUID5 are identical between calls
    assert [w.id for w in resp1.weaknesses] == [w.id for w in resp2.weaknesses]
