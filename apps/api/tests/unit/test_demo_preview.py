import json
import shutil

import pytest

from filingguard.modules.analyses.demo import DemoUnavailable
from filingguard.modules.analyses.demo_preview import FIXTURE_ROOT, load_demo_preview


def test_reviewed_example_has_truthful_provenance_and_exact_evidence():
    preview = load_demo_preview(FIXTURE_ROOT, "curated-v1", mode="demo")
    assert preview.execution_status == "not_run"
    assert preview.review_kind == "delegated_assistant"
    assert len(preview.sources) == 3
    assert len(preview.examples) == 18
    assert sum(case.judgment == "conditional" for case in preview.examples) == 5
    assert "human" in " ".join(preview.limitations)
    for case in preview.examples:
        span = case.filing_span
        assert preview.document[span.start:span.end] == span.text
    by_id = {case.id: case for case in preview.examples}
    assert "unavailable" in by_id["disclosure-omitted"].condition
    assert by_id["quote-altered"].expected_status == "close"
    assert "provisional" in by_id["quote-altered"].condition
    assert by_id["lookup-unavailable"].expected_status == "unavailable"


@pytest.mark.parametrize("mode", ["live", "cached_public", "", None])
def test_preview_never_admits_live_input(mode):
    with pytest.raises(DemoUnavailable):
        load_demo_preview(FIXTURE_ROOT, "curated-v1", mode=mode)


def test_exact_fixture_identity_required():
    preview = load_demo_preview(FIXTURE_ROOT, "curated-v1", mode="demo")
    load_demo_preview(FIXTURE_ROOT, "curated-v1", mode="demo", input_text=preview.document)
    for text in (preview.document + " ", "Different filing"):
        with pytest.raises(DemoUnavailable, match="does not match"):
            load_demo_preview(FIXTURE_ROOT, "curated-v1", mode="demo", input_text=text)
    with pytest.raises(DemoUnavailable, match="Unknown"):
        load_demo_preview(FIXTURE_ROOT, "../secret", mode="demo")


@pytest.fixture
def copied_fixture(tmp_path):
    destination = tmp_path / "curated-v1"
    shutil.copytree(FIXTURE_ROOT, destination)
    return destination


@pytest.mark.parametrize("name", [
    "filing.txt", "filing.pdf", "manifest.json", "sources.json", "expectations.json",
    "scenarios.json", "pdf-extraction.json", "authorities/brown.txt", "authorities/miranda.html",
])
def test_changed_artifact_or_source_is_rejected(copied_fixture, name):
    path = copied_fixture / name
    path.write_bytes(path.read_bytes() + b" ")
    with pytest.raises(DemoUnavailable, match="integrity"):
        load_demo_preview(copied_fixture, "curated-v1", mode="demo")


def test_review_receipt_is_required_and_cannot_claim_human_review(copied_fixture):
    path = copied_fixture / "review.json"
    receipt = json.loads(path.read_text())
    receipt["review_kind"] = "human_reviewed"
    path.write_text(json.dumps(receipt))
    with pytest.raises(DemoUnavailable):
        load_demo_preview(copied_fixture, "curated-v1", mode="demo")
    path.unlink()
    with pytest.raises(DemoUnavailable):
        load_demo_preview(copied_fixture, "curated-v1", mode="demo")


def test_demo_http_endpoint_requires_explicit_mode_and_never_creates_analysis(client):
    response = client.get("/api/v1/demos/curated-v1?mode=demo")
    assert response.status_code == 200
    assert response.json()["execution_status"] == "not_run"
    assert "analysis_id" not in response.json()
    assert response.headers["cache-control"] == "no-store"
    assert client.get("/api/v1/demos/curated-v1").status_code == 422
    assert client.get("/api/v1/demos/curated-v1?mode=live").status_code == 422
    assert client.get("/api/v1/demos/unknown?mode=demo").status_code == 404
    assert client.post("/api/v1/demos/curated-v1?mode=demo").status_code == 405
    assert client.post("/api/v1/analyses", json={"text": "private"}).status_code == 503


def test_demo_unavailability_is_safe_not_stale_or_favorable(client, monkeypatch, tmp_path):
    monkeypatch.setattr("filingguard.api.routes.demos.FIXTURE_ROOT", tmp_path)
    response = client.get("/api/v1/demos/curated-v1?mode=demo")
    assert response.status_code == 503
    assert "examples" not in response.json()
    assert str(tmp_path) not in response.text
