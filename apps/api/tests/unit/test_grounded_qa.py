"""Unit tests for Grounded Q&A service (FR-260 through FR-264)."""

from uuid import uuid4

import pytest

from filingguard.db.models import (
    Authority,
    EvidenceRecord,
    Finding,
    Quote,
)
from filingguard.modules.analyses.schemas import AnalysisStatus
from filingguard.modules.grounded_qa.service import (
    MAX_QUESTIONS_PER_ANALYSIS,
    ask_finding_question,
    classify_question_intent,
    clear_qa_store,
    get_finding_qa_history,
)


class MockAnalysis:
    def __init__(self, id, owner_hash="owner-1", status=AnalysisStatus.COMPLETED):
        self.id = id
        self.owner_hash = owner_hash
        self.status = status
        self.document_snapshot = {"text": "Federal court filing text sample."}


class MockFinding:
    def __init__(
        self,
        id,
        analysis_id,
        type="quote",
        severity="high",
        title="Quotation not found in cited authority",
        description="The quotation could not be verified.",
        authority_id=None,
        citation_id=None,
        claim_id=None,
        quote_id=None,
        start_offset=10,
        end_offset=50,
        rule_id=None,
    ):
        self.id = id
        self.analysis_id = analysis_id
        self.type = type
        self.severity = severity
        self.title = title
        self.description = description
        self.authority_id = authority_id
        self.citation_id = citation_id
        self.claim_id = claim_id
        self.quote_id = quote_id
        self.start_offset = start_offset
        self.end_offset = end_offset
        self.rule_id = rule_id


class MockEvidenceRecord:
    def __init__(
        self,
        id,
        analysis_id,
        finding_id,
        excerpt="The court held that evidence must be suppressed.",
        source_url="https://www.courtlistener.com/opinion/12345/brown-v-board/",
        source_sha256="a" * 64,
        source_label="Brown v. Board of Education",
        method_version="quote-v1",
    ):
        self.id = id
        self.analysis_id = analysis_id
        self.finding_id = finding_id
        self.excerpt = excerpt
        self.source_url = source_url
        self.source_sha256 = source_sha256
        self.source_label = source_label
        self.method_version = method_version


class MockRepository:
    def __init__(self):
        self.analyses = {}
        self.records = {}

    def get_analysis(self, owner_hash, analysis_id):
        analysis = self.analyses.get(analysis_id)
        if not analysis or analysis.owner_hash != owner_hash:
            from filingguard.db.repository import AnalysisNotFound

            raise AnalysisNotFound("Analysis not found")
        return analysis

    def get_record(self, owner_hash, analysis_id, model_class, record_id):
        self.get_analysis(owner_hash, analysis_id)
        return self.records.get((analysis_id, model_class, record_id))

    def list_records(self, owner_hash, analysis_id, model_class):
        self.get_analysis(owner_hash, analysis_id)
        return [
            rec
            for (aid, mclass, _), rec in self.records.items()
            if aid == analysis_id and mclass == model_class
        ]


@pytest.fixture(autouse=True)
def clean_store():
    clear_qa_store()
    yield
    clear_qa_store()


def test_classify_question_intent_allowed():
    status, reason = classify_question_intent("Why was this claim marked weak?")
    assert status == "answered"
    assert reason == "none"

    status, reason = classify_question_intent("What evidence did you use?")
    assert status == "answered"
    assert reason == "none"

    status, reason = classify_question_intent("What source passage supports this?")
    assert status == "answered"
    assert reason == "none"


def test_classify_question_intent_refuses_legal_advice():
    for q in [
        "What should I argue in court?",
        "Should I file this motion?",
        "Will I win my appeal?",
        "What are my odds of winning?",
        "Rewrite my legal strategy for this issue",
        "Give me legal advice on dismissing the claim",
        "Can I sue opposing counsel for this?",
    ]:
        status, reason = classify_question_intent(q)
        assert status == "refused", f"Expected refusal for: {q}"
        assert reason == "broad_legal_advice", f"Expected broad_legal_advice for: {q}"


def test_classify_question_intent_refuses_out_of_scope():
    for q in [
        "Tell me a joke",
        "What is the weather outside?",
        "Summarize the entire document",
        "Summarize everything for me",
        "Write a poem about the judge",
    ]:
        status, reason = classify_question_intent(q)
        assert status == "refused", f"Expected refusal for: {q}"
        assert reason == "out_of_scope", f"Expected out_of_scope for: {q}"


