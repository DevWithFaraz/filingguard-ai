"""Server-side Claim-Authority Graph images from the saved graph, not a second graph."""

from __future__ import annotations

import io
import textwrap
from dataclasses import dataclass
from html import escape
from typing import Any
from urllib.parse import quote
from xml.sax.saxutils import escape as xml_escape

from reportlab.lib.colors import HexColor
from reportlab.platypus import Flowable, Paragraph, Spacer

GRAPH_DISCLAIMER = (
    "This figure is a review graph of stored claim–authority relationships. "
    "It is not a legal conclusion."
)

PAGE_WIDTH = 980
PAGE_HEIGHT = 720
HEADER_HEIGHT = 92
LEFT = 28
NODE_WIDTH = 268
COL_GAP = 54
ROW_GAP = 18
NODE_PAD_X = 10
NODE_PAD_Y = 10
LINE_HEIGHT = 16
FONT_SIZE = 11
KIND_SIZE = 9
MAX_LABEL_WIDTH = 32
KIND_COLUMNS = {"section": 0, "claim": 1, "authority": 2}

_STATUS_COLORS = {
    "supported": ("#ecfdf3", "#15803d"),
    "verified": ("#ecfdf3", "#15803d"),
    "unsupported": ("#fff1f2", "#be123c"),
    "contradicted": ("#fff1f2", "#be123c"),
    "misrepresented": ("#fff1f2", "#be123c"),
    "warning": ("#fff1f2", "#be123c"),
    "heuristic": ("#fffbeb", "#b45309"),
    "unclear": ("#fffbeb", "#b45309"),
    "not_run": ("#faf7ff", "#6a5a7d"),
    "extracted": ("#faf7ff", "#5d2f96"),
    "unavailable": ("#f8fafc", "#475569"),
}


@dataclass(frozen=True)
class GraphBox:
    node: dict[str, Any]
    x: float
    y: float
    width: float
    height: float
    lines: tuple[str, ...]


@dataclass(frozen=True)
class GraphPage:
    index: int
    count: int
    width: float
    height: float
    boxes: tuple[GraphBox, ...]
    edges: tuple[dict[str, Any], ...]
    continued: int


def _nodes(graph: dict[str, Any] | None) -> list[dict[str, Any]]:
    return list((graph or {}).get("nodes") or [])


def _edges(graph: dict[str, Any] | None) -> list[dict[str, Any]]:
    return list((graph or {}).get("edges") or [])


def wrap_label(text: str, width: int = MAX_LABEL_WIDTH) -> list[str]:
    cleaned = " ".join(str(text or "").split())
    if not cleaned:
        return [""]
    return textwrap.wrap(cleaned, width=width, break_long_words=True, replace_whitespace=False) or [
        cleaned
    ]


def _status_colors(status: str) -> tuple[str, str]:
    return _STATUS_COLORS.get(str(status).lower(), ("#ffffff", "#2b1f3d"))


def _column_x(kind: str) -> float:
    return LEFT + KIND_COLUMNS.get(kind, 1) * (NODE_WIDTH + COL_GAP)


