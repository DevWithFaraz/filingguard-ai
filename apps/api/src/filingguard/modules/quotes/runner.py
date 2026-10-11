"""Quote forensics over owner-scoped immutable filing and authority snapshots."""

import json
from datetime import UTC, datetime
from hashlib import sha256
from uuid import uuid4

from pydantic import ValidationError

from filingguard.db.models import Analysis, EvidenceRecord, Finding, Quote
from filingguard.integrations.providers.runtime import ProviderBudget
from filingguard.modules.analyses.execution import StageResult, citation_anchor, validate_segments
from filingguard.modules.analyses.schemas import Coverage, QuoteStatus, StageStatus
from filingguard.modules.evidence.schemas import EvidenceRecord as EvidenceContract
from filingguard.modules.evidence.schemas import validate_snapshot
from filingguard.modules.quotes.schemas import (
    LIMITATION,
    MAX_QUOTES,
    METHOD_VERSION,
    QuoteComparison,
)
from filingguard.modules.quotes.service import associate_quote, compare_quote, extract_quotes

MAX_SNAPSHOT_BYTES = 4 * 1024 * 1024


def _evidence(
    analysis, quote, finding, text, start, end, *, authority=None, metadata=None
) -> EvidenceRecord:
    provenance = "synthetic" if analysis.mode == "demo" else "live"
    provider_provenance = None
    if authority is not None:
        provider_label = (authority.source_metadata or {}).get("provenance", "live")
        provenance = (
            provider_label if provider_label in {"live", "synthetic", "cached_public"} else "live"
        )
        if provider_label == "courtlistener_api_v4":
            provider_provenance = provider_label
    contract = EvidenceContract(
        id=uuid4(),
        analysis_id=analysis.id,
        finding_id=finding.id,
        source_type="opinion_text" if authority is not None else "document",
        source_label="Associated authority snapshot"
        if authority is not None
        else "Filing snapshot",
        source_url=authority.source_url if authority is not None else None,
        retrieved_at=authority.retrieved_at if authority is not None else datetime.now(UTC),
        snapshot_sha256=authority.source_sha256
        if authority is not None
        else sha256(text.encode("utf-8")).hexdigest(),
        excerpt=text[start:end],
        start=start,
        end=end,
        triggering_citation_id=quote.citation_id,
        triggering_quote_id=quote.id,
        method_version=METHOD_VERSION,
        authority_id=authority.id if authority is not None else None,
        external_id=authority.external_id if authority is not None else None,
        provenance=provenance,
    )
    validate_snapshot(contract, text)
    return EvidenceRecord(
        id=contract.id,
        analysis_id=analysis.id,
        finding_id=finding.id,
        segment_id=quote.segment_id,
        citation_id=quote.citation_id,
        quote_id=quote.id,
        authority_id=contract.authority_id,
        source_type=contract.source_type,
        source_label=contract.source_label,
        excerpt=contract.excerpt,
        snapshot_text=text,
        source_url=str(contract.source_url) if contract.source_url else None,
        source_sha256=contract.snapshot_sha256,
        retrieved_at=contract.retrieved_at,
        source_start_offset=start,
        source_end_offset=end,
        start_offset=quote.start_offset,
        end_offset=quote.end_offset,
        page_number=quote.page_number,
        method="string_quote_comparison" if authority is not None else "heuristic_quote_extraction",
        method_version=METHOD_VERSION,
        source_metadata={
            "provenance": provenance,
            "offset_unit": "unicode_code_points",
            "external_id": contract.external_id,
            "provider_provenance": provider_provenance,
            **(metadata or {}),
        },
    )


