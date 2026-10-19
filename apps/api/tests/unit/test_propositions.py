import hashlib
import time
from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

import httpx
import pytest

from filingguard.db.models import Authority, Citation, Claim, ClaimAuthorityLink, EvidenceRecord
from filingguard.integrations.llm.adapter import MODEL, GroqPropositionAdapter
from filingguard.integrations.providers.runtime import ProviderBudget
from filingguard.modules.analyses.schemas import StageName, StageStatus
from filingguard.modules.propositions.passages import select_passages
from filingguard.modules.propositions.service import propositions_stage, review_propositions


def context(source="Notice is required before termination. However, emergencies are excepted."):
    analysis_id, segment_id = uuid4(), uuid4()
    filing = "Notice is required before termination."
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


def test_same_authority_pair_is_reviewed_once_and_updates_each_owned_link():
    import json

    analysis = context()
    original = analysis.document_snapshot["text"]
    analysis.document_snapshot["text"] += "\n\nNotice is never required."
    claim = Claim(
        id=uuid4(),
        analysis_id=analysis.id,
        segment_id=uuid4(),
        text="Notice is never required.",
        start_offset=len(original) + 2,
        end_offset=len(analysis.document_snapshot["text"]),
        extraction_method="heuristic",
    )
    citation = Citation(
        id=uuid4(),
        analysis_id=analysis.id,
        authority_id=analysis.review_authorities[0].id,
        verification_status="verified",
    )
    link = ClaimAuthorityLink(
        id=uuid4(),
        analysis_id=analysis.id,
        claim_id=claim.id,
        citation_id=citation.id,
        authority_id=citation.authority_id,
        support_status="not_run",
    )
    analysis.review_claims += (claim,)
    analysis.review_citations += (citation,)
    analysis.review_links += (link,)
    calls = []

    def handler(request):
        payload = json.loads(request.content)
        data = json.loads(payload["messages"][1]["content"])
        calls.append(payload)
        unit = data["source_passages"][0]["evidence_units"][0]["id"]
        verdicts = [
            {
                "claim_id": f"claim-{i}",
                "status": status,
                "confidence": "low",
                "explanation": "Synthetic independent claim control.",
                "evidence": [{"evidence_id": unit}],
            }
            for i, status in enumerate(("supported", "misrepresented"))
        ]
        return httpx.Response(
            200,
            json={
                "model": MODEL,
                "choices": [
                    {
                        "finish_reason": "stop",
                        "message": {"content": json.dumps({"verdicts": verdicts})},
                    }
                ],
            },
        )

    budget = ProviderBudget(time.monotonic() + 30, max_attempts=1)
    with GroqPropositionAdapter(
        "synthetic", budget, transport=httpx.MockTransport(handler)
    ) as adapter:
        result = review_propositions(analysis, adapter=adapter)
    assert len(calls) == budget.attempts_used == 1
    assert [update.support_status for update in result.updates] == ["supported", "misrepresented"]
    evidence = [record for record in result.records if isinstance(record, EvidenceRecord)]
    assert {record.claim_id for record in evidence} == {analysis.review_claims[0].id, claim.id}
    assert {record.source_metadata["batch_size"] for record in evidence} == {2}


def test_passages_preserve_offsets_and_qualifications():
    source = "Unrelated text.\n\nNotice is required.\n\nHowever, emergencies are excepted."
    passages = select_passages(source, "Notice is required.")
    assert len(passages) == 1
    assert "However, emergencies are excepted" in passages[0].text
    assert source[passages[0].start : passages[0].end] == passages[0].text
    assert passages[0].snapshot_sha256 == hashlib.sha256(source.encode()).hexdigest()


def test_long_opinion_selection_is_bounded():
    source = "Irrelevant. " * 1000 + "\n\nNotice is required.\n\n" + "Other words. " * 1000
    passages = select_passages(source, "Notice required")
    assert sum(len(p.text) for p in passages) <= 12000
    assert any("Notice is required" in p.text for p in passages)


def test_multi_passage_retrieval_across_structural_sections():
    # Long opinion (>15,000 characters) with early, middle, and late relevant sections.
    early = "Background facts. " * 300 + "\n\nNotice is required in preliminary filings.\n\n"
    mid = "Legal analysis. " * 300 + "\n\nNotice requirements apply to all emergency claims.\n\n"
    late = (
        "Judicial disposition. " * 300
        + "\n\nThe court holds that notice must precede any hearing.\n\n"
        + "Closing order. " * 200
    )
    source = early + mid + late
    assert len(source) > 15000

    passages = select_passages(source, "court holds notice required")
    assert 3 <= len(passages) <= 4
    assert sum(len(p.text) for p in passages) <= 12000

    # Ensure all passages are non-overlapping and preserve offsets
    for i, p in enumerate(passages):
        assert source[p.start : p.end] == p.text
        for j, other in enumerate(passages):
            if i != j:
                assert p.end <= other.start or other.end <= p.start

    # Verify structural candidate diversity across early, middle, and late thirds
    third = len(source) / 3
    zones = {min(2, int(p.start / third)) for p in passages}
    assert zones == {0, 1, 2}