def layout_graph_pages(graph: dict[str, Any] | None) -> list[GraphPage]:
    nodes = _nodes(graph)
    edges = _edges(graph)
    if not nodes:
        empty = GraphPage(1, 1, PAGE_WIDTH, 180, (), (), 0)
        return [empty]

    cursor = {kind: HEADER_HEIGHT for kind in KIND_COLUMNS}
    boxes: list[GraphBox] = []
    for node in nodes:
        kind = node.get("kind") if node.get("kind") in KIND_COLUMNS else "claim"
        label_lines = wrap_label(str(node.get("label") or ""))
        lines = (str(kind).replace("_", " ").title(), *label_lines, f"status: {node.get('status')}")
        height = NODE_PAD_Y * 2 + KIND_SIZE + 4 + LINE_HEIGHT * (len(lines) - 1)
        height = max(height, 76)
        y = cursor[kind]
        boxes.append(
            GraphBox(node, _column_x(kind), y, NODE_WIDTH, height, tuple(lines))
        )
        cursor[kind] = y + height + ROW_GAP

    body = PAGE_HEIGHT - HEADER_HEIGHT - 24
    pages: list[list[GraphBox]] = []
    current: list[GraphBox] = []
    origin_y: float | None = None
    for box in sorted(boxes, key=lambda item: (item.y, item.x)):
        if origin_y is None:
            origin_y = box.y
        if current and (box.y + box.height) - origin_y > body:
            pages.append(current)
            current = [box]
            origin_y = box.y
        else:
            current.append(box)
    if current:
        pages.append(current)

    rendered: list[GraphPage] = []
    count = max(len(pages), 1)
    by_id_pages: dict[str, int] = {}
    for index, page_boxes in enumerate(pages, start=1):
        for box in page_boxes:
            by_id_pages[str(box.node.get("id"))] = index
    for index, page_boxes in enumerate(pages, start=1):
        origin = min((box.y for box in page_boxes), default=HEADER_HEIGHT)
        shifted = tuple(
            GraphBox(
                box.node,
                box.x,
                HEADER_HEIGHT + (box.y - origin),
                box.width,
                box.height,
                box.lines,
            )
            for box in page_boxes
        )
        ids = {str(box.node.get("id")) for box in shifted}
        page_edges = tuple(
            edge
            for edge in edges
            if str(edge.get("source")) in ids and str(edge.get("target")) in ids
        )
        continued = sum(
            1
            for edge in edges
            if by_id_pages.get(str(edge.get("source"))) == index
            and by_id_pages.get(str(edge.get("target"))) not in {None, index}
        )
        height = max((box.y + box.height for box in shifted), default=HEADER_HEIGHT) + 28
        rendered.append(
            GraphPage(index, count, PAGE_WIDTH, height, shifted, page_edges, continued)
        )
    return rendered


def accessible_graph_markdown(graph: dict[str, Any] | None) -> str:
    nodes = _nodes(graph)
    edges = _edges(graph)
    by_id = {str(node.get("id")): node for node in nodes}
    lines = [
        "## Claim-Authority Graph",
        "",
        GRAPH_DISCLAIMER,
        "",
        f"Stored nodes: {len(nodes)}. Stored relationships: {len(edges)}.",
        "",
        "### Accessible equivalent",
        "",
        "#### Nodes",
    ]
    if not nodes:
        lines.append("- No stored section, claim, or authority nodes.")
    for node in nodes:
        lines.append(
            f"- {node.get('kind')}: {node.get('label')} "
            f"(id: {node.get('id')}; status: {node.get('status')})"
        )
    lines.extend(["", "#### Relationships"])
    if not edges:
        lines.append("- No stored relationships.")
    for edge in edges:
        source = by_id.get(str(edge.get("source")), {})
        target = by_id.get(str(edge.get("target")), {})
        lines.append(
            f"- {source.get('kind', 'node')} {source.get('label', edge.get('source'))} "
            f"— {edge.get('label')} → "
            f"{target.get('kind', 'node')} {target.get('label', edge.get('target'))}"
        )
    return "\n".join(lines)


def graph_alt_text(graph: dict[str, Any] | None, page: GraphPage) -> str:
    parts = [
        f"Claim-Authority Graph page {page.index} of {page.count}. {GRAPH_DISCLAIMER}",
    ]
    if not page.boxes:
        parts.append("No stored graph nodes.")
    for box in page.boxes:
        node = box.node
        parts.append(f"{node.get('kind')} {node.get('label')}; status {node.get('status')}.")
    for edge in page.edges:
        parts.append(f"Relationship {edge.get('label')}.")
    return " ".join(parts)[:1400]


