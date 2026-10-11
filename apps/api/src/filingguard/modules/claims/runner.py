"""Traceable local candidate propositions; support checking is a separate stage."""

import json
from datetime import UTC, datetime
from hashlib import sha256
from uuid import uuid4

from filingguard.db.models import Analysis, Claim, ClaimAuthorityLink, EvidenceRecord
from filingguard.integrations.providers.runtime import ProviderBudget
from filingguard.modules.analyses.execution import StageResult, validate_citation_records
from filingguard.modules.analyses.schemas import Coverage, StageStatus
from filingguard.modules.claims.schemas import LIMITATION, METHOD_VERSION
from filingguard.modules.claims.service import extract_claims

MAX_SNAPSHOT_BYTES = 6 * 1024 * 1024


def claims_stage(analysis: Analysis, _budget: ProviderBudget) -> StageResult:
    segments = analysis.review_segments
    citations = tuple(sorted(analysis.review_citations, key=lambda row: row.start_offset))
    validate_citation_records(analysis, segments, citations)
    citation_state = (analysis.stage_states or {}).get("citations", {})
    upstream = citation_state.get("coverage", {})
    eligible = max(len(citations), upstream.get("eligible", 0))
    if not citations:
        if citation_state.get("status") == "skipped" and eligible == 0:
            return StageResult(
                status=StageStatus.SKIPPED,
                reason="No locally detected citation contexts to extract. " + LIMITATION,
            )
        return StageResult(
            status=StageStatus.UNAVAILABLE,
            coverage=Coverage(eligible=eligible or 1, unavailable=eligible or 1),
            reason="Citation occurrences are unavailable for context extraction. " + LIMITATION,
        )
    text = analysis.document_snapshot["text"]
    # Each immutable EvidenceRecord includes its full source. Bound cumulative JSON
    # snapshot bytes as well as entity counts so Unicode cannot overflow worker IPC.
    snapshot_bytes = len(json.dumps(text, ensure_ascii=False).encode("utf-8"))
    max_contexts = min(100, max(1, MAX_SNAPSHOT_BYTES // snapshot_bytes))
    extraction = extract_claims(text, segments, citations, max_claims=max_contexts)
    by_id = {row.id: row for row in citations}
    records = []
    for context in extraction.contexts:
        claim = Claim(
            id=uuid4(), analysis_id=analysis.id, text=context.text,
            segment_id=context.segment_id, page_number=context.page_number,
            start_offset=context.start, end_offset=context.end,
            extraction_method="heuristic", confidence=None, model_version=None, prompt_version=None,
        )
        records.append(claim)
        for citation_id in context.citation_ids:
            records.append(ClaimAuthorityLink(
                id=uuid4(), analysis_id=analysis.id, claim_id=claim.id,
                citation_id=citation_id, authority_id=by_id[citation_id].authority_id,
                support_status="not_run", confidence=None, explanation=None,
            ))
        records.append(EvidenceRecord(
            id=uuid4(), analysis_id=analysis.id, claim_id=claim.id,
            citation_id=context.citation_ids[0], segment_id=context.segment_id,
            page_number=context.page_number, start_offset=context.start, end_offset=context.end,
            source_type="document", source_label="Original citation context",
            excerpt=context.text, snapshot_text=text,
            source_sha256=sha256(text.encode()).hexdigest(),
            retrieved_at=datetime.now(UTC), source_start_offset=context.start,
            source_end_offset=context.end, method="citation-context", method_version=METHOD_VERSION,
            source_metadata={
                "provenance": "synthetic" if analysis.mode == "demo" else "live",
                "offset_unit": "unicode_code_points", "context_kind": context.context_kind,
                "citation_ids": [str(value) for value in context.citation_ids],
            },
        ))
    truncated = extraction.truncated or bool(upstream.get("truncated")) or eligible > len(citations)
    unavailable = eligible - extraction.associated_count
    return StageResult(
        status=StageStatus.PARTIAL if truncated or unavailable else StageStatus.COMPLETED,
        coverage=Coverage(
            eligible=eligible, evaluated=extraction.associated_count, unavailable=unavailable,
            truncated=truncated,
            limitation="At most 100 contexts, 200 citations and 6 MiB of document snapshots."
            if truncated else None,
        ),
        reason="Local citation contexts extracted; authority support has not been checked. "
        + LIMITATION,
        records=tuple(records),
    )
