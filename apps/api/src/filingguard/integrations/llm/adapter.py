"""Explicit Groq inference through the fixed-host, zero-retry transport."""

import hashlib
import json
import math
import re
import time

import httpx
from pydantic import ValidationError

from filingguard.integrations.providers.passages import prepare_passage
from filingguard.integrations.providers.runtime import ProviderBudget, ProviderUnavailable
from filingguard.integrations.providers.transport import BoundedProviderClient
from filingguard.modules.propositions.schemas import (
    GroundedVerdict,
    ModelVerdict,
    SourcePassage,
    WireModelVerdict,
)
from filingguard.resources.prompts.proposition_v1 import PROMPT_VERSION, SYSTEM_PROMPT

MODEL = "openai/gpt-oss-120b"
METHOD_VERSION = "grounded-proposition-review-v3"
_INJECTION = re.compile(
    r"ignore\s+(?:all\s+)?(?:previous|prior|above|system)\s+instructions|"
    r"(?:system|developer)\s+prompt|<\|(?:im_start|system|developer)\|>|"
    r"(?:you\s+are\s+now|override\s+(?:the\s+)?instructions)",
    re.I,
)


def evidence_units(passage):
    """Partition exact source text once into bounded immutable evidence references.

    Prefer sentence endings when available; retain every original character, including
    surrounding whitespace. A long sentence is partitioned, never omitted/rewritten.
    Unit IDs only identify text in this request, not an independent legal assertion.
    """
    start, ordinal = 0, 0
    while start < len(passage.text):
        end = min(len(passage.text), start + 600)
        if end < len(passage.text):
            breaks = list(re.finditer(r"[.!?]\s+", passage.text[start:end]))
            if breaks and breaks[-1].end() >= 120:
                end = start + breaks[-1].end()
        text = passage.text[start:end]
        yield f"{passage.id}:{ordinal}", passage.start + start, passage.start + end, text
        start, ordinal = end, ordinal + 1


class ModelOutputRejected(ValueError):
    """Only fixed diagnostic codes; never reflect a provider value or explanation."""

    def __init__(self, code):
        self.code = code
        super().__init__(code)


def suspected_injection(text: str) -> bool:
    return bool(_INJECTION.search(text))