def render_graph_page_svg(graph: dict[str, Any] | None, page: GraphPage) -> str:
    alt = xml_escape(graph_alt_text(graph, page))
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{page.width}" height="{page.height}" '
        f'viewBox="0 0 {page.width} {page.height}" role="img" aria-label="{alt}">',
        f"<title>{alt}</title>",
        '<rect width="100%" height="100%" fill="#faf7ff"/>',
        '<text x="28" y="28" font-family="Helvetica, Arial, sans-serif" font-size="16" '
        'font-weight="bold" fill="#2b1f3d">Claim-Authority Graph</text>',
        '<text x="28" y="48" font-family="Helvetica, Arial, sans-serif" '
        f'font-size="11" fill="#5d2f96">Page {page.index} of {page.count}</text>',
    ]
    disclaimer_lines = wrap_label(GRAPH_DISCLAIMER, width=96)
    for index, line in enumerate(disclaimer_lines):
        parts.append(
            '<text x="28" y="'
            + str(68 + index * 14)
            + '" font-family="Helvetica, Arial, sans-serif" font-size="11" fill="#6a5a7d">'
            + xml_escape(line)
            + "</text>"
        )
    centers = {
        str(box.node.get("id")): (box.x + box.width / 2, box.y + box.height / 2, box)
        for box in page.boxes
    }
    for edge in page.edges:
        source = centers.get(str(edge.get("source")))
        target = centers.get(str(edge.get("target")))
        if not source or not target:
            continue
        _sx, sy, sbox = source
        _tx, ty, tbox = target
        x1 = sbox.x + sbox.width
        x2 = tbox.x
        parts.append(
            f'<line x1="{x1:.1f}" y1="{sy:.1f}" x2="{x2:.1f}" y2="{ty:.1f}" '
            'stroke="#a789c7" stroke-width="1.5"/>'
        )
        mx, my = (x1 + x2) / 2, (sy + ty) / 2 - 4
        parts.append(
            f'<text x="{mx:.1f}" y="{my:.1f}" text-anchor="middle" '
            'font-family="Helvetica, Arial, sans-serif" font-size="10" fill="#5d2f96">'
            + xml_escape(str(edge.get("label") or ""))
            + "</text>"
        )
    for box in page.boxes:
        fill, stroke = _status_colors(str(box.node.get("status") or ""))
        parts.append(
            f'<rect x="{box.x:.1f}" y="{box.y:.1f}" width="{box.width:.1f}" '
            f'height="{box.height:.1f}" rx="10" fill="{fill}" stroke="{stroke}" '
            'stroke-width="1.6"/>'
        )
        text_x = box.x + NODE_PAD_X
        y = box.y + NODE_PAD_Y + 12
        for index, line in enumerate(box.lines):
            size = KIND_SIZE if index == 0 else FONT_SIZE
            weight = "bold" if index == 0 else "normal"
            fill = stroke if index == 0 else "#1a1622"
            parts.append(
                f'<text x="{text_x:.1f}" y="{y:.1f}" font-family="Helvetica, Arial, sans-serif" '
                f'font-size="{size}" font-weight="{weight}" fill="{fill}">'
                + xml_escape(line)
                + "</text>"
            )
            y += LINE_HEIGHT if index else KIND_SIZE + 6
    if not page.boxes:
        parts.append(
            '<text x="28" y="120" font-family="Helvetica, Arial, sans-serif" font-size="13" '
            'fill="#2b1f3d">No stored section, claim, or authority nodes.</text>'
        )
    if page.continued:
        parts.append(
            f'<text x="28" y="{page.height - 12:.1f}" font-family="Helvetica, Arial, sans-serif" '
            'font-size="10" fill="#6a5a7d">'
            + xml_escape(
                f"{page.continued} relationship(s) continue on another graph page; "
                "see the accessible node and relationship list."
            )
            + "</text>"
        )
    parts.append("</svg>")
    return "".join(parts)


def render_graph_svg_document(graph: dict[str, Any] | None) -> str:
    pages = layout_graph_pages(graph)
    if len(pages) == 1:
        return render_graph_page_svg(graph, pages[0])
    gap = 24
    total_h = sum(page.height for page in pages) + gap * (len(pages) - 1)
    width = max(page.width for page in pages)
    chunks = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{total_h}" '
        f'viewBox="0 0 {width} {total_h}" role="img" '
        f'aria-label="{xml_escape(GRAPH_DISCLAIMER)}">'
    ]
    y = 0.0
    for page in pages:
        inner = render_graph_page_svg(graph, page)
        inner_body = inner[inner.find(">") + 1 : inner.rfind("</svg>")]
        chunks.append(f'<g transform="translate(0 {y:.1f})">{inner_body}</g>')
        y += page.height + gap
    chunks.append("</svg>")
    return "".join(chunks)


def graph_data_uri(svg: str) -> str:
    return "data:image/svg+xml;charset=utf-8," + quote(svg, safe="")


def graph_html_figures(graph: dict[str, Any] | None) -> str:
    pages = layout_graph_pages(graph)
    figures = []
    for page in pages:
        svg = render_graph_page_svg(graph, page)
        alt = escape(graph_alt_text(graph, page))
        caption = escape(
            f"Claim-Authority Graph, page {page.index} of {page.count}. {GRAPH_DISCLAIMER}"
        )
        figures.append(
            "<figure>"
            f'<img alt="{alt}" src="{graph_data_uri(svg)}" '
            f'width="{int(page.width)}" height="{int(page.height)}"/>'
            f"<figcaption>{caption}</figcaption>"
            "</figure>"
        )
    return "".join(figures)


