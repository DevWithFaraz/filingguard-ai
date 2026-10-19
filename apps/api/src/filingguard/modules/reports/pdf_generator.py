"""PDF report generator for FilingGuard AI (FR-305).

Uses ReportLab Platypus layout engine for paginated, publication-grade legal assurance reports.
Includes running headers/footers with two-pass dynamic page numbering, readable evidence,
5-hop visual lineage records, score breakdowns, and prominent legal disclaimers.
"""

import io
from html import escape
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from filingguard.modules.reports.graph_export import graph_pdf_flowables

# Brand Color Palette
_COLOR_PRIMARY = colors.HexColor("#2b1f3d")
_COLOR_SECONDARY = colors.HexColor("#5d2f96")
_COLOR_ACCENT = colors.HexColor("#f3ebfc")
_COLOR_BORDER = colors.HexColor("#dcd1ed")
_COLOR_TEXT = colors.HexColor("#1a1622")
_COLOR_MUTED = colors.HexColor("#6a5a7d")
_COLOR_WARN_BG = colors.HexColor("#fef8f8")
_COLOR_WARN_BORDER = colors.HexColor("#fca5a5")
_COLOR_WARN_TEXT = colors.HexColor("#991b1b")
_COLOR_INFO_BG = colors.HexColor("#faf7ff")

_SEVERITY_COLORS = {
    "critical": colors.HexColor("#b91c1c"),
    "high": colors.HexColor("#c2410c"),
    "medium": colors.HexColor("#d97706"),
    "low": colors.HexColor("#4b5563"),
    "info": colors.HexColor("#2563eb"),
}


class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas for dynamic total page count and professional running headers/footers."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._saved_page_states: list[dict[str, Any]] = []

    def showPage(self) -> None:
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self) -> None:
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, total_pages: int) -> None:
        self.saveState()
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(_COLOR_MUTED)

        # Running Top Header (Page 2+)
        if self._pageNumber > 1:
            self.drawString(54, 752, "FilingGuard AI · Pre-Filing Assurance Audit Report")
            self.setFont("Helvetica", 8)
            self.drawRightString(letter[0] - 54, 752, "CONFIDENTIAL & PRIVILEGED")
            self.setStrokeColor(_COLOR_BORDER)
            self.setLineWidth(0.5)
            self.line(54, 746, letter[0] - 54, 746)

        # Running Bottom Footer (All Pages)
        self.setStrokeColor(_COLOR_BORDER)
        self.setLineWidth(0.5)
        self.line(54, 46, letter[0] - 54, 46)

        self.setFont("Helvetica", 7.5)
        self.drawString(
            54,
            34,
            "Notice: Automated forensic analysis. Not legal advice. "
            "Independent source review required.",
        )
        self.setFont("Helvetica-Bold", 7.5)
        self.drawRightString(letter[0] - 54, 34, f"Page {self._pageNumber} of {total_pages}")
        self.restoreState()


