"""Local claim extraction preserves exact context, links, limits and unrun verdicts."""

import json
import time
from hashlib import sha256
from uuid import uuid4

import pytest

from filingguard.db.models import Analysis, Citation, Claim, ClaimAuthorityLink, EvidenceRecord
from filingguard.integrations.providers.runtime import ProviderBudget
from filingguard.modules.analyses.execution import ReviewSegment, citation_anchor
from filingguard.modules.analyses.schemas import StageStatus
from filingguard.modules.citations.service import extract_citations
from filingguard.modules.claims.runner import MAX_SNAPSHOT_BYTES, claims_stage
from filingguard.modules.claims.service import extract_claims
from filingguard.modules.documents.extraction import extract_text, segment
from filingguard.modules.documents.schemas import ExtractedDocument, PageSpan


def context(text: str):
    document = extract_text(text)
    analysis = Analysis(
        id=uuid4(), mode="live", document_snapshot=document.model_dump(mode="json"),
        stage_states={}, document_sha256=document.text_sha256,
    )
    segments = tuple(ReviewSegment(
        id=uuid4(), start=p.start, end=p.end, page_number=p.page_number,
    ) for p in document.paragraphs)
    citations = []
    for item in extract_citations(text).occurrences:
        anchor, warnings = citation_anchor(segments, item.start, item.end)
        citations.append(Citation(
            id=uuid4(), analysis_id=analysis.id, segment_id=anchor.id,
            page_number=anchor.page_number, start_offset=item.start, end_offset=item.end,
            raw_text=item.raw_text, normalized_text=item.normalized_text,
            extraction_metadata=item.extraction.model_copy(
                update={"warnings": warnings}
            ).model_dump(mode="json"), authority_id=None, verification_status="not_run",
        ))
    analysis.review_segments = segments
    analysis.review_citations = tuple(citations)
    analysis.stage_states = {"citations": {
        "status": "partial" if citations else "skipped",
        "coverage": {"eligible": len(citations), "truncated": False},
    }}
    return analysis, segments, tuple(citations)


def run(analysis):
    return claims_stage(analysis, ProviderBudget(deadline=time.monotonic() + 30))


def test_unicode_exact_sentence_and_evidence_without_legal_support():
    text = "😀 Introductory text. Café’s rule follows Brown v. Board, 347 U.S. 483. Another rule."
    analysis, segments, citations = context(text)
    result = run(analysis)
    claim = next(row for row in result.records if isinstance(row, Claim))
    evidence = next(row for row in result.records if isinstance(row, EvidenceRecord))
    link = next(row for row in result.records if isinstance(row, ClaimAuthorityLink))

    assert claim.text == "Café’s rule follows Brown v. Board, 347 U.S. 483."
    assert claim.start_offset == text.index("Café")
    assert claim.segment_id == segments[0].id
    assert text[claim.start_offset:claim.end_offset] == claim.text == evidence.excerpt
    assert evidence.snapshot_text == text
    assert evidence.source_sha256 == sha256(text.encode()).hexdigest()
    assert evidence.method_version == "claims-context-v1"
    assert evidence.source_metadata["offset_unit"] == "unicode_code_points"
    assert evidence.claim_id == claim.id and evidence.citation_id == citations[0].id
    assert link.support_status == "not_run" and link.confidence is None
    assert link.authority_id is None and claim.confidence is None
    assert result.status == StageStatus.COMPLETED
    assert result.coverage.evaluated == 1


def test_same_sentence_deduplicates_claim_preserving_distinct_links():
    text = "Equal treatment is required under 347 U.S. 483 and 576 U.S. 644."
    analysis, _, citations = context(text)
    citations[0].authority_id = uuid4()
    result = run(analysis)
    claims = [row for row in result.records if isinstance(row, Claim)]
    links = [row for row in result.records if isinstance(row, ClaimAuthorityLink)]
    assert len(claims) == 1 and len(links) == 2
    assert {row.claim_id for row in links} == {claims[0].id}
    assert {row.citation_id for row in links} == {row.id for row in citations}
    assert links[0].authority_id == citations[0].authority_id
    assert result.coverage.evaluated == 2