def _png_font(size: int):
    from pathlib import Path

    from PIL import ImageFont

    candidates = [
        Path(r"C:\Windows\Fonts\arial.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"),
        Path("/usr/share/fonts/truetype/freefont/FreeSans.ttf"),
        Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
    ]
    for path in candidates:
        if path.exists():
            return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default()


def render_graph_png(graph: dict[str, Any] | None) -> bytes:
    from PIL import Image, ImageDraw

    pages = layout_graph_pages(graph)
    scale = 2
    rasters = []
    title_font = _png_font(28)
    body_font = _png_font(18)
    small_font = _png_font(16)
    for page in pages:
        image = Image.new(
            "RGB",
            (int(page.width * scale), int(page.height * scale)),
            "#faf7ff",
        )
        draw = ImageDraw.Draw(image)

        def px(value: float) -> int:
            return int(value * scale)

        draw.text((px(28), px(12)), "Claim-Authority Graph", fill="#2b1f3d", font=title_font)
        draw.text(
            (px(28), px(34)),
            f"Page {page.index} of {page.count}",
            fill="#5d2f96",
            font=small_font,
        )
        y = 54
        for line in wrap_label(GRAPH_DISCLAIMER, width=96):
            draw.text((px(28), px(y)), line, fill="#6a5a7d", font=small_font)
            y += 14
        centers = {
            str(box.node.get("id")): (box.x + box.width, box.y + box.height / 2, box)
            for box in page.boxes
        }
        for edge in page.edges:
            source = centers.get(str(edge.get("source")))
            target = centers.get(str(edge.get("target")))
            if not source or not target:
                continue
            x1, sy, _sbox = source
            _tx, ty, tbox = target
            draw.line(
                [(px(x1), px(sy)), (px(tbox.x), px(ty))],
                fill="#a789c7",
                width=3,
            )
            mx, my = (x1 + tbox.x) / 2, (sy + ty) / 2 - 8
            label = str(edge.get("label") or "")
            draw.text((px(mx - 4 * len(label) / 2), px(my)), label, fill="#5d2f96", font=small_font)
        if not page.boxes:
            draw.text(
                (px(28), px(110)),
                "No stored section, claim, or authority nodes.",
                fill="#2b1f3d",
                font=body_font,
            )
        for box in page.boxes:
            fill, stroke = _status_colors(str(box.node.get("status") or ""))
            draw.rounded_rectangle(
                [px(box.x), px(box.y), px(box.x + box.width), px(box.y + box.height)],
                radius=12,
                fill=fill,
                outline=stroke,
                width=3,
            )
            text_y = box.y + NODE_PAD_Y
            for index, line in enumerate(box.lines):
                draw.text(
                    (px(box.x + NODE_PAD_X), px(text_y)),
                    line,
                    fill=stroke if index == 0 else "#1a1622",
                    font=small_font if index == 0 else body_font,
                )
                text_y += LINE_HEIGHT if index else KIND_SIZE + 6
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        rasters.append(buffer.getvalue())

    if len(rasters) == 1:
        return rasters[0]
    images = [Image.open(io.BytesIO(data)).convert("RGB") for data in rasters]
    width = max(image.width for image in images)
    height = sum(image.height for image in images) + 16 * (len(images) - 1)
    stacked = Image.new("RGB", (width, height), "#faf7ff")
    y = 0
    for image in images:
        stacked.paste(image, (0, y))
        y += image.height + 16
    buffer = io.BytesIO()
    stacked.save(buffer, format="PNG")
    return buffer.getvalue()


