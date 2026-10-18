"""Synthetic quote controls: original spans, uncertainty and immutable source lineage."""

import time
from datetime import UTC, datetime
from hashlib import sha256
from uuid import uuid4

import pytest

from filingguard.db.models import Analysis, Authority, Citation, EvidenceRecord, Finding, Quote
from filingguard.integrations.providers.runtime import ProviderBudget
from filingguard.modules.analyses.execution import ReviewSegment
from filingguard.modules.analyses.schemas import QuoteStatus, StageName, StageStatus
from filingguard.modules.quotes.runner import quotes_stage
from filingguard.modules.quotes.schemas import MAX_QUOTE_CHARS, MAX_SOURCE_CHARS
from filingguard.modules.quotes.service import associate_quote, compare_quote, extract_quotes


def context(text, source="Equal access is a fundamental public right."):
    analysis = Analysis(
        id=uuid4(),
        mode="live",
        document_name="Synthetic test",
        document_sha256=sha256(text.encode()).hexdigest(),
    )
    analysis.document_snapshot = {
        "text": text,
        "input_sha256": analysis.document_sha256,
        "text_sha256": analysis.document_sha256,
        "pages": [],
        "method": "original-text-v1",
        "paragraphs": [
            {"paragraph_index": 0, "text": text, "start": 0, "end": len(text), "page_number": None}
        ],
    }
    analysis.review_segments = (ReviewSegment(id=uuid4(), start=0, end=len(text)),)
    authority = Authority(
        id=uuid4(),
        analysis_id=analysis.id,
        source="synthetic_test",
        external_id="123",
        source_url="https://www.courtlistener.com/opinion/123/",
        retrieved_at=datetime.now(UTC),
        opinion_text_available=True,
        opinion_text=source,
        source_sha256=sha256(source.encode()).hexdigest(),
        source_metadata={"provenance": "synthetic"},
    )
    citation = Citation(
        id=uuid4(),
        analysis_id=analysis.id,
        segment_id=analysis.review_segments[0].id,
        raw_text="123 U.S. 456",
        start_offset=text.index("123 U.S. 456"),
        end_offset=text.index("123 U.S. 456") + 12,
        authority_id=authority.id,
        verification_status="verified",
    )
    # Citation offsets must reflect the source string, regardless of reporter formatting.
    citation.end_offset = citation.start_offset + len(citation.raw_text)
    analysis.review_citations = (citation,)
    analysis.review_authorities = (authority,)
    return analysis, authority, citation


def run(analysis):
    return quotes_stage(analysis, ProviderBudget(time.monotonic() + 30))


@pytest.mark.parametrize(
    "text,expected",
    [
        ('😀 The court said "Café rights endure." 123 U.S. 456', "Café rights endure."),
        ("The court said “Café rights endure.” 123 U.S. 456", "Café rights endure."),
        ("The court said ‘Café rights endure.’ 123 U.S. 456", "Café rights endure."),
        (
            "The court states:\n    Equal access is a fundamental public right.\n123 U.S. 456",
            "Equal access is a fundamental public right.",
        ),
        (
            "> Equal access is a fundamental public right.\n123 U.S. 456",
            "Equal access is a fundamental public right.",
        ),
    ],
)
def test_quote_extraction_original_unicode_spans(text, expected):
    result = extract_quotes(text)
    assert len(result) == 1
    assert result[0].text == expected
    assert text[result[0].start : result[0].end] == expected


def test_benign_apostrophes_and_unclosed_quotes_are_not_quotations():
    assert not extract_quotes("A person's rights and don’t surrender. An unfinished “quote.")


def test_curly_single_quote_preserves_internal_possessive_apostrophe():
    text = "‘A person’s rights endure.’ 123 U.S. 456"
    quote = extract_quotes(text)[0]
    assert quote.text == "A person’s rights endure."
    assert text[quote.start : quote.end] == quote.text


def test_unmatched_delimiter_maximum_input_is_a_bounded_scan():
    assert not extract_quotes("“" * 100000)


def test_block_and_delimited_quote_do_not_duplicate():
    assert len(extract_quotes('    "Equal access is a fundamental public right."')) == 1


@pytest.mark.parametrize(
    "quote,source,status",
    [
        (
            "Equal access is a fundamental public right.",
            "Header. Equal access is a fundamental public right. Footer.",
            QuoteStatus.EXACT,
        ),
        (
            "EQUAL access is a fundamental public right!",
            "Equal\naccess is a fundamental public right.",
            QuoteStatus.NORMALIZED,
        ),
        ("strasse rights endure", "😀 Straße rights endure", QuoteStatus.NORMALIZED),
        (
            "Equal access is not a fundamental public right.",
            "Equal access is a fundamental public right.",
            QuoteStatus.CLOSE,
        ),
        (
            "Equal access... public right.",
            "Equal access is a fundamental public right.",
            QuoteStatus.NOT_FOUND,
        ),
        (
            "The moon is made of luminous cheese and orbiting pebbles.",
            "Equal access is a fundamental public right.",
            QuoteStatus.NOT_FOUND,
        ),
    ],
)
def test_comparison_order_and_original_offsets(quote, source, status):
    comparison = compare_quote(quote, source)
    assert comparison.status == status
    if comparison.passage is not None:
        assert source[comparison.source_start : comparison.source_end] == comparison.passage
    if status == QuoteStatus.CLOSE:
        assert "meaning" in comparison.reason


