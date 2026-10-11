"""Local occurrence extraction; source verification remains unavailable."""

import json
from datetime import UTC, datetime
from hashlib import sha256
from uuid import uuid4

from filingguard.db.models import Analysis, Citation, EvidenceRecord, Finding
from filingguard.integrations.providers.runtime import ProviderBudget
from filingguard.modules.analyses.execution import (
    StageResult,
    citation_anchor,
    validate_citation_records,
    validate_segments,
)
from filingguard.modules.analyses.schemas import Coverage, StageStatus
from filingguard.modules.citations.schemas import EXTRACTION_LIMITATION


def citation_stage(analysis: Analysis, _budget: ProviderBudget) -> StageResult:
    # Keep Eyecite's reporter database out of independent privacy/court workers.
    from filingguard.modules.citations.service import extract_citations

    segments = analysis.review_segments
    validate_segments(analysis, segments)
    extraction = extract_citations(analysis.document_snapshot["text"])
    if not extraction.detected_count:
        return StageResult(
            status=StageStatus.SKIPPED,
            reason="No citations detected in supported formats. " + EXTRACTION_LIMITATION,
        )
    records = []
    for item in extraction.occurrences:
        anchor, warnings = citation_anchor(segments, item.start, item.end)
        metadata = item.extraction.model_copy(update={"warnings": warnings})
        records.append(
            Citation(
                id=uuid4(),
                analysis_id=analysis.id,
                raw_text=item.raw_text,
                normalized_text=item.normalized_text,
                segment_id=anchor.id,
                page_number=anchor.page_number,
                start_offset=item.start,
                end_offset=item.end,
                extraction_metadata=metadata.model_dump(mode="json"),
                verification_status="not_run",
                authority_id=None,
            )
        )
    validate_citation_records(analysis, segments, tuple(records))
    return StageResult(
        status=StageStatus.PARTIAL,
        coverage=Coverage(
            eligible=extraction.detected_count,
            unavailable=extraction.detected_count,
            truncated=extraction.truncated,
            limitation="Only the first 200 citation occurrences were retained."
            if extraction.truncated
            else None,
        ),
        reason="Local citation extraction finished; authority lookup has not run. "
        + EXTRACTION_LIMITATION,
        records=tuple(records),
    )


