"""Offline acceptance of persisted grounding/forensics; fake verdicts are not legal QA."""

import logging
import time
from threading import Event
from uuid import UUID, uuid4

import pytest
from analysis_workers import (
    GROUNDING_SOURCE,
    forged_link_context,
    grounded_synthetic_batch,
    grounded_synthetic_citations,
    grounded_synthetic_propositions,
    invalid_synthetic_propositions,
    refused_synthetic_batch,
    refused_synthetic_propositions,
    unavailable_synthetic_propositions,
)
from sqlalchemy import select
from test_orchestrator import owner, prepare
from test_orchestrator import private_client as private_client

from filingguard.db.models import (
    Analysis,
    Claim,
    ClaimAuthorityLink,
    EvidenceRecord,
    Finding,
    Quote,
)
from filingguard.integrations.providers.runtime import ProviderBudget
from filingguard.modules.analyses.execution import (
    ReviewSegment,
    StageExecutionError,
    StageResult,
    execute_stage,
)
from filingguard.modules.analyses.orchestrator import REVIEW_STAGES
from filingguard.modules.analyses.runners import privacy_stage
from filingguard.modules.analyses.schemas import StageName, StageStatus
from filingguard.modules.citations.runner import citation_stage
from filingguard.modules.claims.runner import claims_stage
from filingguard.modules.documents.extraction import extract_text
from filingguard.modules.quotes.runner import quotes_stage

FILING = (
    "SSN 900-12-3456; notice is required before termination under 347 U.S. 483.\n\n"
    "Notice is never required before termination under 347 U.S. 483.\n\n"
    '"Notice is required before termination." 347 U.S. 483.\n\n'
    '"Notice is never required before termination." 347 U.S. 483.'
)


def configure(client, proposition_runner):
    actual = {
        StageName.PRIVACY: privacy_stage,
        StageName.CITATIONS: grounded_synthetic_citations,
        StageName.CLAIMS: claims_stage,
        StageName.PROPOSITIONS: proposition_runner,
        StageName.QUOTES: quotes_stage,
    }
    client.app.state.review_runners = {
        stage: actual.get(stage)
        or StageResult(
            status=StageStatus.UNAVAILABLE, reason="No real court rules selected in synthetic test"
        )
        for stage in REVIEW_STAGES
    }


def execute(client, runner):
    configure(client, runner)
    auth = owner(client)
    identity = prepare(client, auth, text=FILING)
    route = f"/api/v1/analyses/{identity}"
    assert client.post(route + "/run", headers=auth).status_code == 202
    for _ in range(180):
        status_response = client.get(route + "/status", headers=auth)
        assert status_response.status_code == 200, status_response.text
        summary = status_response.json()
        if summary["status"] == "partial":
            break
        time.sleep(0.5)
    else:
        pytest.fail(f"Grounded pipeline did not finish: {summary['status']}")
    response = client.get(route + "/results", headers=auth)
    assert response.status_code == 200, response.text
    return auth, identity, route, summary, response


def check_shared_output(client, auth, identity, route, summary, response):
    result = response.json()
    stages = {stage["name"]: stage for stage in summary["stages"]}
    assert stages["claims"]["status"] == "completed"
    assert stages["privacy"]["status"] == "completed"
    assert stages["quotes"]["status"] == "completed"
    assert stages["court_rules"]["status"] == "unavailable"
    assert result["score"]["provisional"] is True
    assert result["score"]["risk_level"] != "ready_for_review"
    assert "900-12-3456" not in response.text
    assert len(result["claims"]) == 4 and len(result["quotes"]) == 2
    assert result["quotes"][0]["match_status"] == "exact"
    assert result["quotes"][1]["match_status"] in {"close", "not_found"}
    for claim in result["claims"]:
        location = claim["location"]
        assert len(claim["text"]) == location["end"] - location["start"]
        assert location["offset_unit"] == "unicode_code_points"

    graph = client.get(route + "/graph", headers=auth)
    assert graph.status_code == 200, graph.text
    link_labels = {
        link["id"]: link["support_status"] for c in result["claims"] for link in c["links"]
    }
    assert {
        edge["id"]: edge["label"] for edge in graph.json()["edges"] if edge["id"] in link_labels
    } == link_labels
    assert "900-12-3456" not in graph.text
    report = client.get(route + "/report", headers=auth)
    assert report.status_code == 200 and "900-12-3456" not in report.text
    assert "not legal advice" in report.text.lower()
    for status in set(link_labels.values()):
        assert status in report.text
    for finding in result["findings"]:
        detail = client.get(route + f"/findings/{finding['id']}/evidence", headers=auth)
        assert detail.status_code == 200, detail.text
        assert len(detail.json()["evidence"]) == finding["evidence_count"]
        assert detail.json()["evidence"] == finding["evidence"]
        assert "900-12-3456" not in detail.text
    other = owner(client)
    for suffix in ("/results", "/graph", "/report"):
        assert client.get(route + suffix, headers=other).status_code == 404
    factory = client.app.state.analysis_runtime.get_lifecycle().repository._factory
    with factory() as session:
        claims = list(session.scalars(select(Claim).where(Claim.analysis_id == UUID(identity))))
        links = list(
            session.scalars(
                select(ClaimAuthorityLink).where(ClaimAuthorityLink.analysis_id == UUID(identity))
            )
        )
        assert len(claims) == len(links) == 4
        assert all(FILING[c.start_offset : c.end_offset] == c.text for c in claims)
        assert {str(link.id): link.support_status for link in links} == link_labels
        quote_rows = list(session.scalars(select(Quote).where(Quote.analysis_id == UUID(identity))))
        assert {row.match_status for row in quote_rows} == {
            q["match_status"] for q in result["quotes"]
        }
        evidence = list(
            session.scalars(
                select(EvidenceRecord).where(EvidenceRecord.analysis_id == UUID(identity))
            )
        )
        assert all(
            e.snapshot_text[e.source_start_offset : e.source_end_offset] == e.excerpt
            for e in evidence
        )
        assert any(
            e.quote_id is not None
            and e.source_type == "opinion_text"
            and e.source_metadata["provenance"] == "synthetic"
            for e in evidence
        )
    return stages, result


