"""Read-only reviewed examples, separate from executed analysis results."""

import hashlib
import json
from pathlib import Path
from typing import Literal

from pydantic import Field, StrictInt

from filingguard.modules.analyses.demo import DemoUnavailable, _private_fixture_file
from filingguard.modules.analyses.schemas import Contract

FIXTURE_ID = "curated-v1"
# Render uses an editable install from this monorepo; packaged deployments must supply resources.
FIXTURE_ROOT = Path(__file__).resolve().parents[6] / "data" / "demo" / FIXTURE_ID
ARTIFACTS = {
    "manifest.json", "filing.txt", "filing.pdf", "expectations.json", "scenarios.json",
    "sources.json", "pdf-extraction.json",
}


class DemoSpan(Contract):
    start: StrictInt = Field(ge=0)
    end: StrictInt = Field(gt=0)
    text: str = Field(min_length=1)


class DemoSource(Contract):
    authority_id: str
    case_name: str
    citation: str
    source_url: str
    retrieved_at: str
    sha256: str
    provenance: Literal["cached_public"]


class DemoExample(Contract):
    id: str
    category: Literal["citation", "proposition", "quote", "privacy", "court_rules"]
    expected_status: str
    reason: str
    filing_span: DemoSpan
    source_span: DemoSpan | None
    authority_id: str | None
    simulation: str | None
    preconditions: dict[str, str | bool] | None
    judgment: Literal["accepted", "conditional"]
    condition: str | None


class DemoPreview(Contract):
    fixture_id: Literal["curated-v1"]
    mode: Literal["demo"] = "demo"
    execution_status: Literal["not_run"] = "not_run"
    review_kind: Literal["delegated_assistant"] = "delegated_assistant"
    reviewer: str
    reviewed_at: str
    document: str
    document_sha256: str
    sources: list[DemoSource]
    examples: list[DemoExample]
    limitations: list[str]


def _bytes(root: Path, name: str) -> bytes:
    return _private_fixture_file(root, name).read_bytes()


def _json(root: Path, name: str):
    return json.loads(_bytes(root, name))


def _span(text: str, raw: dict) -> DemoSpan:
    span = DemoSpan.model_validate({key: raw[key] for key in ("start", "end", "text")})
    if not 0 <= span.start < span.end <= len(text) or text[span.start:span.end] != span.text:
        raise DemoUnavailable("Demo evidence integrity check failed")
    return span


def load_demo_preview(
    root: Path, fixture_id: str, *, mode: str, input_text: str | None = None
) -> DemoPreview:
    if mode != "demo":
        raise DemoUnavailable("Demo fixtures require explicit demo mode")
    if fixture_id != FIXTURE_ID:
        raise DemoUnavailable("Unknown demo fixture")
    try:
        review = _json(root, "review.json")
        if (
            review["version"] != 1 or review["fixture_id"] != fixture_id
            or review["review_kind"] != "delegated_assistant"
            or review["purpose"] != "controlled_demo_development"
            or set(review["artifact_sha256"]) != ARTIFACTS
        ):
            raise DemoUnavailable("Demo review receipt is invalid")
        artifacts = {name: _bytes(root, name) for name in ARTIFACTS}
        for name, data in artifacts.items():
            if hashlib.sha256(data).hexdigest() != review["artifact_sha256"][name]:
                raise DemoUnavailable("Reviewed demo artifact integrity check failed")
        manifest = json.loads(artifacts["manifest.json"])
        document = artifacts["filing.txt"].decode("utf-8")
        digest = hashlib.sha256(artifacts["filing.txt"]).hexdigest()
        if (
            manifest["fixture_id"] != fixture_id or manifest["is_real_filing"] is not False
            or manifest["mode"] != "cached_public" or manifest["document_sha256"] != digest
        ):
            raise DemoUnavailable("Demo manifest is invalid")
        if input_text is not None and input_text != document:
            raise DemoUnavailable("Input does not match the selected demo")
        sources, texts = [], {}
        for source in json.loads(artifacts["sources.json"])["sources"]:
            data = _bytes(root, source["path"])
            raw = _bytes(root, source["raw_path"])
            if (
                hashlib.sha256(data).hexdigest() != source["sha256"]
                or hashlib.sha256(raw).hexdigest() != source["raw_sha256"]
                or source["authority_id"] in texts
            ):
                raise DemoUnavailable("Demo source integrity check failed")
            texts[source["authority_id"]] = data.decode("utf-8")
            sources.append(DemoSource.model_validate({
                key: source[key] for key in DemoSource.model_fields
            }))
        cases = json.loads(artifacts["expectations.json"])["cases"]
        conditions = review["conditional_cases"]
        ids = [case["id"] for case in cases]
        if (
            len(ids) != 18 or len(set(ids)) != 18 or len(conditions) != 5
            or not set(conditions).issubset(ids)
            or not all(isinstance(note, str) and note.strip() for note in conditions.values())
        ):
            raise DemoUnavailable("Demo scenario review is invalid")
        examples = []
        for case in cases:
            authority = case.get("authority_id")
            if authority is not None and authority not in texts:
                raise DemoUnavailable("Demo source reference is invalid")
            source_span = case["source_span"]
            if source_span is not None and source_span["authority_id"] != authority:
                raise DemoUnavailable("Demo source reference is invalid")
            examples.append(DemoExample(
                id=case["id"], category=case["category"], expected_status=case["expected_status"],
                reason=case["reason"], filing_span=_span(document, case["filing_span"]),
                source_span=_span(texts[authority], source_span) if source_span else None,
                authority_id=authority, simulation=case.get("simulation"),
                preconditions=case.get("preconditions"),
                judgment="conditional" if case["id"] in conditions else "accepted",
                condition=conditions.get(case["id"]),
            ))
        return DemoPreview(
            fixture_id=fixture_id, reviewer=review["reviewer"], reviewed_at=review["reviewed_at"],
            document=document, document_sha256=digest, sources=sources, examples=examples,
            limitations=[
                "Synthetic filing; public cached opinions. No private documents or live API calls.",
                "Reviewed expectations, not engine output, an accuracy benchmark or legal advice.",
                "AI assistant review only; no human or legal-expert validation.",
                "Combined opinions include dissents; selected passages were reviewed in context.",
                "Synthetic disclosure profile is a teaching rule, not a real court requirement.",
            ],
        )
    except DemoUnavailable:
        raise
    except (OSError, ValueError, KeyError, TypeError, IndexError) as error:
        raise DemoUnavailable("Reviewed demo is unavailable") from error
