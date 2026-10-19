"""Finding-grounded Q&A service (FR-260 through FR-264).

Grounded exclusively in persisted findings, evidence records, and authority metadata.
Refuses broad legal advice and general document chat.
"""

import re
from datetime import UTC, datetime
from uuid import UUID

from filingguard.db.models import (
    Authority,
    Citation,
    Claim,
    EvidenceRecord,
    Finding,
    Quote,
)
from filingguard.modules.grounded_qa.schemas import (
    GroundedAnswerResponse,
    GroundedQuestionHistory,
)

# Maximum questions allowed per analysis to prevent quota exhaustion and resource abuse
MAX_QUESTIONS_PER_ANALYSIS = 20

# In-memory session tracking for Q&A history and rate limiting
_qa_history_store: dict[UUID, list[GroundedAnswerResponse]] = {}

# Patterns for questions requesting broad legal advice or litigation strategy (FR-263)
_LEGAL_ADVICE_PATTERNS = [
    r"\bshould\s+i\s+file\b",
    r"\bwhat\s+(should|can)\s+i\s+argue\b",
    r"\bhow\s+(should|can)\s+i\s+argue\b",
    r"\bwhat\s+to\s+argue\b",
    r"\bwill\s+i\s+win\b",
    r"\b(odds|chance|probability)\s+of\s+winning\b",
    r"\bhow\s+to\s+win\b",
    r"\blegal\s+strategy\b",
    r"\b(defense|litigation|appeal)\s+strategy\b",
    r"\brewrite\s+my\s+(brief|motion|argument|filing|strategy)\b",
    r"\bhow\s+do\s+i\s+dismiss\b",
    r"\bgive\s+me\s+legal\s+advice\b",
    r"\bcan\s+i\s+sue\b",
    r"\bwhat\s+is\s+my\s+liability\b",
    r"\bhelp\s+me\s+draft\b",
    r"\bdraft\s+a\s+(motion|brief|pleading|argument)\b",
    r"\bhow\s+to\s+convince\s+the\s+judge\b",
    r"\badvise\s+me\b",
]

# Patterns for questions attempting general document chat or unrelated queries (FR-264)
_OUT_OF_SCOPE_PATTERNS = [
    r"\btell\s+me\s+a\s+joke\b",
    r"\bwho\s+(are\s+you|made\s+you|created\s+you)\b",
    r"\bweather\b",
    r"\brecipe\b",
    r"\bwho\s+is\s+the\s+president\b",
    r"\bsummarize\s+the\s+(whole|entire|all)\s+document\b",
    r"\bsummarize\s+everything\b",
    r"\btell\s+me\s+a\s+story\b",
    r"\bwrite\s+a\s+poem\b",
    r"\bwhat\s+is\s+the\s+meaning\s+of\s+life\b",
]


def classify_question_intent(question: str) -> tuple[str, str]:
    """Classify question intent into normal, broad legal advice refusal, or out of scope.

    Returns (status, refusal_reason).
    """
    clean_q = question.strip().lower()

    for pattern in _LEGAL_ADVICE_PATTERNS:
        if re.search(pattern, clean_q):
            return "refused", "broad_legal_advice"

    for pattern in _OUT_OF_SCOPE_PATTERNS:
        if re.search(pattern, clean_q):
            return "refused", "out_of_scope"

    return "answered", "none"


