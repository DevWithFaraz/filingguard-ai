"""Detect a Table of Authorities and compare reporter identities both ways."""

from __future__ import annotations

import re
from collections import defaultdict

from filingguard.modules.citations.service import extract_citations
from filingguard.modules.table_of_authorities.schemas import (
    LIMITATION,
    ToaAudit,
    ToaEntry,
    ToaSpan,
)

HEADING = re.compile(
    r"(?im)^[ \t]*(TABLE OF AUTHORITIES|TABLE OF CASES|INDEX OF AUTHORITIES)[ \t.]*$"
)
END_HEADING = re.compile(
    r"(?im)^[ \t]*("
    r"TABLE OF CONTENTS|"
    r"STATEMENT OF (?:THE )?(?:CASE|FACTS|ISSUES)|"
    r"JURISDICTION(?:AL STATEMENT)?|"
    r"QUESTIONS PRESENTED|"
    r"SUMMARY OF (?:THE )?ARGUMENT|"
    r"PRELIMINARY STATEMENT|"
    r"NATURE OF (?:THE )?CASE|"
    r"STANDARD OF REVIEW|"
    r"INTRODUCTION|"
    r"ARGUMENT|"
    r"PROCEDURAL HISTORY"
    r")[ \t]*$"
)
FALLBACK_HEADING = re.compile(r"(?m)^[ \t]*([A-Z][A-Z][A-Z \-]{2,40})[ \t]*$")
REPORTER_CORE = re.compile(r"([1-9]\d{0,5})\s+([A-Z][A-Za-z.]{1,20})\s+([1-9]\d{0,5})")
PAGE_LIST = re.compile(r"(?:\.{2,}|\u2026+|\s{2,})\s*((?:\d{1,4})(?:\s*,\s*\d{1,4})*)\s*$")
COMPARABLE = frozenset({"full_case", "law", "journal", "reporter_candidate"})
HEADING_KIND = {
    "TABLE OF AUTHORITIES": "table_of_authorities",
    "TABLE OF CASES": "table_of_cases",
    "INDEX OF AUTHORITIES": "index_of_authorities",
}
SEARCH_WINDOW = 25_000
SECTION_WINDOW = 15_000
MAX_FINDINGS = 50


def _line_bounds(text: str, offset: int) -> tuple[int, int]:
    start = text.rfind("\n", 0, offset) + 1
    end = text.find("\n", offset)
    return start, len(text) if end < 0 else end


def detect_toa_span(text: str) -> tuple[ToaSpan | None, bool]:
    if not isinstance(text, str) or not text.strip():
        return None, False
    window = text[: min(len(text), SEARCH_WINDOW)]
    match = HEADING.search(window)
    if match is None:
        return None, False
    heading = HEADING_KIND[re.sub(r"\s+", " ", match.group(1).upper()).strip()]
    body_start = match.end()
    search_end = min(len(text), body_start + SECTION_WINDOW)
    remainder = text[body_start:search_end]
    end_match = END_HEADING.search(remainder)
    if end_match is not None:
        return (
            ToaSpan(start=match.start(), end=body_start + end_match.start(), heading=heading),
            False,
        )
    fallback = FALLBACK_HEADING.search(remainder)
    if fallback is not None and fallback.group(1) not in HEADING_KIND:
        return (
            ToaSpan(start=match.start(), end=body_start + fallback.start(), heading=heading),
            True,
        )
    return None, True


def _identity_key(normalized: str | None, raw: str) -> str | None:
    source = normalized or raw
    core = REPORTER_CORE.search(source)
    if core is None:
        return None
    volume, reporter, page = core.groups()
    reporter_key = re.sub(r"[.\s]+", "", reporter).casefold()
    return f"{volume} {reporter_key} {page}"


