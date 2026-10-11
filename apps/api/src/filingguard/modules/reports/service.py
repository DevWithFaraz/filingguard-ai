"""Reports and graphs derive only from the owner's saved analysis."""

from hashlib import sha256
from html import escape

from filingguard.db.models import (
    Authority,
    Citation,
    Claim,
    ClaimAuthorityLink,
    DocumentSegment,
    EvidenceRecord,
    Finding,
    Quote,
)
from filingguard.modules.analyses.schemas import Coverage, StageState
from filingguard.modules.privacy.service import mask_excerpt
from filingguard.modules.scoring.service import score_review

LIMITATION = (
    "Human review required. Not legal advice or a filing readiness determination. "
    "Heuristic masking and selected sources may be incomplete."
)


def safe_text(value, filing):
    if value is None:
        return None
    # Preserve full-snapshot identifier detection even when the response is a clipped excerpt.
    masked = mask_excerpt(filing, 0, len(filing))
    output = str(value)
    for detection in masked.detections:
        secret = filing[detection.start : detection.end]
        output = output.replace(secret, "*" * len(secret))
    # Model explanations can contain newly introduced identifiers as well.
    if output:
        if len(output) > 100000:
            output = output[:100000]
        output = mask_excerpt(output, 0, len(output)).text
    return output


def location(row):
    return {
        "start": row.start_offset,
        "end": row.end_offset,
        "page_number": row.page_number,
        "segment_id": str(row.segment_id) if row.segment_id else None,
        "offset_unit": "unicode_code_points",
    }


def saved_results(repository, owner, identity):
    analysis = repository.get_analysis(owner, identity)
    filing = analysis.document_snapshot["text"]
    rows = {
        model: repository.list_records(owner, identity, model)
        for model in (
            Authority,
            Citation,
            Claim,
            ClaimAuthorityLink,
            Quote,
            Finding,
            EvidenceRecord,
        )
    }
    stages = [StageState.model_validate(s) for s in analysis.stage_states.values()]
    coverage = Coverage(
        eligible=sum(s.coverage.eligible for s in stages),
        evaluated=sum(s.coverage.evaluated for s in stages),
        unavailable=sum(s.coverage.unavailable for s in stages),
        pending=sum(s.coverage.pending for s in stages),
        truncated=any(s.coverage.truncated for s in stages),
        limitation="Some checks covered only part of the material"
        if any(s.coverage.truncated for s in stages)
        else None,
    )
    counts = {}
    for row in rows[EvidenceRecord]:
        counts[row.finding_id] = counts.get(row.finding_id, 0) + 1
    findings = [
        {
            "id": str(f.id),
            "type": f.type,
            "severity": f.severity,
            "title": safe_text(f.title, filing),
            "description": safe_text(f.description, filing),
            "masked_excerpt": mask_excerpt(filing, f.start_offset, f.end_offset).text
            if f.start_offset is not None and f.end_offset is not None
            else safe_text(f.document_excerpt, filing),
            "start": f.start_offset,
            "end": f.end_offset,
            "evidence_count": counts.get(f.id, 0),
            "ai_assisted": f.ai_assisted,
            "evidence": [
                _safe_evidence(e, filing) for e in rows[EvidenceRecord] if e.finding_id == f.id
            ],
            **{
                key: str(getattr(f, key)) if getattr(f, key) else None
                for key in ("claim_id", "citation_id", "authority_id", "quote_id", "segment_id")
            },
        }
        for f in rows[Finding]
    ]
    authorities = {
        a.id: {
            "id": str(a.id),
            "source": a.source,
            "external_id": a.external_id,
            "case_name": safe_text(a.case_name, filing),
            "citation": a.citation,
            "court": a.court,
            "year": a.year,
            "source_url": a.source_url,
            "opinion_text_available": a.opinion_text_available,
            "opinion_text": None,  # Excerpts are served through the evidence detail route.
            "source_sha256": a.source_sha256,
            "retrieved_at": a.retrieved_at,
            "source_metadata": {"missing_text": not a.opinion_text_available},
        }
        for a in rows[Authority]
    }
    citations = []
    for c in sorted(rows[Citation], key=lambda r: r.start_offset):
        if filing[c.start_offset : c.end_offset] != c.raw_text:
            raise ValueError("Citation snapshot mismatch")
        masked = mask_excerpt(filing, c.start_offset, c.end_offset).text
        verification = (c.extraction_metadata or {}).get("verification") or {}
        citations.append(
            {
                "id": str(c.id),
                "masked_raw_text": masked,
                "normalized_text": c.normalized_text if masked == c.raw_text else None,
                "location": location(c),
                "extraction": c.extraction_metadata or None,
                "verification_status": c.verification_status,
                "authority_id": str(c.authority_id) if c.authority_id else None,
                "authority": authorities.get(c.authority_id),
                "reason": verification.get("reason"),
                "limitation": verification.get("limitation"),
            }
        )
    links = {}
    for link in rows[ClaimAuthorityLink]:
        links.setdefault(link.claim_id, []).append(
            {
                "id": str(link.id),
                "citation_id": str(link.citation_id),
                "authority_id": str(link.authority_id) if link.authority_id else None,
                "support_status": link.support_status,
                "explanation": safe_text(link.explanation, filing),
                "confidence": link.confidence,
            }
        )
    claims = [
        {
            "id": str(c.id),
            "text": mask_excerpt(filing, c.start_offset, c.end_offset).text,
            "location": location(c),
            "extraction_method": c.extraction_method,
            "links": links.get(c.id, []),
        }
        for c in rows[Claim]
    ]
    quotes = [
        {
            "id": str(q.id),
            "text": mask_excerpt(filing, q.start_offset, q.end_offset).text,
            "location": location(q),
            "citation_id": str(q.citation_id) if q.citation_id else None,
            "match_status": q.match_status,
            "similarity": q.similarity,
            "closest_passage": safe_text(q.closest_passage, filing),
        }
        for q in rows[Quote]
    ]
    return {
        "analysis_id": str(identity),
        "document_name": safe_text(analysis.document_name, filing),
        "created_at": analysis.created_at,
        "court_profile_id": analysis.court_profile_id,
        "mode": analysis.mode,
        "status": analysis.status,
        "stages": [s.model_dump(mode="json") for s in stages],
        "coverage": coverage.model_dump(),
        "score": score_review(stages, rows[Finding], status=analysis.status),
        "citations": citations,
        "claims": claims,
        "quotes": quotes,
        "findings": findings,
        "limitation": LIMITATION,
    }