def test_multi_passage_miranda_fixture_structural_diversity():
    from pathlib import Path

    fixture = Path(__file__).resolve().parents[4] / "data/demo/curated-v1/authorities/miranda.txt"
    if not fixture.exists():
        return
    source = fixture.read_text(encoding="utf-8")
    assert len(source) > 15000

    claim = (
        "statements obtained from interrogation are inadmissible without "
        "procedural safeguards."
    )
    passages = select_passages(source, claim)
    assert len(passages) == 4
    assert sum(len(p.text) for p in passages) <= 12000
    for p in passages:
        assert source[p.start : p.end] == p.text
        assert p.snapshot_sha256 == hashlib.sha256(source.encode()).hexdigest()

    # Verify non-overlapping
    for i, p in enumerate(passages):
        for j, other in enumerate(passages):
            if i != j:
                assert p.end <= other.start or other.end <= p.start

    # Verify multiple zones covered
    third = len(source) / 3
    zones = {min(2, int(p.start / third)) for p in passages}
    assert len(zones) >= 2


def test_long_paragraph_clipping_is_disclosed():
    passages = select_passages("Notice " + "qualification " * 1000, "Notice")
    assert passages[0].truncated
    assert len(passages[0].text) <= 6000


def test_unrelated_source_returns_no_passages():
    assert select_passages("Entirely unrelated judicial discussion", "Notice required") == ()


def test_no_claims_is_explicitly_skipped():
    analysis = context()
    analysis.review_links = ()
    analysis.stage_states = {"claims": {"status": "skipped"}}
    result = review_propositions(analysis, adapter=None)
    assert result.status == StageStatus.SKIPPED
    result.validate(StageName.PROPOSITIONS)


def test_unavailable_claim_extraction_cannot_become_clean_skipped_stage():
    analysis = context()
    analysis.review_links = ()
    analysis.stage_states = {"claims": {"status": "unavailable"}}
    result = review_propositions(analysis, adapter=None)
    assert result.status == StageStatus.UNAVAILABLE
    assert result.coverage.unavailable == 1
    result.validate(StageName.PROPOSITIONS)


@pytest.mark.parametrize("missing", ["opinion", "verified", "hash", "authority"])
def test_missing_source_never_produces_support_or_model_calls(missing):
    analysis = context()
    if missing == "opinion":
        analysis.review_authorities[0].opinion_text_available = False
    if missing == "verified":
        analysis.review_citations[0].verification_status = "not_run"
    if missing == "hash":
        analysis.review_authorities[0].source_sha256 = "0" * 64
    if missing == "authority":
        analysis.review_authorities = ()

    class Never:
        def review(self, *args, **kwargs):
            raise AssertionError("No model request allowed")

    result = review_propositions(analysis, adapter=Never())
    assert result.updates[0].support_status == "insufficient_source"
    assert result.updates[0].confidence is None
    assert result.coverage.unavailable == 1
    assert all(not e.ai_assisted for e in result.records if hasattr(e, "ai_assisted"))
    result.validate(StageName.PROPOSITIONS)


def test_no_credentials_does_not_load_environment(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "should-not-be-read")
    result = propositions_stage(context(), ProviderBudget(time.monotonic() + 30))
    assert result.updates[0].support_status == "unavailable"
    result.validate(StageName.PROPOSITIONS)


def test_grounded_stage_persists_exact_source_and_metadata():
    import json

    analysis = context()

    def handler(request):
        passage = json.loads(json.loads(request.content)["messages"][1]["content"])[
            "source_passages"
        ][0]
        return httpx.Response(
            200,
            json={
                "model": MODEL,
                "choices": [
                    {
                        "finish_reason": "stop",
                        "message": {
                            "content": json.dumps(
                                {
                                    "status": "partially_supported",
                                    "explanation": "Notice is required, except in emergencies.",
                                    "confidence": "medium",
                                    "evidence": [
                                        {
                                            "evidence_id": passage["evidence_units"][0]["id"],
                                        }
                                    ],
                                }
                            )
                        },
                    }
                ],
            },
        )

    with GroqPropositionAdapter(
        "synthetic", ProviderBudget(time.monotonic() + 30), transport=httpx.MockTransport(handler)
    ) as adapter:
        result = review_propositions(analysis, adapter=adapter)
    assert result.coverage.evaluated == 1
    assert result.status == StageStatus.COMPLETED
    assert result.updates[0].support_status == "partially_supported"
    assert result.updates[0].confidence is None
    source_evidence = next(
        e
        for e in result.records
        if isinstance(e, EvidenceRecord) and e.source_type == "opinion_text"
    )
    assert (
        source_evidence.snapshot_text[
            source_evidence.source_start_offset : source_evidence.source_end_offset
        ]
        == source_evidence.excerpt
    )
    assert source_evidence.model_version == MODEL
    assert source_evidence.prompt_version == "proposition-source-review-v3"
    assert source_evidence.source_metadata["confidence_calibrated"] is False
    result.validate(StageName.PROPOSITIONS)


