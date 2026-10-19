"""Original Unicode spans, cautious citation associations, and bounded string matching."""

import re

from rapidfuzz.fuzz import partial_ratio_alignment

from filingguard.db.models import Citation
from filingguard.modules.analyses.schemas import QuoteStatus
from filingguard.modules.quotes.schemas import (
    MAX_QUOTE_CHARS,
    MAX_SOURCE_CHARS,
    SEMANTIC_LIMITATION,
    SEMANTIC_METHOD,
    MeaningAlteration,
    QuoteAssociation,
    QuoteComparison,
    QuoteOccurrence,
    SemanticSimilarity,
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


_NEGATION_WORDS = frozenset(
    {"not", "no", "never", "none", "neither", "nor", "cannot", "without", "hardly", "scarcely"}
)
_MANDATORY_WORDS = frozenset({"shall", "must", "required", "mandatory"})
_PERMISSIVE_WORDS = frozenset({"may", "can", "permitted", "discretionary"})
_QUALIFIER_WORDS = ("unless", "except", "provided that", "excluding", "subject to", "only if")
_ANTONYM_PAIRS = (
    ("granted", "denied"),
    ("reversed", "affirmed"),
    ("guilty", "innocent"),
    ("valid", "invalid"),
    ("constitutional", "unconstitutional"),
    ("liable", "immune"),
    ("enforceable", "unenforceable"),
)
_STOPWORDS = frozenset(
    {
        "a",
        "an",
        "the",
        "and",
        "or",
        "of",
        "to",
        "in",
        "on",
        "for",
        "by",
        "as",
        "at",
        "from",
        "with",
        "that",
        "this",
        "these",
        "those",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "being",
        "it",
        "its",
        "their",
        "there",
    }
)
_TOKEN_RE = re.compile(r"\b[A-Za-z]+(?:'[A-Za-z]+)?\b")


def _word_tokens(text: str) -> set[str]:
    return set(_TOKEN_RE.findall(text.lower()))


def _negation_tokens(tokens: set[str]) -> set[str]:
    found = set(tokens & _NEGATION_WORDS)
    found.update(token for token in tokens if token.endswith("n't"))
    return found


def check_meaning_alteration(quote: str, source_passage: str) -> MeaningAlteration | None:
    """Detect changes in negation, modal obligations, omitted qualifiers, or antonyms."""
    q_tokens = _word_tokens(quote)
    s_tokens = _word_tokens(source_passage)

    # 1. Negation alteration
    q_neg = _negation_tokens(q_tokens)
    s_neg = _negation_tokens(s_tokens)
    if q_neg != s_neg:
        if q_neg - s_neg:
            words = ", ".join(sorted(q_neg - s_neg))
            return MeaningAlteration(
                kind="negation_inserted",
                severity="critical",
                title="Quotation alteration may reverse meaning: Negation added",
                description=(
                    f"The quotation inserts negation ({words}) not present in the source "
                    "passage, which may reverse the legal meaning or court's holding."
                ),
                details={"inserted_words": sorted(q_neg - s_neg)},
            )
        if s_neg - q_neg:
            words = ", ".join(sorted(s_neg - q_neg))
            return MeaningAlteration(
                kind="negation_omitted",
                severity="critical",
                title="Quotation alteration may reverse meaning: Negation omitted",
                description=(
                    f"The quotation omits negation ({words}) present in the source "
                    "passage, which may reverse the legal meaning or court's holding."
                ),
                details={"omitted_words": sorted(s_neg - q_neg)},
            )

    # 2. Modal verb / obligation alteration
    q_mand = q_tokens & _MANDATORY_WORDS
    q_perm = q_tokens & _PERMISSIVE_WORDS
    s_mand = s_tokens & _MANDATORY_WORDS
    s_perm = s_tokens & _PERMISSIVE_WORDS
    if (q_mand and s_perm and not (q_mand & s_mand)) or (
        q_perm and s_mand and not (q_perm & s_perm)
    ):
        q_mod = ", ".join(sorted(q_mand | q_perm))
        s_mod = ", ".join(sorted(s_mand | s_perm))
        return MeaningAlteration(
            kind="modal_altered",
            severity="high",
            title="Quotation alteration may alter meaning: Obligation altered",
            description=(
                f"The quotation changes obligation language ('{q_mod}' vs source '{s_mod}'); "
                "mandatory or permissive standards may be altered."
            ),
            details={
                "quote_modal": sorted(q_mand | q_perm),
                "source_modal": sorted(s_mand | s_perm),
            },
        )

    # 3. Antonym / contradictory terms
    for term_a, term_b in _ANTONYM_PAIRS:
        if (term_a in q_tokens and term_b in s_tokens) or (
            term_b in q_tokens and term_a in s_tokens
        ):
            w_q = term_a if term_a in q_tokens else term_b
            w_s = term_b if term_a in q_tokens else term_a
            return MeaningAlteration(
                kind="antonym_altered",
                severity="critical",
                title="Quotation alteration may reverse meaning: Contradictory term",
                description=(
                    f"The quotation contains an opposing term ('{w_q}' vs '{w_s}'), "
                    "directly altering the judicial disposition or finding."
                ),
                details={"quote_term": w_q, "source_term": w_s},
            )

    # 4. Ellipsis omitting qualifiers
    if "..." in quote or "…" in quote or "[. . .]" in quote or "[ ... ]" in quote:
        lower_source = source_passage.lower()
        lower_quote = quote.lower()
        for qual in _QUALIFIER_WORDS:
            if qual in lower_source and qual not in lower_quote:
                return MeaningAlteration(
                    kind="qualifier_omitted",
                    severity="high",
                    title="Quotation alteration may alter meaning: Exception or qualifier omitted",
                    description=(
                        f"The quotation ellipsis omits a key qualifier or exception ('{qual}') "
                        "present in the source authority passage."
                    ),
                    details={"omitted_qualifier": qual},
                )

    return None


def evaluate_semantic_similarity(quote: str, source_passage: str) -> SemanticSimilarity:
    """Local token-overlap review signal; never treated as exact quotation or legal meaning."""
    q_tokens = _word_tokens(quote)
    s_tokens = _word_tokens(source_passage)
    union = q_tokens | s_tokens
    score = round(len(q_tokens & s_tokens) / len(union), 4) if union else 0.0
    q_neg = _negation_tokens(q_tokens)
    s_neg = _negation_tokens(s_tokens)
    negation = q_neg != s_neg

    def content(tokens: set[str]) -> set[str]:
        return {
            token
            for token in tokens
            if token not in _STOPWORDS
            and token not in _NEGATION_WORDS
            and not token.endswith("n't")
        }

    q_content, s_content = content(q_tokens), content(s_tokens)
    omitted, inserted = s_content - q_content, q_content - s_content
    quote_len = max(len(q_tokens), 1)
    source_len = max(len(s_tokens), 1)
    length_ratio = min(quote_len, source_len) / max(quote_len, source_len)
    omitted_frac = len(omitted) / len(s_content) if s_content else 0.0
    omission = bool(omitted) and length_ratio >= 0.4 and (
        omitted_frac >= 0.15 or length_ratio >= 0.7
    )
    antonym = any(
        (term_a in q_tokens and term_b in s_tokens) or (term_b in q_tokens and term_a in s_tokens)
        for term_a, term_b in _ANTONYM_PAIRS
    )
    q_mand, q_perm = q_tokens & _MANDATORY_WORDS, q_tokens & _PERMISSIVE_WORDS
    s_mand, s_perm = s_tokens & _MANDATORY_WORDS, s_tokens & _PERMISSIVE_WORDS
    modal = (q_mand and s_perm and not (q_mand & s_mand)) or (
        q_perm and s_mand and not (q_perm & s_perm)
    )
    material_change = bool(negation or antonym or modal or (omitted and inserted))
    return SemanticSimilarity(
        score=score,
        method=SEMANTIC_METHOD,
        limitation=SEMANTIC_LIMITATION,
        negation=negation,
        omission=omission,
        material_change=material_change,
    )


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
    passage_text = source[left:right]
    ctx_left = left
    while ctx_left > 0 and source[ctx_left - 1] not in ".!?\n\f" and left - ctx_left < 200:
        ctx_left -= 1
    ctx_right = right
    while (
        ctx_right < len(source)
        and source[ctx_right] not in ".!?\n\f"
        and ctx_right - right < 200
    ):
        ctx_right += 1
    meaning_alt = check_meaning_alteration(quote, source[ctx_left:ctx_right])
    semantic = evaluate_semantic_similarity(quote, passage_text)
    reason = (
        meaning_alt.description
        if meaning_alt
        else (
            "String similarity does not establish equivalent meaning or legal support. "
            "String similarity is not meaning-preservation."
        )
    )
    return QuoteComparison(
        QuoteStatus.CLOSE if similarity >= 0.85 else QuoteStatus.NOT_FOUND,
        similarity,
        passage_text,
        left,
        right,
        reason,
        meaning_alt,
        semantic,
    )
