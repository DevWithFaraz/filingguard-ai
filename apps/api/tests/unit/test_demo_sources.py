"""Cached public source admission never grants results to arbitrary/live input."""

import hashlib
import shutil
import time
from types import SimpleNamespace
from uuid import uuid4

import pytest

from filingguard.db.models import Authority, Citation
from filingguard.integrations.providers.runtime import ProviderBudget
from filingguard.modules.analyses.demo import DemoUnavailable
from filingguard.modules.analyses.demo_preview import FIXTURE_ROOT, load_demo_preview
from filingguard.modules.analyses.demo_sources import CachedDemoSources, cached_demo_citations
from filingguard.modules.analyses.execution import ReviewSegment
from filingguard.modules.analyses.runners import local_runners
from filingguard.modules.analyses.schemas import StageName
from filingguard.modules.documents.extraction import extract_text


def demo_analysis():
    preview = load_demo_preview(FIXTURE_ROOT, "curated-v1", mode="demo")
    identity = uuid4()
    document = extract_text(preview.document)
    return SimpleNamespace(
        id=identity,
        mode="demo",
        demo_fixture_id="curated-v1",
        document_sha256=preview.document_sha256,
        document_snapshot=document.model_dump(),
        review_segments=tuple(
            ReviewSegment(
                id=uuid4(),
                start=p.start,
                end=p.end,
                page_number=p.page_number,
            )
            for p in document.paragraphs
        ),
    )


def test_source_replay_uses_public_snapshots_not_expected_verdicts():
    analysis = demo_analysis()
    adapter = CachedDemoSources(analysis)
    for citation in ("347 U.S. 483", "384 U.S. 436", "576 U.S. 644"):
        lookup, source = adapter.verify_and_resolve(citation)
        assert lookup.status == "verified"
        assert lookup.reason == "cached_public_source"
        assert source.source_metadata["provenance"] == "cached_public"
        assert hashlib.sha256(source.opinion_text.encode()).hexdigest() == source.source_sha256
    lookup, source = adapter.verify_and_resolve("999 F.9th 1234")
    assert lookup.status == "unavailable" and source is None
    assert "not_found" not in lookup.model_dump_json()


@pytest.mark.parametrize("change", ["mode", "id", "text", "hash"])
def test_source_admission_rejects_live_unknown_altered_and_wrong_hash(change):
    analysis = demo_analysis()
    if change == "mode":
        analysis.mode = "live"
    elif change == "id":
        analysis.demo_fixture_id = "other"
    elif change == "text":
        analysis.document_snapshot["text"] += " "
    else:
        analysis.document_sha256 = "a" * 64
    with pytest.raises(DemoUnavailable):
        CachedDemoSources(analysis)
    result = cached_demo_citations(analysis, ProviderBudget(time.monotonic() + 30))
    assert result.status == "unavailable" and not result.records


def test_changed_cached_source_is_rejected(tmp_path):
    root = tmp_path / "curated-v1"
    shutil.copytree(FIXTURE_ROOT, root)
    source = root / "authorities/brown.txt"
    source.write_bytes(source.read_bytes() + b" altered")
    with pytest.raises(DemoUnavailable, match="integrity"):
        CachedDemoSources(demo_analysis(), root=root)


def test_registered_demo_runner_executes_extraction_and_has_cached_receipts():
    result = local_runners()[StageName.CITATIONS](
        demo_analysis(), ProviderBudget(time.monotonic() + 30)
    )
    result.validate(StageName.CITATIONS)
    citations = [r for r in result.records if isinstance(r, Citation)]
    authorities = [r for r in result.records if isinstance(r, Authority)]
    assert len(authorities) == 3
    assert sum(c.verification_status == "verified" for c in citations) >= 4
    for c in citations:
        if c.verification_status == "verified":
            assert c.extraction_metadata["verification"]["method"] == "cached-public-source-v1"
    assert "Cached public" in result.reason


def test_live_input_identical_to_demo_does_not_receive_cached_sources():
    analysis = demo_analysis()
    analysis.mode = "live"
    result = local_runners()[StageName.CITATIONS](analysis, ProviderBudget(time.monotonic() + 30))
    assert not any(isinstance(r, Authority) for r in result.records)
    assert all(r.verification_status == "not_run" for r in result.records)


def test_live_lookup_failure_is_not_a_cached_demo_fallback(monkeypatch):
    from filingguard.modules.analyses import demo_sources
    from filingguard.modules.analyses.execution import StageResult
    from filingguard.modules.analyses.schemas import StageStatus

    analysis = demo_analysis()
    analysis.mode = "live"
    failure = StageResult(status=StageStatus.UNAVAILABLE, reason="Synthetic provider outage")
    monkeypatch.setattr(demo_sources, "verified_citation_stage", lambda *_: failure)
    monkeypatch.setattr(
        demo_sources, "CachedDemoSources", lambda *_: pytest.fail("Unexpected cache")
    )
    assert demo_sources.live_or_demo_citations(analysis, ProviderBudget(time.monotonic() + 30)) is (
        failure
    )