def test_actual_worker_grounding_updates_links_and_retains_quote_evidence(private_client, caplog):
    with caplog.at_level(logging.INFO):
        auth, identity, route, summary, response = execute(
            private_client, grounded_synthetic_propositions
        )
    stages, result = check_shared_output(private_client, auth, identity, route, summary, response)
    assert stages["propositions"]["status"] == "completed"
    statuses = [link["support_status"] for claim in result["claims"] for link in claim["links"]]
    assert statuses.count("supported") == statuses.count("misrepresented") == 2
    factory = private_client.app.state.analysis_runtime.get_lifecycle().repository._factory
    with factory() as session:
        findings = list(
            session.scalars(
                select(Finding).where(
                    Finding.analysis_id == UUID(identity), Finding.type == "claim_support"
                )
            )
        )
        assert len(findings) == 4 and all(f.ai_assisted for f in findings)
        model_evidence = list(
            session.scalars(
                select(EvidenceRecord).where(
                    EvidenceRecord.analysis_id == UUID(identity),
                    EvidenceRecord.model_version.is_not(None),
                )
            )
        )
        assert model_evidence and all(
            e.model_version == "openai/gpt-oss-120b" for e in model_evidence
        )
        assert all(
            e.prompt_version == "proposition-source-review-v3"
            and e.method_version == "grounded-proposition-review-v3"
            for e in model_evidence
        )
        assert any(e.snapshot_text == GROUNDING_SOURCE and e.source_url for e in model_evidence)
    for secret in ("900-12-3456", "SYNTHETIC_GROQ_TOKEN", "SYNTHETIC_COURTLISTENER_TOKEN"):
        assert secret not in caplog.text + response.text


@pytest.mark.parametrize(
    "runner",
    [
        invalid_synthetic_propositions,
        refused_synthetic_propositions,
        unavailable_synthetic_propositions,
    ],
)
def test_invalid_refused_and_unavailable_outputs_preserve_independent_results(
    private_client, runner
):
    auth, identity, route, summary, response = execute(private_client, runner)
    stages, result = check_shared_output(private_client, auth, identity, route, summary, response)
    assert stages["propositions"]["status"] == "partial"
    assert stages["propositions"]["coverage"]["evaluated"] == 2
    assert stages["propositions"]["coverage"]["unavailable"] == 2
    statuses = [link["support_status"] for claim in result["claims"] for link in claim["links"]]
    assert statuses.count("supported") == statuses.count("unavailable") == 2
    assert any(f["type"] == "privacy" for f in result["findings"])
    assert any(f["type"] == "quote" for f in result["findings"])


@pytest.mark.parametrize("refused", [False, True])
def test_actual_worker_shared_source_batch_preserves_owned_results(private_client, refused):
    runner = refused_synthetic_batch if refused else grounded_synthetic_batch
    auth, identity, route, summary, response = execute(private_client, runner)
    stages, result = check_shared_output(private_client, auth, identity, route, summary, response)
    statuses = [link["support_status"] for claim in result["claims"] for link in claim["links"]]
    if refused:
        assert statuses == ["unavailable"] * 4
        assert stages["propositions"]["coverage"]["evaluated"] == 0
    else:
        assert statuses.count("supported") == statuses.count("misrepresented") == 2
        factory = private_client.app.state.analysis_runtime.get_lifecycle().repository._factory
        with factory() as session:
            evidence = list(
                session.scalars(
                    select(EvidenceRecord).where(
                        EvidenceRecord.analysis_id == UUID(identity),
                        EvidenceRecord.model_version.is_not(None),
                    )
                )
            )
            assert all(e.prompt_version == "proposition-source-review-v4-batch" for e in evidence)
            assert len({e.source_metadata["request_group"] for e in evidence}) == 2


def test_parent_rejects_worker_update_with_substituted_claim_identity():
    document = extract_text("Notice is required before termination under 347 U.S. 483.")
    analysis = Analysis(
        id=uuid4(),
        document_name="Synthetic boundary control",
        document_sha256=document.input_sha256,
        document_snapshot=document.model_dump(mode="json"),
        mode="live",
        demo_fixture_id=None,
        court_profile_id="unverified",
        ai_used=False,
        status="running",
        stage_states={},
    )
    segments = tuple(
        ReviewSegment(id=uuid4(), start=p.start, end=p.end, page_number=p.page_number)
        for p in document.paragraphs
    )
    analysis.review_segments = segments
    budget = ProviderBudget(deadline=time.monotonic() + 40)
    citations = citation_stage(analysis, budget).records
    analysis.review_citations = citations
    analysis.stage_states = {"citations": {"status": "partial", "coverage": {"eligible": 1}}}
    extracted = claims_stage(analysis, budget)
    links = tuple(row for row in extracted.records if isinstance(row, ClaimAuthorityLink))
    context = {
        "citations": citations,
        "authorities": (),
        "links": links,
        "claims": tuple(row for row in extracted.records if isinstance(row, Claim)),
    }
    with pytest.raises(StageExecutionError):
        execute_stage(
            forged_link_context,
            analysis,
            StageName.PROPOSITIONS,
            budget,
            stage_seconds=30,
            stop=Event(),
            segments=segments,
            context=context,
        )
    assert links[0].support_status == "not_run"
