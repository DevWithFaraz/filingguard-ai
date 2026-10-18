import io
from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest
from pypdf import PdfReader

from filingguard.modules.analyses.schemas import Coverage, StageName, StageState, StageStatus
from filingguard.modules.reports.service import render_report, safe_text
from filingguard.modules.scoring.service import score_review


def finding(severity, *, kind="quote", status="open"):
    return SimpleNamespace(id=uuid4(), type=kind, severity=severity, status=status)


def stages(*, legal=True, unavailable=0):
    return [
        StageState(
            name=StageName.QUOTES if legal else StageName.PRIVACY,
            status=StageStatus.PARTIAL if unavailable else StageStatus.COMPLETED,
            coverage=Coverage(eligible=1 + unavailable, evaluated=1, unavailable=unavailable),
            reason="A dependency is unavailable" if unavailable else None,
        )
    ]


def test_scoring_weights_are_deterministic_and_critical_exceeds_warning():
    severe, warning = finding("critical"), finding("medium")
    first = score_review(stages(), [severe], status="partial")
    second = score_review(stages(), [warning], status="partial")
    assert first["value"] < second["value"]
    assert first == score_review(stages(), [severe], status="partial")
    assert first["version"] == "integrity-v1"
    assert first["deductions"][0]["finding_id"] == str(severe.id)
    assert first["deductions"][0]["points"] > second["deductions"][0]["points"]


@pytest.mark.parametrize("status", ["not_run", "queued", "running"])
def test_active_or_unrun_analysis_has_no_score(status):
    result = score_review(stages(), [finding("high")], status=status)
    assert result["value"] is None and result["risk_level"] is None


def test_local_privacy_checks_cannot_become_legal_readiness_score():
    result = score_review(stages(legal=False), [finding("low", kind="privacy")], status="partial")
    assert result["value"] is None
    assert result["risk_level"] is None
    by_type = {row["type"]: row for row in result["categories"]}
    assert by_type["privacy"]["value"] == 97
    assert by_type["quote"]["value"] is None
    assert by_type["citation"]["evaluated"] == 0


def test_missing_legal_checks_remain_unknown_and_provisional():
    unavailable = StageState(
        name=StageName.PROPOSITIONS,
        status=StageStatus.UNAVAILABLE,
        coverage=Coverage(eligible=3, unavailable=3),
        reason="Source unavailable",
    )
    unknown = score_review([unavailable], [], status="partial")
    assert unknown["value"] is None
    some = score_review(stages(unavailable=3), [], status="partial")
    assert some["provisional"] is True
    assert some["risk_level"] != "ready_for_review"
    assert "unknown" in some["limitation"].lower()


def test_system_warnings_and_resolved_findings_do_not_deduct_twice():
    result = score_review(
        stages(),
        [
            finding("critical", kind="system"),
            finding("critical", status="resolved"),
            finding("info"),
        ],
        status="partial",
    )
    assert result["value"] == 100
    assert result["risk_level"] != "ready_for_review"
    assert len(result["deductions"]) == 1


def test_score_saturates_at_zero():
    assert (
        score_review(stages(), [finding("critical") for _ in range(8)], status="partial")["value"]
        == 0
    )


def test_explanation_echoes_and_new_identifiers_are_masked():
    filing = "SSN 123-45-6789 and client@example.com"
    output = safe_text("Model repeats 123-45-6789; alternate new@example.com", filing)
    assert "123-45-6789" not in output and "new@example.com" not in output
    assert "***********" in output


def report_input():
    return {
        "analysis_id": str(uuid4()),
        "created_at": datetime.now(UTC),
        "mode": "live",
        "status": "partial",
        "court_profile_id": "unverified",
        "limitation": "Human review required. Not legal advice.",
        "score": score_review(stages(), [finding("high")], status="partial"),
        "coverage": {
            "evaluated": 1,
            "eligible": 2,
            "unavailable": 1,
            "pending": 0,
            "truncated": False,
        },
        "stages": [stages()[0].model_dump(mode="json")],
        "findings": [
            {
                "severity": "high",
                "title": "<script>alert('x')</script>",
                "description": "<img src=x onerror=alert(1)>",
                "masked_excerpt": "<b>source</b>",
                "evidence_count": 1,
            }
        ],
        "citations": [],
        "claims": [],
        "quotes": [],
    }


def test_html_escapes_all_untrusted_finding_markup():
    report = render_report(report_input(), format="html")
    assert "<script>" not in report and "<img " not in report
    assert "&lt;script&gt;" in report and "&lt;img " in report
    assert "&lt;b&gt;source&lt;/b&gt;" in report