def test_invalid_provider_output_preserves_uncertainty():
    with GroqPropositionAdapter(
        "synthetic",
        ProviderBudget(time.monotonic() + 30),
        transport=httpx.MockTransport(lambda r: httpx.Response(200, json={})),
    ) as adapter:
        result = review_propositions(context(), adapter=adapter)
    assert result.updates[0].support_status == "unavailable"
    assert result.coverage.evaluated == 0


def test_original_claim_mismatch_rejected_before_inference():
    analysis = context()
    analysis.review_claims[0].text = "invented"
    with pytest.raises(ValueError, match="original filing"):
        review_propositions(analysis, adapter=None)


def test_large_source_preserves_partial_output_with_explicit_limits(monkeypatch):
    import filingguard.modules.propositions.service as service

    analysis = context()
    monkeypatch.setattr(service, "MAX_SNAPSHOT_BYTES", 100)

    class Never:
        def review(self, *args, **kwargs):
            raise AssertionError("No inference when its provenance cannot fit")

    result = review_propositions(analysis, adapter=Never())
    assert result.coverage.truncated
    assert result.coverage.unavailable == 1
    assert result.records
    assert result.updates[0].support_status == "insufficient_source"
    assert "bounded output" in result.updates[0].explanation


def test_link_limit_keeps_all_eligible_checks_visible(monkeypatch):
    import filingguard.modules.propositions.service as service

    analysis = context()
    analysis.review_links = analysis.review_links * 2
    monkeypatch.setattr(service, "MAX_LINKS", 1)
    result = review_propositions(analysis, adapter=None)
    assert result.coverage.eligible == 2
    assert result.coverage.unavailable == 2
    assert result.coverage.truncated
    assert len(result.updates) == 1


def test_worker_round_trip_preserves_prior_link_update_and_evidence():
    import json

    from filingguard.modules.analyses.execution import (
        result_from_wire,
        result_to_wire,
        validate_stage_context,
    )

    analysis = context()
    result = review_propositions(analysis, adapter=None)
    decoded = result_from_wire(json.loads(json.dumps(result_to_wire(result))), analysis.id)
    prior = {
        "claims": analysis.review_claims,
        "citations": analysis.review_citations,
        "authorities": analysis.review_authorities,
        "links": analysis.review_links,
    }
    validate_stage_context(decoded, analysis, StageName.PROPOSITIONS, (), prior)
    assert decoded.updates[0].id == analysis.review_links[0].id
    assert decoded.updates[0].support_status == "unavailable"
    evidence = next(e for e in decoded.records if isinstance(e, EvidenceRecord))
    assert evidence.snapshot_text == analysis.document_snapshot["text"]


def test_user_correction_does_not_rewrite_original_or_break_filing_span():
    analysis = context()
    claim = analysis.review_claims[0]
    original = claim.text
    claim.correction_history = [
        {
            "id": str(uuid4()),
            "corrected_text": "Emergencies never excuse the notice requirement.",
            "created_at": datetime.now(UTC).isoformat(),
        }
    ]
    result = review_propositions(analysis, adapter=None)
    assert claim.text == original
    assert result.updates[0].claim_id == claim.id
    assert original == analysis.document_snapshot["text"]


def test_cached_brown_controls_retrieve_conclusion_without_expected_span_hint():
    import json
    from pathlib import Path

    fixture = Path(__file__).resolve().parents[4] / "data/demo/curated-v1"
    sources = json.loads((fixture / "sources.json").read_text(encoding="utf-8"))["sources"]
    brown = next(row for row in sources if row["authority_id"] == "brown")
    source = (fixture / brown["path"]).read_text(encoding="utf-8")
    cases = json.loads((fixture / "expectations.json").read_text(encoding="utf-8"))["cases"]
    for case in cases:
        if case["id"] not in {"brown-supported", "brown-misrepresented"}:
            continue
        passages = select_passages(source, case["filing_span"]["text"])
        expected = case["source_span"]
        assert any(p.start <= expected["start"] < expected["end"] <= p.end for p in passages)
        assert sum(len(p.text) for p in passages) <= 12000
