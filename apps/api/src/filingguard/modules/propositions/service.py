"""Bounded source review; unavailable dependencies preserve explicit uncertainty."""

import hashlib
import json
from datetime import UTC, datetime
from uuid import uuid4

from filingguard.db.models import ClaimAuthorityLink, EvidenceRecord, Finding
from filingguard.integrations.llm.adapter import MODEL, GroqPropositionAdapter
from filingguard.integrations.providers.runtime import ProviderUnavailable
from filingguard.modules.analyses.execution import StageResult
from filingguard.modules.analyses.schemas import Coverage, StageStatus
from filingguard.modules.claim_corrections.text import proposition_text, uses_user_correction
from filingguard.modules.propositions.facts import LIMITATION as FACT_LIMITATION
from filingguard.modules.propositions.facts import METHOD_VERSION as FACT_METHOD_VERSION
from filingguard.modules.propositions.facts import compare_facts
from filingguard.modules.propositions.passages import METHOD_VERSION, select_passages

MAX_LINKS = 25
# A conservative raw snapshot allowance leaves room for JSON escaping/metadata in
# the 16 MiB worker envelope; preserve earlier findings when later evidence is large.
MAX_SNAPSHOT_BYTES = 6 * 1024 * 1024
_LABELS = {
    "supported": "Supported by selected source passages",
    "partially_supported": "Partially supported by selected source passages",
    "unclear": "Unclear proposition support",
    "misrepresented": "Potentially misrepresented source",
    "insufficient_source": "Insufficient source text",
    "unavailable": "Proposition review unavailable",
}


def propositions_stage(analysis, budget):
    credentials = getattr(analysis, "provider_credentials", {})
    token = credentials.get("groq")
    if not token:
        return review_propositions(analysis, adapter=None)
    try:
        with GroqPropositionAdapter(
            token, budget, model=credentials.get("groq_model", MODEL)
        ) as adapter:
            return review_propositions(analysis, adapter=adapter)
    except ProviderUnavailable:
        return review_propositions(analysis, adapter=None)