def test_report_uses_given_saved_results_without_new_classification(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("Export attempted a new model classification")

    monkeypatch.setattr(
        "filingguard.integrations.llm.adapter.GroqPropositionAdapter.review", forbidden
    )
    results = report_input()
    rendered = render_report(results)
    assert results["analysis_id"] in rendered
    assert "1/2 evaluated" in rendered
    assert "1 unavailable" in rendered
    assert "integrity-v1" in rendered


def test_report_includes_evidence_lineage_and_determination():
    results = report_input()
    results["findings"] = [
        {
            "severity": "medium",
            "type": "quote",
            "title": "Quotation differs from source",
            "description": "Quotation text differs from the authoritative opinion excerpt.",
            "masked_excerpt": "Equal access is not a fundamental right.",
            "start": 10,
            "end": 30,
            "evidence_count": 1,
            "ai_assisted": False,
            "evidence": [
                {
                    "id": str(uuid4()),
                    "excerpt": "Equal access is a fundamental right.",
                    "source_url": "https://www.courtlistener.com/opinion/123/",
                    "source_sha256": "a" * 64,
                    "retrieved_at": "2026-10-17T12:00:00Z",
                    "source_start": 32,
                    "source_end": 74,
                    "method_version": "quote-forensics-v1",
                    "model_version": None,
                    "prompt_version": None,
                    "provenance": "cached_public",
                    "confidence_level": "high",
                }
            ],
        }
    ]
    rendered = render_report(results)
    assert "Determination methodology:" in rendered
    assert "Deterministic or rule-based check" in rendered
    assert "Lineage chain" in rendered
    assert "1. Document Span: offsets 10-30 (Unicode code points)" in rendered
    assert '   Excerpt: Equal access is not a fundamental right.' in rendered
    assert "2. Extraction Target: quote" in rendered
    assert "3. Source Authority: https://www.courtlistener.com/opinion/123/" in rendered
    assert '   Source Passage: Equal access is a fundamental right.' in rendered
    assert "4. Verification Method: quote-forensics-v1;" in rendered
    assert "provenance: cached_public;" in rendered
    assert "5. Finding Verdict: MEDIUM · Quotation differs from source" in rendered


def test_render_report_pdf_valid_bytes_and_structure():
    results = report_input()
    results["findings"] = [
        {
            "severity": "high",
            "type": "citation",
            "title": "Citation unverified in CourtListener",
            "description": "Reporter volume and page could not be confirmed.",
            "masked_excerpt": "Brown v. Board, 347 U.S. 483 (1954)",
            "start": 100,
            "end": 134,
            "evidence_count": 1,
            "ai_assisted": False,
            "evidence": [
                {
                    "id": str(uuid4()),
                    "excerpt": "Separate educational facilities are inherently unequal.",
                    "source_url": "https://www.courtlistener.com/opinion/105221/brown/",
                    "source_sha256": "c" * 64,
                    "retrieved_at": "2026-10-17T14:00:00Z",
                    "source_start": 50,
                    "source_end": 104,
                    "method_version": "citation-v1",
                    "model_version": None,
                    "prompt_version": None,
                    "provenance": "cached_public",
                    "confidence_level": "high",
                }
            ],
        }
    ]
    results["citations"] = [
        {
            "masked_raw_text": "347 U.S. 483",
            "verification_status": "verified",
            "limitation": None,
            "authority": {
                "case_name": "Brown v. Board of Education",
                "source_url": "https://www.courtlistener.com/opinion/105221/brown/",
                "source_sha256": "c" * 64,
            },
        }
    ]

    pdf_bytes = render_report(results, format="pdf")
    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes.startswith(b"%PDF-1.")

    reader = PdfReader(io.BytesIO(pdf_bytes))
    assert len(reader.pages) >= 1

    extracted_text = "\n".join(page.extract_text() for page in reader.pages)
    assert "FilingGuard AI" in extracted_text
    assert "Pre-Filing Forensic Assurance" in extracted_text
    assert "LEGAL ASSURANCE DISCLAIMER" in extracted_text
    assert "Integrity Score:" in extracted_text
    assert "Verification Stage Coverage" in extracted_text
    assert "Forensic Findings" in extracted_text
    assert "01 Document Span" in extracted_text
    assert "02 Extraction Target" in extracted_text
    assert "03 Source Authority" in extracted_text
    assert "04 Verification Method" in extracted_text
    assert "05 Finding Verdict" in extracted_text
    assert "Brown v. Board of Education" in extracted_text
    assert "Page 1 of " in extracted_text


def test_render_report_pdf_handles_long_finding_wrapping_and_multipage():
    results = report_input()
    long_desc = "This is a detailed legal forensic finding description. " * 30
    long_excerpt = (
        "The petitioner claims that procedural due process requires immediate stay. " * 15
    )

    results["findings"] = [
        {
            "severity": "critical",
            "type": "claim_support",
            "title": f"Complex Multi-Hop Finding #{i} With Extensive Procedural Reasoning",
            "description": long_desc,
            "masked_excerpt": long_excerpt,
            "start": i * 100,
            "end": i * 100 + 200,
            "evidence_count": 1,
            "ai_assisted": True,
            "evidence": [
                {
                    "id": str(uuid4()),
                    "excerpt": (
                        "A balancing test must be applied in all non-emergency procedures. " * 8
                    ),
                    "source_url": f"https://www.courtlistener.com/opinion/{1000 + i}/test-case/",
                    "source_sha256": "d" * 64,
                    "retrieved_at": "2026-10-17T15:00:00Z",
                    "source_start": 0,
                    "source_end": 400,
                    "method_version": "proposition-v1",
                    "model_version": "gpt-oss-120b",
                    "prompt_version": "v1",
                    "provenance": "synthetic",
                    "confidence_level": "medium",
                }
            ],
        }
        for i in range(5)
    ]

    pdf_bytes = render_report(results, format="pdf")
    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes.startswith(b"%PDF-1.")

    reader = PdfReader(io.BytesIO(pdf_bytes))
    # 5 long findings with evidence must span multiple pages cleanly without clipping
    assert len(reader.pages) >= 2

    # Check footer pagination across multiple pages
    last_page_text = reader.pages[-1].extract_text()
    assert f"Page {len(reader.pages)} of {len(reader.pages)}" in last_page_text


def test_pdf_escapes_xml_and_untrusted_markup():
    results = report_input()
    results["findings"] = [
        {
            "severity": "high",
            "type": "privacy",
            "title": "<script>alert('xss')</script> & <b>bold</b>",
            "description": "Found tag <img src='x' onerror='alert(1)'> inside & outside.",
            "masked_excerpt": "Span <tag>with special & characters</tag>",
            "start": 0,
            "end": 50,
            "evidence_count": 0,
            "ai_assisted": False,
        }
    ]

    # ReportLab parses XML tags inside Paragraphs; unescaped tags would cause XML errors.
    # The generator escapes all untrusted text, so this builds successfully.
    pdf_bytes = render_report(results, format="pdf")
    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes.startswith(b"%PDF-1.")


def test_saved_graph_multiple_claims_per_authority_and_unsupported_warning_nodes(monkeypatch):
    """Verifies FR-064 (multiple claims to single authority) and FR-106 (unsupported claims)."""
    from filingguard.modules.reports.service import saved_graph

    auth_id = str(uuid4())
    cit1_id = str(uuid4())
    cit2_id = str(uuid4())
    claim1_id = str(uuid4())
    claim2_id = str(uuid4())
    seg_id = str(uuid4())
    finding_unsupported = str(uuid4())

    mock_results = {
        "analysis_id": str(uuid4()),
        "citations": [
            {
                "id": cit1_id,
                "masked_raw_text": "347 U.S. 483",
                "verification_status": "verified",
                "authority_id": auth_id,
                "authority": {"case_name": "Brown v. Board", "source_url": "https://example.com"},
            },
            {
                "id": cit2_id,
                "masked_raw_text": "347 U.S. 483 at 485",
                "verification_status": "verified",
                "authority_id": auth_id,
                "authority": {"case_name": "Brown v. Board", "source_url": "https://example.com"},
            },
        ],
        "claims": [
            {
                "id": claim1_id,
                "text": "Claim 1: Segregation in public schools violates equal protection.",
                "location": {"segment_id": seg_id},
                "links": [
                    {
                        "id": str(uuid4()),
                        "citation_id": cit1_id,
                        "authority_id": auth_id,
                        "support_status": "supported",
                    }
                ],
            },
            {
                "id": claim2_id,
                "text": "Claim 2: The doctrine of separate but equal was upheld.",
                "location": {"segment_id": seg_id},
                "links": [
                    {
                        "id": str(uuid4()),
                        "citation_id": cit2_id,
                        "authority_id": auth_id,
                        "support_status": "contradicted",
                    }
                ],
            },
        ],
        "findings": [
            {
                "id": finding_unsupported,
                "claim_id": claim2_id,
                "authority_id": auth_id,
                "citation_id": cit2_id,
                "segment_id": seg_id,
                "type": "claim_support",
                "severity": "critical",
                "title": "Proposition contradicted by source authority",
            }
        ],
    }

    class MockSegment:
        paragraph_index = 0

    class MockRepo:
        def list_records(self, owner, identity, model):
            s = MockSegment()
            s.id = seg_id
            return [s]

    monkeypatch.setattr(
        "filingguard.modules.reports.service.saved_results",
        lambda repo, owner, ident: mock_results,
    )

    graph = saved_graph(MockRepo(), "owner", "ident")

    # FR-064: Multiple claims associated with a single authority node
    authority_nodes = [n for n in graph["nodes"] if n["kind"] == "authority"]
    assert len(authority_nodes) == 1
    auth_node = authority_nodes[0]
    assert auth_node["id"] == f"authority:{auth_id}"
    assert auth_node["label"] == "Brown v. Board"

    # Both claims link to this same authority node
    auth_edges = [e for e in graph["edges"] if e["target"] == f"authority:{auth_id}"]
    assert len(auth_edges) == 2
    assert {e["source"] for e in auth_edges} == {f"claim:{claim1_id}", f"claim:{claim2_id}"}

    # FR-106: Unsupported claim is marked with "unsupported" status as a warning node
    claim_nodes = {n["id"]: n for n in graph["nodes"] if n["kind"] == "claim"}
    assert claim_nodes[f"claim:{claim1_id}"]["status"] == "supported"
    assert claim_nodes[f"claim:{claim2_id}"]["status"] == "unsupported"

    # Finding IDs linked correctly
    assert finding_unsupported in claim_nodes[f"claim:{claim2_id}"]["finding_ids"]
    assert finding_unsupported in auth_node["finding_ids"]



