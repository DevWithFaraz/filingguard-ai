"""Integrity checks on the actual T014 artifacts, not invented legal verdicts."""

import hashlib
import json
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import pytest
from pypdf import PdfReader

from filingguard.integrations.storage.service import _validate_pdf
from filingguard.modules.analyses.demo import DemoUnavailable, load_demo

ROOT = Path(__file__).resolve().parents[4]
FIXTURE = ROOT / "data" / "demo" / "curated-v1"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read_json(name):
    return json.loads((FIXTURE / name).read_text("utf-8"))


def fixture_file(relative):
    path = (FIXTURE / relative).resolve()
    assert path.is_relative_to(FIXTURE.resolve())
    assert path.is_file()
    return path


def test_public_sources_have_verified_snapshot_hashes_and_provenance():
    sources = read_json("sources.json")["sources"]
    assert {source["authority_id"] for source in sources} == {"brown", "miranda", "obergefell"}
    for source in sources:
        text_bytes = fixture_file(source["path"]).read_bytes()
        assert digest(text_bytes) == source["sha256"]
        assert digest(fixture_file(source["raw_path"]).read_bytes()) == source["raw_sha256"]
        assert len(text_bytes.decode("utf-8")) == source["characters"]
        assert source["provenance"] == "cached_public"
        assert source["attribution"]
        assert source["case_name"] and source["citation"]
        assert source["cluster_id"] > 0 and source["opinion_id"] > 0
        url = urlparse(source["source_url"])
        assert url.scheme == "https" and url.hostname == "www.courtlistener.com"
        assert url.path == f"/api/rest/v4/opinions/{source['opinion_id']}/"
        assert datetime.fromisoformat(source["retrieved_at"]).utcoffset() is not None
        assert source["provider_opinion_type"] in {"010combined", "020lead"}
        assert source["text_conversion"] in {"identity-v1", "htmlparser-block-boundaries-v1"}


def test_curated_pdf_preserves_words_and_exact_extraction_page_offsets():
    filing_bytes = (FIXTURE / "filing.txt").read_bytes()
    pdf_bytes = (FIXTURE / "filing.pdf").read_bytes()
    extraction = read_json("pdf-extraction.json")
    assert extraction["schema_version"] == 1
    assert extraction["method"] == "pypdf.extract_text"
    assert extraction["pypdf_version"]
    assert extraction["filing_sha256"] == digest(filing_bytes)
    assert extraction["pdf_sha256"] == digest(pdf_bytes)
    reader = PdfReader(FIXTURE / "filing.pdf", strict=True)
    assert not reader.is_encrypted
    assert 1 <= len(reader.pages) <= 20
    assert len(pdf_bytes) <= 10 * 1024 * 1024
    page_texts = [page.extract_text() for page in reader.pages]
    canonical = "".join(page_texts)
    assert canonical == extraction["text"]
    assert canonical.split() == filing_bytes.decode("utf-8").split()
    assert 0 < len(canonical) <= 100_000
    assert extraction["text_sha256"] == digest(canonical.encode("utf-8"))
    assert len(extraction["pages"]) == len(page_texts)
    start = 0
    for number, (text, span) in enumerate(zip(page_texts, extraction["pages"], strict=True), 1):
        assert span == {"page_number": number, "start": start, "end": start + len(text)}
        assert canonical[span["start"] : span["end"]] == text
        start += len(text)
    assert start == len(canonical)
    assert _validate_pdf(pdf_bytes) == (len(page_texts), len(canonical))


def test_curated_unreviewed_fixture_cannot_replay_results():
    manifest = read_json("manifest.json")
    assert manifest["fixture_id"] == "curated-v1"
    assert manifest["validation_status"] == "awaiting_human_review"
    assert manifest["mode"] == "cached_public"
    assert manifest["is_real_filing"] is False
    assert manifest["filing_path"] == "filing.txt"
    assert manifest["pdf_path"] == "filing.pdf"
    assert manifest["document_sha256"] == digest(fixture_file(manifest["filing_path"]).read_bytes())
    with pytest.raises(DemoUnavailable, match="human review"):
        load_demo(FIXTURE, manifest["fixture_id"], mode="demo")


def assert_exact_span(text, span):
    assert type(span["start"]) is int and type(span["end"]) is int
    assert 0 <= span["start"] < span["end"] <= len(text)
    assert text[span["start"] : span["end"]] == span["text"]
    assert span["text"].strip()


def test_expectations_link_exact_filing_and_public_source_spans_without_review():
    expectations = read_json("expectations.json")
    assert expectations["fixture_id"] == "curated-v1"
    assert expectations["validation_status"] == "awaiting_human_review"
    assert expectations["offset_unit"] == "unicode_code_points"
    assert expectations["interval"] == "half_open"
    filing = (FIXTURE / "filing.txt").read_bytes().decode("utf-8")
    sources = {
        source["authority_id"]: fixture_file(source["path"]).read_bytes().decode("utf-8")
        for source in read_json("sources.json")["sources"]
    }
    cases = expectations["cases"]
    assert len(cases) == 18
    assert {case["category"] for case in cases} == {
        "citation",
        "proposition",
        "quote",
        "privacy",
        "court_rules",
    }
    assert len({case["id"] for case in cases}) == len(cases)
    for case in cases:
        assert case["id"] and case["category"] and case["expected_status"] and case["reason"]
        assert_exact_span(filing, case["filing_span"])
        if "authority_id" in case:
            assert case["authority_id"] in sources
        if case["source_span"] is not None:
            span = case["source_span"]
            assert span["authority_id"] == case["authority_id"]
            assert_exact_span(sources[span["authority_id"]], span)
        elif case["category"] in {"proposition", "quote"}:
            assert case["expected_status"] == "insufficient_source"
            assert case["simulation"] == "opinion_text_unavailable"
    by_id = {case["id"]: case for case in cases}
    for authority in sources:
        assert by_id[f"citation-{authority}"]["expected_status"] == "verified"
        assert by_id[f"{authority}-supported"]["expected_status"] == "supported"
    assert by_id["brown-misrepresented"]["expected_status"] == "misrepresented"
    assert (
        by_id["quote-exact"]["filing_span"]["text"] == by_id["quote-exact"]["source_span"]["text"]
    )
    assert (
        by_id["quote-altered"]["filing_span"]["text"]
        != by_id["quote-altered"]["source_span"]["text"]
    )
    assert by_id["benign-event-date"]["expected_status"] == "no_finding"
    assert by_id["citation-unresolved"]["simulation"] == "lookup_not_found"
    assert by_id["lookup-unavailable"]["expected_status"] == "unavailable"
    assert by_id["lookup-unavailable"]["simulation"] == "provider_timeout"
    for case_id, ai_used, status in (
        ("disclosure-omitted", True, "needs_review"),
        ("disclosure-not-applicable", False, "skipped"),
    ):
        case = by_id[case_id]
        assert case["expected_status"] == status
        assert case["preconditions"] == {
            "ai_used": ai_used,
            "court_profile_id": "synthetic-demo-v1",
        }