def review_propositions(analysis, *, adapter):
    """Use persisted prior context only; an explicit adapter supports offline tests."""
    filing = analysis.document_snapshot["text"]
    claims = {r.id: r for r in getattr(analysis, "review_claims", ())}
    authorities = {r.id: r for r in getattr(analysis, "review_authorities", ())}
    citations = {r.id: r for r in getattr(analysis, "review_citations", ())}
    links = tuple(getattr(analysis, "review_links", ()))
    if not links:
        claim_state = getattr(analysis, "stage_states", {}).get("claims", {})
        if claim_state.get("status") not in {"completed", "skipped"}:
            return StageResult(
                status=StageStatus.UNAVAILABLE,
                coverage=Coverage(eligible=1, unavailable=1),
                reason="Claim extraction unavailable; proposition coverage cannot be determined",
            )
        return StageResult(status=StageStatus.SKIPPED, reason="No extracted claim-citation links")
    records, updates = [], []
    batch_cache = {}
    evaluated = 0
    clipped = len(links) > MAX_LINKS
    snapshot_bytes = 0
    filing_bytes = len(json.dumps(filing, ensure_ascii=False).encode())
    for link_index, link in enumerate(links[:MAX_LINKS]):
        if snapshot_bytes + filing_bytes > MAX_SNAPSHOT_BYTES:
            clipped = True
            break
        claim = claims.get(link.claim_id)
        citation = citations.get(link.citation_id)
        authority = authorities.get(link.authority_id)
        if (
            claim is None
            or citation is None
            or any(r.analysis_id != analysis.id for r in (claim, citation, link))
        ):
            raise ValueError("Proposition context mismatch")
        start, end = claim.start_offset, claim.end_offset
        if not 0 <= start < end <= len(filing) or filing[start:end] != claim.text:
            raise ValueError("Claim does not match original filing")
        reviewed = proposition_text(claim)
        corrected = uses_user_correction(claim)
        status = "insufficient_source"
        explanation = "Source text unavailable. Review the cited authority manually."
        source = authority.opinion_text if authority is not None else None
        result = None
        passages = ()
        quota = None
        valid_source = (
            authority is not None
            and authority.analysis_id == analysis.id
            and citation.verification_status == "verified"
            and citation.authority_id == authority.id
            and authority.opinion_text_available
            and bool(source)
            and authority.source_url
            and authority.external_id
            and authority.retrieved_at
            and hashlib.sha256(source.encode()).hexdigest() == authority.source_sha256
        )
        if valid_source:
            passages = select_passages(source, reviewed)
            clipped |= end - start > 8000 or any(p.truncated for p in passages)
            source_bytes = len(json.dumps(source, ensure_ascii=False).encode())
            oversized = snapshot_bytes + filing_bytes + source_bytes * 3 > MAX_SNAPSHOT_BYTES
            if oversized:
                clipped = True
                passages = ()
                explanation = "Source evidence exceeds bounded output. Review the full source."
            if not passages:
                if not oversized:
                    explanation = "No bounded relevant passage found. Review the full source."
            elif adapter is None:
                status = "unavailable"
                explanation = "Semantic provider is unconfigured. Review the source manually."
            else:
                try:
                    if link.id not in batch_cache and hasattr(adapter, "review_batch"):
                        # Same verified authority only; no expected verdict or fixture ID
                        # participates in grouping. Preserve every selected source character.
                        for peer in links[link_index + 1 : MAX_LINKS]:
                            peer_claim = claims.get(peer.claim_id)
                            peer_citation = citations.get(peer.citation_id)
                            if (
                                corrected
                                or peer.id == link.id
                                or peer.id in batch_cache
                                or peer.claim_id == link.claim_id
                                or peer.authority_id != authority.id
                                or peer_claim is None
                                or peer_citation is None
                                or uses_user_correction(peer_claim)
                                or any(
                                    r.analysis_id != analysis.id
                                    for r in (peer, peer_claim, peer_citation)
                                )
                                or peer_citation.authority_id != authority.id
                                or peer_citation.verification_status != "verified"
                            ):
                                continue
                            left, right = peer_claim.start_offset, peer_claim.end_offset
                            if (
                                not 0 <= left < right <= len(filing)
                                or filing[left:right] != peer_claim.text
                                or snapshot_bytes + 2 * (filing_bytes + source_bytes * 3)
                                > MAX_SNAPSHOT_BYTES
                            ):
                                continue
                            peer_passages = select_passages(source, proposition_text(peer_claim))
                            if not peer_passages:
                                continue
                            try:
                                batch = adapter.review_batch(
                                    filing,
                                    (
                                        (start, end, passages),
                                        (left, right, peer_passages),
                                    ),
                                    source=source,
                                )
                            except ProviderUnavailable as error:
                                batch_cache[link.id] = batch_cache[peer.id] = error.code
                                raise
                            if batch is not None:
                                batch_cache[link.id], batch_cache[peer.id] = batch
                            break
                    if link.id in batch_cache:
                        cached = batch_cache[link.id]
                        if isinstance(cached, str):
                            raise ProviderUnavailable(cached)
                        result = cached
                        passages = result.source_passages or passages
                    else:
                        if corrected:
                            result = adapter.review(
                                reviewed, 0, len(reviewed), passages, source=source
                            )
                        else:
                            result = adapter.review(filing, start, end, passages, source=source)
                    status = result.verdict.status
                    explanation = result.verdict.explanation
                    if corrected:
                        explanation = "Reviewed user-corrected extraction. " + explanation
                    evaluated += status != "insufficient_source"
                    clipped |= result.filing_truncated or any(p.truncated for p in passages)
                except ProviderUnavailable as error:
                    status = "unavailable"
                    explanation = (
                        f"Semantic provider output unavailable ({error.code}). Review the source."
                    )
                quota = (
                    result.token_quota
                    if result
                    else getattr(getattr(adapter, "client", None), "last_token_quota", None)
                )
        update = ClaimAuthorityLink(
            id=link.id,
            analysis_id=analysis.id,
            claim_id=link.claim_id,
            citation_id=link.citation_id,
            authority_id=link.authority_id,
            support_status=status,
            confidence=None,
            explanation=explanation + " Review flag, not a legal determination.",
        )
        updates.append(update)
        finding = Finding(
            id=uuid4(),
            analysis_id=analysis.id,
            type="claim_support",
            severity={
                "supported": "info",
                "partially_supported": "medium",
                "misrepresented": "high",
            }.get(status, "low"),
            title=_LABELS[status],
            description=update.explanation,
            status="open",
            stage="propositions",
            segment_id=claim.segment_id,
            citation_id=citation.id,
            authority_id=link.authority_id,
            claim_id=claim.id,
            page_number=claim.page_number,
            start_offset=start,
            end_offset=end,
            document_excerpt=claim.text,
            confidence=None,
            ai_assisted=result is not None,
        )
        records.append(finding)
        meta = {
            "provenance": "live" if analysis.mode == "live" else "synthetic",
            "offset_unit": "unicode_code_points",
            "proposition_status": status,
            "token_quota": quota,
            "confidence_level": result.verdict.confidence if result else "unknown",
            "confidence_method": "uncalibrated-model-assessment" if result else None,
            "confidence_calibrated": False,
            "external_id": authority.external_id if authority is not None else None,
            "retrieval_method": METHOD_VERSION,
            "selected_passages": [
                {"id": p.id, "start": p.start, "end": p.end, "truncated": p.truncated}
                for p in passages
            ],
            "limitation": "Selected passages may omit relevant context; human review required.",
            "used_user_correction": corrected,
        }
        if result:
            meta.update(
                {
                    "elapsed_seconds": result.elapsed_seconds,
                    "prompt_tokens": result.prompt_tokens,
                    "completion_tokens": result.completion_tokens,
                    "token_quota": result.token_quota,
                    "request_group": result.request_group,
                    "batch_size": result.batch_size,
                    "filing_truncated": result.filing_truncated,
                }
            )
        common = {
            "analysis_id": analysis.id,
            "finding_id": finding.id,
            "segment_id": claim.segment_id,
            "citation_id": citation.id,
            "authority_id": link.authority_id,
            "claim_id": claim.id,
            "page_number": claim.page_number,
            "start_offset": start,
            "end_offset": end,
            "method": "grounded_proposition_review" if result else "source_availability",
            "method_version": result.method_version if result else METHOD_VERSION,
            "model_version": result.model_version if result else None,
            "prompt_version": result.prompt_version if result else None,
            "source_metadata": meta,
        }
        records.append(
            EvidenceRecord(
                id=uuid4(),
                source_type="document",
                source_label="Original filing proposition",
                excerpt=claim.text,
                snapshot_text=filing,
                source_url=None,
                source_sha256=hashlib.sha256(filing.encode()).hexdigest(),
                retrieved_at=datetime.now(UTC),
                source_start_offset=start,
                source_end_offset=end,
                **common,
            )
        )
        snapshot_bytes += filing_bytes
        fact_rows = _fact_comparison_records(
            analysis=analysis,
            claim=claim,
            citation=citation,
            authority=authority,
            link=link,
            filing=filing,
            start=start,
            end=end,
            reviewed=reviewed,
            corrected=corrected,
            source=source if valid_source else None,
            passages=passages,
            valid_source=valid_source,
        )
        records.extend(fact_rows)
        if result:
            for evidence in result.verdict.evidence:
                snapshot_bytes += source_bytes
                records.append(
                    EvidenceRecord(
                        id=uuid4(),
                        source_type="opinion_text",
                        source_label="Cited authority passage",
                        excerpt=evidence.excerpt,
                        snapshot_text=source,
                        source_url=authority.source_url,
                        source_sha256=authority.source_sha256,
                        retrieved_at=authority.retrieved_at,
                        source_start_offset=evidence.start,
                        source_end_offset=evidence.end,
                        **(
                            common
                            | {
                                "source_metadata": meta
                                | {
                                    "provenance": (authority.source_metadata or {}).get(
                                        "provenance"
                                    )
                                    if (authority.source_metadata or {}).get("provenance")
                                    in {"cached_public", "synthetic", "live"}
                                    else "live",
                                }
                            }
                        ),
                    )
                )
    coverage = Coverage(
        eligible=len(links),
        evaluated=evaluated,
        unavailable=len(links) - evaluated,
        truncated=clipped,
        limitation="Bounded proposition selection or filing/source clipping" if clipped else None,
    )
    return StageResult(
        status=StageStatus.COMPLETED if coverage.complete else StageStatus.PARTIAL,
        reason=None
        if coverage.complete
        else "Some proposition checks lack usable source or model output",
        coverage=coverage,
        records=tuple(records),
        updates=tuple(updates),
    )


