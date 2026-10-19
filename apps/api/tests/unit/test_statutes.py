"""Statute/regulation verification: configured lookups never treat transport errors as not-found."""

from uuid import uuid4

import httpx
import pytest

from filingguard.db.models import Analysis, Citation, Finding
from filingguard.integrations.providers.runtime import ProviderBudget
from filingguard.modules.analyses.schemas import StageName
from filingguard.modules.citations.service import extract_citations, verify_citations_for_analysis
from filingguard.modules.statutes.adapter import CatalogStatuteAdapter, HttpStatuteAdapter
from filingguard.modules.statutes.runner import statutes_stage
from filingguard.modules.statutes.service import collect_law_identities


def _analysis(text: str) -> Analysis:
    analysis = Analysis(
        id=uuid4(),
        mode="live",
        court_profile_id="unverified",
        ai_used=False,
        document_name="brief.txt",
        document_sha256="0" * 64,
    )
    analysis.document_snapshot = {"text": text, "pages": []}
    return analysis


CATALOG = {
    "usc:42:1983": {
        "jurisdiction": "US-federal",
        "version": "2024",
        "effective_date": "1996-05-20",
        "coverage_limitation": "Synthetic public catalog covers selected USC sections only.",
        "source_url": "https://www.law.cornell.edu/uscode/text/42/1983",
    }
}


class _RejectLawAdapter:
    def verify_and_resolve(self, lookup_key: str):
        raise AssertionError(f"Law citation was sent to the case adapter: {lookup_key}")


def test_unconfigured_source_skips_when_no_law_citations():
    result = statutes_stage(_analysis("See 347 U.S. 483."), ProviderBudget(0), adapter=None)
    result.validate(StageName.STATUTES)
    assert result.status.value == "skipped"
    assert result.coverage.eligible == 0
    assert result.records == ()


def test_unconfigured_source_is_unavailable_not_skipped():
    result = statutes_stage(_analysis("42 U.S.C. § 1983"), ProviderBudget(0), adapter=None)
    result.validate(StageName.STATUTES)
    assert result.status.value == "unavailable"
    assert result.coverage.evaluated == 0
    assert result.coverage.unavailable == 1
    assert result.records == ()
    assert "no statute or regulation source is configured" in (result.reason or "").lower()


def test_verified_statute_records_jurisdiction_and_effective_date():
    adapter = CatalogStatuteAdapter(CATALOG)
    result = statutes_stage(
        _analysis("The claim arises under 42 U.S.C. § 1983."),
        ProviderBudget(0),
        adapter=adapter,
    )
    result.validate(StageName.STATUTES)
    assert result.status.value == "completed"
    assert result.coverage.evaluated == result.coverage.eligible == 1
    findings = [row for row in result.records if isinstance(row, Finding)]
    assert findings == []
    identities = collect_law_identities("The claim arises under 42 U.S.C. § 1983.")
    assert identities[0].jurisdiction == "US-federal"
    assert identities[0].normalized_key == "usc:42:1983"


def test_not_found_is_not_fabrication():
    adapter = CatalogStatuteAdapter(CATALOG)
    result = statutes_stage(
        _analysis("See 99 U.S.C. § 1."),
        ProviderBudget(0),
        adapter=adapter,
    )
    result.validate(StageName.STATUTES)
    findings = [row for row in result.records if isinstance(row, Finding)]
    assert findings[0].type == "citation"
    assert findings[0].stage == "statutes"
    assert "absent" in findings[0].title.lower()
    assert "not prove fabrication" in findings[0].description.lower()
    evidence = [row for row in result.records if not isinstance(row, Finding)][0]
    assert evidence.source_metadata["verification_status"] == "not_found"
    assert evidence.source_metadata["jurisdiction"] == "US-federal"


