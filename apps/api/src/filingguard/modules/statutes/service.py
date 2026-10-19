"""Detect law citations and compare them to a configured statute source."""

import re
from typing import TYPE_CHECKING

from filingguard.modules.citations.service import extract_citations
from filingguard.modules.statutes.schemas import (
    LIMITATION,
    LawIdentity,
    StatuteLookupResult,
    StatuteStatus,
)

if TYPE_CHECKING:
    from filingguard.modules.statutes.adapter import StatuteAdapter

MAX_LOOKUPS = 25
STATUTE_CANDIDATE = re.compile(
    r"(?<!\w)(?:(?P<usc_title>[1-9]\d{0,3})\s+U\.S\.C(?:\.A)?\.?\s*§\s*"
    r"(?P<usc_section>[\dA-Za-z().-]+)|(?P<cfr_title>[1-9]\d{0,3})\s+C\.F\.R\.?\s*§\s*"
    r"(?P<cfr_section>[\dA-Za-z().-]+))",
    re.IGNORECASE,
)
YEAR_AFTER = re.compile(r"^\s*\((\d{4})\)")
REPORTER_NORMALIZE = re.compile(r"[^a-z0-9]+")


def _cited_year(text: str, end: int) -> str | None:
    match = YEAR_AFTER.match(text[end : min(len(text), end + 12)])
    return match.group(1) if match else None


def _jurisdiction(reporter: str) -> str:
    compact = REPORTER_NORMALIZE.sub("", reporter.lower())
    if compact in {"usc", "usca", "cfr"}:
        return "US-federal"
    if compact.startswith("cal"):
        return "US-CA"
    return "unknown"


def _normalized_key(reporter: str, title: str | None, section: str) -> str:
    compact = REPORTER_NORMALIZE.sub("", reporter.lower())
    section_key = section.lower().rstrip(".")
    if compact in {"usc", "usca"}:
        return f"usc:{title or ''}:{section_key}"
    if compact == "cfr":
        return f"cfr:{title or ''}:{section_key}"
    return f"{compact}:{title or ''}:{section_key}"


def identity_from_occurrence(
    raw_text: str, start: int, end: int, text: str, *, kind: str = "law"
) -> LawIdentity | None:
    match = STATUTE_CANDIDATE.search(raw_text)
    reporter = ""
    title = None
    section = ""
    if match:
        if match.group("usc_title"):
            reporter = "U.S.C."
            title = match.group("usc_title")
            section = match.group("usc_section")
        else:
            reporter = "C.F.R."
            title = match.group("cfr_title")
            section = match.group("cfr_section")
    else:
        parts = re.search(
            r"(?P<reporter>.+?)\s*§\s*(?P<section>[\dA-Za-z().-]+)", raw_text, re.IGNORECASE
        )
        if parts is None:
            return None
        reporter = parts.group("reporter").strip()
        section = parts.group("section")
        title_match = re.search(r"^(?P<title>\d+)\s+", reporter)
        if title_match:
            title = title_match.group("title")
            reporter = reporter[title_match.end() :].strip()
    if not reporter or not section:
        return None
    return LawIdentity(
        raw_text=raw_text,
        start=start,
        end=end,
        normalized_key=_normalized_key(reporter, title, section),
        reporter=reporter,
        title=title,
        section=section,
        jurisdiction=_jurisdiction(reporter),
        cited_year=_cited_year(text, end),
        kind="statute_candidate" if kind != "law" else "law",
    )


def collect_law_identities(text: str) -> list[LawIdentity]:
    extraction = extract_citations(text)
    identities: list[LawIdentity] = []
    spanned: list[tuple[int, int]] = []
    for item in extraction.occurrences:
        if item.extraction.kind != "law":
            spanned.append((item.start, item.end))
            continue
        identity = identity_from_occurrence(item.raw_text, item.start, item.end, text)
        if identity is None:
            spanned.append((item.start, item.end))
            continue
        identities.append(identity)
        spanned.append((item.start, item.end))
    for match in STATUTE_CANDIDATE.finditer(text):
        start, end = match.span()
        if any(
            start < existing_end and end > existing_start
            for existing_start, existing_end in spanned
        ):
            continue
        identity = identity_from_occurrence(
            text[start:end], start, end, text, kind="statute_candidate"
        )
        if identity is not None:
            identities.append(identity)
            spanned.append((start, end))
    identities.sort(key=lambda item: (item.start, item.end))
    return identities


def _version_year(result: StatuteLookupResult) -> str | None:
    if result.version and re.fullmatch(r"\d{4}", result.version):
        return result.version
    if result.effective_date and re.match(r"^\d{4}", result.effective_date):
        return result.effective_date[:4]
    return None


def verify_law_identity(identity: LawIdentity, adapter: "StatuteAdapter") -> StatuteLookupResult:
    result = adapter.lookup(identity)
    if result.status != StatuteStatus.VERIFIED:
        return result
    cited = identity.cited_year
    source_year = _version_year(result)
    if cited and source_year and cited != source_year:
        return result.model_copy(
            update={
                "status": StatuteStatus.VERSION_MISMATCH,
                "reason": "version_or_effective_date_mismatch",
                "coverage_limitation": (
                    f"Cited year {cited} does not match source version/effective year "
                    f"{source_year}. {LIMITATION}"
                ),
            }
        )
    return result