def test_persisted_occurrences_may_arrive_in_database_identity_order():
    analysis, _, citations = context("A rule follows 347 U.S. 483 and 576 U.S. 644.")
    analysis.review_citations = tuple(reversed(citations))
    assert run(analysis).coverage.evaluated == 2


@pytest.mark.parametrize("signal", ["See", "Cf.", "But see"])
def test_citation_only_sentence_retains_preceding_proposition(signal):
    text = (
        f"A warrant is required before entry. {signal} Brown v. Board, "
        "347 U.S. 483 (1954). Unrelated."
    )
    _, segments, citations = context(text)
    result = extract_claims(text, segments, citations)
    assert result.contexts[0].text == text[:text.index(" Unrelated")]
    assert result.contexts[0].context_kind == "preceding_sentence"


def test_short_references_remain_linked_without_inferred_authority():
    text = "A rule is stated in 347 U.S. 483. Id. at 484. A second rule follows 347 U.S. at 485."
    analysis, _, citations = context(text)
    result = run(analysis)
    links = [row for row in result.records if isinstance(row, ClaimAuthorityLink)]
    assert len(links) == len(citations) == 3
    assert all(row.authority_id is None and row.support_status == "not_run" for row in links)
    assert any(c.extraction_metadata["kind"] == "id" for c in citations)


def test_paragraph_and_pdf_page_anchors():
    text = "First rule follows 347 U.S. 483.\n\nSecond rule follows 576 U.S. 644."
    _, segments, citations = context(text)
    result = extract_claims(text, segments, citations)
    assert [row.segment_id for row in result.contexts] == [row.id for row in segments]
    assert [row.start for row in result.contexts] == [row.start for row in segments]
    # Service can preserve PDF anchors; the runner additionally validates canonical PDF spans.
    segments = tuple(s.model_copy(update={"page_number": index + 1})
                     for index, s in enumerate(segments))
    for index, citation in enumerate(citations):
        citation.page_number = index + 1
    assert [row.page_number for row in extract_claims(text, segments, citations).contexts] == [1, 2]


def test_legal_abbreviations_do_not_split_case_name_or_reporter():
    text = "The U.S. rule applies to Acme Inc. under Brown v. Board, 347 U.S. 483. Other text."
    _, segments, citations = context(text)
    claim = extract_claims(text, segments, citations).contexts[0]
    assert claim.text == text[:text.index(" Other")]


def test_runner_preserves_canonical_pdf_page_and_paragraph_locations():
    text = "First page text.\fThe second page rule follows 347 U.S. 483."
    digest = sha256(text.encode()).hexdigest()
    pages = [PageSpan(page_number=1, start=0, end=text.index("\f")),
             PageSpan(page_number=2, start=text.index("\f") + 1, end=len(text))]
    document = ExtractedDocument(
        text=text, input_sha256=digest, text_sha256=digest, pages=pages,
        paragraphs=segment(text, pages), method="pypdf-bounded-v1",
    )
    analysis, _, citations = context(text)
    segments = tuple(ReviewSegment(id=uuid4(), start=p.start, end=p.end, page_number=p.page_number)
                     for p in document.paragraphs)
    analysis.document_snapshot = document.model_dump(mode="json")
    analysis.review_segments = segments
    citations[0].segment_id = segments[1].id
    citations[0].page_number = 2
    claim = next(row for row in run(analysis).records if isinstance(row, Claim))
    assert claim.page_number == 2 and claim.segment_id == segments[1].id
    assert claim.start_offset == segments[1].start and claim.end_offset == segments[1].end