def saved_graph(repository, owner, identity):
    results = saved_results(repository, owner, identity)
    segments = {str(s.id): s for s in repository.list_records(owner, identity, DocumentSegment)}
    nodes, edges = {}, []
    citations = {c["id"]: c for c in results["citations"]}
    for claim in results["claims"]:
        claim_node = "claim:" + claim["id"]
        segment_id = claim["location"]["segment_id"]
        segment = segments[segment_id]
        section_node = "section:" + segment_id
        nodes[section_node] = {
            "id": section_node,
            "label": f"Paragraph {segment.paragraph_index + 1}",
            "kind": "section",
            "status": "extracted",
        }
        nodes[claim_node] = {
            "id": claim_node,
            "label": claim["text"][:140],
            "kind": "claim",
            "status": "heuristic",
        }
        edges.append(
            {
                "id": "context:" + claim["id"],
                "source": section_node,
                "target": claim_node,
                "label": "citation context",
            }
        )
        for link in claim["links"]:
            citation = citations[link["citation_id"]]
            authority = citation["authority"]
            authority_node = "authority:" + (link["authority_id"] or citation["id"])
            nodes[authority_node] = {
                "id": authority_node,
                "kind": "authority",
                "label": (authority["case_name"] if authority else None)
                or citation["masked_raw_text"],
                "status": citation["verification_status"],
            }
            edges.append(
                {
                    "id": link["id"],
                    "source": claim_node,
                    "target": authority_node,
                    "label": link["support_status"],
                }
            )
    for node in nodes.values():
        relation = node["id"].split(":", 1)[1]
        node["finding_ids"] = [
            f["id"]
            for f in results["findings"]
            if relation in {f["claim_id"], f["authority_id"], f["citation_id"], f["segment_id"]}
        ]
    return {"analysis_id": str(identity), "nodes": list(nodes.values()), "edges": edges}


def saved_evidence(repository, owner, identity, finding_id):
    finding = repository.get_record(owner, identity, Finding, finding_id)
    if finding is None:
        raise LookupError("Finding not found")
    filing = repository.get_analysis(owner, identity).document_snapshot["text"]
    evidence = []
    for row in repository.list_records(owner, identity, EvidenceRecord):
        if row.finding_id != finding_id:
            continue
        evidence.append(_safe_evidence(row, filing))
    return {"analysis_id": str(identity), "finding_id": str(finding_id), "evidence": evidence}


