"""Local Table of Authorities audit; skipped when no table is detected."""

from datetime import UTC, datetime
from hashlib import sha256
from uuid import uuid4

from filingguard.db.models import Analysis, EvidenceRecord, Finding
from filingguard.integrations.providers.runtime import ProviderBudget
from filingguard.modules.analyses.orchestrator import StageResult
from filingguard.modules.analyses.schemas import Coverage, StageStatus
from filingguard.modules.table_of_authorities.schemas import LIMITATION, METHOD_VERSION
from filingguard.modules.table_of_authorities.service import (
    MAX_FINDINGS,
    audit_table_of_authorities,
    first_entry,
    grouped_pages,
    mismatch_page_keys,
)


def _evidence(
    analysis: Analysis, finding: Finding, text: str, start: int, end: int, metadata: dict
):
    provenance = "synthetic" if analysis.mode == "demo" else "live"
    return EvidenceRecord(
        id=uuid4(),
        analysis_id=analysis.id,
        finding_id=finding.id,
        source_type="document",
        source_label="Private filing",
        excerpt=text[start:end],
        snapshot_text=text,
        source_sha256=sha256(text.encode()).hexdigest(),
        retrieved_at=datetime.now(UTC),
        source_start_offset=start,
        source_end_offset=end,
        start_offset=start,
        end_offset=end,
        method="toa-compare",
        method_version=METHOD_VERSION,
        source_metadata={"provenance": provenance, **metadata},
    )


def _pages_label(pages: list[int]) -> str:
    return ", ".join(str(page) for page in pages) if pages else "not recorded"


