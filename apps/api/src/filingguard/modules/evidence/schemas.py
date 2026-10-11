"""Provenance contracts and exact snapshot-bound passage validation."""

import hashlib
from typing import Annotated, Literal, Self
from urllib.parse import urlsplit
from uuid import UUID

from pydantic import AwareDatetime, Field, HttpUrl, model_validator

from filingguard.modules.analyses.schemas import Contract, DocumentLocation, Label, Nonnegative

Sha256 = Annotated[str, Field(pattern=r"^[a-f0-9]{64}$")]


class EvidenceRecord(Contract):
    id: UUID
    analysis_id: UUID
    finding_id: UUID | None = None
    source_type: Literal["document", "api", "opinion_text", "ai_analysis", "rule"]
    source_label: Label
    source_url: HttpUrl | None = None
    retrieved_at: AwareDatetime
    snapshot_sha256: Sha256
    excerpt: Annotated[str, Field(min_length=1, max_length=100000)]
    start: Nonnegative
    end: Nonnegative
    offset_unit: Literal["unicode_code_points"] = "unicode_code_points"
    document_location: DocumentLocation | None = None
    triggering_citation_id: UUID | None = None
    triggering_quote_id: UUID | None = None
    method_version: Label
    model_version: Label | None = None
    prompt_version: Label | None = None
    rule_version: Label | None = None
    authority_id: UUID | None = None
    external_id: Label | None = None
    court_profile_id: Label | None = None
    rule_id: Label | None = None
    provenance: Literal["live", "synthetic", "cached_public"]

    @model_validator(mode="after")
    def complete_lineage(self) -> Self:
        if self.end <= self.start or self.end - self.start != len(self.excerpt):
            raise ValueError("Evidence excerpt must match its nonempty span length")
        if self.source_type == "ai_analysis" and (
            not self.model_version or not self.prompt_version
        ):
            raise ValueError("AI evidence needs model and prompt versions")
        if self.source_type == "rule" and (
            not self.rule_version or not self.court_profile_id or not self.rule_id
        ):
            raise ValueError("Rule evidence needs profile, rule identity and version")
        if self.source_type in {"api", "opinion_text"} and (
            self.source_url is None or self.authority_id is None or self.external_id is None
        ):
            raise ValueError("External evidence needs a source URL and authority identity")
        if self.source_url is not None and urlsplit(str(self.source_url)).username is not None:
            raise ValueError("Source URLs must not embed credentials")
        return self


def validate_snapshot(record: EvidenceRecord, source_text: str) -> None:
    """Call before persisting evidence; offsets always refer to unnormalized text."""
    actual_hash = hashlib.sha256(source_text.encode("utf-8")).hexdigest()
    if actual_hash != record.snapshot_sha256:
        raise ValueError("Source snapshot hash mismatch")
    if record.end > len(source_text) or source_text[record.start : record.end] != record.excerpt:
        raise ValueError("Evidence passage does not match the snapshot")
