"""Deterministic lexical retrieval with contiguous surrounding qualifications."""

import hashlib
import re
from uuid import uuid4

from filingguard.integrations.providers.passages import MAX_SOURCE_PASSAGE, prepare_passage
from filingguard.modules.propositions.schemas import SourcePassage

METHOD_VERSION = "lexical-qualified-multi-passage-v3"
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
    """Select up to four qualified windows, <=12000 total code points, without normalization.

    Rankings are retrieval heuristics, not a determination of source support. A window
    includes surrounding context around its matching paragraph to retain caveats and exceptions.
    For opinions exceeding 15,000 characters, structural candidate diversity across early,
    middle, and late sections ensures comprehensive opinion coverage within the character budget.
    """
    if not source or len(source) > 4 * 1024 * 1024:
        return ()
    terms = _terms(claim)
    if not terms:
        return ()

    is_long = len(source) > 15000
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
            if is_long:
                start = max(0, min(paragraph.start() - 1000, center))
                end = min(len(source), paragraph.end() + 1000)
                clipped = end - start > 3000
                if clipped:
                    start = max(start, center - 1200)
                    end = min(end, start + 3000)
                zone = min(2, int(paragraph.start() / (len(source) / 3)))
            else:
                start = max(0, min(paragraph.start() - 1200, center))
                end = min(len(source), paragraph.end() + 1200)
                clipped = end - start > 6000
                if clipped:
                    start = max(start, center - 1500)
                    end = min(end, start + 6000)
                zone = 0
            candidates.append((score, start, end, clipped, zone))

    sorted_candidates = sorted(candidates, key=lambda item: (-item[0], item[1]))
    selected: list[SourcePassage] = []
    sha = hashlib.sha256(source.encode()).hexdigest()

    def try_add(candidate: tuple[int, int, int, bool, int]) -> bool:
        _, start, end, clipped, _ = candidate
        if any(start < p.end and end > p.start for p in selected):
            return False
        used = sum(len(p.text) for p in selected)
        rem = MAX_SOURCE_PASSAGE - used
        if rem <= 0:
            return False
        if end - start > rem:
            if rem >= 1200:
                end = start + rem
                clipped = True
            else:
                return False
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
        return True

    if is_long and sorted_candidates:
        # 1. Primary anchor: globally highest scoring candidate
        try_add(sorted_candidates[0])
        covered_zones = {sorted_candidates[0][4]}

        # 2. Structural diversity: represent other sections (early, middle, late)
        for z in (0, 1, 2):
            if z not in covered_zones and len(selected) < 4:
                for cand in sorted_candidates:
                    if cand[4] == z:
                        if try_add(cand):
                            covered_zones.add(z)
                            break

        # 3. Fill remaining slots up to 4 with next best non-overlapping candidates
        for cand in sorted_candidates:
            if len(selected) >= 4:
                break
            try_add(cand)
    else:
        for cand in sorted_candidates:
            if len(selected) >= 4:
                break
            try_add(cand)

    assert sum(len(p.text) for p in selected) <= MAX_SOURCE_PASSAGE
    return tuple(selected)