class GraphPageFlowable(Flowable):
    """Draw one saved-graph page with ReportLab so PDF text stays selectable."""

    def __init__(self, page: GraphPage, max_width: float):
        super().__init__()
        self.page = page
        self.max_width = max_width
        self.scale = min(1.0, max_width / page.width)
        self.width = page.width * self.scale
        self.height = page.height * self.scale

    def wrap(self, availWidth, availHeight):
        self.scale = min(1.0, min(availWidth, self.max_width) / self.page.width)
        self.width = self.page.width * self.scale
        self.height = self.page.height * self.scale
        return self.width, self.height

    def draw(self):
        canv = self.canv
        scale = self.scale
        page = self.page
        canv.setFillColor(HexColor("#faf7ff"))
        canv.rect(0, 0, self.width, self.height, fill=1, stroke=0)

        def y_up(svg_y: float, height: float = 0) -> float:
            return (page.height - svg_y - height) * scale

        canv.setFillColor(HexColor("#2b1f3d"))
        canv.setFont("Helvetica-Bold", 11)
        canv.drawString(12, y_up(28) - 4, "Claim-Authority Graph")
        canv.setFillColor(HexColor("#5d2f96"))
        canv.setFont("Helvetica", 8)
        canv.drawString(12, y_up(46) - 4, f"Page {page.index} of {page.count}")
        canv.setFillColor(HexColor("#6a5a7d"))
        text_y = 64
        for line in wrap_label(GRAPH_DISCLAIMER, width=88):
            canv.drawString(12, y_up(text_y) - 4, line)
            text_y += 12
        centers = {
            str(box.node.get("id")): (box.x + box.width, box.y + box.height / 2, box)
            for box in page.boxes
        }
        canv.setStrokeColor(HexColor("#a789c7"))
        canv.setLineWidth(1)
        canv.setFillColor(HexColor("#5d2f96"))
        canv.setFont("Helvetica", 7)
        for edge in page.edges:
            source = centers.get(str(edge.get("source")))
            target = centers.get(str(edge.get("target")))
            if not source or not target:
                continue
            x1, sy, _sbox = source
            _tx, ty, tbox = target
            canv.line(x1 * scale, y_up(sy), tbox.x * scale, y_up(ty))
            mx = (x1 + tbox.x) / 2 * scale
            my = y_up((sy + ty) / 2 - 3)
            canv.drawCentredString(mx, my, str(edge.get("label") or ""))
        if not page.boxes:
            canv.setFillColor(HexColor("#2b1f3d"))
            canv.setFont("Helvetica", 9)
            canv.drawString(12, y_up(110), "No stored section, claim, or authority nodes.")
        for box in page.boxes:
            fill, stroke = _status_colors(str(box.node.get("status") or ""))
            canv.setFillColor(HexColor(fill))
            canv.setStrokeColor(HexColor(stroke))
            canv.roundRect(
                box.x * scale,
                y_up(box.y, box.height),
                box.width * scale,
                box.height * scale,
                6,
                fill=1,
                stroke=1,
            )
            text_y = box.y + NODE_PAD_Y + 11
            for index, line in enumerate(box.lines):
                canv.setFillColor(HexColor(stroke if index == 0 else "#1a1622"))
                font_name = "Helvetica-Bold" if index == 0 else "Helvetica"
                canv.setFont(font_name, 7 if index == 0 else 8)
                canv.drawString((box.x + NODE_PAD_X) * scale, y_up(text_y) - 2, line)
                text_y += 12 if index else 11


def graph_pdf_flowables(results: dict[str, Any], styles: dict) -> list:
    graph = results.get("graph") or {"nodes": [], "edges": []}
    pages = layout_graph_pages(graph)
    story: list = [
        Paragraph("Claim-Authority Graph", styles["Heading1"]),
        Paragraph(escape(GRAPH_DISCLAIMER), styles["Disclaimer"]),
        Spacer(1, 6),
    ]
    for page in pages:
        caption = (
            f"Claim-Authority Graph, page {page.index} of {page.count}. {GRAPH_DISCLAIMER}"
        )
        block = [
            GraphPageFlowable(page, 504),
            Spacer(1, 4),
            Paragraph(escape(caption), styles["Muted"]),
            Spacer(1, 8),
        ]
        story.extend(block)
    accessible = accessible_graph_markdown(graph).splitlines()
    story.append(Paragraph("Accessible graph equivalent", styles["Heading2"]))
    for line in accessible:
        if line.startswith("#"):
            continue
        if line:
            story.append(Paragraph(escape(line), styles["Body"]))
    story.append(Spacer(1, 10))
    return story


def markdown_graph_section(results: dict[str, Any]) -> str:
    graph = results.get("graph") or {"nodes": [], "edges": []}
    pages = layout_graph_pages(graph)
    lines = [accessible_graph_markdown(graph), ""]
    for page in pages:
        svg = render_graph_page_svg(graph, page)
        alt = graph_alt_text(graph, page)
        caption = f"Claim-Authority Graph, page {page.index} of {page.count}. {GRAPH_DISCLAIMER}"
        lines.append(
            f'<figure><img alt="{escape(alt)}" src="{graph_data_uri(svg)}"/>'
            f"<figcaption>{escape(caption)}</figcaption></figure>"
        )
        lines.append("")
    return "\n".join(lines)
