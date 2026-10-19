"""Focused original-text citation extraction checks."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from filingguard.modules.citations.schemas import CitationOccurrence
from filingguard.modules.citations.service import extract_citations

FIXTURE = Path(__file__).resolve().parents[4] / "data/demo/curated-v1/filing.txt"


def test_curated_filing_retains_five_case_occurrences() -> None:
    text = FIXTURE.read_text(encoding="utf-8")
    result = extract_citations(text)
    cases = [item for item in result.occurrences if item.extraction.kind == "full_case"]

    assert len(cases) == 5
    assert [item.raw_text for item in cases].count("347 U.S. 483") == 2
    assert "999 U.S. 999" in [item.raw_text for item in cases]
    assert result.detected_count == 5
    assert not result.truncated
    assert all(item.extraction.support == "recognized" for item in cases)
    assert all(text[item.start : item.end] == item.raw_text for item in result.occurrences)


def test_unicode_and_newline_offsets_remain_original() -> None:
    text = "😀 Café\nBrown v. Board, 347 U.S. 483.\n347 U.S. 483"
    result = extract_citations(text)

    assert [item.start for item in result.occurrences] == [text.index("347"), text.rindex("347")]
    assert [item.raw_text for item in result.occurrences] == ["347 U.S. 483"] * 2
    assert all(text[item.start : item.end] == item.raw_text for item in result.occurrences)


def test_normalization_does_not_change_original_span() -> None:
    text = "😀\n347 U. S. 483"
    occurrence = extract_citations(text).occurrences[0]

    assert occurrence.start == 2
    assert occurrence.raw_text == text[occurrence.start : occurrence.end] == "347 U. S. 483"
    assert occurrence.normalized_text == "347 U.S. 483"


@pytest.mark.parametrize("separator", ["\n", "\n\n", "\f", "  "])
def test_split_reporter_formats_are_retained_as_unsupported_candidates(separator) -> None:
    text = "347 U.S." + separator + "483"
    occurrence = extract_citations(text).occurrences[0]
    assert occurrence.raw_text == text
    assert occurrence.start == 0 and occurrence.end == len(text)
    assert occurrence.extraction.support in {"recognized", "unsupported"}


def test_references_remain_unresolved() -> None:
    text = "Brown v. Board, 347 U.S. 483. Id. at 484. Brown, 347 U.S. at 485. Brown, supra, at 2."
    result = extract_citations(text)
    references = [item for item in result.occurrences if item.extraction.kind != "full_case"]

    assert {item.extraction.kind for item in references} == {"id", "short_case", "supra"}
    assert all(item.extraction.support == "unresolved_reference" for item in references)
    assert all(item.normalized_text is None for item in references)
    assert all(text[item.start : item.end] == item.raw_text for item in references)


def test_ambiguous_reporter_keeps_candidates() -> None:
    result = extract_citations("1 Wash. 1")
    occurrence = result.occurrences[0]

    assert occurrence.extraction.kind == "full_case"
    assert occurrence.extraction.support == "ambiguous"
    assert occurrence.normalized_text is None
    assert "Wash." in occurrence.extraction.reporter_candidates
    assert len(occurrence.extraction.reporter_candidates) > 1


def test_unsupported_law_journal_and_unknown_reporter() -> None:
    text = "42 U.S.C. § 1983; 123 Yale L.J. 456; 123 QQQ 456"
    result = extract_citations(text)
    by_kind = {item.extraction.kind: item for item in result.occurrences}

    assert {"law", "journal", "reporter_candidate"} <= by_kind.keys()
    assert all(item.extraction.support == "unsupported" for item in result.occurrences)
    assert by_kind["law"].normalized_text is None
    assert by_kind["reporter_candidate"].raw_text == "123 QQQ 456"
    assert all(text[item.start : item.end] == item.raw_text for item in result.occurrences)
    assert "false positives" in result.limitation


def test_no_citations() -> None:
    result = extract_citations("A filing without a citation.")
    assert result.occurrences == []
    assert result.detected_count == 0
    assert not result.truncated


@pytest.mark.parametrize("text", ["", " \n\t", None])
def test_invalid_input(text: str | None) -> None:
    with pytest.raises(ValueError):
        extract_citations(text)  # type: ignore[arg-type]


def test_input_over_limit() -> None:
    with pytest.raises(ValueError):
        extract_citations("x" * 100_001)


def test_occurrence_contract_rejects_bad_span() -> None:
    with pytest.raises(ValidationError):
        CitationOccurrence.model_validate(
            {
                "raw_text": "347 U.S. 483",
                "normalized_text": None,
                "start": 2,
                "end": 5,
                "extraction": {
                    "parser_version": "2.7.8",
                    "kind": "full_case",
                    "support": "recognized",
                },
            }
        )


def test_first_200_retained_and_total_count_reported() -> None:
    text = "; ".join(["347 U.S. 483"] * 205)
    result = extract_citations(text)

    assert result.detected_count == 205
    assert len(result.occurrences) == 200
    assert result.truncated
    assert result.occurrences[-1].start == text.index("347 U.S. 483", result.occurrences[-2].end)
    assert all(text[item.start : item.end] == item.raw_text for item in result.occurrences)