def test_http_timeout_429_and_5xx_are_unavailable():
    def handler(request: httpx.Request) -> httpx.Response:
        path = str(request.url.params.get("citation"))
        if path.endswith("timeout"):
            raise httpx.ReadTimeout("timed out")
        if path.endswith("429"):
            return httpx.Response(429, json={"detail": "rate limited"})
        if path.endswith("500"):
            return httpx.Response(500, json={"detail": "error"})
        if path.endswith("404"):
            return httpx.Response(404, json={"detail": "missing route"})
        return httpx.Response(200, json={"found": False})

    http_adapter = HttpStatuteAdapter(
        "https://statutes.test",
        transport=httpx.MockTransport(handler),
    )
    from filingguard.modules.statutes.schemas import LawIdentity

    def identity(suffix: str) -> LawIdentity:
        return LawIdentity(
            raw_text=f"42 U.S.C. § {suffix}",
            start=0,
            end=10,
            normalized_key=f"usc:42:{suffix}",
            reporter="U.S.C.",
            title="42",
            section=suffix,
            jurisdiction="US-federal",
        )

    timeout = http_adapter.lookup(identity("timeout"))
    limited = http_adapter.lookup(identity("429"))
    server = http_adapter.lookup(identity("500"))
    missing_route = http_adapter.lookup(identity("404"))
    assert timeout.status.value == limited.status.value == server.status.value == "unavailable"
    assert missing_route.status.value == "unavailable"
    assert timeout.reason == "timeout"
    assert limited.reason == "rate_limited"
    assert server.reason == "http_failure"


def test_version_mismatch_when_cited_year_differs():
    adapter = CatalogStatuteAdapter(CATALOG)
    result = statutes_stage(
        _analysis("Liability under 42 U.S.C. § 1983 (2010) still applies."),
        ProviderBudget(0),
        adapter=adapter,
    )
    result.validate(StageName.STATUTES)
    findings = [row for row in result.records if isinstance(row, Finding)]
    assert any("version or effective date" in item.title.lower() for item in findings)
    evidence = next(row for row in result.records if not isinstance(row, Finding))
    assert evidence.source_metadata["verification_status"] == "version_mismatch"
    assert evidence.source_metadata["version"] == "2024"
    assert evidence.source_metadata["effective_date"] == "1996-05-20"
    assert evidence.source_metadata["cited_year"] == "2010"


def test_no_law_citations_are_skipped_when_source_configured():
    adapter = CatalogStatuteAdapter(CATALOG)
    result = statutes_stage(
        _analysis("The holding in 347 U.S. 483 controls."),
        ProviderBudget(0),
        adapter=adapter,
    )
    result.validate(StageName.STATUTES)
    assert result.status.value == "skipped"
    assert result.coverage.eligible == 0
    assert result.records == ()


def test_law_citations_are_not_verified_as_cases():
    text = "42 U.S.C. § 1983; 123 Yale L.J. 456"
    extraction = extract_citations(text)
    assert {item.extraction.kind for item in extraction.occurrences} >= {"law", "journal"}
    assert all(item.extraction.support == "unsupported" for item in extraction.occurrences)
    analysis_id = uuid4()
    segment = uuid4()
    rows = [
        Citation(
            id=uuid4(),
            analysis_id=analysis_id,
            raw_text=item.raw_text,
            normalized_text=item.normalized_text,
            segment_id=segment,
            page_number=1,
            start_offset=item.start,
            end_offset=item.end,
            extraction_metadata=item.extraction.model_dump(mode="json"),
            verification_status="not_run",
        )
        for item in extraction.occurrences
    ]
    verified, authorities = verify_citations_for_analysis(analysis_id, rows, _RejectLawAdapter())
    assert authorities == []
    assert {row.verification_status for row in verified} == {"not_run"}
    assert all(row.authority_id is None for row in verified)


def test_http_found_false_is_not_found_not_unavailable():
    adapter = HttpStatuteAdapter(
        "https://statutes.test",
        transport=httpx.MockTransport(
            lambda _request: httpx.Response(200, json={"found": False})
        ),
    )
    from filingguard.modules.statutes.schemas import LawIdentity

    result = adapter.lookup(
        LawIdentity(
            raw_text="42 U.S.C. § 1983",
            start=0,
            end=16,
            normalized_key="usc:42:1983",
            reporter="U.S.C.",
            title="42",
            section="1983",
            jurisdiction="US-federal",
        )
    )
    assert result.status.value == "not_found"


@pytest.mark.parametrize("status_code", [429, 500, 503])
def test_http_error_status_never_becomes_not_found(status_code: int):
    adapter = HttpStatuteAdapter(
        "https://statutes.test",
        transport=httpx.MockTransport(
            lambda _request: httpx.Response(status_code, json={"found": False})
        ),
    )
    from filingguard.modules.statutes.schemas import LawIdentity

    result = adapter.lookup(
        LawIdentity(
            raw_text="42 U.S.C. § 1983",
            start=0,
            end=16,
            normalized_key="usc:42:1983",
            reporter="U.S.C.",
            title="42",
            section="1983",
            jurisdiction="US-federal",
        )
    )
    assert result.status.value == "unavailable"
    assert result.status.value != "not_found"