def quotes_stage(analysis: Analysis, budget: ProviderBudget) -> StageResult:
    validate_segments(analysis, analysis.review_segments)
    text = analysis.document_snapshot["text"]
    citations = tuple(getattr(analysis, "review_citations", ()))
    authorities = {row.id: row for row in getattr(analysis, "review_authorities", ())}
    if any(row.analysis_id != analysis.id for row in (*citations, *authorities.values())):
        raise ValueError("Quote inputs belong to another analysis")
    occurrences = extract_quotes(text)
    if not occurrences:
        return StageResult(
            StageStatus.SKIPPED,
            reason="No quotations detected in supported delimiter or block formats.",
        )
    records, evaluated, unavailable, processed, snapshot_bytes = [], 0, 0, 0, 0
    # Bound the serialized snapshots too: JSON escaping can expand control/Unicode text.
    document_bytes = len(json.dumps(text).encode("utf-8"))
    for occurrence in occurrences[:MAX_QUOTES]:
        budget.remaining()
        if snapshot_bytes + document_bytes > MAX_SNAPSHOT_BYTES:
            break
        snapshot_bytes += document_bytes
        processed += 1
        association = associate_quote(occurrence, citations, text)
        authority = authorities.get(association.authority_id)
        comparison = QuoteComparison(
            QuoteStatus.SOURCE_UNAVAILABLE,
            reason=association.reason or "Associated authority snapshot is unavailable.",
        )
        source_evidence = None
        anchor, _ = citation_anchor(analysis.review_segments, occurrence.start, occurrence.end)
        quote = Quote(
            id=uuid4(),
            analysis_id=analysis.id,
            quote_text=occurrence.text,
            segment_id=anchor.id,
            citation_id=association.citation_id,
            start_offset=occurrence.start,
            end_offset=occurrence.end,
            page_number=anchor.page_number,
        )
        finding = Finding(
            id=uuid4(),
            analysis_id=analysis.id,
            type="quote",
            stage="quotes",
            status="open",
            segment_id=quote.segment_id,
            citation_id=quote.citation_id,
            quote_id=quote.id,
            authority_id=None,
            document_excerpt=occurrence.text,
            start_offset=quote.start_offset,
            end_offset=quote.end_offset,
            page_number=quote.page_number,
            ai_assisted=False,
            confidence=None,
        )
        if authority is not None and authority.opinion_text_available and authority.opinion_text:
            source_bytes = len(json.dumps(authority.opinion_text).encode("utf-8"))
            if snapshot_bytes + source_bytes <= MAX_SNAPSHOT_BYTES:
                comparison = compare_quote(occurrence.text, authority.opinion_text)
                if comparison.passage is not None:
                    try:
                        source_evidence = _evidence(
                            analysis,
                            quote,
                            finding,
                            authority.opinion_text,
                            comparison.source_start,
                            comparison.source_end,
                            authority=authority,
                            metadata={
                                "match_status": comparison.status.value,
                                "similarity": comparison.similarity,
                            },
                        )
                    except (ValidationError, ValueError):
                        comparison = QuoteComparison(
                            QuoteStatus.SOURCE_UNAVAILABLE,
                            reason="Authority snapshot provenance could not be validated.",
                        )
                    else:
                        snapshot_bytes += source_bytes
                # Even a short not-found outcome needs a valid complete source snapshot.
                elif comparison.status != QuoteStatus.SOURCE_UNAVAILABLE:
                    try:
                        source_evidence = _evidence(
                            analysis,
                            quote,
                            finding,
                            authority.opinion_text,
                            0,
                            min(len(authority.opinion_text), 100),
                            authority=authority,
                            metadata={
                                "match_status": comparison.status.value,
                                "comparison_context_only": True,
                            },
                        )
                    except (ValidationError, ValueError):
                        comparison = QuoteComparison(
                            QuoteStatus.SOURCE_UNAVAILABLE,
                            reason="Authority snapshot provenance could not be validated.",
                        )
                    else:
                        snapshot_bytes += source_bytes
            else:
                comparison = QuoteComparison(
                    QuoteStatus.SOURCE_UNAVAILABLE,
                    reason="Stage snapshot evidence budget exhausted.",
                )
        quote.match_status = comparison.status.value
        quote.similarity = comparison.similarity
        quote.closest_passage = comparison.passage
        finding.authority_id = authority.id if source_evidence is not None else None
        finding.severity = (
            "info"
            if comparison.status
            in {QuoteStatus.EXACT, QuoteStatus.NORMALIZED, QuoteStatus.SOURCE_UNAVAILABLE}
            else "medium"
        )
        finding.title = {
            QuoteStatus.EXACT: "Exact quotation match",
            QuoteStatus.NORMALIZED: "Quotation matches after normalization",
            QuoteStatus.CLOSE: "Quotation differs from closest source passage",
            QuoteStatus.NOT_FOUND: "Quotation not found in associated source",
            QuoteStatus.SOURCE_UNAVAILABLE: "Quotation source comparison unavailable",
        }[comparison.status]
        finding.description = (
            (comparison.reason or "String comparison completed.") + " " + LIMITATION
        )
        metadata = {
            "quote_kind": occurrence.kind,
            "association_candidates": [str(value) for value in association.candidates],
            "reason": comparison.reason,
            "match_status": comparison.status.value,
            "similarity": comparison.similarity,
        }
        records.extend(
            (
                quote,
                finding,
                _evidence(
                    analysis,
                    quote,
                    finding,
                    text,
                    occurrence.start,
                    occurrence.end,
                    metadata=metadata,
                ),
            )
        )
        if source_evidence is not None:
            records.append(source_evidence)
        if comparison.status == QuoteStatus.SOURCE_UNAVAILABLE:
            unavailable += 1
        else:
            evaluated += 1
    pending = len(occurrences) - processed
    coverage = Coverage(
        eligible=len(occurrences),
        evaluated=evaluated,
        unavailable=unavailable,
        pending=pending,
        truncated=bool(pending),
        limitation="At most 50 quotations and 4 MiB of evidence snapshots are processed."
        if pending
        else None,
    )
    return StageResult(
        StageStatus.COMPLETED if coverage.complete else StageStatus.PARTIAL,
        coverage=coverage,
        reason="Quote comparison completed. " + LIMITATION
        if coverage.complete
        else "Some quotations have unavailable sources or were not processed within limits.",
        records=tuple(records),
    )