def _get_styles() -> dict[str, ParagraphStyle]:
    sample = getSampleStyleSheet()

    styles = {
        "Title": ParagraphStyle(
            "DocTitle",
            parent=sample["Title"],
            fontName="Helvetica-Bold",
            fontSize=22,
            leading=26,
            textColor=_COLOR_PRIMARY,
            alignment=0,
            spaceAfter=4,
        ),
        "Subtitle": ParagraphStyle(
            "DocSubtitle",
            parent=sample["Normal"],
            fontName="Helvetica",
            fontSize=11,
            leading=15,
            textColor=_COLOR_SECONDARY,
            spaceAfter=12,
        ),
        "Heading1": ParagraphStyle(
            "Heading1",
            parent=sample["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=18,
            textColor=_COLOR_PRIMARY,
            spaceBefore=14,
            spaceAfter=8,
            keepWithNext=True,
        ),
        "Heading2": ParagraphStyle(
            "Heading2",
            parent=sample["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=15,
            textColor=_COLOR_SECONDARY,
            spaceBefore=10,
            spaceAfter=6,
            keepWithNext=True,
        ),
        "Body": ParagraphStyle(
            "Body",
            parent=sample["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=13,
            textColor=_COLOR_TEXT,
            spaceAfter=4,
        ),
        "BodyBold": ParagraphStyle(
            "BodyBold",
            parent=sample["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=13,
            textColor=_COLOR_TEXT,
            spaceAfter=4,
        ),
        "Muted": ParagraphStyle(
            "Muted",
            parent=sample["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=11,
            textColor=_COLOR_MUTED,
        ),
        "Code": ParagraphStyle(
            "Code",
            parent=sample["Code"],
            fontName="Courier",
            fontSize=7.5,
            leading=10,
            textColor=_COLOR_PRIMARY,
        ),
        "Disclaimer": ParagraphStyle(
            "Disclaimer",
            parent=sample["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=11,
            textColor=_COLOR_WARN_TEXT,
        ),
        "TableCell": ParagraphStyle(
            "TableCell",
            parent=sample["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=11,
            textColor=_COLOR_TEXT,
        ),
        "TableHeader": ParagraphStyle(
            "TableHeader",
            parent=sample["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=11,
            textColor=colors.white,
        ),
    }
    return styles


def generate_pdf_report(results: dict[str, Any]) -> bytes:
    """Render a comprehensive pre-filing assurance report as a PDF binary stream."""
    buffer = io.BytesIO()

    # 54pt margins = 0.75 in; usable width = 612 - 108 = 504pt
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54,
    )

    styles = _get_styles()
    story = []

    # Title & Subtitle
    story.append(Paragraph("FilingGuard AI", styles["Title"]))
    story.append(
        Paragraph("Pre-Filing Forensic Assurance & Compliance Audit Report", styles["Subtitle"])
    )
    story.append(HRFlowable(width="100%", thickness=1.5, color=_COLOR_SECONDARY, spaceAfter=10))

    # Executive Summary & Metadata Table
    meta_data = [
        [
            Paragraph("<b>Analysis UUID:</b>", styles["TableCell"]),
            Paragraph(escape(str(results.get("analysis_id", ""))), styles["Code"]),
            Paragraph("<b>Created:</b>", styles["TableCell"]),
            Paragraph(escape(str(results.get("created_at", ""))), styles["TableCell"]),
        ],
        [
            Paragraph("<b>Document:</b>", styles["TableCell"]),
            Paragraph(
                escape(str(results.get("document_name", "Unnamed filing"))),
                styles["TableCell"],
            ),
            Paragraph("<b>Mode:</b>", styles["TableCell"]),
            Paragraph(escape(str(results.get("mode", ""))), styles["TableCell"]),
        ],
        [
            Paragraph("<b>Court Profile:</b>", styles["TableCell"]),
            Paragraph(escape(str(results.get("court_profile_id", ""))), styles["TableCell"]),
            Paragraph("<b>Status:</b>", styles["TableCell"]),
            Paragraph(escape(str(results.get("status", "")).upper()), styles["TableCell"]),
        ],
    ]
    meta_table = Table(meta_data, colWidths=[90, 162, 70, 182])
    meta_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), _COLOR_INFO_BG),
                ("BOX", (0, 0), (-1, -1), 0.5, _COLOR_BORDER),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#eae2f5")),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(meta_table)
    story.append(Spacer(1, 10))

    # Prominent Legal Disclaimer Callout
    disclaimer_text = (
        "<b>LEGAL ASSURANCE DISCLAIMER:</b> "
        f"{escape(str(results.get('limitation', '')))} "
        "This document is an automated pre-filing compliance and verification report. "
        "It evaluates citations against public court records, compares quotations, checks "
        "local court rules, and flags sensitive personal identifiers. It does NOT "
        "constitute legal advice, litigation strategy, or a judicial determination. "
        "Absence of an authority in a public database does not conclusively establish "
        "fabrication. Licensed legal counsel must independently review all findings."
    )
    disclaimer_table = Table(
        [[Paragraph(disclaimer_text, styles["Disclaimer"])]],
        colWidths=[504],
    )
    disclaimer_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), _COLOR_WARN_BG),
                ("BOX", (0, 0), (-1, -1), 1, _COLOR_WARN_BORDER),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    story.append(disclaimer_table)
    story.append(Spacer(1, 12))

    # Overall Integrity Score & Coverage Summary
    score = results.get("score", {})
    score_val = score.get("value")
    score_display = f"{score_val}/100" if score_val is not None else "Unavailable (Provisional)"
    risk_level = str(score.get("risk_level", "uncalibrated")).upper()

    cov = results.get("coverage", {})
    cov_text = (
        f"Evaluated: <b>{cov.get('evaluated', 0)}/{cov.get('eligible', 0)}</b> eligible checks | "
        f"Unavailable: {cov.get('unavailable', 0)} | Pending: {cov.get('pending', 0)} | "
        f"Truncated: {'Yes' if cov.get('truncated') else 'No'}"
    )

    score_card_data = [
        [
            Paragraph("<b>Integrity Score:</b>", styles["TableCell"]),
            Paragraph(f"<b>{score_display}</b> (Risk: {risk_level})", styles["TableCell"]),
            Paragraph("<b>Coverage:</b>", styles["TableCell"]),
            Paragraph(cov_text, styles["TableCell"]),
        ]
    ]
    score_table = Table(score_card_data, colWidths=[90, 162, 70, 182])
    score_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), _COLOR_ACCENT),
                ("BOX", (0, 0), (-1, -1), 1, _COLOR_SECONDARY),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(score_table)
    story.append(Spacer(1, 14))
    story.extend(graph_pdf_flowables(results, styles))

    # Stage Coverage Breakdown Table
    story.append(Paragraph("Verification Stage Coverage", styles["Heading1"]))
    stages_data = [
        [
            Paragraph("Stage Name", styles["TableHeader"]),
            Paragraph("Status", styles["TableHeader"]),
            Paragraph("Coverage (Eval/Elig)", styles["TableHeader"]),
            Paragraph("Diagnostic Details", styles["TableHeader"]),
        ]
    ]
    for s in results.get("stages", []):
        sc = s.get("coverage", {})
        cov_str = f"{sc.get('evaluated', 0)}/{sc.get('eligible', 0)}"
        stages_data.append(
            [
                Paragraph(escape(s.get("name", "").replace("_", " ").title()), styles["TableCell"]),
                Paragraph(f"<b>{escape(s.get('status', '').upper())}</b>", styles["TableCell"]),
                Paragraph(cov_str, styles["TableCell"]),
                Paragraph(escape(s.get("reason") or "Complete"), styles["TableCell"]),
            ]
        )
    stages_table = Table(stages_data, colWidths=[110, 80, 100, 214])
    stages_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), _COLOR_PRIMARY),
                ("GRID", (0, 0), (-1, -1), 0.5, _COLOR_BORDER),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, _COLOR_INFO_BG]),
            ]
        )
    )
    story.append(stages_table)
    story.append(Spacer(1, 14))

    # Findings Section (with Evidence & 5-Hop Lineage Chain)
    findings = results.get("findings", [])
    story.append(Paragraph(f"Forensic Findings ({len(findings)})", styles["Heading1"]))

    if not findings:
        story.append(
            Paragraph(
                "<i>No compliance issues or citation anomalies were flagged.</i>",
                styles["Body"],
            )
        )
    else:
        for idx, f in enumerate(findings, 1):
            sev = f.get("severity", "info").lower()
            sev_color = _SEVERITY_COLORS.get(sev, _COLOR_MUTED)
            ai_flag = "AI-Assisted" if f.get("ai_assisted") else "Deterministic Check"

            finding_flowables = []

            # Finding Header
            f_title = f"#{idx} [{sev.upper()}] {f.get('title', 'Finding')}"
            finding_flowables.append(
                Paragraph(
                    f"<font color='{sev_color.hexval()}'><b>{escape(f_title)}</b></font> · "
                    f"<i>{ai_flag}</i>",
                    styles["Heading2"],
                )
            )

            # Description
            finding_flowables.append(Paragraph(escape(f.get("description", "")), styles["Body"]))

            # Excerpt Box
            if f.get("masked_excerpt"):
                span_str = (
                    f"offsets {f['start']}–{f['end']} (Unicode code points)"
                    if f.get("start") is not None
                    else "Document scope"
                )
                excerpt_content = (
                    f"<b>Filing Excerpt ({span_str}):</b><br/>"
                    f"\"{escape(f['masked_excerpt'])}\""
                )
                excerpt_table = Table(
                    [[Paragraph(excerpt_content, styles["TableCell"])]],
                    colWidths=[500],
                )
                excerpt_table.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                            ("LEFTPADDING", (0, 0), (-1, -1), 6),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                            ("TOPPADDING", (0, 0), (-1, -1), 4),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                        ]
                    )
                )
                finding_flowables.append(excerpt_table)
                finding_flowables.append(Spacer(1, 4))

            # 5-Hop Lineage Chain
            lineage_lines = [
                f"<b>01 Document Span:</b> offsets {f.get('start', 'N/A')}–{f.get('end', 'N/A')}",
                (
                    "<b>02 Extraction Target:</b> "
                    f"{escape(f.get('type', '').replace('_', ' ').title())}"
                ),
            ]

            evidence_items = f.get("evidence", [])
            if evidence_items:
                ev0 = evidence_items[0]
                auth_link = ev0.get("source_url") or "Stored snapshot"
                sha = ev0.get("source_sha256", "N/A")
                sha_short = sha[:16] + "…" if len(sha) > 16 else sha
                lineage_lines.append(
                    f"<b>03 Source Authority:</b> {escape(auth_link)} "
                    f"(SHA-256: {escape(sha_short)})"
                )
                lineage_lines.append(
                    f"<b>04 Verification Method:</b> {escape(ev0.get('method_version', 'N/A'))} "
                    f"[Provenance: {escape(str(ev0.get('provenance', 'N/A')))}]"
                )
            else:
                lineage_lines.append("<b>03 Source Authority:</b> Filing / local rule registry")
                lineage_lines.append(
                    "<b>04 Verification Method:</b> Deterministic "
                    f"{escape(f.get('type', 'rule'))} rule evaluation"
                )

            lineage_lines.append(
                f"<b>05 Finding Verdict:</b> {sev.upper()} · {escape(f.get('title', ''))}"
            )

            lineage_table = Table(
                [[Paragraph("<br/>".join(lineage_lines), styles["TableCell"])]],
                colWidths=[500],
            )
            lineage_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, -1), _COLOR_INFO_BG),
                        ("BOX", (0, 0), (-1, -1), 0.5, _COLOR_BORDER),
                        ("LEFTPADDING", (0, 0), (-1, -1), 6),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                        ("TOPPADDING", (0, 0), (-1, -1), 4),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ]
                )
            )
            finding_flowables.append(lineage_table)

            # Evidence passages
            if evidence_items:
                for ev in evidence_items:
                    ev_text = (
                        f"<b>Retrieved Source Passage:</b> \"{escape(ev.get('excerpt', ''))}\"<br/>"
                        f"<font color='#6a5a7d'>Source offsets: {ev.get('source_start')}–"
                        f"{ev.get('source_end')} | SHA-256: {ev.get('source_sha256')}</font>"
                    )
                    ev_table = Table([[Paragraph(ev_text, styles["Muted"])]], colWidths=[500])
                    ev_table.setStyle(
                        TableStyle(
                            [
                                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f1f5f9")),
                                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#94a3b8")),
                                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                                ("TOPPADDING", (0, 0), (-1, -1), 3),
                                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                            ]
                        )
                    )
                    finding_flowables.append(Spacer(1, 3))
                    finding_flowables.append(ev_table)

            finding_flowables.append(Spacer(1, 8))
            story.append(KeepTogether(finding_flowables))

    # Citations Table
    citations = results.get("citations", [])
    if citations:
        story.append(Spacer(1, 10))
        story.append(
            Paragraph(f"Citation Verification Records ({len(citations)})", styles["Heading1"])
        )
        cit_data = [
            [
                Paragraph("Citation Text", styles["TableHeader"]),
                Paragraph("Status", styles["TableHeader"]),
                Paragraph("Authority / Source Details", styles["TableHeader"]),
            ]
        ]
        for c in citations:
            auth = c.get("authority") or {}
            auth_info = (
                f"{escape(auth.get('case_name') or 'N/A')}<br/>"
                f"<font color='#5d2f96'>"
                f"{escape(auth.get('source_url') or 'Stored snapshot')}</font>"
            )
            cit_data.append(
                [
                    Paragraph(escape(c.get("masked_raw_text", "")), styles["TableCell"]),
                    Paragraph(
                        f"<b>{escape(c.get('verification_status', '').upper())}</b>",
                        styles["TableCell"],
                    ),
                    Paragraph(auth_info, styles["TableCell"]),
                ]
            )
        cit_table = Table(cit_data, colWidths=[150, 90, 264])
        cit_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), _COLOR_PRIMARY),
                    ("GRID", (0, 0), (-1, -1), 0.5, _COLOR_BORDER),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, _COLOR_INFO_BG]),
                ]
            )
        )
        story.append(cit_table)

    # Build the PDF using NumberedCanvas
    doc.build(story, canvasmaker=NumberedCanvas)
    buffer.seek(0)
    return buffer.getvalue()