def ask_finding_question(
    repository,
    owner_hash: str,
    analysis_id: UUID,
    finding_id: UUID,
    question: str,
    *,
    timestamp: datetime | None = None,
) -> GroundedAnswerResponse:
    """Answer a question grounded strictly in a specific finding and its stored evidence."""
    now = timestamp or datetime.now(UTC)

    # 1. Verify analysis ownership and terminal state
    analysis = repository.get_analysis(owner_hash, analysis_id)
    if analysis.status in {"queued", "running"}:
        raise ValueError("Analysis is still running")

    # 2. Verify finding exists and belongs to this analysis
    finding = repository.get_record(owner_hash, analysis_id, Finding, finding_id)
    if finding is None:
        raise LookupError("Finding not found")

    # 3. Rate limiting and history check
    history = _qa_history_store.setdefault(analysis_id, [])
    if len(history) >= MAX_QUESTIONS_PER_ANALYSIS:
        raise OverflowError("Maximum questions limit reached for this analysis session")

    # 4. Check for disallowed legal advice or out-of-scope chat (FR-263, FR-264)
    status, refusal_reason = classify_question_intent(question)
    if status == "refused":
        if refusal_reason == "broad_legal_advice":
            refusal_text = (
                "FilingGuard AI is an automated filing verification tool and cannot provide legal "
                "advice, formulate litigation strategy, or predict court rulings. As an AI safety "
                "platform, its role is confined to identifying citation anomalies, quotation "
                "discrepancies, and rule non-compliance. Please consult licensed legal counsel "
                "to evaluate substantive legal arguments."
            )
        else:
            refusal_text = (
                "General document chat is out of scope. Grounded Q&A is strictly limited to "
                "answering forensic questions about this specific finding, its extracted span, "
                "and its retrieved evidence records."
            )

        resp = GroundedAnswerResponse(
            analysis_id=analysis_id,
            finding_id=finding_id,
            question=question.strip(),
            answer=refusal_text,
            status="refused",
            refusal_reason=refusal_reason,
            evidence_record_ids=[],
            source_authorities=[],
            source_urls=[],
            created_at=now,
        )
        history.append(resp)
        return resp

    # 5. Retrieve associated evidence records and authorities
    evidence_records: list[EvidenceRecord] = [
        row
        for row in repository.list_records(owner_hash, analysis_id, EvidenceRecord)
        if row.finding_id == finding_id
    ]

    linked_authority = None
    if finding.authority_id:
        linked_authority = repository.get_record(
            owner_hash, analysis_id, Authority, finding.authority_id
        )

    linked_citation = None
    if finding.citation_id:
        linked_citation = repository.get_record(
            owner_hash, analysis_id, Citation, finding.citation_id
        )

    linked_claim = None
    if finding.claim_id:
        linked_claim = repository.get_record(owner_hash, analysis_id, Claim, finding.claim_id)

    linked_quote = None
    if finding.quote_id:
        linked_quote = repository.get_record(owner_hash, analysis_id, Quote, finding.quote_id)

    # 6. Generate grounded answer
    resp = _generate_grounded_answer(
        analysis_id=analysis_id,
        finding=finding,
        question=question.strip(),
        evidence_records=evidence_records,
        authority=linked_authority,
        citation=linked_citation,
        claim=linked_claim,
        quote=linked_quote,
        now=now,
    )
    history.append(resp)
    return resp


def get_finding_qa_history(
    repository,
    owner_hash: str,
    analysis_id: UUID,
    finding_id: UUID,
) -> GroundedQuestionHistory:
    """Retrieve existing Q&A history for a specific finding."""
    # Ensure owner and finding exist
    repository.get_analysis(owner_hash, analysis_id)
    finding = repository.get_record(owner_hash, analysis_id, Finding, finding_id)
    if finding is None:
        raise LookupError("Finding not found")

    all_history = _qa_history_store.get(analysis_id, [])
    finding_history = [q for q in all_history if q.finding_id == finding_id]

    return GroundedQuestionHistory(
        analysis_id=analysis_id,
        finding_id=finding_id,
        questions=finding_history,
        count=len(finding_history),
        limit=MAX_QUESTIONS_PER_ANALYSIS,
    )


def clear_qa_store(analysis_id: UUID | None = None) -> None:
    """Clear in-memory Q&A store (used for test teardown and cleanup)."""
    if analysis_id is not None:
        _qa_history_store.pop(analysis_id, None)
    else:
        _qa_history_store.clear()


