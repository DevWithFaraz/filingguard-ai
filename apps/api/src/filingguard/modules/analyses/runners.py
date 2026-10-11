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
            }[signal.kind],
            description=(
                "Review whether this identifier needs redaction before filing; "
                "automated detection is not a compliance determination."
            ),
            status="open",
            stage="privacy",
            start_offset=signal.start,
            end_offset=signal.end,
            document_excerpt=signal.masked_snippet,
            ai_assisted=False,
        )
        records.extend((finding, _evidence(analysis, finding, text, signal.start, signal.end)))
    return StageResult(
        status=StageStatus.COMPLETED,
        coverage=Coverage(eligible=1, evaluated=1),
        records=tuple(records),
    )


def court_stage(analysis: Analysis, _budget: ProviderBudget) -> StageResult:
    result = evaluate_disclosure(
        analysis.court_profile_id,
        analysis.document_snapshot["text"],
        analysis.ai_used,
        demo=analysis.mode == "demo",
    )
    if result.status == "unavailable":
        return StageResult(
            status=StageStatus.UNAVAILABLE,
            coverage=Coverage(eligible=1, unavailable=1),
            reason=result.reason,
        )
    records = []
    if result.status == "missing":
        profile = load_profile(analysis.court_profile_id)
        rule_text = profile.ai_disclosure.requirement
        finding = Finding(
            id=uuid4(),
            analysis_id=analysis.id,
            type="court_rule",
            severity="medium",
            title="Synthetic AI-use disclosure missing",
            status="open",
            stage="court_rules",
            description=(
                f"{rule_text} This is a training-only requirement; "
                "verify actual court rules independently."
            ),
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
    return StageResult(
        status=StageStatus.COMPLETED,
        coverage=Coverage(eligible=1, evaluated=1),
        reason=(
            f"{result.requirement} "
            f"{result.reason or 'AI-use flag is no; requirement not triggered.'} "
            "Automated heading check is not a legal sufficiency review."
        ),
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
