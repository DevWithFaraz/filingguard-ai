"""Explicit synthetic-provider workers, importable in the contained child process."""

import json

import httpx

from filingguard.integrations.courtlistener import CourtListenerAdapter
from filingguard.modules.citations.runner import verified_citation_stage

GROUNDING_SOURCE = "Notice is required before termination.\n\nHowever, emergencies are excepted."


def verified_synthetic_citations(analysis, budget):
    def handler(request):
        if "citation-lookup" in request.url.path:
            if "576" in request.read().decode():
                return httpx.Response(401)
            return httpx.Response(
                200,
                json=[
                    {
                        "status": 200,
                        "normalized_citations": ["347 U.S. 483"],
                        "clusters": [
                            {
                                "id": 105221,
                                "case_name": "Synthetic integration authority",
                                "sub_opinions": [105221],
                            }
                        ],
                    }
                ],
            )
        return httpx.Response(
            200,
            json={
                "id": 105221,
                "type": "010combined",
                "plain_text": "Synthetic public opinion passage.",
            },
        )

    adapter = CourtListenerAdapter(
        token="SYNTHETIC_COURTLISTENER_TOKEN", budget=budget, transport=httpx.MockTransport(handler)
    )
    try:
        return verified_citation_stage(analysis, budget, adapter=adapter)
    finally:
        adapter.close()


def grounded_synthetic_citations(analysis, budget):
    """A fabricated public source exercises plumbing, not legal accuracy."""
    from filingguard.db.models import Authority

    def handler(request):
        if "citation-lookup" in request.url.path:
            return httpx.Response(
                200,
                json=[
                    {
                        "status": 200,
                        "normalized_citations": ["347 U.S. 483"],
                        "clusters": [
                            {
                                "id": 105221,
                                "case_name": "Synthetic grounding control",
                                "sub_opinions": [105221],
                            }
                        ],
                    }
                ],
            )
        return httpx.Response(
            200, json={"id": 105221, "type": "010combined", "plain_text": GROUNDING_SOURCE}
        )

    adapter = CourtListenerAdapter(
        token="SYNTHETIC_COURTLISTENER_TOKEN", budget=budget, transport=httpx.MockTransport(handler)
    )
    try:
        result = verified_citation_stage(analysis, budget, adapter=adapter)
    finally:
        adapter.close()
    for row in result.records:
        if isinstance(row, Authority):
            row.source_metadata = {**row.source_metadata, "provenance": "synthetic"}
    return result


def _grounded_review(analysis, budget, failure=None, *, batch=False):
    from filingguard.integrations.llm.adapter import MODEL, GroqPropositionAdapter
    from filingguard.modules.propositions.service import review_propositions

    def handler(request):
        payload = json.loads(request.content)
        # Verify the actual transport payload rather than a separately prepared fixture.
        assert "900-12-3456" not in json.dumps(payload)
        assert payload["response_format"]["json_schema"]["strict"] is True
        data = json.loads(payload["messages"][1]["content"])
        if "propositions" in data:
            if failure == "refusal":
                return httpx.Response(
                    200,
                    json={
                        "model": MODEL,
                        "choices": [
                            {
                                "finish_reason": "stop",
                                "message": {"refusal": "Synthetic refusal", "content": None},
                            }
                        ],
                    },
                )
            unit = data["source_passages"][0]["evidence_units"][0]["id"]
            verdicts = [
                {
                    "claim_id": p["claim_id"],
                    "status": "misrepresented"
                    if "never" in p["filing_proposition"].lower()
                    else "supported",
                    "explanation": "Synthetic shared-source plumbing control.",
                    "confidence": "low",
                    "evidence": [{"evidence_id": unit}],
                }
                for p in data["propositions"]
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
                    "usage": {"prompt_tokens": 200, "completion_tokens": 100},
                },
            )
        proposition = data["filing_proposition"]
        passage = data["source_passages"][0]
        misleading = "never" in proposition.lower()
        if misleading and failure == "unavailable":
            return httpx.Response(401)
        if misleading and failure == "refusal":
            return httpx.Response(
                200,
                json={
                    "model": MODEL,
                    "choices": [
                        {
                            "finish_reason": "stop",
                            "message": {"refusal": "Synthetic refusal", "content": None},
                        }
                    ],
                },
            )
        verdict = {
            "status": "misrepresented" if misleading else "supported",
            "explanation": "Synthetic plumbing control citing the selected source passage.",
            "confidence": "low",
            "evidence": [
                {
                    "evidence_id": passage["evidence_units"][0]["id"],
                }
            ],
        }
        if misleading and failure == "invalid":
            verdict["evidence"][0]["evidence_id"] = "invented-source-id"
        return httpx.Response(
            200,
            json={
                "model": MODEL,
                "choices": [
                    {
                        "finish_reason": "stop",
                        "message": {
                            "content": json.dumps(verdict),
                            "refusal": None,
                        },
                    }
                ],
                "usage": {"prompt_tokens": 100, "completion_tokens": 50},
            },
        )

    with GroqPropositionAdapter(
        "SYNTHETIC_GROQ_TOKEN", budget, transport=httpx.MockTransport(handler)
    ) as adapter:
        if not batch:
            # Existing single-operation fault controls retain their original scope.
            adapter.review_batch = lambda *args, **kwargs: None
        return review_propositions(analysis, adapter=adapter)


def grounded_synthetic_propositions(analysis, budget):
    return _grounded_review(analysis, budget)


def grounded_synthetic_batch(analysis, budget):
    return _grounded_review(analysis, budget, batch=True)


def refused_synthetic_batch(analysis, budget):
    return _grounded_review(analysis, budget, "refusal", batch=True)


def refused_synthetic_propositions(analysis, budget):
    return _grounded_review(analysis, budget, "refusal")


def invalid_synthetic_propositions(analysis, budget):
    return _grounded_review(analysis, budget, "invalid")


def unavailable_synthetic_propositions(analysis, budget):
    return _grounded_review(analysis, budget, "unavailable")


def forged_link_context(analysis, _budget):
    from uuid import uuid4

    from filingguard.db.models import ClaimAuthorityLink
    from filingguard.modules.analyses.execution import StageResult
    from filingguard.modules.analyses.schemas import Coverage, StageStatus

    original = analysis.review_links[0]
    return StageResult(
        status=StageStatus.PARTIAL,
        reason="Synthetic tampered claim identity",
        coverage=Coverage(eligible=1, unavailable=1),
        updates=(
            ClaimAuthorityLink(
                id=original.id,
                analysis_id=analysis.id,
                claim_id=uuid4(),
                citation_id=original.citation_id,
                authority_id=original.authority_id,
                support_status="unavailable",
                confidence=None,
                explanation="Synthetic control",
            ),
        ),
    )