def _generate_grounded_answer(
    analysis_id: UUID,
    finding: Finding,
    question: str,
    evidence_records: list[EvidenceRecord],
    authority: Authority | None,
    citation: Citation | None,
    claim: Claim | None,
    quote: Quote | None,
    now: datetime,
) -> GroundedAnswerResponse:
    """Generate finding-grounded answer citing exact evidence IDs and authentic authorities."""
    q_lower = question.lower()
    evidence_ids = [e.id for e in evidence_records]
    source_auth_names = []
    source_urls = []

    if authority and authority.case_name:
        source_auth_names.append(authority.case_name)
    elif citation and citation.raw_text:
        source_auth_names.append(citation.raw_text)

    for e in evidence_records:
        if e.source_url and e.source_url not in source_urls:
            source_urls.append(e.source_url)
        if e.source_label and e.source_label not in source_auth_names:
            source_auth_names.append(e.source_label)

    # Check for missing evidence situation when asked for evidence or source passages
    asking_for_evidence = any(
        k in q_lower for k in ["evidence", "source", "passage", "what did you use", "support"]
    )
    if (
        not evidence_records
        and asking_for_evidence
        and finding.type in {"citation", "quote", "claim_support"}
    ):
        status = "no_evidence"
        explanation = (
            f"No corroborating evidence records could be retrieved for finding '{finding.title}'. "
            "The referenced authority or opinion text was not returned by public court records. "
            "Important: Absence from an automated database does not definitively establish that "
            "an authority was fabricated or does not exist, but indicates that independent "
            "verification was unavailable. Review official dockets or reporters directly."
        )
        return GroundedAnswerResponse(
            analysis_id=analysis_id,
            finding_id=finding.id,
            question=question,
            answer=explanation,
            status=status,
            refusal_reason="none",
            evidence_record_ids=[],
            source_authorities=source_auth_names,
            source_urls=source_urls,
            created_at=now,
        )

    # 1. Question asking about evidence / source passages / passages used
    if asking_for_evidence:
        if evidence_records:
            passages = []
            for _i, ev in enumerate(evidence_records[:3], 1):
                clean_excerpt = ev.excerpt.strip().replace("\n", " ")
                passages.append(
                    f"Evidence Record [{ev.id}]: \"{clean_excerpt}\" "
                    f"(retrieved via {ev.method_version}, SHA-256: {ev.source_sha256[:12]}…)"
                )
            answer = (
                f"This finding is grounded in {len(evidence_records)} evidence record(s). "
                f"Key retrieved passage(s): {' | '.join(passages)}. "
                f"Official authority: {', '.join(source_auth_names) or 'Stored snapshot'}."
            )
        else:
            answer = (
                f"This finding is grounded in deterministic rule evaluation against rule ID "
                f"'{finding.rule_id or 'local_check'}'. Original document span: "
                f"offsets {finding.start_offset}–{finding.end_offset}."
            )

        return GroundedAnswerResponse(
            analysis_id=analysis_id,
            finding_id=finding.id,
            question=question,
            answer=answer,
            status="answered",
            refusal_reason="none",
            evidence_record_ids=evidence_ids,
            source_authorities=source_auth_names,
            source_urls=source_urls,
            created_at=now,
        )

    # 2. Question asking why it was flagged / weak / suspicious / invalid
    if any(k in q_lower for k in ["why", "flagged", "weak", "suspicious", "invalid", "reason"]):
        f_type = finding.type
        if f_type == "quote":
            quote_status = quote.match_status if quote else "unverified"
            answer = (
                f"The quotation was flagged as '{finding.title}' (severity: {finding.severity}) "
                f"because the filing text could not be verified as an authentic, verbatim excerpt "
                f"(status: {quote_status}). Forensic comparison against the official opinion "
                f"revealed alterations, missing words, or an unverified passage. "
                f"Review the exact opinion text to restore accuracy."
            )
        elif f_type == "claim_support":
            support_status = claim.support_status if claim else "unverified"
            answer = (
                f"The legal claim was marked '{finding.title}' (severity: {finding.severity}) "
                f"because proposition verification determined that the cited holding does not "
                f"categorically support the assertion (support status: {support_status}). "
                f"The retrieved opinion either articulates a narrower standard or contradicts "
                f"the filing's interpretation."
            )
        elif f_type == "citation":
            cit_status = citation.verification_status if citation else "unverified"
            answer = (
                f"The citation was flagged as '{finding.title}' (severity: {finding.severity}) "
                f"because public citation index resolution resulted in status '{cit_status}'. "
                f"The cited reporter volume, page, or title could not be confirmed in "
                f"CourtListener records."
            )
        elif f_type == "privacy":
            answer = (
                f"This finding was flagged because an unredacted sensitive identifier was detected "
                f"at character span {finding.start_offset}–{finding.end_offset}. "
                f"Rule requirements mandate redaction of sensitive identifiers before submission."
            )
        elif f_type == "court_rule":
            answer = (
                f"This finding was flagged for court rule non-compliance under profile rule "
                f"'{finding.rule_id or 'court_rule'}'. {finding.description}"
            )
        elif f_type == "table_of_authorities":
            answer = (
                f"This finding was flagged as '{finding.title}' because the Table of Authorities "
                f"audit compared comparable reporter identities in the table and body. "
                f"{finding.description}"
            )
        else:
            answer = (
                f"Finding '{finding.title}' was flagged with severity {finding.severity}. "
                f"{finding.description}"
            )

        return GroundedAnswerResponse(
            analysis_id=analysis_id,
            finding_id=finding.id,
            question=question,
            answer=answer,
            status="answered",
            refusal_reason="none",
            evidence_record_ids=evidence_ids,
            source_authorities=source_auth_names,
            source_urls=source_urls,
            created_at=now,
        )

    # 3. Default fallback for other relevant finding-related questions
    answer = (
        f"Regarding finding '{finding.title}' (severity: {finding.severity}): "
        f"{finding.description} Original filing span: offsets {finding.start_offset}–"
        f"{finding.end_offset}. "
        + (
            f"Grounded in {len(evidence_records)} evidence record(s) from "
            f"{', '.join(source_auth_names) or 'stored snapshot'}."
            if evidence_records
            else "Evaluated via deterministic rule checks."
        )
    )

    return GroundedAnswerResponse(
        analysis_id=analysis_id,
        finding_id=finding.id,
        question=question,
        answer=answer,
        status="answered",
        refusal_reason="none",
        evidence_record_ids=evidence_ids,
        source_authorities=source_auth_names,
        source_urls=source_urls,
        created_at=now,
    )
