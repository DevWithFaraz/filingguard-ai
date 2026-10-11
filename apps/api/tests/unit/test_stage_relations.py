"""Contained output cannot attach a finding to unrelated persisted identities."""

from hashlib import sha256
from types import SimpleNamespace
from uuid import uuid4

import pytest

from filingguard.db.models import Analysis, EvidenceRecord, Finding
from filingguard.modules.analyses.execution import StageResult, validate_stage_context
from filingguard.modules.analyses.schemas import Coverage, StageName, StageStatus


def sample():
    analysis = Analysis(id=uuid4(), document_snapshot={"text": "Synthetic filing"})
    authority = SimpleNamespace(id=uuid4())
    citation = SimpleNamespace(id=uuid4(), authority_id=authority.id)
    claim = SimpleNamespace(id=uuid4())
    link = SimpleNamespace(
        id=uuid4(), claim_id=claim.id, citation_id=citation.id, authority_id=authority.id
    )
    context = {
        "citations": (citation,),
        "authorities": (authority,),
        "claims": (claim,),
        "links": (link,),
    }
    finding = Finding(
        id=uuid4(),
        analysis_id=analysis.id,
        citation_id=citation.id,
        authority_id=authority.id,
        claim_id=claim.id,
        quote_id=None,
    )
    return analysis, context, finding


def check(analysis, context, records):
    result = StageResult(
        StageStatus.COMPLETED, Coverage(eligible=1, evaluated=1), records=tuple(records)
    )
    validate_stage_context(result, analysis, StageName.PROPOSITIONS, (), context)


def test_original_relation_is_accepted():
    analysis, context, finding = sample()
    check(analysis, context, [finding])


@pytest.mark.parametrize("field", ["citation_id", "authority_id", "claim_id", "quote_id"])
def test_unknown_relation_is_rejected_before_persistence(field):
    analysis, context, finding = sample()
    setattr(finding, field, uuid4())
    with pytest.raises(ValueError, match="outside stage context"):
        check(analysis, context, [finding])


def test_known_but_unrelated_authority_is_rejected():
    analysis, context, finding = sample()
    other = SimpleNamespace(id=uuid4())
    context["authorities"] += (other,)
    finding.authority_id = other.id
    with pytest.raises(ValueError, match="does not match citation"):
        check(analysis, context, [finding])


def test_known_but_unlinked_claim_is_rejected():
    analysis, context, finding = sample()
    other = SimpleNamespace(id=uuid4())
    context["claims"] += (other,)
    finding.claim_id = other.id
    with pytest.raises(ValueError, match="no matching citation link"):
        check(analysis, context, [finding])


def test_evidence_cannot_attach_to_unrelated_finding():
    analysis, context, finding = sample()
    text = analysis.document_snapshot["text"]
    evidence = EvidenceRecord(
        id=uuid4(),
        analysis_id=analysis.id,
        finding_id=uuid4(),
        citation_id=finding.citation_id,
        authority_id=None,
        claim_id=finding.claim_id,
        quote_id=None,
        source_type="document",
        snapshot_text=text,
        excerpt=text,
        source_sha256=sha256(text.encode()).hexdigest(),
        source_start_offset=0,
        source_end_offset=len(text),
    )
    with pytest.raises(ValueError, match="finding relations"):
        check(analysis, context, [finding, evidence])


def test_document_evidence_can_prove_filing_without_an_authority_reference():
    analysis, context, finding = sample()
    text = analysis.document_snapshot["text"]
    evidence = EvidenceRecord(
        id=uuid4(),
        analysis_id=analysis.id,
        finding_id=finding.id,
        citation_id=finding.citation_id,
        authority_id=None,
        claim_id=finding.claim_id,
        quote_id=None,
        source_type="document",
        snapshot_text=text,
        excerpt=text,
        source_sha256=sha256(text.encode()).hexdigest(),
        source_start_offset=0,
        source_end_offset=len(text),
    )
    check(analysis, context, [finding, evidence])
    evidence.source_type = "opinion_text"
    with pytest.raises(ValueError, match="finding relations"):
        check(analysis, context, [finding, evidence])
