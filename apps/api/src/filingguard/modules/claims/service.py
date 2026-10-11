"""Conservative, deterministic citation contexts; no provider requests or verdicts."""

import re
from dataclasses import replace

from filingguard.db.models import Citation
from filingguard.modules.analyses.execution import ReviewSegment, citation_anchor
from filingguard.modules.claims.schemas import MAX_CLAIMS, ClaimContext, ClaimExtraction

# Periods in known citations are protected separately. These cover nearby case names
# and legal prose; an uncertain abbreviation keeps the larger context intact.
_ABBREVIATIONS = {
    "v", "vs", "id", "ibid", "cf", "e.g", "i.e", "no", "nos", "inc", "co", "corp",
    "ltd", "assn", "dept", "dr", "mr", "mrs", "ms", "jr", "sr", "st", "cir", "app",
    "supp", "dist", "ct", "jan", "feb", "mar", "apr", "jun", "jul", "aug", "sep",
    "sept", "oct", "nov", "dec",
}
_SIGNALS = {"see", "also", "but", "cf", "accord", "contra", "id", "ibid", "at", "supra"}


def _trim(text: str, start: int, end: int) -> tuple[int, int]:
    while start < end and text[start].isspace():
        start += 1
    while start < end and text[end - 1].isspace():
        end -= 1
    return start, end


def _sentences(text: str, segment: ReviewSegment, citations: tuple[Citation, ...]):
    """Keep boundaries outside citations and recognized abbreviations only."""
    cursor = segment.start
    spans = []
    boundaries = re.finditer(
        r'[.!?][\)\]"”’]*\s+(?=[\("“‘]*[A-Z])', text[segment.start:segment.end]
    )
    for match in boundaries:
        position = segment.start + match.start()
        if any(c.start_offset <= position < c.end_offset for c in citations):
            continue
        if text[position] == ".":
            token = re.search(r"[\w.]+$", text[segment.start:position])
            if token:
                value = token.group().lower()
                if value in _ABBREVIATIONS or "." in value or len(value) == 1:
                    continue
        end = segment.start + match.end()
        spans.append(_trim(text, cursor, end))
        cursor = end
    spans.append(_trim(text, cursor, segment.end))
    return [span for span in spans if span[0] < span[1]]


def _citation_only(text: str, start: int, end: int, citations: tuple[Citation, ...]) -> bool:
    if re.match(
        r"(?:But\s+see|See(?:\s+also)?|Cf\.|Accord|Contra)(?=\s)",
        text[start:end], re.IGNORECASE,
    ):
        return True
    pieces = []
    cursor = start
    for citation in citations:
        if start <= citation.start_offset and citation.end_offset <= end:
            pieces.append(text[cursor:citation.start_offset])
            cursor = citation.end_offset
    pieces.append(text[cursor:end])
    words = re.findall(r"[^\W\d_]+", " ".join(pieces), flags=re.UNICODE)
    return len([word for word in words if word.lower() not in _SIGNALS]) < 3


def extract_claims(
    text: str,
    segments: tuple[ReviewSegment, ...],
    citations: tuple[Citation, ...],
    *,
    max_claims: int = MAX_CLAIMS,
) -> ClaimExtraction:
    """Deduplicate exact contexts while retaining every linked occurrence.

    The caller validates snapshot/segment ownership. This function also checks
    slices and anchors so tampered local inputs cannot silently change context.
    """
    if type(max_claims) is not int or not 1 <= max_claims <= MAX_CLAIMS:
        raise ValueError("Invalid claim context limit")
    if not isinstance(text, str) or not text.strip() or len(text) > 100000:
        raise ValueError("Invalid claim source snapshot")
    if len(citations) > 200 or len({c.id for c in citations}) != len(citations):
        raise ValueError("Invalid claim citation context")
    previous_end = -1
    for citation in citations:
        start, end = citation.start_offset, citation.end_offset
        if (
            type(start) is not int or type(end) is not int
            or not previous_end <= start < end <= len(text)
            or citation.raw_text != text[start:end]
        ):
            raise ValueError("Claim citation span mismatch")
        anchor, _ = citation_anchor(segments, start, end)
        if citation.segment_id != anchor.id or citation.page_number != anchor.page_number:
            raise ValueError("Claim citation anchor mismatch")
        previous_end = end
    contexts = {}
    omitted = []
    sentence_cache = {}
    for citation in citations:
        anchor, _ = citation_anchor(segments, citation.start_offset, citation.end_offset)
        start, end = anchor.start, anchor.end
        kind = "paragraph"
        if citation.end_offset > anchor.end:
            ending = next((s for s in segments if s.start < citation.end_offset <= s.end), None)
            if ending is None:
                raise ValueError("Cross-segment citation has no ending anchor")
            end = ending.end
            kind = "cross_segment"
        else:
            if anchor.id not in sentence_cache:
                sentence_cache[anchor.id] = _sentences(text, anchor, citations)
            spans = sentence_cache[anchor.id]
            for index, (left, right) in enumerate(spans):
                if left <= citation.start_offset and citation.end_offset <= right:
                    start, end = left, right
                    kind = "sentence"
                    if _citation_only(text, start, end, citations):
                        if index:
                            start = spans[index - 1][0]
                            kind = "preceding_sentence"
                        else:
                            start, end = anchor.start, anchor.end
                            kind = "paragraph"
                    break
        key = (start, end)
        if key in contexts:
            contexts[key] = replace(
                contexts[key], citation_ids=(*contexts[key].citation_ids, citation.id)
            )
        elif len(contexts) < max_claims:
            contexts[key] = ClaimContext(
                text=text[start:end], start=start, end=end, segment_id=anchor.id,
                page_number=anchor.page_number, citation_ids=(citation.id,), context_kind=kind,
            )
        else:
            omitted.append(citation.id)
    return ClaimExtraction(
        contexts=tuple(contexts.values()), detected_count=len(citations),
        associated_count=len(citations) - len(omitted), omitted_citation_ids=tuple(omitted),
    )
