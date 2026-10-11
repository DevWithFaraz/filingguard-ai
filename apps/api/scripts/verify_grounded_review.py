"""Opt-in two-call production-adapter check over cached public Brown controls.

Without --live this only verifies cached hashes/spans and lexical retrieval. Live
mode uses the selected 120B model, <=2 attempts, 20s transport deadlines, no retry
and no alternate model. Output contains sanitized metadata, never raw responses.
This small AI-reviewed control does not establish expert legal accuracy.
"""

import argparse
import hashlib
import json
import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from filingguard.core.config import Settings
from filingguard.db.models import (
    Analysis,
    Authority,
    Citation,
    Claim,
    ClaimAuthorityLink,
    EvidenceRecord,
)
from filingguard.integrations.llm.adapter import MODEL, GroqPropositionAdapter
from filingguard.integrations.providers.runtime import ProviderBudget, ProviderUnavailable
from filingguard.modules.propositions.passages import select_passages
from filingguard.modules.propositions.service import review_propositions

API_ROOT = Path(__file__).resolve().parents[1]
ROOT = API_ROOT.parents[1]
FIXTURE = ROOT / "data/demo/curated-v1"
CASE_IDS = ("brown-supported", "brown-misrepresented")


def fixture_context():
    filing = (FIXTURE / "filing.txt").read_text(encoding="utf-8")
    manifest = json.loads((FIXTURE / "manifest.json").read_text(encoding="utf-8"))
    if hashlib.sha256(filing.encode()).hexdigest() != manifest["document_sha256"]:
        raise ValueError("fixture_hash")
    sources = json.loads((FIXTURE / "sources.json").read_text(encoding="utf-8"))["sources"]
    reference = next(row for row in sources if row["authority_id"] == "brown")
    source = (FIXTURE / reference["path"]).read_text(encoding="utf-8")
    if hashlib.sha256(source.encode()).hexdigest() != reference["sha256"]:
        raise ValueError("source_hash")
    cases = json.loads((FIXTURE / "expectations.json").read_text(encoding="utf-8"))["cases"]
    cases = [next(row for row in cases if row["id"] == identity) for identity in CASE_IDS]
    analysis_id, authority_id = uuid4(), uuid4()
    authority = Authority(
        id=authority_id,
        analysis_id=analysis_id,
        source="courtlistener",
        external_id=str(reference["cluster_id"]),
        source_url=reference["source_url"],
        opinion_text_available=True,
        opinion_text=source,
        source_sha256=reference["sha256"],
        retrieved_at=datetime.fromisoformat(reference["retrieved_at"]),
        source_metadata={"provenance": "cached_public"},
    )
    claims, citations, links, checks = [], [], [], []
    for row in cases:
        span, expected_source = row["filing_span"], row["source_span"]
        if filing[span["start"] : span["end"]] != span["text"]:
            raise ValueError("filing_span")
        if source[expected_source["start"] : expected_source["end"]] != expected_source["text"]:
            raise ValueError("source_span")
        claim = Claim(
            id=uuid4(),
            analysis_id=analysis_id,
            segment_id=uuid4(),
            text=span["text"],
            start_offset=span["start"],
            end_offset=span["end"],
            extraction_method="heuristic",
        )
        citation = Citation(
            id=uuid4(),
            analysis_id=analysis_id,
            authority_id=authority_id,
            verification_status="verified",
            raw_text=reference["citation"],
        )
        claims.append(claim)
        citations.append(citation)
        links.append(
            ClaimAuthorityLink(
                id=uuid4(),
                analysis_id=analysis_id,
                claim_id=claim.id,
                citation_id=citation.id,
                authority_id=authority_id,
                support_status="not_run",
            )
        )
        passages = select_passages(source, claim.text)
        checks.append(
            {
                "case_id": row["id"],
                "expected_status": row["expected_status"],
                "selected_passages": len(passages),
                "selected_characters": sum(len(p.text) for p in passages),
                "truncated": any(p.truncated for p in passages),
                "reference_passage_in_selection": any(
                    p.start <= expected_source["start"] < expected_source["end"] <= p.end
                    for p in passages
                ),
            }
        )
    analysis = Analysis(id=analysis_id, mode="demo", document_snapshot={"text": filing})
    analysis.review_claims = tuple(claims)
    analysis.review_citations = tuple(citations)
    analysis.review_authorities = (authority,)
    analysis.review_links = tuple(links)
    return analysis, checks


