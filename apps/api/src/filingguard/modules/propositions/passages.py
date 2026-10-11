"""Deterministic lexical retrieval with contiguous surrounding qualifications."""

import hashlib
import re
from uuid import uuid4

from filingguard.integrations.providers.passages import MAX_SOURCE_PASSAGE, prepare_passage
from filingguard.modules.propositions.schemas import SourcePassage

METHOD_VERSION = "lexical-qualified-windows-v2"
_STOP = frozenset(
    (
        "a an and are as at be by for from has have in is it of on or that "
        "the this to was were with"
    ).split()
)

# Expand related forms without erasing negation from the original evidence text.
_FAMILIES = (
    frozenset({"school", "schools", "education", "educational"}),
    frozenset({"equal", "unequal", "equality", "inequality"}),
    frozenset({"segregation", "segregated", "separate", "separated"}),
)


def _terms(text):
    terms = {t.lower() for t in re.findall(r"[A-Za-z]{3,}", text)} - _STOP
    for family in _FAMILIES:
        if terms & family:
            terms |= family
    return terms


def select_passages(source: str, claim: str) -> tuple[SourcePassage, ...]:
    """Select at most two windows, <=12000 total code points, without normalization.

    Rankings are retrieval heuristics, not a determination of source support. A window
    includes 1200 characters before/after its matching paragraph, retaining caveats.
    Long paragraphs are centered on the first matching term; clipping is disclosed.
    """
    if not source or len(source) > 4 * 1024 * 1024:
        return ()
    terms = _terms(claim)
    if not terms:
        return ()
    candidates = []
    for paragraph in re.finditer(r"[^\n]+(?:\n(?!\n)[^\n]+)*", source):
        tokens = {t.lower() for t in re.findall(r"[A-Za-z]{3,}", paragraph.group())}
        score = len(terms & tokens)
        if score and re.search(
            r"\b(?:we (?:hold|conclude)|the court (?:holds|concludes))\b", paragraph.group(), re.I
        ):
            score += 3
        if score:
            first = next(
                t
                for t in re.finditer(r"[A-Za-z]{3,}", paragraph.group())
                if t.group().lower() in terms
            )
            center = paragraph.start() + first.start()
            start = max(0, min(paragraph.start() - 1200, center))
            end = min(len(source), paragraph.end() + 1200)
            clipped = end - start > 6000
            if clipped:
                start = max(start, center - 1500)
                end = min(end, start + 6000)
            candidates.append((score, start, end, clipped))
    selected = []
    sha = hashlib.sha256(source.encode()).hexdigest()
    for _, start, end, clipped in sorted(candidates, key=lambda item: (-item[0], item[1])):
        if any(start < p.end and end > p.start for p in selected):
            continue
        passage = prepare_passage(source, start, end, filing=False)
        selected.append(
            SourcePassage(
                str(uuid4()),
                passage.text,
                passage.original_start,
                passage.original_end,
                sha,
                clipped or passage.truncated,
            )
        )
        if len(selected) == 2:
            break
    assert sum(len(p.text) for p in selected) <= MAX_SOURCE_PASSAGE
    return tuple(selected)
