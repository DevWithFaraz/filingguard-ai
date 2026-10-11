from datetime import UTC, datetime
from hashlib import sha256
from types import SimpleNamespace
from uuid import uuid4

from filingguard.db.models import Citation
from filingguard.modules.analyses.schemas import CitationStatus
from filingguard.modules.citations.service import verify_citations_for_analysis


class Adapter:
    def __init__(self, text="Public source"):
        self.calls = 0
        self.text = text

    def verify_and_resolve(self, query):
        self.calls += 1
        # A separate canonical alias must not count as another outbound query.
        lookup = SimpleNamespace(
            status=CitationStatus.VERIFIED,
            reason="single_match",
            limitation=None,
            normalized_citation="canonical " + query,
        )
        authority = SimpleNamespace(
            cluster_id=self.calls,
            case_name="Synthetic budget control",
            citation=query,
            court="synthetic",
            year=2000,
            source_url="https://www.courtlistener.com/opinion/1/",
            opinion_text_available=True,
            opinion_text=self.text,
            source_sha256=sha256(self.text.encode()).hexdigest(),
            retrieved_at=datetime.now(UTC),
            source_metadata={"provenance": "synthetic"},
        )
        return lookup, authority


def rows(identity, count):
    return [
        Citation(
            id=uuid4(),
            analysis_id=identity,
            raw_text=f"{index + 1} U.S. 1",
            normalized_text=f"{index + 1} U.S. 1",
            extraction_metadata={"support": "recognized"},
            verification_status="not_run",
        )
        for index in range(count)
    ]


def test_query_cap_counts_requests_and_preserves_every_occurrence():
    identity, adapter = uuid4(), Adapter()
    citations, authorities = verify_citations_for_analysis(identity, rows(identity, 26), adapter)
    assert adapter.calls == len(authorities) == 25
    assert len(citations) == 26
    assert citations[-1].verification_status == "unavailable"
    assert citations[-1].extraction_metadata["verification"]["reason"] == "authority_limit"


def test_unicode_snapshot_budget_preserves_identity_without_partial_source_text():
    identity, adapter = uuid4(), Adapter("漢" * 500_000)
    citations, authorities = verify_citations_for_analysis(identity, rows(identity, 3), adapter)
    assert all(c.verification_status == "verified" for c in citations)
    assert [a.opinion_text_available for a in authorities] == [True, True, False]
    limited = authorities[-1]
    assert limited.opinion_text is None and limited.source_sha256 is None
    assert limited.source_metadata["text_unavailable_reason"] == "analysis_source_snapshot_budget"
