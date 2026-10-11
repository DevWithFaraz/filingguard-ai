import hashlib
import json
import time
from dataclasses import replace

import httpx
import pytest

from filingguard.integrations.llm.adapter import MODEL, GroqPropositionAdapter
from filingguard.integrations.llm.batch import pooled_passages
from filingguard.integrations.providers.runtime import ProviderBudget, ProviderUnavailable
from filingguard.modules.propositions.schemas import SourcePassage

SOURCE = "Notice is required before termination. However, emergencies are excepted."
SHA = hashlib.sha256(SOURCE.encode()).hexdigest()
PASSAGE = SourcePassage("source-1", SOURCE, 0, len(SOURCE), SHA)
FILING = "test@example.com. Notice is required. Notice is never required."
REQUESTS = ((0, 37, (PASSAGE,)), (37, len(FILING), (PASSAGE,)))


def envelope(payload, failure=None):
    data = json.loads(payload["messages"][1]["content"])
    unit = data["source_passages"][0]["evidence_units"][0]["id"]
    items = [
        {
            "claim_id": f"claim-{i}",
            "status": "supported" if i == 0 else "misrepresented",
            "explanation": "Synthetic independent verdict control.",
            "confidence": "low",
            "evidence": [{"evidence_id": unit}],
        }
        for i in range(2)
    ]
    if failure == "duplicate":
        items[1]["claim_id"] = "claim-0"
    if failure == "unknown":
        items[1]["claim_id"] = "foreign-claim"
    if failure == "evidence":
        items[1]["evidence"][0]["evidence_id"] = "foreign-unit"
    if failure == "one":
        items.pop()
    value = {"verdicts": list(reversed(items))}
    if failure == "extra":
        value["extra"] = "not allowed"
    return httpx.Response(
        200,
        json={
            "model": MODEL,
            "usage": {"prompt_tokens": 1000, "completion_tokens": 400},
            "choices": [
                {
                    "finish_reason": "length" if failure == "length" else "stop",
                    "message": {
                        "content": json.dumps(value),
                        "refusal": "refused" if failure == "refusal" else None,
                    },
                }
            ],
        },
    )


def test_batch_masks_each_proposition_deduplicates_source_and_binds_independent_verdicts():
    calls = []

    def handler(request):
        payload = json.loads(request.content)
        calls.append(payload)
        assert "test@example.com" not in request.content.decode()
        data = json.loads(payload["messages"][1]["content"])
        assert (
            "".join(unit["text"] for p in data["source_passages"] for unit in p["evidence_units"])
            == SOURCE
        )
        assert payload["response_format"]["json_schema"]["strict"]
        return envelope(payload)

    budget = ProviderBudget(time.monotonic() + 30)
    with GroqPropositionAdapter(
        "synthetic", budget, transport=httpx.MockTransport(handler)
    ) as adapter:
        results = adapter.review_batch(FILING, REQUESTS, source=SOURCE)
    assert len(calls) == budget.attempts_used == 1
    assert [r.verdict.status for r in results] == ["supported", "misrepresented"]
    assert len({r.request_group for r in results}) == 1
    for result in results:
        assert result.batch_size == 2
        assert result.prompt_version == "proposition-source-review-v4-batch"
        evidence = result.verdict.evidence[0]
        assert SOURCE[evidence.start : evidence.end] == evidence.excerpt


@pytest.mark.parametrize(
    "failure", ["duplicate", "unknown", "evidence", "one", "extra", "length", "refusal"]
)
def test_invalid_batch_rejected_atomically_without_retry(failure):
    budget = ProviderBudget(time.monotonic() + 30)
    with GroqPropositionAdapter(
        "synthetic",
        budget,
        transport=httpx.MockTransport(
            lambda request: envelope(json.loads(request.content), failure)
        ),
    ) as adapter:
        with pytest.raises(ProviderUnavailable, match="invalid_response"):
            adapter.review_batch(FILING, REQUESTS, source=SOURCE)
    assert budget.attempts_used == 1


def test_overlapping_windows_merge_without_dropping_qualifications():
    first = replace(PASSAGE, text=SOURCE[:50], end=50)
    second = replace(PASSAGE, id="second", text=SOURCE[30:], start=30)
    pool = pooled_passages(((0, 10, (first,)), (10, 20, (second,))), SOURCE)
    assert len(pool) == 1 and pool[0].text == SOURCE


def test_batch_bounds_decline_without_request_or_clipping_source():
    source = "qualification " * 1500
    sha = hashlib.sha256(source.encode()).hexdigest()
    passages = [
        SourcePassage(str(i), source[start : start + 6000], start, start + 6000, sha)
        for i, start in enumerate((0, 6500, 13000))
    ]
    budget = ProviderBudget(time.monotonic() + 30)
    with GroqPropositionAdapter(
        "synthetic",
        budget,
        transport=httpx.MockTransport(
            lambda _: pytest.fail("Cannot send oversized pooled context")
        ),
    ) as adapter:
        assert (
            adapter.review_batch(
                FILING, ((0, 10, tuple(passages[:2])), (10, 20, (passages[2],))), source=source
            )
            is None
        )
    assert budget.attempts_used == 0


def test_foreign_source_hash_rejected_before_request():
    budget = ProviderBudget(time.monotonic() + 30)
    with GroqPropositionAdapter(
        "synthetic",
        budget,
        transport=httpx.MockTransport(lambda _: pytest.fail("Cannot send foreign source")),
    ) as adapter:
        with pytest.raises(ProviderUnavailable, match="invalid_request"):
            adapter.review_batch(
                FILING,
                ((0, 10, (replace(PASSAGE, snapshot_sha256="0" * 64),)), REQUESTS[1]),
                source=SOURCE,
            )
    assert budget.attempts_used == 0