class RecordedAdapter:
    """Keep only bounded failure codes; do not retain a provider error body."""

    def __init__(self, adapter):
        self.adapter = adapter
        self.failures = []
        self.rejections = []

    def review(self, *args, **kwargs):
        try:
            return self.adapter.review(*args, **kwargs)
        except ProviderUnavailable as error:
            self.failures.append(error.code)
            self.rejections.append(self.adapter.last_rejection)
            raise


def run(live=False, diagnostic=False):
    analysis, checks = fixture_context()
    if diagnostic:
        checks = checks[:1]
        analysis.review_claims = analysis.review_claims[:1]
        analysis.review_citations = analysis.review_citations[:1]
        analysis.review_links = analysis.review_links[:1]
        live = True
    output = {
        "checked_at": datetime.now(UTC).isoformat(),
        "mode": "diagnostic" if diagnostic else "live" if live else "offline",
        "model": MODEL,
        "fixture_id": "curated-v1",
        "cases": checks,
        "provider_attempts": 0,
        "limitation": (
            "Two synthetic filing controls with cached public sources; no expert legal QA."
        ),
    }
    if not live:
        output["status"] = "offline_sources_and_offsets_verified"
        return output, 0
    settings = Settings()
    if not settings.groq_api_key:
        output.update(status="blocked", blocker="missing_credential")
        return output, 2
    if settings.groq_model != MODEL:
        output.update(status="blocked", blocker="selected_model_mismatch")
        return output, 2
    budget = ProviderBudget(deadline=time.monotonic() + 45, max_attempts=1 if diagnostic else 2)
    began = time.monotonic()
    with GroqPropositionAdapter(
        settings.groq_api_key.get_secret_value(), budget, model=MODEL
    ) as adapter:
        recorded = RecordedAdapter(adapter)
        result = review_propositions(analysis, adapter=recorded)
    by_claim = {update.claim_id: update for update in result.updates}
    for check, claim in zip(checks, analysis.review_claims, strict=True):
        evidence = [
            row
            for row in result.records
            if isinstance(row, EvidenceRecord) and row.claim_id == claim.id
        ]
        check.update(
            actual_status=by_claim[claim.id].support_status,
            expected_match=by_claim[claim.id].support_status == check["expected_status"],
            source_evidence_count=sum(row.source_type == "opinion_text" for row in evidence),
            prompt_version=next(
                (row.prompt_version for row in evidence if row.prompt_version), None
            ),
            method_version=next(
                (row.method_version for row in evidence if row.model_version), None
            ),
        )
    output.update(
        status=result.status.value,
        provider_attempts=budget.attempts_used,
        elapsed_seconds=round(time.monotonic() - began, 3),
        failures=recorded.failures,
        rejections=recorded.rejections,
    )
    return output, 0 if all(check["expected_match"] for check in checks) else 2


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--live", action="store_true", help="Authorize at most two Groq model calls"
    )
    mode.add_argument(
        "--diagnostic", action="store_true", help="Authorize one diagnostic Groq call"
    )
    parser.add_argument("--output", type=Path, help="Save sanitized metadata inside the project")
    args = parser.parse_args()
    logging.disable(logging.CRITICAL)
    try:
        output, code = run(args.live, args.diagnostic)
    except ProviderUnavailable as error:
        output, code = {"status": "blocked", "blocker": error.code}, 2
    except Exception as error:
        output, code = (
            {
                "status": "blocked",
                "blocker": "fixture_or_configuration_error",
                "error_kind": type(error).__name__,
            },
            2,
        )
    content = json.dumps(output, ensure_ascii=True, indent=2)
    if args.output:
        target = args.output.resolve()
        if not target.is_relative_to(ROOT.resolve()):
            print(json.dumps({"status": "blocked", "blocker": "output_outside_project"}))
            return 2
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content + "\n", encoding="utf-8")
    print(content)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
