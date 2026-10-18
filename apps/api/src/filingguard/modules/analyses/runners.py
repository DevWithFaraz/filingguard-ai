"""First local stages; unavailable engines remain explicit partial coverage."""

from datetime import UTC, datetime
from hashlib import sha256
from uuid import uuid4

from filingguard.db.models import Analysis, EvidenceRecord, Finding
from filingguard.integrations.providers.runtime import ProviderBudget
from filingguard.modules.analyses.demo_sources import (
    live_or_demo_citations,
    local_or_demo_citations,
)
from filingguard.modules.analyses.orchestrator import StageResult
from filingguard.modules.analyses.schemas import Coverage, StageName, StageStatus
from filingguard.modules.court_rules.service import evaluate_disclosure, load_profile
from filingguard.modules.privacy.checks import detect_sensitive


def _evidence(
    analysis: Analysis,
    finding: Finding,
    text: str,
    start: int,
    end: int,
    *,
    source_type: str = "document",
    rule_id: str | None = None,
    rule_version: str | None = None,
) -> EvidenceRecord:
    return EvidenceRecord(
        id=uuid4(),
        analysis_id=analysis.id,
        finding_id=finding.id,
        source_type=source_type,
        source_label="Private filing" if source_type == "document" else "Synthetic training rule",
        excerpt=text[start:end],
        snapshot_text=text,
        source_sha256=sha256(text.encode()).hexdigest(),
        retrieved_at=datetime.now(UTC),
        source_start_offset=start,
        source_end_offset=end,
        start_offset=start if source_type == "document" else None,
        end_offset=end if source_type == "document" else None,
        method="local-pattern" if source_type == "document" else "versioned-profile",
        method_version="privacy-v1" if source_type == "document" else rule_version,
        source_metadata={
            "provenance": "synthetic" if analysis.mode == "demo" else "live",
            "court_profile_id": analysis.court_profile_id if source_type == "rule" else None,
            "rule_id": rule_id,
            "rule_version": rule_version,
        },
    )


def privacy_stage(analysis: Analysis, _budget: ProviderBudget) -> StageResult:
    text = analysis.document_snapshot["text"]
    records = []
    for signal in detect_sensitive(text):
        finding = Finding(
            id=uuid4(),
            analysis_id=analysis.id,
            type="privacy",
            severity=signal.severity,
            title={
                "ssn": "SSN-shaped identifier",
                "financial_account": "Possible account number",
                "birth_date": "Possible full date of birth",
                "minor_name": "Possible unredacted minor name",
            }[signal.kind],
            description=(
                "Review whether this name refers to a minor requiring initials under "
                "Fed. R. Civ. P. 5.2(a)(3) or local privacy rules; automated heuristic "
                "detection carries explicit uncertainty."
                if signal.kind == "minor_name"
                else (
                    "Review whether this identifier needs redaction before filing; "
                    "automated detection is not a compliance determination."
                )
            ),
            status="open",
            stage="privacy",
            start_offset=signal.start,
            end_offset=signal.end,
            document_excerpt=signal.masked_snippet,
            ai_assisted=False,
        )
        records.extend((finding, _evidence(analysis, finding, text, signal.start, signal.end)))
    diagnostics = (analysis.document_snapshot or {}).get("diagnostics") or []
    if diagnostics:
        diag_text = "; ".join(diagnostics)
        has_critical = any(
            "no extractable text" in d.lower() or "excessive" in d.lower() for d in diagnostics
        )
        severity = "high" if has_critical else "medium"
        diag_finding = Finding(
            id=uuid4(),
            analysis_id=analysis.id,
            type="system",
            severity=severity,
            title="Document text parsing quality warning",
            description=(
                f"Potential text extraction quality issues detected: {diag_text}. "
                "Unextracted, fused, or degraded text cannot be verified for citations, "
                "quotations, or privacy risks."
            ),
            status="open",
            stage="document",
            start_offset=0,
            end_offset=min(len(text), 100),
            document_excerpt=text[:100],
            ai_assisted=False,
        )
        records.extend(
            (diag_finding, _evidence(analysis, diag_finding, text, 0, min(len(text), 100)))
        )
    return StageResult(
        status=StageStatus.COMPLETED,
        coverage=Coverage(eligible=1, evaluated=1),
        records=tuple(records),
    )


