"""Original Unicode spans, cautious citation associations, and bounded string matching."""

import re

from rapidfuzz.fuzz import partial_ratio_alignment

from filingguard.db.models import Citation
from filingguard.modules.analyses.schemas import QuoteStatus
from filingguard.modules.quotes.schemas import (
    MAX_QUOTE_CHARS,
    MAX_SOURCE_CHARS,
    QuoteAssociation,
    QuoteComparison,
    QuoteOccurrence,
)

_BLOCK = re.compile(r"(?m)^(?: {4,}|\t|> )\S[^\n\f]*(?:\n(?: {4,}|\t|> )\S[^\n\f]*)*")


def extract_quotes(text: str) -> tuple[QuoteOccurrence, ...]:
    """Retain content spans; indentation/Markdown blocks are explicitly heuristic."""
    found = []
    # Scan once: repeated unmatched curly openers must not cause regex backtracking.
    opener, closing = None, None
    for index, char in enumerate(text):
        if char == "\f":
            opener, closing = None, None
            continue
        if opener is None:
            if char in {'"', "“", "‘"} and not (
                char == "‘" and index > 0 and text[index - 1].isalnum()
            ):
                opener, closing = index, {'"': '"', "“": "”", "‘": "’"}[char]
            continue
        if char != closing or (
            closing == "’" and index + 1 < len(text) and text[index + 1].isalnum()
        ):
            continue
        start, end = opener + 1, index
        opener, closing = None, None
        while start < end and text[start].isspace():
            start += 1
        while end > start and text[end - 1].isspace():
            end -= 1
        if start < end and any(char.isalnum() for char in text[start:end]):
            found.append(QuoteOccurrence(text[start:end], start, end, "delimited"))
    for match in _BLOCK.finditer(text):
        start, end = match.span()
        if any(item.start < end and item.end > start for item in found):
            continue
        start += len(re.match(r"(?: {4,}|\t|> )", match.group()).group())
        if len(text[start:end].split()) >= 4:
            found.append(QuoteOccurrence(text[start:end], start, end, "block_heuristic"))
    return tuple(sorted(found, key=lambda item: item.start))


def associate_quote(
    quote: QuoteOccurrence, citations: tuple[Citation, ...], text: str
) -> QuoteAssociation:
    """A sentence-local unique authority may associate; distinct candidates stay unresolved."""
    candidates = []
    for citation in citations:
        start, end = citation.start_offset, citation.end_offset
        if (
            not isinstance(start, int)
            or not isinstance(end, int)
            or not 0 <= start < end <= len(text)
        ):
            continue
        if end <= quote.start:
            gap_start, gap_end = end, quote.start
        elif start >= quote.end:
            gap_start, gap_end = quote.end, start
        else:
            continue
        gap = text[gap_start:gap_end]
        # Reporter punctuation inside intervening citations is not a sentence boundary.
        for other in sorted(citations, key=lambda row: row.start_offset or 0, reverse=True):
            if (
                isinstance(other.start_offset, int)
                and isinstance(other.end_offset, int)
                and gap_start <= other.start_offset < other.end_offset <= gap_end
            ):
                left, right = other.start_offset - gap_start, other.end_offset - gap_start
                gap = gap[:left] + " " * (right - left) + gap[right:]
        gap = re.sub(r"\bv\.", "v", gap)
        if end <= quote.start:
            # An explicit attribution can refer back to the immediately preceding
            # cited sentence. Keep the same 300-character/paragraph bounds and
            # reject additional sentence boundaries or distinct candidates.
            gap = re.sub(
                r"[.!?](\s+The [Cc]ourt (?:stated|held|explained|said|wrote|observed):\s*)$",
                r" \1",
                gap.rstrip('"“'),
            )
        # Closing quote punctuation does not create a new sentence before its citation.
        gap = gap.lstrip('"”’') if start >= quote.end else gap
        if start >= quote.end:
            gap = re.sub(r"^\s*[.!?]\s*", "", gap, count=1)
        if len(gap) > 300 or re.search(r"[.!?\f]|\n\s*\n", gap):
            continue
        candidates.append(citation)
    ids = tuple(item.id for item in candidates)
    if not candidates:
        return QuoteAssociation(None, None, "No unique nearby citation was detected.")
    keys = {item.authority_id or item.id for item in candidates}
    if len(keys) != 1:
        return QuoteAssociation(
            None, None, "Multiple nearby citation candidates are ambiguous.", ids
        )
    citation = min(
        candidates,
        key=lambda item: min(
            abs(item.start_offset - quote.end), abs(item.end_offset - quote.start)
        ),
    )
    if citation.verification_status != "verified" or citation.authority_id is None:
        return QuoteAssociation(
            citation.id, None, "Associated citation has no verified source.", ids
        )
    return QuoteAssociation(citation.id, citation.authority_id, candidates=ids)


def _normalized_map(text: str) -> tuple[str, list[int]]:
    chars, offsets = [], []
    for index, char in enumerate(text):
        for folded in char.casefold():
            if folded.isalnum():
                chars.append(folded)
                offsets.append(index)
    return "".join(chars), offsets


def compare_quote(quote: str, source: str) -> QuoteComparison:
    """Similarity is a string signal only; every passage slices the original source."""
    if not source:
        return QuoteComparison(QuoteStatus.SOURCE_UNAVAILABLE, reason="Source text is unavailable.")
    if len(quote) > MAX_QUOTE_CHARS or len(source) > MAX_SOURCE_CHARS:
        return QuoteComparison(
            QuoteStatus.SOURCE_UNAVAILABLE, reason="Quote or source exceeds comparison limits."
        )
    if not quote or not any(char.isalnum() for char in quote):
        raise ValueError("Quote must contain text")
    start = source.find(quote)
    if start >= 0:
        return QuoteComparison(QuoteStatus.EXACT, 1.0, quote, start, start + len(quote))
    normalized, _ = _normalized_map(quote)
    source_normalized, offsets = _normalized_map(source)
    start = source_normalized.find(normalized)
    if start >= 0:
        left, right = offsets[start], offsets[start + len(normalized) - 1] + 1
        return QuoteComparison(QuoteStatus.NORMALIZED, 1.0, source[left:right], left, right)
    if len(normalized) < 20 or not source_normalized:
        return QuoteComparison(
            QuoteStatus.NOT_FOUND,
            reason="No match; quote is too short for reliable fuzzy matching.",
        )
    alignment = partial_ratio_alignment(normalized, source_normalized)
    if alignment is None or alignment.dest_end <= alignment.dest_start:
        return QuoteComparison(QuoteStatus.NOT_FOUND, reason="No comparable source passage found.")
    left, right = offsets[alignment.dest_start], offsets[alignment.dest_end - 1] + 1
    # Prevent whitespace/punctuation-heavy sources from producing oversized excerpts.
    if right - left > MAX_QUOTE_CHARS * 2:
        return QuoteComparison(
            QuoteStatus.SOURCE_UNAVAILABLE, reason="Closest source passage exceeds excerpt limits."
        )
    similarity = alignment.score / 100
    return QuoteComparison(
        QuoteStatus.CLOSE if similarity >= 0.85 else QuoteStatus.NOT_FOUND,
        similarity,
        source[left:right],
        left,
        right,
        "String similarity does not establish equivalent meaning or legal support.",
    )
