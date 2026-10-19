"""Filing-versus-case fact comparison; no live provider calls."""

import hashlib
import time
from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

from filingguard.db.models import (
    Authority,
    Citation,
    Claim,
    ClaimAuthorityLink,
    EvidenceRecord,
    Finding,
)
from filingguard.integrations.providers.runtime import ProviderBudget
from filingguard.modules.analyses.runners import local_runners
from filingguard.modules.analyses.schemas import StageName, StageStatus
from filingguard.modules.propositions.facts import compare_facts, extract_facts
from filingguard.modules.propositions.passages import select_passages
from filingguard.modules.propositions.schemas import SourcePassage
from filingguard.modules.propositions.service import review_propositions


def _analysis(filing: str, source: str):
    analysis_id, segment_id = uuid4(), uuid4()
    claim = Claim(
        id=uuid4(),
        analysis_id=analysis_id,
        text=filing,
        segment_id=segment_id,
        start_offset=0,
        end_offset=len(filing),
        page_number=1,
        extraction_method="heuristic",
    )
    authority = Authority(
        id=uuid4(),
        analysis_id=analysis_id,
        source="courtlistener",
        external_id="123",
        source_url="https://www.courtlistener.com/opinion/123/",
        opinion_text_available=True,
        opinion_text=source,
        source_sha256=hashlib.sha256(source.encode()).hexdigest(),
        retrieved_at=datetime.now(UTC),
    )
    citation = Citation(
        id=uuid4(),
        analysis_id=analysis_id,
        authority_id=authority.id,
        verification_status="verified",
    )
    link = ClaimAuthorityLink(
        id=uuid4(),
        analysis_id=analysis_id,
        claim_id=claim.id,
        citation_id=citation.id,
        authority_id=authority.id,
        support_status="not_run",
    )
    return SimpleNamespace(
        id=analysis_id,
        mode="live",
        document_snapshot={"text": filing},
        review_claims=(claim,),
        review_citations=(citation,),
        review_authorities=(authority,),
        review_links=(link,),
        provider_credentials={},
    )


def _fact_findings(result):
    return [
        row
        for row in result.records
        if isinstance(row, Finding) and "fact" in row.title.lower()
    ]


class Never:
    def review(self, *args, **kwargs):
        raise AssertionError("No model request allowed")

    def review_batch(self, *args, **kwargs):
        raise AssertionError("No model request allowed")


def test_extracts_dates_parties_and_numeric_holdings():
    facts = extract_facts(
        "On May 17, 1954, Brown v. Board of Education required 14 days notice and $500."
    )
    kinds = {item.kind for item in facts}
    assert kinds == {"date", "party", "numeric"}
    assert any(item.year == 1954 and item.month == 5 and item.day == 17 for item in facts)
    assert {item.normalized for item in facts if item.kind == "party"} == {
        "brown",
        "board education",
    }
    assert any(item.unit == "day" and item.value == 14 for item in facts)
    assert any(item.unit == "usd" and item.value == 500 for item in facts)


def test_matching_facts_produce_no_fact_finding():
    filing = (
        "On May 17, 1954, Brown v. Board of Education held that 14 days notice "
        "is required before termination."
    )
    source = (
        "Decided May 17, 1954. Brown v. Board of Education of Topeka. "
        "Notice is required before termination after 14 days."
    )
    assert select_passages(source, filing)
    result = review_propositions(_analysis(filing, source), adapter=None)
    assert _fact_findings(result) == []
    result.validate(StageName.PROPOSITIONS)


def test_contradictory_date_and_party_are_flagged():
    filing = (
        "In 1954, Brown v. Board of Education held that 14 days notice is "
        "required before termination."
    )
    source = (
        "In 1966, Miranda v. Arizona held that 7 days notice is required before termination."
    )
    assert select_passages(source, filing)
    result = review_propositions(_analysis(filing, source), adapter=None)
    findings = _fact_findings(result)
    assert len(findings) == 1
    assert findings[0].title == "Filing fact may not match source fact"
    assert findings[0].severity == "medium"
    assert findings[0].ai_assisted is False
    assert "heuristic review signal" in findings[0].description.lower()
    evidence = [
        row
        for row in result.records
        if isinstance(row, EvidenceRecord) and row.finding_id == findings[0].id
    ]
    assert any(row.source_type == "document" for row in evidence)
    assert any(row.source_type == "opinion_text" for row in evidence)
    assert any(row.source_metadata.get("evidence_passage_id") for row in evidence)
    assert any(row.source_metadata.get("passage_ids") for row in evidence)
    result.validate(StageName.PROPOSITIONS)


