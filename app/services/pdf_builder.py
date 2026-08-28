from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Any

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import ListFlowable, ListItem, Paragraph, SimpleDocTemplate, Spacer

from app.services.cv_render import contact_line, format_month, load_cv, section_labels

INK = HexColor("#1a2332")


def _register_fonts() -> tuple[str, str]:
    """Return (body_font, heading_font). Prefer Calibri/Arial, else Helvetica."""
    candidates = [
        # macOS
        ("/System/Library/Fonts/Supplemental/Arial.ttf", "ArialLocal"),
        ("/Library/Fonts/Arial.ttf", "ArialLocal"),
        ("/System/Library/Fonts/Supplemental/Calibri.ttf", "CalibriLocal"),
        # Linux
        ("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", "LiberationSans"),
        ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "DejaVuSans"),
        # Windows
        ("C:/Windows/Fonts/arial.ttf", "ArialWin"),
        ("C:/Windows/Fonts/calibri.ttf", "CalibriWin"),
    ]
    registered: list[str] = []
    for path, name in candidates:
        p = Path(path)
        if p.exists():
            try:
                pdfmetrics.registerFont(TTFont(name, str(p)))
                registered.append(name)
            except Exception:
                continue
    if registered:
        body = registered[0]
        heading = registered[0]
        return body, heading
    return "Helvetica", "Helvetica-Bold"


def build_pdf(facts: dict[str, Any], path: Path | None = None) -> bytes:
    cv = load_cv(facts)
    labels = section_labels(cv.language)
    body_font, _heading_unused = _register_fonts()
    head_font = "Helvetica-Bold" if body_font == "Helvetica" else body_font

    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=2.0 * cm,
        rightMargin=2.0 * cm,
        topMargin=1.8 * cm,
        bottomMargin=1.8 * cm,
    )
    styles = getSampleStyleSheet()
    name_style = ParagraphStyle(
        "CVName",
        parent=styles["Normal"],
        fontName=head_font,
        fontSize=16,
        leading=20,
        textColor=INK,
        spaceAfter=4,
    )
    meta_style = ParagraphStyle(
        "CVMeta",
        parent=styles["Normal"],
        fontName=body_font,
        fontSize=10.5,
        leading=14,
        textColor=INK,
        spaceAfter=10,
    )
    h_style = ParagraphStyle(
        "CVH",
        parent=styles["Normal"],
        fontName=head_font,
        fontSize=12,
        leading=16,
        textColor=INK,
        spaceBefore=12,
        spaceAfter=6,
    )
    body_style = ParagraphStyle(
        "CVBody",
        parent=styles["Normal"],
        fontName=body_font,
        fontSize=11,
        leading=14,
        textColor=INK,
        spaceAfter=3,
    )
    bold_body = ParagraphStyle(
        "CVBold",
        parent=body_style,
        fontName=head_font,
    )

    story: list[Any] = []
    story.append(Paragraph(_esc(cv.personal.full_name), name_style))
    contact = contact_line(cv)
    if contact:
        story.append(Paragraph(_esc(contact), meta_style))

    if cv.summary.strip():
        story.append(Paragraph(_esc(labels["profile"]), h_style))
        story.append(Paragraph(_esc(cv.summary.strip()), body_style))

    story.append(Paragraph(_esc(labels["experience"]), h_style))
    for exp in cv.experience:
        head = ", ".join(x for x in (exp.title, exp.employer, exp.location) if x)
        story.append(Paragraph(_esc(head), bold_body))
        period = (
            f"{format_month(exp.start, cv.language)} – "
            f"{format_month(exp.end, cv.language)}"
        )
        story.append(Paragraph(_esc(period), meta_style))
        items = []
        for b in exp.bullets:
            items.append(ListItem(Paragraph(_esc(b.text), body_style), leftIndent=10))
        if items:
            story.append(ListFlowable(items, bulletType="bullet", leftIndent=12))
        story.append(Spacer(1, 6))

    if cv.education:
        story.append(Paragraph(_esc(labels["education"]), h_style))
        for edu in cv.education:
            bits = [edu.degree, edu.institution, edu.field]
            story.append(Paragraph(_esc(", ".join(x for x in bits if x)), body_style))

    if cv.skills:
        story.append(Paragraph(_esc(labels["skills"]), h_style))
        story.append(Paragraph(_esc(", ".join(s.name for s in cv.skills)), body_style))

    if cv.languages:
        story.append(Paragraph(_esc(labels["languages"]), h_style))
        story.append(
            Paragraph(
                _esc(", ".join(f"{lang.name} ({lang.level})" for lang in cv.languages)),
                body_style,
            )
        )

    if cv.certifications:
        story.append(Paragraph(_esc(labels["certifications"]), h_style))
        for c in cv.certifications:
            bit = c.name
            if c.year:
                bit += f" ({c.year})"
            if c.issuer:
                bit += f" — {c.issuer}"
            story.append(Paragraph(f"• {_esc(bit)}", body_style))

    doc.build(story)
    data = buf.getvalue()
    if path is not None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    return data


def _esc(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
