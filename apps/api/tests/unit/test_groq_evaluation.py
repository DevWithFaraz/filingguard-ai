import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from evaluate_groq import CASES, validate_response  # noqa: E402


def valid_payload():
    findings = [{"id": case["id"], "verdict": case["expected"],
                 "evidence_quote": (
                     "A tenant must give written notice thirty days before ending "
                     "a month-to-month lease."
                     if case["expected"] == "supported" else
                     "Oral notice does not satisfy this requirement."
                     if case["expected"] == "contradicted" else None
                 )}
                for case in CASES]
    return {"choices": [{"finish_reason": "stop", "message": {
        "content": json.dumps({"findings": findings}),
    }}]}


def test_valid_response():
    assert len(validate_response(valid_payload()).findings) == 5


@pytest.mark.parametrize("kind", ["refusal", "truncated", "invalid_json", "bad_quote",
                                 "duplicate", "missing", "extra", "missing_evidence"])
def test_fail_closed(kind):
    payload = valid_payload()
    choice = payload["choices"][0]
    message = choice["message"]
    findings = json.loads(message["content"])["findings"]
    if kind == "refusal":
        message["refusal"] = "synthetic test refusal"
    elif kind == "truncated":
        choice["finish_reason"] = "length"
    elif kind == "invalid_json":
        message["content"] = "not json"
    else:
        if kind == "bad_quote":
            findings[0]["evidence_quote"] = "invented quotation"
        elif kind == "duplicate":
            findings[1]["id"] = findings[0]["id"]
        elif kind == "missing":
            findings.pop()
        elif kind == "extra":
            findings[0]["unexpected"] = True
        elif kind == "missing_evidence":
            findings[0]["evidence_quote"] = None
        message["content"] = json.dumps({"findings": findings})
    with pytest.raises(ValueError):
        validate_response(payload)
