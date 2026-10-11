import json
import time

import httpx
import pytest

from filingguard.integrations.providers.passages import (
    MAX_FILING_PASSAGE,
    MAX_SOURCE_PASSAGE,
    prepare_passage,
)
from filingguard.integrations.providers.runtime import ProviderBudget
from filingguard.integrations.providers.transport import BoundedProviderClient


def test_mask_before_slicing_includes_identifiers_crossing_the_passage_cutoff():
    original = "\U0001f600 " + "a" * (MAX_FILING_PASSAGE - 8) + " 900-12-3456"
    passage = prepare_passage(original, 0, len(original), filing=True)
    assert len(passage.text) == MAX_FILING_PASSAGE
    assert passage.truncated
    assert passage.text.endswith("*****")
    assert passage.original_end == MAX_FILING_PASSAGE
    assert passage.requested_end == len(original)
    assert original.endswith("900-12-3456")
    assert passage.masking.detections[0].end > passage.original_end


def test_prepared_filing_context_sent_to_fake_transport_is_masked_and_offset_preserving():
    original = "\U0001f600 SSN 900-12-3456; account number 000123456789; DOB 04/17/2000."
    passage = prepare_passage(original, 0, len(original), filing=True)
    captured = []

    def handler(request):
        captured.append(json.loads(request.content))
        return httpx.Response(200, json={"fixture": True})

    with BoundedProviderClient(
        "groq",
        "SYNTHETIC_KEY",
        ProviderBudget(deadline=time.monotonic() + 10),
        transport=httpx.MockTransport(handler),
    ) as client:
        client.request_json(
            "POST",
            "/openai/v1/chat/completions",
            payload={
                "messages": [{"role": "user", "content": passage.text}],
            },
        )
    transmitted = captured[0]["messages"][0]["content"]
    assert len(transmitted) == len(original)
    assert all(value not in transmitted for value in ("900-12-3456", "000123456789", "04/17/2000"))
    assert passage.original_start == 0 and passage.original_end == len(original)


def test_public_source_passage_is_bounded_and_truncation_is_not_hidden():
    text = "Public authority text. " * 2000
    passage = prepare_passage(text, 4, len(text), filing=False)
    assert passage.text == text[4 : 4 + MAX_SOURCE_PASSAGE]
    assert passage.truncated and passage.masking is None
    assert passage.original_start == 4 and passage.original_end == 4 + MAX_SOURCE_PASSAGE
    whole = prepare_passage("Public text", 0, 11, filing=False)
    assert not whole.truncated


@pytest.mark.parametrize("start,end", [(-1, 4), (2, 2), (3, 2), (0, 100), (False, 4)])
def test_invalid_passages_fail_without_including_input(start, end):
    with pytest.raises(ValueError) as error:
        prepare_passage("SYNTHETIC_PRIVATE_SENTINEL", start, end, filing=True)
    assert "SYNTHETIC_PRIVATE_SENTINEL" not in str(error.value)