_FACT_TITLES = {
    "mismatch": "Filing fact may not match source fact",
    "insufficient_source": "Insufficient source text for fact comparison",
    "unavailable": "Filing-versus-case fact comparison unavailable",
}


def _fact_comparison_records(
    *,
    analysis,
    claim,
    citation,
    authority,
    link,
    filing,
    start,
    end,
    reviewed,
    corrected,
    source,
    passages,
    valid_source,
):
    comparison = compare_facts(reviewed, passages, source_available=valid_source)
    if comparison.status in {"match", "not_applicable"}:
        return ()
    passage_ids = [p.id for p in passages]
    meta = {
        "provenance": "live" if analysis.mode == "live" else "synthetic",
        "offset_unit": "unicode_code_points",
        "check_kind": "fact_comparison",
        "fact_comparison_status": comparison.status,
        "confidence_level": "unknown",
        "confidence_calibrated": False,
        "retrieval_method": METHOD_VERSION,
        "selected_passages": [
            {"id": p.id, "start": p.start, "end": p.end, "truncated": p.truncated}
            for p in passages
        ],
        "passage_ids": passage_ids,
        "used_user_correction": corrected,
        "filing_facts": [
            {
                "kind": f.kind,
                "text": f.text,
                "normalized": f.normalized,
                "start": f.start,
                "end": f.end,
            }
            for f in comparison.filing_facts
        ],
        "source_facts": [
            {
                "kind": f.kind,
                "text": f.text,
                "normalized": f.normalized,
                "start": f.start,
                "end": f.end,
                "passage_id": f.passage_id,
            }
            for f in comparison.source_facts
        ],
        "limitation": FACT_LIMITATION,
    }
    finding = Finding(
        id=uuid4(),
        analysis_id=analysis.id,
        type="claim_support",
        severity="medium" if comparison.status == "mismatch" else "low",
        title=_FACT_TITLES[comparison.status],
        description=comparison.explanation,
        status="open",
        stage="propositions",
        segment_id=claim.segment_id,
        citation_id=citation.id,
        authority_id=link.authority_id,
        claim_id=claim.id,
        page_number=claim.page_number,
        start_offset=start,
        end_offset=end,
        document_excerpt=claim.text,
        confidence=None,
        ai_assisted=False,
    )
    common = {
        "analysis_id": analysis.id,
        "finding_id": finding.id,
        "segment_id": claim.segment_id,
        "citation_id": citation.id,
        "authority_id": link.authority_id,
        "claim_id": claim.id,
        "page_number": claim.page_number,
        "method": "heuristic_fact_comparison",
        "method_version": FACT_METHOD_VERSION,
        "model_version": None,
        "prompt_version": None,
        "source_metadata": meta,
    }
    rows = [finding]
    fact_start, fact_end = start, end
    if not corrected and (comparison.conflicts or comparison.unmatched_filing):
        focus = (comparison.conflicts or comparison.unmatched_filing)[0]
        fact_start, fact_end = start + focus.start, start + focus.end
        if not 0 <= fact_start < fact_end <= len(filing):
            fact_start, fact_end = start, end
    rows.append(
        EvidenceRecord(
            id=uuid4(),
            source_type="document",
            source_label="Filing fact excerpt",
            excerpt=filing[fact_start:fact_end],
            snapshot_text=filing,
            source_url=None,
            source_sha256=hashlib.sha256(filing.encode()).hexdigest(),
            retrieved_at=datetime.now(UTC),
            source_start_offset=fact_start,
            source_end_offset=fact_end,
            start_offset=fact_start,
            end_offset=fact_end,
            **common,
        )
    )
    peer = next(
        (
            item
            for item in comparison.source_facts
            if item.kind
            in {f.kind for f in (*comparison.conflicts, *comparison.unmatched_filing)}
        ),
        comparison.source_facts[0] if comparison.source_facts else None,
    )
    if peer is not None and source and authority is not None:
        rows.append(
            EvidenceRecord(
                id=uuid4(),
                source_type="opinion_text",
                source_label="Cited authority fact passage",
                excerpt=source[peer.start : peer.end],
                snapshot_text=source,
                source_url=authority.source_url,
                source_sha256=authority.source_sha256,
                retrieved_at=authority.retrieved_at,
                source_start_offset=peer.start,
                source_end_offset=peer.end,
                **(
                    common
                    | {
                        "source_metadata": meta
                        | {
                            "evidence_passage_id": peer.passage_id,
                            "provenance": (authority.source_metadata or {}).get("provenance")
                            if (authority.source_metadata or {}).get("provenance")
                            in {"cached_public", "synthetic", "live"}
                            else "live",
                        }
                    }
                ),
            )
        )
    elif passages and source and authority is not None:
        passage = passages[0]
        rows.append(
            EvidenceRecord(
                id=uuid4(),
                source_type="opinion_text",
                source_label="Cited authority selected passage",
                excerpt=passage.text,
                snapshot_text=source,
                source_url=authority.source_url,
                source_sha256=authority.source_sha256,
                retrieved_at=authority.retrieved_at,
                source_start_offset=passage.start,
                source_end_offset=passage.end,
                **(
                    common
                    | {
                        "source_metadata": meta
                        | {
                            "evidence_passage_id": passage.id,
                            "provenance": (authority.source_metadata or {}).get("provenance")
                            if (authority.source_metadata or {}).get("provenance")
                            in {"cached_public", "synthetic", "live"}
                            else "live",
                        }
                    }
                ),
            )
        )
    return tuple(rows)