def test_ask_finding_question_answered_with_evidence():
    repo = MockRepository()
    aid = uuid4()
    fid = uuid4()
    eid1 = uuid4()
    eid2 = uuid4()
    auth_id = uuid4()

    repo.analyses[aid] = MockAnalysis(aid)
    repo.records[(aid, Finding, fid)] = MockFinding(
        fid,
        aid,
        type="claim_support",
        severity="critical",
        title="Claim contradicts cited authority",
        description="The cited authority held opposite of claim.",
        authority_id=auth_id,
    )
    repo.records[(aid, Authority, auth_id)] = Authority(
        id=auth_id,
        analysis_id=aid,
        source="courtlistener",
        case_name="Miranda v. Arizona",
        citation="384 U.S. 436",
        court="scotus",
        year=1966,
        source_url="https://www.courtlistener.com/opinion/107252/miranda-v-arizona/",
        source_sha256="b" * 64,
        opinion_text_available=True,
    )
    repo.records[(aid, EvidenceRecord, eid1)] = MockEvidenceRecord(
        eid1,
        aid,
        fid,
        excerpt="The prosecution may not use statements stemming from custodial interrogation.",
        source_url="https://www.courtlistener.com/opinion/107252/miranda-v-arizona/",
    )
    repo.records[(aid, EvidenceRecord, eid2)] = MockEvidenceRecord(
        eid2,
        aid,
        fid,
        excerpt="Prior to any questioning, the person must be warned.",
        source_url="https://www.courtlistener.com/opinion/107252/miranda-v-arizona/",
    )

    resp = ask_finding_question(repo, "owner-1", aid, fid, "What evidence did you use?")
    assert resp.status == "answered"
    assert resp.refusal_reason == "none"
    assert eid1 in resp.evidence_record_ids
    assert eid2 in resp.evidence_record_ids
    assert "Miranda v. Arizona" in resp.source_authorities
    assert "Evidence Record" in resp.answer
    assert "retrieved via quote-v1" in resp.answer

    history = get_finding_qa_history(repo, "owner-1", aid, fid)
    assert history.count == 1
    assert history.questions[0].question == "What evidence did you use?"


def test_ask_finding_question_why_flagged():
    repo = MockRepository()
    aid = uuid4()
    fid = uuid4()
    quote_id = uuid4()

    repo.analyses[aid] = MockAnalysis(aid)
    repo.records[(aid, Finding, fid)] = MockFinding(
        fid,
        aid,
        type="quote",
        severity="high",
        title="Quotation not found in cited opinion",
        description="The quotation could not be matched verbatim.",
        quote_id=quote_id,
    )
    repo.records[(aid, Quote, quote_id)] = Quote(
        id=quote_id,
        analysis_id=aid,
        segment_id=uuid4(),
        quote_text="fabricated quote",
        match_status="not_found",
        start_offset=10,
        end_offset=30,
        page_number=1,
    )

    resp = ask_finding_question(repo, "owner-1", aid, fid, "Why is this quote flagged?")
    assert resp.status == "answered"
    assert "Quotation not found in cited opinion" in resp.answer
    assert "high" in resp.answer
    assert "status: not_found" in resp.answer


def test_ask_finding_question_no_evidence_transparency():
    repo = MockRepository()
    aid = uuid4()
    fid = uuid4()

    repo.analyses[aid] = MockAnalysis(aid)
    repo.records[(aid, Finding, fid)] = MockFinding(
        fid,
        aid,
        type="citation",
        severity="critical",
        title="Citation not found in public database",
        description="No matching record in CourtListener.",
    )

    resp = ask_finding_question(
        repo, "owner-1", aid, fid, "What source passage supports this citation?"
    )
    assert resp.status == "no_evidence"
    assert "No corroborating evidence records could be retrieved" in resp.answer
    assert "Absence from an automated database does not definitively establish" in resp.answer
    assert resp.evidence_record_ids == []


def test_ask_finding_question_refuses_legal_advice():
    repo = MockRepository()
    aid = uuid4()
    fid = uuid4()

    repo.analyses[aid] = MockAnalysis(aid)
    repo.records[(aid, Finding, fid)] = MockFinding(fid, aid)

    resp = ask_finding_question(
        repo, "owner-1", aid, fid, "What should I argue in court to beat this finding?"
    )
    assert resp.status == "refused"
    assert resp.refusal_reason == "broad_legal_advice"
    assert "cannot provide legal advice" in resp.answer
    assert "licensed legal counsel" in resp.answer
    assert resp.evidence_record_ids == []


def test_ask_finding_question_rate_limiting():
    repo = MockRepository()
    aid = uuid4()
    fid = uuid4()

    repo.analyses[aid] = MockAnalysis(aid)
    repo.records[(aid, Finding, fid)] = MockFinding(fid, aid)

    for i in range(MAX_QUESTIONS_PER_ANALYSIS):
        ask_finding_question(repo, "owner-1", aid, fid, f"Question {i} about evidence")

    with pytest.raises(OverflowError, match="Maximum questions limit reached"):
        ask_finding_question(repo, "owner-1", aid, fid, "Question 21")


def test_cross_session_isolation_and_running_guard():
    repo = MockRepository()
    aid = uuid4()
    fid = uuid4()

    repo.analyses[aid] = MockAnalysis(aid, owner_hash="owner-A")
    repo.records[(aid, Finding, fid)] = MockFinding(fid, aid)

    # Different owner raises AnalysisNotFound
    from filingguard.db.repository import AnalysisNotFound

    with pytest.raises(AnalysisNotFound):
        ask_finding_question(repo, "owner-B", aid, fid, "What evidence?")

    # Missing finding raises LookupError
    with pytest.raises(LookupError):
        ask_finding_question(repo, "owner-A", aid, uuid4(), "What evidence?")

    # Running analysis raises ValueError
    repo.analyses[aid].status = AnalysisStatus.RUNNING
    with pytest.raises(ValueError, match="Analysis is still running"):
        ask_finding_question(repo, "owner-A", aid, fid, "What evidence?")