def court_stage(analysis: Analysis, _budget: ProviderBudget) -> StageResult:
    snapshot = analysis.document_snapshot or {}
    text = snapshot.get("text", "")
    raw_pages = snapshot.get("pages")
    pages_text: list[str] | None = None
    if raw_pages:
        extracted = []
        for p in raw_pages:
            if isinstance(p, str):
                extracted.append(p)
            elif isinstance(p, dict) and "start" in p and "end" in p:
                extracted.append(text[p["start"] : p["end"]])
            elif hasattr(p, "start") and hasattr(p, "end"):
                extracted.append(text[p.start : p.end])
        if extracted:
            pages_text = extracted

    result = evaluate_disclosure(
        analysis.court_profile_id,
        text,
        analysis.ai_used,
        demo=analysis.mode == "demo",
        pages=pages_text,
    )
    if result.status == "unavailable":
        return StageResult(
            status=StageStatus.UNAVAILABLE,
            coverage=Coverage(eligible=1, unavailable=1),
            reason=result.reason,
        )
    records = []
    profile = load_profile(analysis.court_profile_id)
    rule_text = profile.ai_disclosure.requirement
    if result.status == "missing":
        if profile.is_demo:
            title = "Synthetic AI-use disclosure missing"
            description = (
                f"{rule_text} This is a training-only requirement; "
                "verify actual court rules independently."
            )
        else:
            title = "Required N.D. Tex. Local Rule 7.2(f) AI-use disclosure missing"
            description = (
                f"{rule_text} Automated detection checks heading presence only; "
                "substantive legal compliance requires independent human review."
            )
        finding = Finding(
            id=uuid4(),
            analysis_id=analysis.id,
            type="court_rule",
            severity="medium",
            title=title,
            status="open",
            stage="court_rules",
            description=description,
            rule_id=result.rule_id,
            ai_assisted=False,
        )
        records.extend(
            (
                finding,
                _evidence(
                    analysis,
                    finding,
                    rule_text,
                    0,
                    len(rule_text),
                    source_type="rule",
                    rule_id=result.rule_id,
                    rule_version=profile.version,
                ),
            )
        )
    if profile.is_demo:
        stage_reason = (
            f"{result.reason or 'AI-use flag is no; requirement not triggered.'} "
            "Synthetic court rule is an unvalidated synthetic exercise; "
            "verify actual court rules independently."
        )
    else:
        stage_reason = (
            f"{result.reason or 'AI-use flag is no; requirement not triggered.'} "
            "Automated heading check is not a legal sufficiency review."
        )
    if len(stage_reason) > 300:
        stage_reason = stage_reason[:299] + "…"
    return StageResult(
        status=StageStatus.COMPLETED,
        coverage=Coverage(eligible=1, evaluated=1),
        reason=stage_reason,
        records=tuple(records),
    )


def claims_stage(analysis, budget):
    from filingguard.modules.claims.runner import claims_stage as run

    return run(analysis, budget)


def propositions_stage(analysis, budget):
    from filingguard.modules.propositions.service import propositions_stage as run

    return run(analysis, budget)


def quotes_stage(analysis, budget):
    from filingguard.modules.quotes.runner import quotes_stage as run

    return run(analysis, budget)


def local_runners(settings=None):
    return {
        StageName.PRIVACY: privacy_stage,
        StageName.COURT_RULES: court_stage,
        StageName.CITATIONS: live_or_demo_citations
        if settings and settings.source_verification_enabled
        else local_or_demo_citations,
        StageName.CLAIMS: claims_stage,
        StageName.QUOTES: quotes_stage,
        StageName.PROPOSITIONS: propositions_stage
        if settings and settings.semantic_review_enabled
        else StageResult(status=StageStatus.UNAVAILABLE, reason="Semantic review is disabled"),
    }
