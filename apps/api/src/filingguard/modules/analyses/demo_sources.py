"""Hash-bound public opinion replay; no cached classifications or network fallback."""

import json
from datetime import datetime

from filingguard.integrations.courtlistener import CourtListenerAdapter
from filingguard.integrations.courtlistener.schemas import (
    CourtListenerLookupResult,
    CourtListenerResolvedAuthority,
)
from filingguard.modules.analyses.demo import DemoUnavailable, _private_fixture_file
from filingguard.modules.analyses.demo_preview import FIXTURE_ROOT, load_demo_preview
from filingguard.modules.analyses.execution import StageResult
from filingguard.modules.analyses.schemas import CitationStatus, Coverage, StageStatus
from filingguard.modules.citations.runner import citation_stage, verified_citation_stage


class CachedDemoSources(CourtListenerAdapter):
    """Explicit server-owned adapter. Deliberately does not initialize an HTTP client."""

    def __init__(self, analysis, *, root=FIXTURE_ROOT):
        preview = load_demo_preview(
            root,
            analysis.demo_fixture_id,
            mode=analysis.mode,
            input_text=analysis.document_snapshot["text"],
        )
        if analysis.document_sha256 != preview.document_sha256:
            raise DemoUnavailable("Demo document hash does not match")
        self.sources = {}
        for item in json.loads(_private_fixture_file(root, "sources.json").read_text("utf-8"))[
            "sources"
        ]:
            self.sources[item["citation"]] = CourtListenerResolvedAuthority(
                cluster_id=item["cluster_id"],
                opinion_id=item["opinion_id"],
                case_name=item["case_name"],
                citation=item["citation"],
                court=item["court"],
                year=item["year"],
                source_url=item["source_url"],
                opinion_text_available=True,
                opinion_text=_private_fixture_file(root, item["path"]).read_text("utf-8"),
                source_sha256=item["sha256"],
                retrieved_at=datetime.fromisoformat(item["retrieved_at"]),
                source_metadata={
                    "provenance": "cached_public",
                    "fixture_id": preview.fixture_id,
                    "document_sha256": preview.document_sha256,
                    "review_kind": preview.review_kind,
                    "replay_method": "cached-public-source-v1",
                    "raw_sha256": item["raw_sha256"],
                    "attribution": item["attribution"],
                    "limitation": (
                        "Cached public opinion; no live lookup. AI review, not expert validation."
                    ),
                },
            )

    def verify_and_resolve(self, citation):
        source = self.sources.get(" ".join(citation.split()))
        return CourtListenerLookupResult(
            query_text=citation,
            normalized_citation=citation,
            status=CitationStatus.VERIFIED if source else CitationStatus.UNAVAILABLE,
            reason="cached_public_source" if source else "not_in_demo_sources",
            limitation="Cached public source identity; no live lookup."
            if source
            else "No cached source for this citation; no live absence or fabrication is inferred.",
        ), source

    def close(self):
        pass


def cached_demo_citations(analysis, budget):
    try:
        adapter = CachedDemoSources(analysis)
    except DemoUnavailable:
        return StageResult(
            status=StageStatus.UNAVAILABLE,
            coverage=Coverage(eligible=1, unavailable=1),
            reason="Cached demo source admission failed; no replay or live fallback.",
        )
    result = verified_citation_stage(analysis, budget, adapter=adapter)
    for row in result.records:
        metadata = getattr(row, "extraction_metadata", None)
        if metadata and metadata.get("verification"):
            metadata["verification"]["method"] = "cached-public-source-v1"
        if getattr(row, "method", None) == "citation-lookup":
            row.method_version = "cached-public-source-v1"
    return StageResult(
        status=result.status,
        coverage=result.coverage,
        records=result.records,
        reason="Cached public opinions for exact curated-v1 fixture. " + (result.reason or ""),
    )


def local_or_demo_citations(analysis, budget):
    return (
        cached_demo_citations(analysis, budget)
        if analysis.mode == "demo"
        else citation_stage(analysis, budget)
    )


def live_or_demo_citations(analysis, budget):
    return (
        cached_demo_citations(analysis, budget)
        if analysis.mode == "demo"
        else (verified_citation_stage(analysis, budget))
    )
