from __future__ import annotations

from typing import Any

from app.services.cv_render import contact_line, format_month, load_cv, section_labels


def build_txt(facts: dict[str, Any]) -> str:
    cv = load_cv(facts)
    labels = section_labels(cv.language)
    lines: list[str] = []

    lines.append(cv.personal.full_name)
    contact = contact_line(cv)
    if contact:
        lines.append(contact)
    lines.append("")
    lines.append("---")
    lines.append("")

    if cv.summary.strip():
        lines.append(labels["profile"].upper())
        lines.append(cv.summary.strip())
        lines.append("")

    lines.append(labels["experience"].upper())
    lines.append("")
    for exp in cv.experience:
        head = ", ".join(x for x in (exp.title, exp.employer, exp.location) if x)
        lines.append(head)
        period = (
            f"{format_month(exp.start, cv.language)} – "
            f"{format_month(exp.end, cv.language)}"
        )
        lines.append(period)
        for b in exp.bullets:
            lines.append(f"• {b.text}")
        lines.append("")

    if cv.education:
        lines.append(labels["education"].upper())
        lines.append("")
        for edu in cv.education:
            bits = [edu.degree, edu.institution, edu.field]
            lines.append(", ".join(x for x in bits if x))
            if edu.start or edu.end:
                lines.append(
                    f"{format_month(edu.start or '', cv.language)} – "
                    f"{format_month(edu.end or '', cv.language)}"
                )
            lines.append("")

    if cv.skills:
        lines.append(labels["skills"].upper())
        lines.append(", ".join(s.name for s in cv.skills))
        lines.append("")

    if cv.languages:
        lines.append(labels["languages"].upper())
        lines.append(", ".join(f"{lang.name} ({lang.level})" for lang in cv.languages))
        lines.append("")

    if cv.certifications:
        lines.append(labels["certifications"].upper())
        for c in cv.certifications:
            bit = c.name
            if c.year:
                bit += f" ({c.year})"
            if c.issuer:
                bit += f" — {c.issuer}"
            lines.append(f"• {bit}")
        lines.append("")

    return "\n".join(lines).strip() + "\n"
