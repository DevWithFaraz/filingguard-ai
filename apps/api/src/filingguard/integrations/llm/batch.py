"""Two independent propositions, one bounded shared authority snapshot."""

import hashlib
import json
import time
from uuid import uuid4

from pydantic import ValidationError

from filingguard.integrations.llm.adapter import (
    ModelOutputRejected,
    evidence_units,
    suspected_injection,
)
from filingguard.integrations.providers.passages import prepare_passage
from filingguard.integrations.providers.runtime import ProviderUnavailable
from filingguard.modules.propositions.schemas import (
    GroundedVerdict,
    SourcePassage,
    WireBatchVerdicts,
    WireModelVerdict,
)
from filingguard.resources.prompts.proposition_v1 import SYSTEM_PROMPT


def pooled_passages(requests, source):
    sha = hashlib.sha256(source.encode()).hexdigest()
    spans = []
    for _, _, passages in requests:
        if not passages or len(passages) > 2 or sum(len(p.text) for p in passages) > 12000:
            raise ProviderUnavailable("invalid_request")
        for p in passages:
            if (
                p.snapshot_sha256 != sha
                or not 0 <= p.start < p.end <= len(source)
                or source[p.start : p.end] != p.text
                or suspected_injection(p.text)
            ):
                raise ProviderUnavailable("invalid_request")
            spans.append((p.start, p.end, p.truncated))
    merged = []
    for left, right, truncated in sorted(spans):
        if merged and left <= merged[-1][1]:
            before = merged.pop()
            merged.append((before[0], max(before[1], right), before[2] or truncated))
        else:
            merged.append((left, right, truncated))
    if len(merged) > 2 or sum(right - left for left, right, _ in merged) > 12000:
        return None  # Cannot batch without dropping context: use independent calls.
    return tuple(
        SourcePassage(str(uuid4()), source[left:right], left, right, sha, truncated)
        for left, right, truncated in merged
    )


def review_batch(adapter, filing, requests, *, source):
    adapter.last_rejection = None
    if len(requests) != 2:
        raise ProviderUnavailable("invalid_request")
    passages = pooled_passages(requests, source)
    if passages is None:
        return None
    masked = [prepare_passage(filing, start, end, filing=True) for start, end, _ in requests]
    if any(suspected_injection(m.text) for m in masked):
        raise ProviderUnavailable("invalid_request")
    payload = {
        "model": adapter.model,
        "temperature": 0,
        "reasoning_effort": "low",
        "max_completion_tokens": 1024,
        "messages": [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
                + (
                    "\nReview each proposition independently against this same authority. "
                    "Return exactly one verdict for each supplied claim_id. Never copy one "
                    "proposition's status to another. Both may agree or contradict the source. "
                    "Keep explanations concise. All claim IDs and evidence IDs are data references."
                ),
            },
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "propositions": [
                            {
                                "claim_id": f"claim-{i}",
                                "filing_proposition": m.text,
                                "filing_truncated": m.truncated,
                            }
                            for i, m in enumerate(masked)
                        ],
                        "source_passages": [
                            {
                                "id": p.id,
                                "start": p.start,
                                "end": p.end,
                                "truncated": p.truncated,
                                "evidence_units": [
                                    {"id": identity, "text": text}
                                    for identity, _, _, text in evidence_units(p)
                                ],
                            }
                            for p in passages
                        ],
                        "retrieval_limitation": "Lexical windows may omit relevant context.",
                    },
                    ensure_ascii=False,
                ),
            },
        ],
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "proposition_batch_review",
                "strict": True,
                "schema": WireBatchVerdicts.model_json_schema(),
            },
        },
    }
    raw, request_bytes, began = adapter._send(payload)
    try:
        if not isinstance(raw, dict) or raw.get("model") != adapter.model:
            raise ModelOutputRejected("model_mismatch")
        choices = raw["choices"]
        if not isinstance(choices, list) or len(choices) != 1:
            raise ModelOutputRejected("choices_shape")
        choice = choices[0]
        message = choice["message"]
        if (
            choice["finish_reason"] != "stop"
            or message.get("refusal")
            or message.get("tool_calls")
            or not isinstance(message.get("content"), str)
        ):
            raise ModelOutputRejected("refused_or_incomplete")
        wire = WireBatchVerdicts.model_validate_json(message["content"])
        by_claim = {item.claim_id: item for item in wire.verdicts}
        if set(by_claim) != {"claim-0", "claim-1"}:
            raise ModelOutputRejected("claim_identity")
        verdicts = []
        for i, mask in enumerate(masked):
            item = WireModelVerdict.model_validate(
                by_claim[f"claim-{i}"].model_dump(exclude={"claim_id"})
            )
            verdict = adapter._bind_evidence(item, passages)
            adapter._validate(verdict, passages, mask.truncated)
            verdicts.append(verdict)
        tokens = adapter._usage(raw, request_bytes)
        group = str(uuid4())
        return tuple(
            GroundedVerdict(
                verdict,
                adapter.model,
                "proposition-source-review-v4-batch",
                "grounded-proposition-review-v4-batch",
                mask.truncated,
                time.monotonic() - began,
                *tokens,
                dict(adapter.client.last_token_quota),
                passages,
                group,
                2,
            )
            for verdict, mask in zip(verdicts, masked, strict=True)
        )
    except ModelOutputRejected as error:
        adapter.last_rejection = error.code
    except ValidationError:
        adapter.last_rejection = "schema_validation"
    except (KeyError, TypeError, ValueError):
        adapter.last_rejection = "envelope_shape"
    raise ProviderUnavailable("invalid_response") from None