def test_missing_source_is_insufficient_not_a_pass():
    filing = "In 1954, Brown v. Board of Education required notice before termination."
    analysis = _analysis(filing, "In 1954 Brown required notice before termination.")
    analysis.review_authorities = ()
    result = review_propositions(analysis, adapter=Never())
    assert result.updates[0].support_status == "insufficient_source"
    findings = _fact_findings(result)
    assert len(findings) == 1
    assert findings[0].title == "Insufficient source text for fact comparison"
    assert findings[0].severity == "low"
    assert "not a pass" in findings[0].description.lower() or "cannot be compared" in (
        findings[0].description.lower()
    )
    result.validate(StageName.PROPOSITIONS)


def test_no_source_passages_is_insufficient_not_a_mismatch():
    filing = "In 1954, Brown v. Board of Education required notice before termination."
    source = "Entirely unrelated judicial discussion without overlapping terms."
    assert select_passages(source, filing) == ()
    result = review_propositions(_analysis(filing, source), adapter=Never())
    findings = _fact_findings(result)
    assert len(findings) == 1
    assert findings[0].title == "Insufficient source text for fact comparison"
    assert findings[0].title != "Filing fact may not match source fact"
    result.validate(StageName.PROPOSITIONS)


def test_missing_source_facts_are_insufficient_not_a_pass():
    filing = "In 1954, the court held that 14 days notice is required before termination."
    source = "Notice is required before termination in emergency and ordinary cases."
    passages = select_passages(source, filing)
    assert passages
    comparison = compare_facts(filing, passages, source_available=True)
    assert comparison.status == "insufficient_source"
    result = review_propositions(_analysis(filing, source), adapter=None)
    findings = _fact_findings(result)
    assert findings[0].title == "Insufficient source text for fact comparison"
    assert "not a pass" in findings[0].description.lower()


def test_disabled_semantic_review_makes_fact_comparison_unavailable():
    stage = local_runners(
        SimpleNamespace(semantic_review_enabled=False, source_verification_enabled=False)
    )[StageName.PROPOSITIONS]
    assert stage.status == StageStatus.UNAVAILABLE
    assert "fact comparison is unavailable" in stage.reason
    stage.validate(StageName.PROPOSITIONS)


def test_compare_facts_does_not_invent_analogies_when_source_lacks_the_fact():
    passage = SourcePassage("p1", "The court discussed notice.", 0, 28, "0" * 64)
    comparison = compare_facts(
        "On May 17, 1954, Brown v. Board required notice.",
        (passage,),
        source_available=True,
    )
    assert comparison.status == "insufficient_source"
    assert comparison.conflicts == ()


def test_year_only_matches_full_source_date():
    source = "Decided May 17, 1954. Notice is required before termination."
    passages = select_passages(source, "In 1954 notice is required before termination.")
    comparison = compare_facts(
        "In 1954 notice is required before termination.",
        passages,
        source_available=True,
    )
    assert comparison.status == "match"


def test_no_credentials_path_does_not_call_network(monkeypatch):
    from filingguard.modules.propositions.service import propositions_stage

    monkeypatch.setenv("GROQ_API_KEY", "should-not-be-read")
    filing = "In 1954 notice is required before termination."
    source = "In 1966 notice is required before termination."
    result = propositions_stage(
        _analysis(filing, source), ProviderBudget(time.monotonic() + 30)
    )
    findings = _fact_findings(result)
    assert findings[0].title == "Filing fact may not match source fact"
    assert findings[0].ai_assisted is False
    result.validate(StageName.PROPOSITIONS)