def test_short_unmatched_quote_does_not_receive_fuzzy_certification():
    result = compare_quote("rights", "right")
    assert result.status == QuoteStatus.NOT_FOUND
    assert result.similarity is None


def test_empty_and_oversized_source_are_explicitly_unavailable():
    assert compare_quote("rights", "").status == QuoteStatus.SOURCE_UNAVAILABLE
    assert (
        compare_quote("rights", "a" * (MAX_SOURCE_CHARS + 1)).status
        == QuoteStatus.SOURCE_UNAVAILABLE
    )
    assert compare_quote("a" * (MAX_QUOTE_CHARS + 1), "a").status == QuoteStatus.SOURCE_UNAVAILABLE


def test_exact_runner_has_document_and_source_lineage():
    text = "😀 “Equal access is a fundamental public right.” 123 U.S. 456"
    analysis, authority, citation = context(
        text, "😀 Prefix Equal access is a fundamental public right."
    )
    result = run(analysis)
    assert result.status == StageStatus.COMPLETED
    result.validate(StageName.QUOTES)
    quote = next(row for row in result.records if isinstance(row, Quote))
    assert quote.match_status == "exact" and quote.citation_id == citation.id
    assert text[quote.start_offset : quote.end_offset] == quote.quote_text
    evidence = [row for row in result.records if isinstance(row, EvidenceRecord)]
    assert len(evidence) == 2
    for row in evidence:
        assert row.analysis_id == analysis.id and row.quote_id == quote.id
        assert row.snapshot_text[row.source_start_offset : row.source_end_offset] == row.excerpt
        assert sha256(row.snapshot_text.encode()).hexdigest() == row.source_sha256
    source = next(row for row in evidence if row.source_type == "opinion_text")
    assert source.authority_id == authority.id and source.source_start_offset > 0
    assert result.coverage.evaluated == 1


def test_courtlistener_provider_label_maps_to_live_evidence_provenance():
    analysis, authority, _ = context("“Equal access is a fundamental public right.” 123 U.S. 456")
    authority.source_metadata = {"provenance": "courtlistener_api_v4"}
    result = run(analysis)
    assert result.status == StageStatus.COMPLETED
    source = next(
        row
        for row in result.records
        if isinstance(row, EvidenceRecord) and row.source_type == "opinion_text"
    )
    assert source.source_metadata["provenance"] == "live"
    assert source.source_metadata["provider_provenance"] == "courtlistener_api_v4"


@pytest.mark.parametrize("missing", ["text", "hash", "url", "time", "external_id"])
def test_source_unavailable_does_not_become_not_found(missing):
    analysis, authority, _ = context("“Equal access is a fundamental public right.” 123 U.S. 456")
    if missing == "text":
        authority.opinion_text_available = False
    else:
        setattr(
            authority,
            {
                "hash": "source_sha256",
                "url": "source_url",
                "time": "retrieved_at",
                "external_id": "external_id",
            }[missing],
            None,
        )
    result = run(analysis)
    assert result.status == StageStatus.PARTIAL
    assert result.coverage.unavailable == 1 and result.coverage.evaluated == 0
    quote = next(row for row in result.records if isinstance(row, Quote))
    assert quote.match_status == "source_unavailable" and quote.similarity is None


def test_multiple_nearby_authorities_never_select_first_arbitrarily():
    text = "“Equal access is a fundamental public right.” 123 U.S. 456; 222 U.S. 333"
    analysis, _, _ = context(text)
    second = Citation(
        id=uuid4(),
        analysis_id=analysis.id,
        start_offset=text.index("222"),
        end_offset=len(text),
        authority_id=uuid4(),
        verification_status="verified",
    )
    analysis.review_citations += (second,)
    occurrence = extract_quotes(text)[0]
    association = associate_quote(occurrence, analysis.review_citations, text)
    assert association.citation_id is None and association.authority_id is None
    assert len(association.candidates) == 2
    result = run(analysis)
    assert next(row for row in result.records if isinstance(row, Quote)).citation_id is None


def test_new_sentence_does_not_associate_unrelated_citation():
    text = "“Equal access is a fundamental public right.” Another assertion. 123 U.S. 456"
    analysis, _, _ = context(text)
    association = associate_quote(extract_quotes(text)[0], analysis.review_citations, text)
    assert association.citation_id is None


