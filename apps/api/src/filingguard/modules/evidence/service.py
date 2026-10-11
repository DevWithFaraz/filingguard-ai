"""Store and retrieve validated provenance through the analysis ownership boundary."""

from uuid import UUID

from filingguard.db.models import EvidenceRecord as StoredEvidence
from filingguard.db.models import Finding
from filingguard.db.repository import AnalysisRepository, StageWrite
from filingguard.modules.evidence.schemas import EvidenceRecord, validate_snapshot


def persist_evidence(writer: StageWrite, evidence: EvidenceRecord, source_text: str) -> None:
    if evidence.analysis_id != writer.analysis.id:
        raise ValueError("Evidence belongs to a different analysis")
    validate_snapshot(evidence, source_text)
    location = evidence.document_location
    writer.add(
        StoredEvidence(
            id=evidence.id,
            analysis_id=evidence.analysis_id,
            finding_id=evidence.finding_id,
            segment_id=location.segment_id if location else None,
            citation_id=evidence.triggering_citation_id,
            quote_id=evidence.triggering_quote_id,
            authority_id=evidence.authority_id,
            source_type=evidence.source_type,
            source_label=evidence.source_label,
            excerpt=evidence.excerpt,
            snapshot_text=source_text,
            source_url=str(evidence.source_url) if evidence.source_url else None,
            source_sha256=evidence.snapshot_sha256,
            retrieved_at=evidence.retrieved_at,
            source_start_offset=evidence.start,
            source_end_offset=evidence.end,
            page_number=location.page_number if location else None,
            start_offset=location.start if location else None,
            end_offset=location.end if location else None,
            method=evidence.source_type,
            method_version=evidence.method_version,
            model_version=evidence.model_version,
            prompt_version=evidence.prompt_version,
            source_metadata={
                "provenance": evidence.provenance,
                "offset_unit": evidence.offset_unit,
                "external_id": evidence.external_id,
                "rule_version": evidence.rule_version,
                "court_profile_id": evidence.court_profile_id,
                "rule_id": evidence.rule_id,
            },
        )
    )


def finding_evidence(
    repository: AnalysisRepository,
    owner_hash: str,
    analysis_id: UUID,
    finding_id: UUID,
) -> list[StoredEvidence]:
    """Every returned passage is owner-scoped and rechecked against its stored snapshot."""
    finding = repository.get_record(owner_hash, analysis_id, Finding, finding_id)
    if finding is None:
        raise LookupError("Finding not found")
    records = [
        record
        for record in repository.list_records(
            owner_hash,
            analysis_id,
            StoredEvidence,
        )
        if record.finding_id == finding_id
    ]
    for record in records:
        if record.snapshot_text is None:
            raise ValueError("Stored source snapshot is unavailable")
        typed = EvidenceRecord(
            id=record.id,
            analysis_id=record.analysis_id,
            finding_id=record.finding_id,
            source_type=record.source_type,
            source_label=record.source_label,
            source_url=record.source_url,
            retrieved_at=record.retrieved_at,
            snapshot_sha256=record.source_sha256,
            excerpt=record.excerpt,
            start=record.source_start_offset,
            end=record.source_end_offset,
            authority_id=record.authority_id,
            method_version=record.method_version,
            model_version=record.model_version,
            prompt_version=record.prompt_version,
            provenance=record.source_metadata.get("provenance"),
            external_id=record.source_metadata.get("external_id"),
            rule_version=record.source_metadata.get("rule_version"),
            court_profile_id=record.source_metadata.get("court_profile_id"),
            rule_id=record.source_metadata.get("rule_id"),
        )
        validate_snapshot(typed, record.snapshot_text)
    return records
