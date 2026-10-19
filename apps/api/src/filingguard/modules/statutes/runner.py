"""Statute/regulation verification stage; unconfigured sources are unavailable."""

from datetime import UTC, datetime
from hashlib import sha256
from typing import cast
from uuid import uuid4

from filingguard.db.models import Analysis, EvidenceRecord, Finding
from filingguard.integrations.providers.runtime import ProviderBudget
from filingguard.modules.analyses.orchestrator import StageResult
from filingguard.modules.analyses.schemas import Coverage, StageStatus
from filingguard.modules.statutes.adapter import StatuteAdapter, configured_statute_adapter
from filingguard.modules.statutes.schemas import (
    LIMITATION,
    METHOD_VERSION,
    UNCONFIGURED_REASON,
    StatuteStatus,
)
from filingguard.modules.statutes.service import (
    MAX_LOOKUPS,
    collect_law_identities,
    verify_law_identity,
)

TITLES = {
    StatuteStatus.NOT_FOUND: "Statute absent from configured source",
    StatuteStatus.UNAVAILABLE: "Statute source unavailable",
    StatuteStatus.VERSION_MISMATCH: "Statute version or effective date differs",
    StatuteStatus.INVALID: "Statute citation could not be parsed",
}


def _evidence(
    analysis: Analysis, finding: Finding, text: str, start: int, end: int, metadata: dict
):
    return EvidenceRecord(
        id=uuid4(),
        analysis_id=analysis.id,
        finding_id=finding.id,
        source_type="document",
        source_label="Cited filing text",
        excerpt=text[start:end],
        snapshot_text=text,
        source_sha256=sha256(text.encode()).hexdigest(),
        retrieved_at=datetime.now(UTC),
        source_start_offset=start,
        source_end_offset=end,
        start_offset=start,
        end_offset=end,
        method="statute-lookup",
        method_version=METHOD_VERSION,
        source_metadata={
            "provenance": "synthetic" if analysis.mode == "demo" else "live",
            **metadata,
        },
    )


_MISSING = object()


def statutes_stage(
    analysis: Analysis,
    budget: ProviderBudget,
    *,
    adapter: StatuteAdapter | None | object = _MISSING,
) -> StageResult:
    text = (analysis.document_snapshot or {}).get("text") or ""
    identities = (
        collect_law_identities(text)
        if isinstance(text, str) and text.strip()
        else ()
    )
    if not identities:
        return StageResult(
            status=StageStatus.SKIPPED,
            reason=("No statute or regulation citations detected. " + LIMITATION)[:300],
        )

    source = configured_statute_adapter(budget=budget) if adapter is _MISSING else adapter
    if source is None:
        return StageResult(
            status=StageStatus.UNAVAILABLE,
            coverage=Coverage(eligible=len(identities), unavailable=len(identities)),
            reason=(UNCONFIGURED_REASON + " " + LIMITATION)[:300],
        )
    lookup_adapter = cast(StatuteAdapter, source)

    records = []
    evaluated = 0
    unavailable = 0
    truncated = len(identities) > MAX_LOOKUPS
    described = 0
    for index, identity in enumerate(identities):
        if index >= MAX_LOOKUPS:
            unavailable += 1
            continue
        result = verify_law_identity(identity, lookup_adapter)
        metadata = {
            "verification_status": result.status.value,
            "reason": result.reason,
            "jurisdiction": result.jurisdiction or identity.jurisdiction,
            "version": result.version,
            "effective_date": result.effective_date,
            "coverage_limitation": result.coverage_limitation,
            "normalized_key": identity.normalized_key,
            "cited_year": identity.cited_year,
            "method": result.method,
            "source_url": result.source_url,
        }
        if result.status == StatuteStatus.UNAVAILABLE:
            unavailable += 1
        elif result.status == StatuteStatus.VERIFIED:
            evaluated += 1
            continue
        else:
            evaluated += 1
        if described >= 50:
            continue
        described += 1
        finding = Finding(
            id=uuid4(),
            analysis_id=analysis.id,
            type="citation",
            severity="medium",
            title=TITLES.get(result.status, TITLES[StatuteStatus.UNAVAILABLE])[:255],
            description=(
                f"{identity.raw_text} was checked against the configured statute source. "
                f"{result.coverage_limitation} Database absence does not prove fabrication."
            ),
            status="open",
            stage="statutes",
            start_offset=identity.start,
            end_offset=identity.end,
            document_excerpt=identity.raw_text,
            ai_assisted=False,
        )
        records.extend(
            (
                finding,
                _evidence(analysis, finding, text, identity.start, identity.end, metadata),
            )
        )

    eligible = len(identities)
    if truncated:
        limitation = "Only the first 25 statute lookups were attempted."
    else:
        limitation = None
    if unavailable:
        status = StageStatus.PARTIAL
        reason = (
            f"Statute checks partial: {evaluated} evaluated, {unavailable} unavailable. "
            + LIMITATION
        )
    else:
        status = StageStatus.PARTIAL if truncated else StageStatus.COMPLETED
        reason = (f"Statute checks evaluated {evaluated} citation(s). " + LIMITATION)[:300]
    return StageResult(
        status=status,
        coverage=Coverage(
            eligible=eligible,
            evaluated=evaluated,
            unavailable=unavailable,
            truncated=truncated,
            limitation=limitation[:300] if limitation else None,
        ),
        reason=reason[:300],
        records=tuple(records),
    )
