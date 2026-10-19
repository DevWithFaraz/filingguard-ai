"""Legal Red-Team synthesis engine (FR-240 through FR-245).

Synthesizes adversarial challenges solely from saved findings and evidence.
Does not draft new legal arguments or invent ungrounded facts.
"""

from datetime import UTC, datetime
from uuid import UUID, uuid5

from filingguard.db.models import (
    Citation,
    Claim,
    Finding,
    Quote,
)
from filingguard.modules.red_team.schemas import RedTeamResponse, RedTeamWeakness

_NAMESPACE_REDTEAM = UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")

_SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}


def _derive_weakness_id(finding_id: UUID, salt: str) -> UUID:
    return uuid5(_NAMESPACE_REDTEAM, f"{finding_id}:{salt}")


def synthesize_weaknesses(
    analysis_id: UUID,
    findings: list,
    citations: list | None = None,
    claims: list | None = None,
    quotes: list | None = None,
    *,
    generated_at: datetime | None = None,
) -> RedTeamResponse:
    """Synthesize ranked weaknesses grounded exclusively in existing analysis findings."""
    weaknesses: list[RedTeamWeakness] = []
    timestamp = generated_at or datetime.now(UTC)

    citation_map = {c.id: c for c in (citations or [])}
    claim_map = {c.id: c for c in (claims or [])}
    quote_map = {q.id: q for q in (quotes or [])}

    for f in findings:
        f_type = getattr(f, "type", "")
        f_sev = getattr(f, "severity", "low")
        f_title = getattr(f, "title", "") or ""
        f_desc = getattr(f, "description", "") or ""
        f_id = getattr(f, "id", None)
        if not f_id:
            continue

        f_claim_id = getattr(f, "claim_id", None)
        f_cit_id = getattr(f, "citation_id", None)
        f_quote_id = getattr(f, "quote_id", None)

        linked_findings = [f_id]
        linked_citations = [f_cit_id] if f_cit_id and f_cit_id in citation_map else []
        linked_claims = [f_claim_id] if f_claim_id and f_claim_id in claim_map else []
        linked_quotes = [f_quote_id] if f_quote_id and f_quote_id in quote_map else []

        # 1. Misrepresented or Contradicted Authority (FR-241, FR-243)
        if f_type == "claim_support" and (
            "misrepresented" in f_title.lower()
            or "misrepresented" in f_desc.lower()
            or f_sev in ("critical", "high")
        ):
            weaknesses.append(
                RedTeamWeakness(
                    id=_derive_weakness_id(f_id, "misrepresented_authority"),
                    vulnerability_type="misrepresented_authority",
                    severity="critical" if f_sev == "critical" else "high",
                    title=f"Misrepresented Legal Authority: {f_title}"[:255],
                    challenge_theory=(
                        "Opposing counsel will highlight that the cited precedent does not stand "
                        "for the proposition asserted in the filing, but rather establishes "
                        "contrary or distinct principles. Opposing counsel will quote the "
                        "authentic opinion text in their response to impeach filer credibility "
                        "and move to strike the claim."
                    ),
                    impact_summary=(
                        "Immediate loss of credibility before the court, judicial skepticism on "
                        "remaining arguments, and potential exposure to Rule 11 inquiry for "
                        "misstating governing precedent."
                    ),
                    remediation_recommendation=(
                        "Review the authentic holding in the cited authority at the referenced "
                        "passage. Reframe the claim to accurately reflect the court's actual "
                        "rule, or substitute with on-point authority."
                    ),
                    linked_finding_ids=linked_findings,
                    linked_citation_ids=linked_citations,
                    linked_claim_ids=linked_claims,
                    linked_quote_ids=linked_quotes,
                )
            )

        # 2. Unverified or Non-Existent Citation (FR-241, FR-243)
        elif f_type == "citation" and (
            "not found" in f_title.lower()
            or "not found" in f_desc.lower()
            or f_sev in ("critical", "high")
        ):
            weaknesses.append(
                RedTeamWeakness(
                    id=_derive_weakness_id(f_id, "unverified_citation"),
                    vulnerability_type="unverified_citation",
                    severity="critical",
                    title=f"Unverified / Non-Existent Authority: {f_title}"[:255],
                    challenge_theory=(
                        "Opposing counsel or the court clerk will attempt to retrieve this "
                        "citation and find no matching authority in official legal reporters. "
                        "Opposing counsel will file a notice of non-existent authority, raising "
                        "suspicion of unverified AI hallucination and asking the judge to strike "
                        "the citation."
                    ),
                    impact_summary=(
                        "Severe risk of judicial reprimand, mandatory show-cause orders under "
                        "Rule 11, and complete dismissal of the legal theory dependent on the "
                        "absent citation."
                    ),
                    remediation_recommendation=(
                        "Verify reporter volume, series, and page numbers in primary sources. "
                        "If the authority cannot be independently verified, withdraw the citation "
                        "immediately."
                    ),
                    linked_finding_ids=linked_findings,
                    linked_citation_ids=linked_citations,
                    linked_claim_ids=linked_claims,
                    linked_quote_ids=linked_quotes,
                )
            )

        # 3. Critical Privacy Exposure (FR-241, FR-243)
        elif f_type == "privacy" and f_sev in ("critical", "high"):
            weaknesses.append(
                RedTeamWeakness(
                    id=_derive_weakness_id(f_id, "privacy_exposure"),
                    vulnerability_type="privacy_exposure",
                    severity="critical",
                    title=f"Public Privacy Identifier Exposure: {f_title}"[:255],
                    challenge_theory=(
                        "The filing exposes sensitive personal identifier patterns (such as SSN "
                        "or financial account digits) on the public record in direct violation of "
                        "Fed. R. Civ. P. 5.2 and local privacy rules. Opposing counsel or the "
                        "clerk's office will file an emergency motion to seal the document."
                    ),
                    impact_summary=(
                        "Confidentiality breach, public exposure of client or party data, "
                        "mandatory motion to seal, and potential disciplinary admonishment."
                    ),
                    remediation_recommendation=(
                        "Redact all but the permitted digits (e.g., truncate to last 4 digits of "
                        "SSN or account number) before docket submission."
                    ),
                    linked_finding_ids=linked_findings,
                    linked_citation_ids=linked_citations,
                    linked_claim_ids=linked_claims,
                    linked_quote_ids=linked_quotes,
                )
            )

        # 4. Altered Direct Quotation (FR-241, FR-243)
        elif f_type == "quote" and f_sev in ("critical", "high"):
            weaknesses.append(
                RedTeamWeakness(
                    id=_derive_weakness_id(f_id, "altered_quotation"),
                    vulnerability_type="altered_quotation",
                    severity="high",
                    title=f"Altered Direct Quotation: {f_title}"[:255],
                    challenge_theory=(
                        "Opposing counsel will present a side-by-side textual comparison between "
                        "the filing's quoted passage and the official court reporter, arguing that "
                        "counsel altered or omitted material phrasing to distort the holding."
                    ),
                    impact_summary=(
                        "Impeachment of brief veracity, loss of credibility on statutory or "
                        "precedential interpretation, and judicial reprimand."
                    ),
                    remediation_recommendation=(
                        "Restore verbatim wording from the official opinion text. Use brackets "
                        "and ellipses strictly in accordance with citation standards to denote "
                        "any alterations."
                    ),
                    linked_finding_ids=linked_findings,
                    linked_citation_ids=linked_citations,
                    linked_claim_ids=linked_claims,
                    linked_quote_ids=linked_quotes,
                )
            )

        # 5. Court Rule Non-Compliance (FR-241, FR-243)
        elif f_type == "court_rule" and f_sev in ("critical", "high"):
            weaknesses.append(
                RedTeamWeakness(
                    id=_derive_weakness_id(f_id, "court_rule_violation"),
                    vulnerability_type="court_rule_violation",
                    severity="high",
                    title=f"Court Rule Non-Compliance: {f_title}"[:255],
                    challenge_theory=(
                        "The filing fails to comply with the court's standing order or local rule "
                        "requiring explicit AI-use disclosure. Opposing counsel can file a "
                        "procedural objection, or the court clerk may issue an intake deficiency."
                    ),
                    impact_summary=(
                        "Procedural delay, rejection of filing by the clerk, or an order directing "
                        "an immediate compliance amendment."
                    ),
                    remediation_recommendation=(
                        "Insert the required declaration and exact heading mandated by the "
                        "governing court profile or standing order."
                    ),
                    linked_finding_ids=linked_findings,
                    linked_citation_ids=linked_citations,
                    linked_claim_ids=linked_claims,
                    linked_quote_ids=linked_quotes,
                )
            )

        elif f_type == "table_of_authorities" and f_sev in ("critical", "high", "medium"):
            weaknesses.append(
                RedTeamWeakness(
                    id=_derive_weakness_id(f_id, "unresolved_authority"),
                    vulnerability_type="unresolved_authority",
                    severity="medium",
                    title=f"Table of Authorities inconsistency: {f_title}"[:255],
                    challenge_theory=(
                        "Opposing counsel can argue the filing's Table of Authorities is "
                        "incomplete or padded, undermining the reliability of the cited "
                        "authorities and inviting a clerk or court to question the brief's care."
                    ),
                    impact_summary=(
                        "Procedural objection, reduced credibility, or a request to correct the "
                        "table before the court relies on the cited authorities."
                    ),
                    remediation_recommendation=(
                        "Reconcile body citations with Table of Authorities entries and listed "
                        "page references. Confirm each comparable reporter identity appears in "
                        "both places or is intentionally omitted for a documented reason."
                    ),
                    linked_finding_ids=linked_findings,
                    linked_citation_ids=linked_citations,
                    linked_claim_ids=linked_claims,
                    linked_quote_ids=linked_quotes,
                )
            )

        # 6. Under-Supported or Ambiguous Claim (FR-241, FR-243)
        elif f_type == "claim_support" and f_sev in ("medium", "low"):
            weaknesses.append(
                RedTeamWeakness(
                    id=_derive_weakness_id(f_id, "unsupported_claim"),
                    vulnerability_type="unsupported_claim",
                    severity="medium",
                    title=f"Vulnerable Legal Assertion: {f_title}"[:255],
                    challenge_theory=(
                        "Opposing counsel will argue that the cited precedent is factually "
                        "distinguishable, contains qualifying exceptions not acknowledged by "
                        "the brief, or lacks source authority for the broad proposition claimed."
                    ),
                    impact_summary=(
                        "Substantive argument vulnerability allowing opposing counsel to "
                        "neutralize the point on the merits."
                    ),
                    remediation_recommendation=(
                        "Strengthen argument by citing direct holding language and addressing any "
                        "distinctions or limiting criteria."
                    ),
                    linked_finding_ids=linked_findings,
                    linked_citation_ids=linked_citations,
                    linked_claim_ids=linked_claims,
                    linked_quote_ids=linked_quotes,
                )
            )

        # 7. Minor Privacy or Quote Variation (FR-241, FR-243)
        elif f_type == "privacy" and f_sev in ("medium", "low"):
            weaknesses.append(
                RedTeamWeakness(
                    id=_derive_weakness_id(f_id, "privacy_exposure"),
                    vulnerability_type="privacy_exposure",
                    severity="low",
                    title=f"Privacy Redaction Notice: {f_title}"[:255],
                    challenge_theory=(
                        "The filing includes personal information (such as full birth date) "
                        "contrary to local privacy redaction rules."
                    ),
                    impact_summary="Clerk deficiency notice or minor administrative delay.",
                    remediation_recommendation="Truncate birth date to year of birth only.",
                    linked_finding_ids=linked_findings,
                    linked_citation_ids=linked_citations,
                    linked_claim_ids=linked_claims,
                    linked_quote_ids=linked_quotes,
                )
            )

        elif f_type == "quote" and f_sev in ("medium", "low"):
            weaknesses.append(
                RedTeamWeakness(
                    id=_derive_weakness_id(f_id, "altered_quotation"),
                    vulnerability_type="altered_quotation",
                    severity="low",
                    title=f"Quotation Formatting Variation: {f_title}"[:255],
                    challenge_theory=(
                        "Minor textual or punctuation variations exist between the filing "
                        "quotation and the source opinion."
                    ),
                    impact_summary=(
                        "Opposing counsel may nitpick quote accuracy to question drafting care."
                    ),
                    remediation_recommendation=(
                        "Align quotation formatting, punctuation, and capitalization with the "
                        "official reporter."
                    ),
                    linked_finding_ids=linked_findings,
                    linked_citation_ids=linked_citations,
                    linked_claim_ids=linked_claims,
                    linked_quote_ids=linked_quotes,
                )
            )

    # Sort deterministically by severity priority, then title
    weaknesses.sort(
        key=lambda w: (_SEVERITY_ORDER.get(w.severity, 99), w.title)
    )

    crit_count = sum(1 for w in weaknesses if w.severity == "critical")
    high_count = sum(1 for w in weaknesses if w.severity == "high")
    med_count = sum(1 for w in weaknesses if w.severity == "medium")
    low_count = sum(1 for w in weaknesses if w.severity == "low")
    total = len(weaknesses)

    if total == 0:
        summary = (
            "No high-risk adversarial vulnerabilities detected from evaluated checks. "
            "Ensure all eligible review stages were evaluated before filing."
        )
    else:
        summary = (
            f"Identified {total} potential adversarial challenge{'s' if total != 1 else ''} "
            f"({crit_count} critical, {high_count} high, {med_count} medium, {low_count} low). "
            "Inspect challenge theories and review evidence before submission."
        )

    return RedTeamResponse(
        analysis_id=analysis_id,
        generated_at=timestamp,
        weaknesses=weaknesses,
        summary=summary,
        total_weaknesses=total,
        critical_count=crit_count,
        high_count=high_count,
        medium_count=med_count,
        low_count=low_count,
    )


def synthesize_red_team(repository, owner: str, analysis_id: UUID) -> RedTeamResponse:
    """Load persisted analysis entities and execute grounded red-team synthesis."""
    repository.get_analysis(owner, analysis_id)
    findings = repository.list_records(owner, analysis_id, Finding)
    citations = repository.list_records(owner, analysis_id, Citation)
    claims = repository.list_records(owner, analysis_id, Claim)
    quotes = repository.list_records(owner, analysis_id, Quote)

    return synthesize_weaknesses(analysis_id, findings, citations, claims, quotes)
