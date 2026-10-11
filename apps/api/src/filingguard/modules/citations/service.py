"""Local Eyecite detection only; no source resolution or legal verdicts."""

import json
import re
from bisect import bisect_right
from datetime import UTC, datetime
from importlib.metadata import version
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from eyecite import get_citations
from eyecite.models import (
    FullCaseCitation,
    FullJournalCitation,
    FullLawCitation,
    IdCitation,
    ReferenceCitation,
    ShortCaseCitation,
    SupraCitation,
)

from filingguard.modules.analyses.schemas import CitationStatus
from filingguard.modules.citations.schemas import (
    EXTRACTION_LIMITATION,
    CitationExtraction,
    CitationExtractionMetadata,
    CitationOccurrence,
    CitationVerificationMetadata,
)

if TYPE_CHECKING:
    from filingguard.db.models import Authority, Citation
    from filingguard.integrations.courtlistener import CourtListenerAdapter
    from filingguard.integrations.courtlistener.schemas import CourtListenerResolvedAuthority


MAX_INPUT = 100_000
MAX_OCCURRENCES = 200
REPORTER_CANDIDATE = re.compile(r"(?<!\w)[1-9]\d{0,5}\s+[A-Z][A-Za-z.]{1,15}\s+[1-9]\d{0,5}(?!\w)")


def _kind(citation: object) -> str:
    if isinstance(citation, FullCaseCitation):
        return "full_case"
    if isinstance(citation, ShortCaseCitation):
        return "short_case"
    if isinstance(citation, IdCitation):
        return "id"
    if isinstance(citation, SupraCitation):
        return "supra"
    if isinstance(citation, ReferenceCitation):
        return "reference"
    if isinstance(citation, FullLawCitation):
        return "law"
    if isinstance(citation, FullJournalCitation):
        return "journal"
    return "unknown"


def extract_citations(text: str) -> CitationExtraction:
    if not isinstance(text, str) or not text.strip() or len(text) > MAX_INPUT:
        raise ValueError("Citation input must contain 1 to 100000 nonblank characters")

    parser_version = version("eyecite")
    occurrences: list[CitationOccurrence] = []
    parsed = get_citations(text, remove_ambiguous=False)
    spans = [citation.span() for citation in parsed]
    merged_spans: list[tuple[int, int]] = []
    for start, end in sorted(spans):
        if merged_spans and start <= merged_spans[-1][1]:
            merged_spans[-1] = (merged_spans[-1][0], max(end, merged_spans[-1][1]))
        else:
            merged_spans.append((start, end))
    merged_starts = [start for start, _ in merged_spans]

    for citation in parsed:
        start, end = citation.span()
        if not 0 <= start < end <= len(text):
            raise ValueError("Eyecite returned a span outside the original text")
        raw = text[start:end]
        kind = _kind(citation)
        editions = getattr(citation, "all_editions", ())
        candidates = list(dict.fromkeys(edition.short_name for edition in editions))[:16]
        normalized = None
        if kind == "full_case":
            if len(editions) > 1 and citation.edition_guess is None:
                support = "ambiguous"
            elif citation.edition_guess is not None and len(editions) == 1:
                support = "recognized"
                normalized = citation.corrected_citation()
            else:
                support = "ambiguous"
        elif kind in {"short_case", "id", "supra", "reference"}:
            support = "unresolved_reference"
        else:
            support = "unsupported"
        occurrences.append(
            CitationOccurrence(
                raw_text=raw,
                normalized_text=normalized,
                start=start,
                end=end,
                extraction=CitationExtractionMetadata(
                    parser_version=parser_version,
                    kind=kind,
                    support=support,
                    reporter_candidates=candidates,
                ),
            )
        )

    for match in REPORTER_CANDIDATE.finditer(text):
        start, end = match.span()
        previous = bisect_right(merged_starts, start) - 1
        if (previous >= 0 and start < merged_spans[previous][1]) or (
            previous + 1 < len(merged_spans) and merged_spans[previous + 1][0] < end
        ):
            continue
        occurrences.append(
            CitationOccurrence(
                raw_text=text[start:end],
                normalized_text=None,
                start=start,
                end=end,
                extraction=CitationExtractionMetadata(
                    parser_version=parser_version,
                    kind="reporter_candidate",
                    support="unsupported",
                ),
            )
        )

    occurrences.sort(key=lambda occurrence: (occurrence.start, occurrence.end))
    detected_count = len(occurrences)
    return CitationExtraction(
        occurrences=occurrences[:MAX_OCCURRENCES],
        detected_count=detected_count,
        truncated=detected_count > MAX_OCCURRENCES,
        limitation=EXTRACTION_LIMITATION,
    )