def _listed_pages(text: str, start: int, end: int) -> list[int]:
    line_start, line_end = _line_bounds(text, start)
    line = text[line_start:line_end]
    # Only inspect the suffix after this occurrence so reporter pages are not listed pages.
    suffix = line[end - line_start :]
    match = PAGE_LIST.search(suffix) if suffix else PAGE_LIST.search(line)
    if match is None:
        return []
    pages = [int(item) for item in re.split(r"\s*,\s*", match.group(1)) if item]
    return list(dict.fromkeys(page for page in pages if 1 <= page <= 20))[:32]


def _page_at(offset: int, pages: list[dict] | None) -> int | None:
    if not pages:
        return None
    for page in pages:
        start = page.get("start") if isinstance(page, dict) else getattr(page, "start", None)
        end = page.get("end") if isinstance(page, dict) else getattr(page, "end", None)
        number = (
            page.get("page_number")
            if isinstance(page, dict)
            else getattr(page, "page_number", None)
        )
        if isinstance(start, int) and isinstance(end, int) and start <= offset < end:
            return number if isinstance(number, int) else None
    return None


def _entry(text: str, occurrence, pages: list[dict] | None) -> ToaEntry | None:
    kind = occurrence.extraction.kind
    if kind not in COMPARABLE:
        return None
    key = _identity_key(occurrence.normalized_text, occurrence.raw_text)
    if key is None:
        return None
    display = re.sub(r"\s+", " ", occurrence.normalized_text or occurrence.raw_text).strip()
    return ToaEntry(
        key=key,
        display=display[:300],
        start=occurrence.start,
        end=occurrence.end,
        page_number=_page_at(occurrence.start, pages),
        listed_pages=_listed_pages(text, occurrence.start, occurrence.end),
        kind=kind,
    )


def audit_table_of_authorities(text: str, pages: list[dict] | None = None) -> ToaAudit:
    span, uncertain = detect_toa_span(text)
    if span is None:
        return ToaAudit(detected=False, bound_uncertain=uncertain, limitation=LIMITATION)
    extraction = extract_citations(text)
    table: list[ToaEntry] = []
    body: list[ToaEntry] = []
    for occurrence in extraction.occurrences:
        entry = _entry(text, occurrence, pages)
        if entry is None:
            continue
        if span.start <= occurrence.start < span.end:
            table.append(entry)
        else:
            body.append(entry.model_copy(update={"listed_pages": []}))
    table_keys = list(dict.fromkeys(item.key for item in table))
    body_keys = list(dict.fromkeys(item.key for item in body))
    table_set, body_set = set(table_keys), set(body_keys)
    return ToaAudit(
        detected=True,
        span=span,
        table_entries=table[:200],
        body_entries=body[:200],
        missing_from_table=[key for key in body_keys if key not in table_set][:200],
        extra_in_table=[key for key in table_keys if key not in body_set][:200],
        bound_uncertain=uncertain,
        limitation=LIMITATION,
    )


def grouped_pages(entries: list[ToaEntry], key: str, *, listed: bool = False) -> list[int]:
    values: list[int] = []
    for entry in entries:
        if entry.key != key:
            continue
        if listed:
            values.extend(entry.listed_pages)
        elif entry.page_number is not None:
            values.append(entry.page_number)
    return list(dict.fromkeys(values))


def first_entry(entries: list[ToaEntry], key: str) -> ToaEntry | None:
    for entry in entries:
        if entry.key == key:
            return entry
    return None


def mismatch_page_keys(audit: ToaAudit) -> list[str]:
    mismatches: list[str] = []
    listed = defaultdict(list)
    body = defaultdict(list)
    for entry in audit.table_entries:
        listed[entry.key].extend(entry.listed_pages)
    for entry in audit.body_entries:
        if entry.page_number is not None:
            body[entry.key].append(entry.page_number)
    shared = set(listed) & set(body) - set(audit.missing_from_table) - set(audit.extra_in_table)
    for key in sorted(shared):
        table_pages = list(dict.fromkeys(listed[key]))
        body_pages = list(dict.fromkeys(body[key]))
        if table_pages and body_pages and not set(table_pages) & set(body_pages):
            mismatches.append(key)
    return mismatches[:MAX_FINDINGS]