class GroqPropositionAdapter:
    def __init__(
        self,
        credential: str,
        budget: ProviderBudget,
        *,
        model: str = MODEL,
        transport: httpx.BaseTransport | None = None,
    ):
        # This selected free-credit model is deliberate; unsupported models need review.
        if model != MODEL:
            raise ProviderUnavailable("invalid_policy")
        self.model = model
        self.last_rejection = None
        self._previous_prompt_tokens: int | None = None
        self._previous_request_bytes = 0
        self.client = BoundedProviderClient("groq", credential, budget, transport=transport)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.client.close()

    def review(
        self,
        filing: str,
        start: int,
        end: int,
        passages: tuple[SourcePassage, ...],
        *,
        source: str,
    ) -> GroundedVerdict:
        # Never accept caller-provided prompt strings or independently copied claim text.
        self.last_rejection = None
        masked = prepare_passage(filing, start, end, filing=True)
        if not passages or len(passages) > 2 or sum(len(p.text) for p in passages) > 12000:
            raise ProviderUnavailable("invalid_request")
        sha = hashlib.sha256(source.encode()).hexdigest()
        if len({p.id for p in passages}) != len(passages) or any(
            p.snapshot_sha256 != sha
            or not 0 <= p.start < p.end <= len(source)
            or source[p.start : p.end] != p.text
            for p in passages
        ):
            raise ProviderUnavailable("invalid_request")
        if suspected_injection(masked.text) or any(suspected_injection(p.text) for p in passages):
            raise ProviderUnavailable("invalid_request")
        schema = WireModelVerdict.model_json_schema()
        payload = {
            "model": self.model,
            "temperature": 0,
            "reasoning_effort": "low",
            "max_completion_tokens": 768,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "filing_proposition": masked.text,
                            "filing_truncated": masked.truncated,
                            "source_passages": [
                                {
                                    "id": p.id,
                                    "evidence_units": [
                                        {"id": identity, "text": text}
                                        for identity, _, _, text in evidence_units(p)
                                    ],
                                    "start": p.start,
                                    "end": p.end,
                                    "truncated": p.truncated,
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
                    "name": "proposition_review",
                    "strict": True,
                    "schema": schema,
                },
            },
        }
        raw, request_bytes, began = self._send(payload)
        try:
            if not isinstance(raw, dict):
                raise ModelOutputRejected("envelope_shape")
            if raw.get("model") != self.model:
                raise ModelOutputRejected("model_mismatch")
            choices = raw["choices"]
            if not isinstance(choices, list) or len(choices) != 1:
                raise ModelOutputRejected("choices_shape")
            choice = choices[0]
            message = choice["message"]
            if choice["finish_reason"] != "stop" or message.get("refusal"):
                raise ModelOutputRejected("refused_or_incomplete")
            if message.get("tool_calls") or not isinstance(message.get("content"), str):
                raise ModelOutputRejected("message_shape")
            wire_verdict = WireModelVerdict.model_validate_json(message["content"])
            verdict = self._bind_evidence(wire_verdict, passages)
            self._validate(verdict, passages, masked.truncated)
            tokens = self._usage(raw, request_bytes)
            return GroundedVerdict(
                verdict,
                self.model,
                PROMPT_VERSION,
                METHOD_VERSION,
                masked.truncated,
                time.monotonic() - began,
                *tokens,
                dict(self.client.last_token_quota),
            )
        except ModelOutputRejected as error:
            self.last_rejection = error.code
        except ValidationError:
            self.last_rejection = "schema_validation"
        except (KeyError, TypeError, ValueError):
            self.last_rejection = "envelope_shape"
        raise ProviderUnavailable("invalid_response") from None

    def review_batch(self, filing, requests, *, source):
        from .batch import review_batch

        return review_batch(self, filing, requests, source=source)

    def _send(self, payload):
        began = time.monotonic()
        # Conservative byte-based estimate for pacing, not a guaranteed token count.
        # Source context is unchanged; unfinished responses still fail closed.
        request_bytes = len(json.dumps(payload, ensure_ascii=False).encode())
        if self._previous_prompt_tokens is not None and self._previous_request_bytes:
            estimated_tokens = (
                math.ceil(
                    self._previous_prompt_tokens
                    * request_bytes
                    / self._previous_request_bytes
                    * 1.05
                )
                + payload["max_completion_tokens"]
            )
        else:
            estimated_tokens = math.ceil(request_bytes / 3) + payload["max_completion_tokens"]
        raw = self.client.request_json(
            "POST", "/openai/v1/chat/completions", payload, token_cost=estimated_tokens
        )
        return raw, request_bytes, began

    def _usage(self, raw, request_bytes):
        usage = raw.get("usage", {})
        tokens = []
        for key in ("prompt_tokens", "completion_tokens"):
            value = usage.get(key) if isinstance(usage, dict) else None
            tokens.append(value if type(value) is int and 0 <= value <= 100000 else None)
        if tokens[0] is not None and tokens[0] > 0:
            self._previous_prompt_tokens = tokens[0]
            self._previous_request_bytes = request_bytes
        return tokens

    @staticmethod
    def _bind_evidence(verdict, passages):
        allowed = {
            identity: (passage, start, end, text)
            for passage in passages
            for identity, start, end, text in evidence_units(passage)
        }
        evidence = []
        seen = set()
        for item in verdict.evidence:
            unit = allowed.get(item.evidence_id)
            if unit is None or item.evidence_id in seen:
                raise ModelOutputRejected("evidence_identity_or_span")
            seen.add(item.evidence_id)
            passage, start, end, text = unit
            evidence.append(
                {
                    "passage_id": passage.id,
                    "excerpt": text,
                    "start": start,
                    "end": end,
                }
            )
        return ModelVerdict.model_validate(verdict.model_dump() | {"evidence": evidence})

    @staticmethod
    def _validate(verdict, passages, filing_truncated):
        if not verdict.explanation.strip() or suspected_injection(verdict.explanation):
            raise ModelOutputRejected("untrusted_explanation")
        by_id = {p.id: p for p in passages}
        seen = set()
        for evidence in verdict.evidence:
            p = by_id.get(evidence.passage_id)
            key = (evidence.passage_id, evidence.start, evidence.end)
            if p is None or key in seen or not p.start <= evidence.start < evidence.end <= p.end:
                raise ModelOutputRejected("evidence_identity_or_span")
            if p.text[evidence.start - p.start : evidence.end - p.start] != evidence.excerpt:
                raise ModelOutputRejected("evidence_excerpt_mismatch")
            seen.add(key)
        substantive = verdict.status in {"supported", "partially_supported", "misrepresented"}
        if substantive and not verdict.evidence:
            raise ModelOutputRejected("substantive_evidence_missing")
        if verdict.status == "insufficient_source" and verdict.confidence != "unknown":
            raise ModelOutputRejected("unsupported_confidence")
        if verdict.status in {"supported", "misrepresented"} and (
            filing_truncated or any(p.truncated for p in passages)
        ):
            raise ModelOutputRejected("clipped_verdict")