def create_authority_record(
    analysis_id: UUID,
    resolved: "CourtListenerResolvedAuthority",
    *,
    authority_id: UUID | None = None,
) -> "Authority":
    """Create a persistent Authority DB model from resolved CourtListener data."""
    from filingguard.db.models import Authority

    return Authority(
        id=authority_id or uuid4(),
        analysis_id=analysis_id,
        source="courtlistener",
        external_id=str(resolved.cluster_id),
        case_name=resolved.case_name,
        citation=resolved.citation,
        court=resolved.court,
        year=resolved.year,
        source_url=resolved.source_url,
        opinion_text_available=resolved.opinion_text_available,
        opinion_text=resolved.opinion_text,
        source_sha256=resolved.source_sha256,
        retrieved_at=resolved.retrieved_at,
        source_metadata=resolved.source_metadata,
    )


def verify_citations_for_analysis(
    analysis_id: UUID,
    citations: list["Citation"],
    adapter: "CourtListenerAdapter",
) -> tuple[list["Citation"], list["Authority"]]:
    """Verify citations for an analysis, deduplicating outbound lookups.

    Preserves every original occurrence and its location, while ensuring that
    repeated citations share a single authority lookup and link to the same
    Authority entity. Only one Authority record is created per resolved cluster.
    """
    from filingguard.db.models import Authority

    authorities_by_cluster: dict[int, Authority] = {}
    lookup_cache_by_key: dict[str, tuple[str, UUID | None, dict]] = {}
    lookup_count = 0
    snapshot_bytes = 0

    for citation in citations:
        lookup_key = (citation.normalized_text or citation.raw_text or "").strip()
        normalized_key = " ".join(lookup_key.split())

        extraction = citation.extraction_metadata or {}
        support = extraction.get("support")
        if support in {"unresolved_reference", "unsupported", "ambiguous"}:
            citation.verification_status = CitationStatus.NOT_RUN.value
            citation.authority_id = None
            continue

        if normalized_key in lookup_cache_by_key:
            status_val, auth_id, verification = lookup_cache_by_key[normalized_key]
            citation.verification_status = status_val
            citation.authority_id = auth_id
            citation.extraction_metadata = {**extraction, "verification": verification}
            continue

        if lookup_count >= 25:
            citation.verification_status = CitationStatus.UNAVAILABLE.value
            citation.authority_id = None
            citation.extraction_metadata = {
                **extraction,
                "verification": CitationVerificationMetadata(
                    retrieved_at=datetime.now(UTC),
                    reason="authority_limit",
                    limitation="At most 25 distinct authority queries.",
                ).model_dump(mode="json"),
            }
            continue

        lookup_count += 1
        lookup, resolved = adapter.verify_and_resolve(lookup_key)
        status_val = lookup.status.value
        citation.verification_status = status_val
        verification = CitationVerificationMetadata(
            retrieved_at=datetime.now(UTC), reason=lookup.reason, limitation=lookup.limitation
        ).model_dump(mode="json")
        citation.extraction_metadata = {**extraction, "verification": verification}

        if lookup.status == CitationStatus.VERIFIED and resolved is not None:
            if resolved.cluster_id in authorities_by_cluster:
                auth_record = authorities_by_cluster[resolved.cluster_id]
            else:
                auth_record = create_authority_record(analysis_id, resolved)
                if auth_record.opinion_text:
                    size = len(json.dumps(auth_record.opinion_text).encode())
                    if snapshot_bytes + size > 6 * 1024 * 1024:
                        auth_record.opinion_text = None
                        auth_record.opinion_text_available = False
                        auth_record.source_sha256 = None
                        auth_record.source_metadata = {
                            **(auth_record.source_metadata or {}),
                            "text_unavailable_reason": "analysis_source_snapshot_budget",
                            "limitation": (
                                "Public source identity resolved; "
                                "opinion snapshot budget exhausted."
                            ),
                        }
                    else:
                        snapshot_bytes += size
                authorities_by_cluster[resolved.cluster_id] = auth_record

            citation.authority_id = auth_record.id
            lookup_cache_by_key[normalized_key] = (status_val, auth_record.id, verification)
            if lookup.normalized_citation:
                canon_key = " ".join(lookup.normalized_citation.strip().split())
                lookup_cache_by_key[canon_key] = (status_val, auth_record.id, verification)
        else:
            citation.authority_id = None
            lookup_cache_by_key[normalized_key] = (status_val, None, verification)
            if lookup.normalized_citation:
                canon_key = " ".join(lookup.normalized_citation.strip().split())
                lookup_cache_by_key[canon_key] = (status_val, None, verification)

    return citations, list(authorities_by_cluster.values())