def test_runner_rejects_foreign_citation_owner_and_tampered_snapshot():
    analysis, _, citations = context("The rule follows 347 U.S. 483.")
    citations[0].analysis_id = uuid4()
    with pytest.raises(ValueError):
        run(analysis)
    citations[0].analysis_id = analysis.id
    analysis.document_snapshot["text_sha256"] = "0" * 64
    with pytest.raises(ValueError):
        run(analysis)


def test_paragraph_fallback_for_citation_only_initial_sentence():
    text = "347 U.S. 483."
    _, segments, citations = context(text)
    claim = extract_claims(text, segments, citations).contexts[0]
    assert claim.text == text and claim.context_kind == "paragraph"


def test_100_context_limit_is_partial_and_links_retained_ones():
    text = "\n\n".join(f"Rule number {i} follows 347 U.S. 483." for i in range(105))
    analysis, _, _ = context(text)
    result = run(analysis)
    assert len([row for row in result.records if isinstance(row, Claim)]) == 100
    assert len([row for row in result.records if isinstance(row, ClaimAuthorityLink)]) == 100
    assert result.status == StageStatus.PARTIAL
    assert result.coverage.evaluated == 100 and result.coverage.unavailable == 5
    assert result.coverage.eligible == 105 and result.coverage.truncated
    assert result.coverage.limitation


def test_upstream_truncation_and_absent_upstream_are_not_clean():
    analysis, _, _ = context("The rule follows 347 U.S. 483.")
    analysis.stage_states["citations"]["coverage"] = {"eligible": 205, "truncated": True}
    result = run(analysis)
    assert result.coverage.evaluated == 1 and result.coverage.unavailable == 204
    assert result.coverage.truncated and result.status == StageStatus.PARTIAL
    analysis, _, _ = context("No recognized citations here.")
    assert run(analysis).status == StageStatus.SKIPPED
    analysis.stage_states = {"citations": {"status": "failed"}}
    assert run(analysis).status == StageStatus.UNAVAILABLE


@pytest.mark.parametrize("field,value", [("start_offset", 0), ("raw_text", "tampered"),
                                         ("segment_id", uuid4()), ("page_number", 2)])
def test_tampered_citation_provenance_is_rejected(field, value):
    analysis, _, citations = context("The rule follows 347 U.S. 483.")
    setattr(citations[0], field, value)
    with pytest.raises(ValueError):
        run(analysis)


def test_cross_segment_context_keeps_full_original_span():
    text = "The rule follows 347 U.S.\n\n483 and applies here."
    analysis, _, citations = context(text)
    result = run(analysis)
    claim = next(row for row in result.records if isinstance(row, Claim))
    assert len(citations) == 1 and claim.text == text
    evidence = next(row for row in result.records if isinstance(row, EvidenceRecord))
    assert evidence.source_metadata["context_kind"] == "cross_segment"


def test_context_limit_rejects_unbounded_parameters():
    _, segments, citations = context("The rule follows 347 U.S. 483.")
    with pytest.raises(ValueError):
        extract_claims("The rule follows 347 U.S. 483.", segments, citations, max_claims=101)


def test_long_unicode_filing_bounds_cumulative_evidence_snapshot_bytes():
    text = "\n\n".join("😀" * 1800 + f" Rule {index} follows 347 U.S. 483." for index in range(50))
    analysis, _, _ = context(text)
    result = run(analysis)
    evidence = [row for row in result.records if isinstance(row, EvidenceRecord)]
    snapshot_bytes = len(json.dumps(text, ensure_ascii=False).encode("utf-8"))
    assert 0 < len(evidence) == MAX_SNAPSHOT_BYTES // snapshot_bytes < 50
    assert len(evidence) * snapshot_bytes <= MAX_SNAPSHOT_BYTES
    assert result.coverage.evaluated == len(evidence)
    assert result.coverage.unavailable == 50 - len(evidence)
    assert result.coverage.truncated and result.status == StageStatus.PARTIAL