def test_explicit_court_attribution_preserves_prior_citation():
    text = '123 U.S. 456 establishes equal access. The Court stated: "Equal access is a right."'
    analysis, _, citation = context(text)
    assert associate_quote(
        extract_quotes(text)[0], analysis.review_citations, text
    ).citation_id == (citation.id)


@pytest.mark.parametrize(
    "bridge",
    [
        "Other unrelated assertion. The Court stated: ",
        "\n\nThe Court stated: ",
        "The opponent stated: ",
    ],
)
def test_attribution_does_not_cross_unrelated_or_paragraph_boundaries(bridge):
    text = "123 U.S. 456 establishes equal access. " + bridge + '"Equal access is a right."'
    analysis, _, _ = context(text)
    assert (
        associate_quote(extract_quotes(text)[0], analysis.review_citations, text).citation_id
        is None
    )


def test_case_name_between_quotation_and_citation_is_supported():
    text = "“Equal access is a fundamental public right.” Brown v. Board, 123 U.S. 456"
    analysis, _, citation = context(text)
    assert (
        associate_quote(extract_quotes(text)[0], analysis.review_citations, text).citation_id
        == citation.id
    )


def test_missing_and_ambiguous_sources_have_explanations_and_no_fuzzy_score():
    analysis, _, citation = context("“Equal access is a fundamental public right.” 123 U.S. 456")
    citation.verification_status = "ambiguous"
    result = run(analysis)
    quote = next(row for row in result.records if isinstance(row, Quote))
    assert quote.match_status == "source_unavailable"
    assert quote.closest_passage is None and quote.similarity is None
    assert (
        "verified source"
        in next(row for row in result.records if isinstance(row, Finding)).description
    )


def test_cap_preserves_true_pending_coverage():
    text = " ".join(["“Equal access is a fundamental public right.”"] * 51) + " 123 U.S. 456"
    analysis, _, _ = context(text)
    result = run(analysis)
    assert result.coverage.eligible == 51
    assert result.coverage.pending == 1 and result.coverage.truncated
    assert result.status == StageStatus.PARTIAL
    assert len([row for row in result.records if isinstance(row, Quote)]) == 50
    assert len(result.records) <= 200


def test_foreign_authority_is_rejected_before_comparison():
    analysis, authority, _ = context("“Equal access is a fundamental public right.” 123 U.S. 456")
    authority.analysis_id = uuid4()
    with pytest.raises(ValueError, match="another analysis"):
        run(analysis)


def test_no_quotes_is_skipped():
    analysis, _, _ = context("No quoted statement. 123 U.S. 456")
    result = run(analysis)
    assert result.status == StageStatus.SKIPPED and not result.records


def test_meaning_alteration_negation_inserted_escalates_to_critical():
    text = '“Equal access is not a fundamental public right.” 123 U.S. 456'
    analysis, _, _ = context(text, source="Equal access is a fundamental public right.")
    result = run(analysis)
    finding = next(row for row in result.records if isinstance(row, Finding))
    assert finding.severity == "critical"
    assert "Negation added" in finding.title
    assert "reverse the legal meaning" in finding.description


def test_meaning_alteration_negation_omitted_escalates_to_critical():
    text = '“Discrimination is permitted under the Fourteenth Amendment.” 123 U.S. 456'
    analysis, _, _ = context(
        text, source="Discrimination is not permitted under the Fourteenth Amendment."
    )
    result = run(analysis)
    finding = next(row for row in result.records if isinstance(row, Finding))
    assert finding.severity == "critical"
    assert "Negation omitted" in finding.title


def test_meaning_alteration_modal_obligation_altered_escalates_to_high():
    text = '“The court must consider equitable factors.” 123 U.S. 456'
    analysis, _, _ = context(text, source="The court may consider equitable factors.")
    result = run(analysis)
    finding = next(row for row in result.records if isinstance(row, Finding))
    assert finding.severity == "high"
    assert "Obligation altered" in finding.title


def test_meaning_alteration_ellipsis_omitting_qualifier_escalates_to_high():
    text = '“Notice is required before termination ... to all occupants.” 123 U.S. 456'
    analysis, _, _ = context(
        text,
        source="Notice is required before termination except in emergencies to all occupants.",
    )
    result = run(analysis)
    finding = next(row for row in result.records if isinstance(row, Finding))
    assert finding.severity == "high"
    assert "Exception or qualifier omitted" in finding.title
    assert "except" in finding.description


def test_meaning_alteration_antonym_contradictory_term_escalates_to_critical():
    text = '“The preliminary injunction is denied.” 123 U.S. 456'
    analysis, _, _ = context(text, source="The preliminary injunction is granted.")
    result = run(analysis)
    finding = next(row for row in result.records if isinstance(row, Finding))
    assert finding.severity == "critical"
    assert "Contradictory term" in finding.title