def _safe_evidence(row, filing):
    if (
        not row.snapshot_text
        or type(row.source_start_offset) is not int
        or type(row.source_end_offset) is not int
        or not 0 <= row.source_start_offset < row.source_end_offset <= len(row.snapshot_text)
        or sha256(row.snapshot_text.encode()).hexdigest() != row.source_sha256
        or row.snapshot_text[row.source_start_offset : row.source_end_offset] != row.excerpt
    ):
        raise ValueError("Evidence snapshot mismatch")
    return {
        "id": str(row.id),
        "excerpt": safe_text(row.excerpt, filing),
        "source_url": row.source_url,
        "source_start": row.source_start_offset,
        "source_end": row.source_end_offset,
        "source_sha256": row.source_sha256,
        "retrieved_at": row.retrieved_at,
        "method_version": row.method_version,
        "model_version": row.model_version,
        "prompt_version": row.prompt_version,
        "provenance": (row.source_metadata or {}).get("provenance"),
        "confidence_level": (row.source_metadata or {}).get("confidence_level", "unknown"),
    } | {
        "excerpt": safe_text(
            mask_excerpt(row.snapshot_text, row.source_start_offset, row.source_end_offset).text,
            filing,
        )
    }


def render_report(results, *, format="markdown"):
    score = results["score"]
    score_label = score["value"] if score["value"] is not None else "unavailable"
    coverage = results["coverage"]
    lines = [
        "# FilingGuard AI review report",
        "",
        results["limitation"],
        "",
        f"Analysis: {results['analysis_id']}",
        f"Document: {results.get('document_name', 'Unnamed document')}",
        f"Created: {results['created_at']}",
        f"Mode: {results['mode']}",
        "Source mode: cached_public opinions; fresh checks, no cached classifications."
        if results["mode"] == "demo"
        else "Source mode: configured live review; availability disclosed.",
        f"Status: {results['status']}",
        f"Court profile: {results['court_profile_id']}",
        f"Provisional score ({score['version']}): {score_label}",
        f"Coverage: {coverage['evaluated']}/{coverage['eligible']} evaluated; "
        f"{coverage['unavailable']} unavailable; {coverage['pending']} pending; "
        f"truncated={coverage['truncated']}",
        "",
        "## Stage coverage",
    ]
    for stage in results["stages"]:
        lines.append(f"- {stage['name']}: {stage['status']}. {stage.get('reason') or ''}")
    lines.extend(["", "## Category scores (provisional)"])
    for category in score.get("categories", []):
        label = category["value"] if category["value"] is not None else "unknown"
        lines.append(
            f"- {category['type']}: {label}; {category['evaluated']}/"
            f"{category['eligible']} evaluated; deductions {category['deducted_points']}"
        )
    lines.extend(["", "## Findings"])
    for finding in results["findings"]:
        lines.extend(
            [
                f"### {finding['severity']}: {finding['title']}",
                finding["description"],
                finding["masked_excerpt"] or "",
                f"Evidence records: {finding['evidence_count']}",
                "",
            ]
        )
        for evidence in finding.get("evidence", []):
            lines.extend(
                [
                    evidence["excerpt"],
                    f"Source: {evidence['source_url'] or 'Original filing/rule snapshot'}; "
                    f"SHA256: {evidence['source_sha256']}; retrieved {evidence['retrieved_at']}",
                    f"Offsets: {evidence['source_start']}-{evidence['source_end']}; "
                    f"method: {evidence['method_version']}; "
                    f"model: {evidence['model_version'] or 'none'}; "
                    f"prompt: {evidence['prompt_version'] or 'none'}; "
                    f"provenance: {evidence.get('provenance') or 'unknown'}; "
                    f"confidence: {evidence['confidence_level']} (uncalibrated)",
                    "",
                ]
            )
    lines.extend(["## Citation results"])
    for citation in results["citations"]:
        lines.append(
            f"- {citation['masked_raw_text']}: {citation['verification_status']}. "
            f"{citation['limitation'] or ''}"
        )
        if citation["authority"]:
            lines.append(
                f"  Source: {citation['authority']['source_url']}; "
                f"SHA256: {citation['authority']['source_sha256']}"
            )
    lines.extend(["", "## Claim contexts"])
    for claim in results["claims"]:
        lines.append(claim["text"])
        for link in claim["links"]:
            lines.append(
                f"- {link['support_status']}: {link['explanation'] or 'Support check not run'}"
            )
    lines.extend(["", "## Quote comparisons"])
    for quote in results["quotes"]:
        lines.extend(
            [
                quote["text"],
                f"Match: {quote['match_status']}; "
                f"similarity: {quote['similarity']}; similarity is not legal support.",
                quote["closest_passage"] or "Source comparison unavailable",
            ]
        )
    lines.extend(["", "## Score deductions"])
    for deduction in score["deductions"]:
        lines.append(f"- {deduction['type']}/{deduction['severity']}: {deduction['points']} points")
    content = "\n".join(lines)
    if format == "html":
        return (
            "<!doctype html><html lang='en'><meta charset='utf-8'><title>FilingGuard review</title>"
            "<body><pre>" + escape(content) + "</pre></body></html>"
        )
    return content