def table_of_authorities_stage(analysis: Analysis, _budget: ProviderBudget) -> StageResult:
    snapshot = analysis.document_snapshot or {}
    text = snapshot.get("text") or ""
    pages = snapshot.get("pages") or []
    audit = audit_table_of_authorities(text, pages if isinstance(pages, list) else [])
    if not audit.detected:
        reason = (
            "Table of Authorities heading found but section bounds could not be determined; "
            "comparison was not evaluated. "
            if audit.bound_uncertain
            else (
                "No Table of Authorities section detected; "
                "body-to-table comparison was not evaluated. "
            )
        )
        return StageResult(
            status=StageStatus.UNAVAILABLE if audit.bound_uncertain else StageStatus.SKIPPED,
            coverage=Coverage(eligible=1, unavailable=1) if audit.bound_uncertain else Coverage(),
            reason=(reason + LIMITATION)[:300],
        )

    comparable = len(
        {item.key for item in audit.table_entries} | {item.key for item in audit.body_entries}
    )
    if comparable == 0:
        start, end = audit.span.start, min(audit.span.end, audit.span.start + 80)
        finding = Finding(
            id=uuid4(),
            analysis_id=analysis.id,
            type="table_of_authorities",
            severity="info",
            title="Table of Authorities detected without comparable citations",
            description=(
                "A Table of Authorities heading was found, but no comparable reporter, "
                "statute, or journal identities were extracted from the table or body. "
                + LIMITATION
            ),
            status="open",
            stage="table_of_authorities",
            start_offset=start,
            end_offset=end,
            page_number=None,
            document_excerpt=text[start:end],
            ai_assisted=False,
        )
        return StageResult(
            status=StageStatus.COMPLETED,
            coverage=Coverage(eligible=1, evaluated=1),
            reason=(
                "Table of Authorities detected; no comparable identities extracted. "
                + LIMITATION
            )[:300],
            records=(
                finding,
                _evidence(
                    analysis,
                    finding,
                    text,
                    start,
                    end,
                    {"toa_heading": audit.span.heading},
                ),
            ),
        )

    records = []
    for key in audit.missing_from_table[:MAX_FINDINGS]:
        entry = first_entry(audit.body_entries, key)
        if entry is None:
            continue
        body_pages = grouped_pages(audit.body_entries, key)
        finding = Finding(
            id=uuid4(),
            analysis_id=analysis.id,
            type="table_of_authorities",
            severity="medium",
            title=f"Authority missing from Table of Authorities: {entry.display}"[:255],
            description=(
                f"The body cites {entry.display}, but that identity was not found in the "
                f"detected Table of Authorities. Body pages: {_pages_label(body_pages)}. "
                "This is a document-consistency signal, not a court-rule determination. "
                + LIMITATION
            ),
            status="open",
            stage="table_of_authorities",
            start_offset=entry.start,
            end_offset=entry.end,
            page_number=entry.page_number,
            document_excerpt=text[entry.start : entry.end],
            ai_assisted=False,
        )
        records.extend(
            (
                finding,
                _evidence(
                    analysis,
                    finding,
                    text,
                    entry.start,
                    entry.end,
                    {
                        "toa_issue": "missing_from_table",
                        "authority_key": key,
                        "body_pages": body_pages,
                    },
                ),
            )
        )
    remaining = MAX_FINDINGS - (len(records) // 2)
    for key in audit.extra_in_table[: max(0, remaining)]:
        entry = first_entry(audit.table_entries, key)
        if entry is None:
            continue
        listed = grouped_pages(audit.table_entries, key, listed=True)
        finding = Finding(
            id=uuid4(),
            analysis_id=analysis.id,
            type="table_of_authorities",
            severity="low",
            title=f"Table of Authorities entry not cited in body: {entry.display}"[:255],
            description=(
                f"The Table of Authorities lists {entry.display}, which was not found as a "
                f"comparable citation in the body. Listed pages: {_pages_label(listed)}. "
                "This is a document-consistency signal, not a court-rule determination. "
                + LIMITATION
            ),
            status="open",
            stage="table_of_authorities",
            start_offset=entry.start,
            end_offset=entry.end,
            page_number=entry.page_number,
            document_excerpt=text[entry.start : entry.end],
            ai_assisted=False,
        )
        records.extend(
            (
                finding,
                _evidence(
                    analysis,
                    finding,
                    text,
                    entry.start,
                    entry.end,
                    {
                        "toa_issue": "extra_in_table",
                        "authority_key": key,
                        "listed_pages": listed,
                    },
                ),
            )
        )
    page_mismatches = mismatch_page_keys(audit)
    remaining = MAX_FINDINGS - (len(records) // 2)
    for key in page_mismatches[: max(0, remaining)]:
        entry = first_entry(audit.table_entries, key) or first_entry(audit.body_entries, key)
        if entry is None:
            continue
        listed = grouped_pages(audit.table_entries, key, listed=True)
        body_pages = grouped_pages(audit.body_entries, key)
        finding = Finding(
            id=uuid4(),
            analysis_id=analysis.id,
            type="table_of_authorities",
            severity="low",
            title=f"Table of Authorities page references differ: {entry.display}"[:255],
            description=(
                f"Listed pages ({_pages_label(listed)}) do not overlap body occurrence pages "
                f"({_pages_label(body_pages)}) for {entry.display}. Page leaders are parsed "
                "only when present. "
                + LIMITATION
            ),
            status="open",
            stage="table_of_authorities",
            start_offset=entry.start,
            end_offset=entry.end,
            page_number=entry.page_number,
            document_excerpt=text[entry.start : entry.end],
            ai_assisted=False,
        )
        records.extend(
            (
                finding,
                _evidence(
                    analysis,
                    finding,
                    text,
                    entry.start,
                    entry.end,
                    {
                        "toa_issue": "page_mismatch",
                        "authority_key": key,
                        "listed_pages": listed,
                        "body_pages": body_pages,
                    },
                ),
            )
        )
    truncated = (
        len(audit.missing_from_table) + len(audit.extra_in_table) + len(page_mismatches)
        > MAX_FINDINGS
    )
    reason = (
        f"Compared {comparable} unique reporter identities in the Table of Authorities and body. "
        + LIMITATION
    )
    return StageResult(
        status=StageStatus.PARTIAL if truncated else StageStatus.COMPLETED,
        coverage=Coverage(
            eligible=comparable,
            evaluated=comparable,
            truncated=truncated,
            limitation="Only the first 50 Table of Authorities differences were retained."
            if truncated
            else None,
        ),
        reason=reason[:300],
        records=tuple(records),
    )