def verified_citation_stage(
    analysis: Analysis,
    budget: ProviderBudget,
    *,
    adapter: object | None = None,
) -> StageResult:
    """Extract and verify citations, deduplicating outbound lookups and caching sources."""
    from filingguard.integrations.courtlistener import CourtListenerAdapter
    from filingguard.modules.citations.service import (
        extract_citations,
        verify_citations_for_analysis,
    )

    segments = analysis.review_segments
    validate_segments(analysis, segments)
    extraction = extract_citations(analysis.document_snapshot["text"])
    if not extraction.detected_count:
        return StageResult(
            status=StageStatus.SKIPPED,
            reason="No citations detected in supported formats. " + EXTRACTION_LIMITATION,
        )
    records: list[Citation] = []
    for item in extraction.occurrences:
        anchor, warnings = citation_anchor(segments, item.start, item.end)
        metadata = item.extraction.model_copy(update={"warnings": warnings})
        records.append(
            Citation(
                id=uuid4(),
                analysis_id=analysis.id,
                raw_text=item.raw_text,
                normalized_text=item.normalized_text,
                segment_id=anchor.id,
                page_number=anchor.page_number,
                start_offset=item.start,
                end_offset=item.end,
                extraction_metadata=metadata.model_dump(mode="json"),
                verification_status="not_run",
                authority_id=None,
            )
        )
    cl_adapter = (
        adapter
        if isinstance(adapter, CourtListenerAdapter)
        else CourtListenerAdapter(
            token=getattr(analysis, "provider_credentials", {}).get("courtlistener", ""),
            budget=budget,
        )
    )
    try:
        verified_citations, authorities = verify_citations_for_analysis(
            analysis.id, records, cl_adapter
        )
    finally:
        if adapter is not cl_adapter:
            cl_adapter.close()

    evaluated_count = sum(
        1 for c in verified_citations if c.verification_status not in {"not_run", "unavailable"}
    )
    if evaluated_count == extraction.detected_count and not extraction.truncated:
        status = StageStatus.COMPLETED
        coverage = Coverage(
            eligible=extraction.detected_count,
            evaluated=evaluated_count,
            truncated=extraction.truncated,
            limitation="Only the first 200 citation occurrences were retained."
            if extraction.truncated
            else None,
        )
        reason = (
            f"Citation verification completed ({evaluated_count} citations evaluated, "
            f"{len(authorities)} distinct authorities resolved)."
        )
    else:
        status = StageStatus.PARTIAL
        coverage = Coverage(
            eligible=extraction.detected_count,
            evaluated=evaluated_count,
            unavailable=extraction.detected_count - evaluated_count,
            truncated=extraction.truncated,
            limitation="Only the first 200 citation occurrences were retained."
            if extraction.truncated
            else None,
        )
        reason = (
            f"Citation checks partial: {evaluated_count} evaluated, "
            f"{extraction.detected_count - evaluated_count} unavailable or unresolved; "
            "database absence does not prove fabrication."
        )

    detail_records = []
    described = set()
    text = analysis.document_snapshot["text"]
    snapshot_size = len(json.dumps(text).encode())
    detail_limit = min(25, (6 * 1024 * 1024) // max(1, snapshot_size))
    omitted_details = False
    for citation in verified_citations:
        verdict = citation.verification_status
        metadata = citation.extraction_metadata.get("verification") or {}
        identity = (
            "authority_limit"
            if metadata.get("reason") == "authority_limit"
            else citation.normalized_text or citation.raw_text,
            verdict,
        )
        if verdict in {"not_run", "verified"} or identity in described:
            continue
        if len(described) >= detail_limit:
            omitted_details = True
            continue
        described.add(identity)
        explanation = metadata.get("limitation") or (
            "Authority check is incomplete. Review the citation manually."
        )
        finding = Finding(
            id=uuid4(),
            analysis_id=analysis.id,
            citation_id=citation.id,
            segment_id=citation.segment_id,
            page_number=citation.page_number,
            start_offset=citation.start_offset,
            end_offset=citation.end_offset,
            type="citation",
            severity="high" if verdict == "invalid" else "medium",
            title={
                "not_found": "Citation absent from source database",
                "invalid": "Citation syntax rejected",
                "ambiguous": "Ambiguous authority",
                "unavailable": "Citation service unavailable",
            }[verdict],
            description=explanation,
            status="open",
            stage="citations",
            ai_assisted=False,
            document_excerpt=citation.raw_text,
        )
        detail_records.extend(
            (
                finding,
                EvidenceRecord(
                    id=uuid4(),
                    analysis_id=analysis.id,
                    finding_id=finding.id,
                    citation_id=citation.id,
                    segment_id=citation.segment_id,
                    page_number=citation.page_number,
                    start_offset=citation.start_offset,
                    end_offset=citation.end_offset,
                    source_type="document",
                    source_label="Cited filing text",
                    excerpt=citation.raw_text,
                    snapshot_text=text,
                    source_sha256=sha256(text.encode()).hexdigest(),
                    source_start_offset=citation.start_offset,
                    source_end_offset=citation.end_offset,
                    retrieved_at=datetime.now(UTC),
                    method="citation-lookup",
                    method_version="courtlistener-v4-v1",
                    source_metadata={
                        "provenance": "synthetic" if analysis.mode == "demo" else "live",
                        "verification_status": verdict,
                        "reason": metadata.get("reason"),
                    },
                ),
            )
        )
    if omitted_details:
        limitation = "Finding details bounded by snapshot budget; all citation outcomes retained."
        coverage = coverage.model_copy(
            update={
                "limitation": (coverage.limitation + " " if coverage.limitation else "")
                + limitation,
            }
        )
    all_records = tuple(authorities + verified_citations + detail_records)
    return StageResult(
        status=status,
        coverage=coverage,
        reason=reason,
        records=all_records,
    )
