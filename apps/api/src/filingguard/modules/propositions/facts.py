"""Heuristic filing-versus-source fact comparison; never invents legal analogies."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

from filingguard.modules.propositions.schemas import SourcePassage

METHOD_VERSION = "filing-source-fact-compare-v1"
LIMITATION = (
    "Heuristic review signal from dates, named parties, and numeric holdings in "
    "the filing excerpt versus selected source passages. Missing source facts are "
    "insufficient or unavailable, not a pass. This is not a legal analogy, "
    "strategy, or determination; human review is required."
)

Kind = Literal["date", "party", "numeric"]
Status = Literal["match", "mismatch", "insufficient_source", "unavailable", "not_applicable"]

_MONTHS = {
    "january": 1,
    "jan": 1,
    "february": 2,
    "feb": 2,
    "march": 3,
    "mar": 3,
    "april": 4,
    "apr": 4,
    "may": 5,
    "june": 6,
    "jun": 6,
    "july": 7,
    "jul": 7,
    "august": 8,
    "aug": 8,
    "september": 9,
    "sept": 9,
    "sep": 9,
    "october": 10,
    "oct": 10,
    "november": 11,
    "nov": 11,
    "december": 12,
    "dec": 12,
}
_MONTH_PATTERN = "|".join(sorted((_MONTHS), key=len, reverse=True))
_YEAR = r"(?:1[6-9]\d{2}|20\d{2})"
_PARTY_CHUNK = r"[A-Z][A-Za-z][A-Za-z.'-]*(?:\s+(?:of|the|and|&|[A-Z][A-Za-z][A-Za-z.'-]*)){0,6}"
_PARTY_RE = re.compile(rf"({_PARTY_CHUNK})\s+v(?:s\.?|\.)\s+({_PARTY_CHUNK})")
_FULL_DATE_RE = re.compile(
    rf"(?P<month>{_MONTH_PATTERN})\.?\s+(?P<day>\d{{1,2}}),?\s+(?P<year>{_YEAR})",
    re.I,
)
_US_DATE_RE = re.compile(rf"(?P<m>\d{{1,2}})/(?P<d>\d{{1,2}})/(?P<year>{_YEAR})")
_ISO_DATE_RE = re.compile(rf"(?P<year>{_YEAR})-(?P<m>\d{{2}})-(?P<d>\d{{2}})")
_YEAR_RE = re.compile(rf"\b(?P<year>{_YEAR})\b")
_MONEY_RE = re.compile(r"\$\s?(?P<value>\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d+(?:\.\d+)?)")
_PERCENT_RE = re.compile(r"(?P<value>\d+(?:\.\d+)?)\s*%")
_UNIT_RE = re.compile(
    r"\b(?P<value>\d+)\s+(?P<unit>days?|years?|months?|weeks?)\b",
    re.I,
)
_PARTY_STOP = frozenset({"of", "the", "and", "&", "a"})


@dataclass(frozen=True)
class ExtractedFact:
    kind: Kind
    text: str
    start: int
    end: int
    normalized: str
    year: int | None = None
    month: int | None = None
    day: int | None = None
    value: float | None = None
    unit: str | None = None
    passage_id: str | None = None


@dataclass(frozen=True)
class FactComparison:
    status: Status
    explanation: str
    filing_facts: tuple[ExtractedFact, ...]
    source_facts: tuple[ExtractedFact, ...]
    conflicts: tuple[ExtractedFact, ...]
    unmatched_filing: tuple[ExtractedFact, ...]


def _overlaps(start: int, end: int, occupied: list[tuple[int, int]]) -> bool:
    return any(start < right and end > left for left, right in occupied)


def _add_date(
    facts: list[ExtractedFact],
    occupied: list[tuple[int, int]],
    match: re.Match[str],
    *,
    year: int,
    month: int | None,
    day: int | None,
) -> None:
    start, end = match.start(), match.end()
    if not 1 <= year <= 2100:
        return
    if month is not None and not 1 <= month <= 12:
        return
    if day is not None and not 1 <= day <= 31:
        return
    if _overlaps(start, end, occupied):
        return
    occupied.append((start, end))
    facts.append(
        ExtractedFact(
            kind="date",
            text=match.group(),
            start=start,
            end=end,
            normalized=f"{year:04d}-{month or 0:02d}-{day or 0:02d}",
            year=year,
            month=month,
            day=day,
        )
    )


def _shift(fact: ExtractedFact, offset: int, passage_id: str | None = None) -> ExtractedFact:
    return ExtractedFact(
        kind=fact.kind,
        text=fact.text,
        start=fact.start + offset,
        end=fact.end + offset,
        normalized=fact.normalized,
        year=fact.year,
        month=fact.month,
        day=fact.day,
        value=fact.value,
        unit=fact.unit,
        passage_id=passage_id,
    )


def extract_facts(text: str) -> tuple[ExtractedFact, ...]:
    """Pull bounded dates, v. parties, and numeric holdings from a single excerpt."""
    if not text:
        return ()
    facts: list[ExtractedFact] = []
    occupied: list[tuple[int, int]] = []
    for match in _FULL_DATE_RE.finditer(text):
        _add_date(
            facts,
            occupied,
            match,
            year=int(match.group("year")),
            month=_MONTHS[match.group("month").rstrip(".").lower()],
            day=int(match.group("day")),
        )
    for match in _US_DATE_RE.finditer(text):
        _add_date(
            facts,
            occupied,
            match,
            year=int(match.group("year")),
            month=int(match.group("m")),
            day=int(match.group("d")),
        )
    for match in _ISO_DATE_RE.finditer(text):
        _add_date(
            facts,
            occupied,
            match,
            year=int(match.group("year")),
            month=int(match.group("m")),
            day=int(match.group("d")),
        )
    for match in _YEAR_RE.finditer(text):
        _add_date(
            facts,
            occupied,
            match,
            year=int(match.group("year")),
            month=None,
            day=None,
        )
    for match in _PARTY_RE.finditer(text):
        for group in (1, 2):
            start, end = match.start(group), match.end(group)
            if _overlaps(start, end, occupied):
                continue
            name = match.group(group).strip()
            occupied.append((start, end))
            facts.append(
                ExtractedFact(
                    kind="party",
                    text=name,
                    start=start,
                    end=end,
                    normalized=_normalize_party(name),
                )
            )
    for match in _MONEY_RE.finditer(text):
        _add_numeric(facts, occupied, match, float(match.group("value").replace(",", "")), "usd")
    for match in _PERCENT_RE.finditer(text):
        _add_numeric(facts, occupied, match, float(match.group("value")), "percent")
    for match in _UNIT_RE.finditer(text):
        unit = match.group("unit").lower().rstrip("s")
        _add_numeric(facts, occupied, match, float(match.group("value")), unit)
    return tuple(facts)


def _add_numeric(
    facts: list[ExtractedFact],
    occupied: list[tuple[int, int]],
    match: re.Match[str],
    value: float,
    unit: str,
) -> None:
    start, end = match.start(), match.end()
    if _overlaps(start, end, occupied):
        return
    occupied.append((start, end))
    facts.append(
        ExtractedFact(
            kind="numeric",
            text=match.group(),
            start=start,
            end=end,
            normalized=f"{value:g}:{unit}",
            value=value,
            unit=unit,
        )
    )


def _normalize_party(name: str) -> str:
    tokens = re.findall(r"[a-z0-9]+", name.lower())
    return " ".join(token for token in tokens if token not in _PARTY_STOP)


def _dates_compatible(left: ExtractedFact, right: ExtractedFact) -> bool:
    if left.year != right.year:
        return False
    if left.month and right.month and left.month != right.month:
        return False
    if left.day and right.day and left.day != right.day:
        return False
    return True


def _party_compatible(left: ExtractedFact, right: ExtractedFact) -> bool:
    if not left.normalized or not right.normalized:
        return False
    if (
        left.normalized == right.normalized
        or left.normalized in right.normalized
        or right.normalized in left.normalized
    ):
        return True
    left_tokens = set(left.normalized.split())
    right_tokens = set(right.normalized.split())
    return bool(left_tokens) and (left_tokens <= right_tokens or right_tokens <= left_tokens)


def _numeric_compatible(left: ExtractedFact, right: ExtractedFact) -> bool:
    return left.unit == right.unit and left.value == right.value


def _compatible(left: ExtractedFact, right: ExtractedFact) -> bool:
    if left.kind != right.kind:
        return False
    if left.kind == "date":
        return _dates_compatible(left, right)
    if left.kind == "party":
        return _party_compatible(left, right)
    return _numeric_compatible(left, right)


def _same_kind_source(
    fact: ExtractedFact, source_facts: tuple[ExtractedFact, ...]
) -> tuple[ExtractedFact, ...]:
    return tuple(item for item in source_facts if item.kind == fact.kind)


def extract_source_facts(passages: tuple[SourcePassage, ...]) -> tuple[ExtractedFact, ...]:
    facts: list[ExtractedFact] = []
    seen: set[tuple[str, str]] = set()
    for passage in passages:
        for fact in extract_facts(passage.text):
            shifted = _shift(fact, passage.start, passage.id)
            key = (shifted.kind, shifted.normalized)
            if key in seen:
                continue
            seen.add(key)
            facts.append(shifted)
    return tuple(facts)


def compare_facts(
    filing_excerpt: str,
    passages: tuple[SourcePassage, ...],
    *,
    source_available: bool,
) -> FactComparison:
    """Compare extractable filing facts with selected source passages only."""
    filing_facts = extract_facts(filing_excerpt)
    if not filing_facts:
        return FactComparison(
            status="not_applicable",
            explanation=(
                "No bounded date, party, or numeric holding was extracted from the filing "
                "excerpt, so fact comparison was not evaluated. " + LIMITATION
            ),
            filing_facts=(),
            source_facts=(),
            conflicts=(),
            unmatched_filing=(),
        )
    if not source_available:
        return FactComparison(
            status="insufficient_source",
            explanation=(
                "Cited source text is unavailable, so filing facts cannot be compared. "
                + LIMITATION
            ),
            filing_facts=filing_facts,
            source_facts=(),
            conflicts=(),
            unmatched_filing=filing_facts,
        )
    if not passages:
        return FactComparison(
            status="insufficient_source",
            explanation=(
                "No bounded source passage is available to compare filing facts. " + LIMITATION
            ),
            filing_facts=filing_facts,
            source_facts=(),
            conflicts=(),
            unmatched_filing=filing_facts,
        )
    source_facts = extract_source_facts(passages)
    conflicts: list[ExtractedFact] = []
    unmatched: list[ExtractedFact] = []
    for fact in filing_facts:
        peers = _same_kind_source(fact, source_facts)
        if not peers:
            unmatched.append(fact)
            continue
        if any(_compatible(fact, peer) for peer in peers):
            continue
        conflicts.append(fact)
    if conflicts:
        labels = "; ".join(f"{item.kind} {item.text!r}" for item in conflicts)
        return FactComparison(
            status="mismatch",
            explanation=(
                "Filing fact may not match selected source passages: "
                f"{labels}. Passage evidence is bound below. {LIMITATION}"
            ),
            filing_facts=filing_facts,
            source_facts=source_facts,
            conflicts=tuple(conflicts),
            unmatched_filing=tuple(unmatched),
        )
    if unmatched:
        labels = "; ".join(f"{item.kind} {item.text!r}" for item in unmatched)
        return FactComparison(
            status="insufficient_source",
            explanation=(
                "Selected source passages do not state comparable facts for "
                f"{labels}. Missing source facts are insufficient, not a pass. {LIMITATION}"
            ),
            filing_facts=filing_facts,
            source_facts=source_facts,
            conflicts=(),
            unmatched_filing=tuple(unmatched),
        )
    return FactComparison(
        status="match",
        explanation="Extracted filing facts appear in selected source passages. " + LIMITATION,
        filing_facts=filing_facts,
        source_facts=source_facts,
        conflicts=(),
        unmatched_filing=(),
    )
